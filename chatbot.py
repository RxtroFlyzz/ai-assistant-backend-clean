from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import os
import re
import resend

from dotenv import load_dotenv
from openai import OpenAI

from database import SessionLocal, engine
from models import Base, Client, Conversation, Message as MessageModel

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "superadmin123")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


# ── Migration automatique ─────────────────────────────────────────────────────
def run_migrations():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN state VARCHAR DEFAULT 'normal'"))
            conn.commit()
            print("Migration OK: colonne state ajoutee")
        except Exception:
            pass  # colonne deja existante

run_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── États de conversation ─────────────────────────────────────────────────────
# normal   → conversation normale
# proposed → l'IA a proposé un humain, on attend oui/non
# asking   → on attend les coordonnées du visiteur
# done     → coordonnées collectées, email envoyé
STATE_NORMAL   = "normal"
STATE_PROPOSED = "proposed"
STATE_ASKING   = "asking"
STATE_DONE     = "done"


# ── Messages fixes ────────────────────────────────────────────────────────────
HUMAN_PROPOSAL  = "Souhaitez-vous etre mis en relation avec un membre de notre equipe ?"
ASKING_CONTACT  = "Parfait ! Donnez-moi votre prenom et votre numero de telephone, notre equipe vous contactera rapidement."
HUMAN_CONFIRMED = "Merci ! Notre equipe va vous contacter tres rapidement. A bientot !"
DECLINED        = "Pas de probleme ! N hesitez pas si vous avez d autres questions."


# ── Détection demande humain (dans le message utilisateur) ───────────────────
HUMAN_REGEX = re.compile(
    r'\b(humain|assistant|conseiller|agent|support|contact|personne|'
    r'rappel|rappeler|rendez.?vous|rdv|prendre contact|devis|intervention|'
    r'technicien|plombier|electricien|quelqu.un|votre equipe|votre service)\b',
    re.IGNORECASE
)

# ── Détection si GPT propose spontanément un humain ──────────────────────────
GPT_PROPOSES_HUMAN = re.compile(
    r'(mettre en relation|vous contacter|vous rappeler|prendre rendez|'
    r'un devis|un technicien|notre equipe|nos conseillers|'
    r'un professionnel|un expert|contactez.nous)',
    re.IGNORECASE
)


def is_affirmative(text: str) -> bool:
    """
    Détecte si un message est affirmatif.
    Règle : affirmatif sauf si explicitement négatif.
    """
    t = text.strip().lower()
    if not t:
        return False

    # Explicitement négatif
    negative = re.compile(
        r'\b(non|no|nope|pas|jamais|nan|naan|nah|negative|'
        r'je ne veux pas|ca ne m interesse pas|sans suite)\b',
        re.IGNORECASE
    )
    if negative.search(t):
        return False

    # Réponse courte sans négation → affirmatif
    if len(t.split()) <= 8:
        return True

    # Réponse longue avec mots affirmatifs
    positive = re.compile(
        r'\b(oui|yes|ok|okay|ouais|yep|bien|super|parfait|'
        r'volontiers|svp|s.il vous plait|avec plaisir|'
        r'pourquoi pas|allez|go|tout a fait|absolument|'
        r'evidemment|bien sur|d accord|je veux|je voudrais|'
        r'je souhaite|je suis interesse|carrément)\b',
        re.IGNORECASE
    )
    return bool(positive.search(t))


# ── Gestion de l'état en base ─────────────────────────────────────────────────
def get_state(conv_id: str, db: Session) -> str:
    try:
        row = db.execute(
            text("SELECT state FROM conversations WHERE id = :id"),
            {"id": conv_id}
        ).fetchone()
        return row[0] if row and row[0] else STATE_NORMAL
    except Exception:
        return STATE_NORMAL


def set_state(conv_id: str, state: str, db: Session):
    try:
        db.execute(
            text("UPDATE conversations SET state = :s WHERE id = :id"),
            {"s": state, "id": conv_id}
        )
        db.commit()
    except Exception as e:
        print("SET_STATE ERROR:", e)


def save_message(conv_id: str, role: str, content: str, db: Session):
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role=role,
        content=content
    ))
    db.commit()


def bot_reply(text_content: str, conv_id: str, needs_human: bool = False):
    return {"reply": text_content, "conversation_id": conv_id, "needs_human": needs_human}


# ── Email ─────────────────────────────────────────────────────────────────────
def send_human_email(conv_id: str, contact_info: str, client_obj: Client):
    print("EMAIL START")
    if not client_obj.client_email:
        print("EMAIL SKIP: pas d email configure")
        return
    try:
        params = {
            "from": "Replai <noreply@gianluca-ai.fr>",
            "to": [client_obj.client_email],
            "subject": "Nouveau client a rappeler - " + client_obj.business_name,
            "html": (
                "<div style='font-family:Arial,sans-serif;max-width:600px'>"
                "<h2 style='color:#6366f1'>Nouveau client a rappeler</h2>"
                "<p><strong>Business :</strong> " + client_obj.business_name + "</p>"
                "<p><strong>Conversation :</strong> " + conv_id[:8] + "</p>"
                "<p><strong>Coordonnees :</strong> "
                "<span style='color:#4f8eff;font-weight:bold;font-size:16px'>"
                + contact_info +
                "</span></p>"
                "<p>Recontactez ce client rapidement !</p>"
                "<hr style='border:none;border-top:1px solid #eee'>"
                "<p style='color:#888;font-size:12px'>Replai — AI Widget pour TPEs</p>"
                "</div>"
            )
        }
        email = resend.Emails.send(params)
        print("EMAIL SENT:", email['id'])
    except Exception as e:
        print("EMAIL ERROR:", str(e))


# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    page_content: Optional[str] = None
    client_token: Optional[str] = None

class ContactHumanRequest(BaseModel):
    conversation_id: Optional[str] = None
    client_token: Optional[str] = None

class CreateClientRequest(BaseModel):
    business_name: str
    admin_password: str
    client_email: Optional[str] = None
    superadmin_password: str

class UpdateClientRequest(BaseModel):
    token: str
    superadmin_password: str
    system_prompt: Optional[str] = None
    business_name: Optional[str] = None
    admin_password: Optional[str] = None
    client_email: Optional[str] = None


# ── Super-admin ───────────────────────────────────────────────────────────────
@app.post("/superadmin/create-client")
def create_client(req: CreateClientRequest, db: Session = Depends(get_db)):
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    token = req.business_name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:6]
    new_client = Client(
        token=token,
        business_name=req.business_name,
        admin_password=req.admin_password,
        client_email=req.client_email
    )
    db.add(new_client)
    db.commit()
    return {
        "token": token,
        "business_name": req.business_name,
        "admin_url": "/admin?token=" + token,
        "widget_script": '<script src="https://ai-assistant-backend-clean-iz6y.onrender.com/static/ai-widget.js?token=' + token + '"></script>'
    }


@app.post("/superadmin/update-client")
def update_client(req: UpdateClientRequest, db: Session = Depends(get_db)):
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    c = db.query(Client).filter(Client.token == req.token).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if req.system_prompt is not None:
        c.system_prompt = req.system_prompt
    if req.business_name is not None:
        c.business_name = req.business_name
    if req.admin_password is not None:
        c.admin_password = req.admin_password
    if req.client_email is not None:
        c.client_email = req.client_email
    db.commit()
    return {"ok": True, "token": c.token}


@app.get("/superadmin/clients")
def list_clients(superadmin_password: str, db: Session = Depends(get_db)):
    if superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    return [{"token": c.token, "business_name": c.business_name, "client_email": c.client_email}
            for c in db.query(Client).all()]


# ── Dashboard Admin ───────────────────────────────────────────────────────────
ADMIN_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Replai Admin</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: #0f1117; color: #e2e8f0; height: 100vh; overflow: hidden; }
    #login { display: flex; align-items: center; justify-content: center; height: 100vh; }
    .card { background: #1a1d27; border: 1px solid #2d3148; border-radius: 16px; padding: 48px 40px; width: 380px; text-align: center; }
    .logo { width: 52px; height: 52px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 24px; }
    .card h2 { font-size: 22px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
    .card .sub { font-size: 14px; color: #64748b; margin-bottom: 28px; }
    .pwd-row { position: relative; margin-bottom: 12px; }
    .pwd-row input { width: 100%; padding: 12px 44px 12px 16px; background: #0f1117; border: 1px solid #2d3148; border-radius: 10px; color: #f1f5f9; font-size: 15px; font-family: 'Inter', sans-serif; outline: none; }
    .pwd-row input:focus { border-color: #6366f1; }
    .eye { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 16px; user-select: none; }
    .btn-login { width: 100%; padding: 13px; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-login:hover { opacity: 0.9; }
    .err { color: #f87171; font-size: 13px; margin-top: 12px; padding: 10px; background: rgba(127,29,29,0.2); border: 1px solid #7f1d1d; border-radius: 8px; display: none; }
    #dashboard { display: none; height: 100vh; }
    .layout { display: flex; height: 100vh; }
    .sidebar { width: 280px; background: #1a1d27; border-right: 1px solid #2d3148; display: flex; flex-direction: column; }
    .sb-top { padding: 20px; border-bottom: 1px solid #2d3148; }
    .brand { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
    .brand-icon { width: 32px; height: 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 15px; }
    .brand-name { font-size: 15px; font-weight: 600; color: #f1f5f9; }
    .stats { display: flex; gap: 8px; }
    .stat { background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; padding: 8px 10px; flex: 1; text-align: center; }
    .stat-n { display: block; font-size: 18px; font-weight: 700; color: #f1f5f9; }
    .stat-l { font-size: 11px; color: #64748b; }
    .sb-mid { padding: 12px 16px; border-bottom: 1px solid #2d3148; display: flex; flex-direction: column; gap: 8px; }
    .search-input { width: 100%; padding: 8px 12px; background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; color: #f1f5f9; font-size: 13px; font-family: 'Inter', sans-serif; outline: none; }
    .search-input:focus { border-color: #6366f1; }
    .btn-refresh { width: 100%; padding: 9px; background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; color: #94a3b8; font-size: 13px; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-refresh:hover { border-color: #6366f1; color: #6366f1; }
    .conv-list { flex: 1; overflow-y: auto; padding: 8px; }
    .conv-list::-webkit-scrollbar { width: 3px; }
    .conv-list::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }
    .ci { padding: 12px 14px; border-radius: 10px; margin-bottom: 4px; cursor: pointer; border: 1px solid transparent; }
    .ci:hover { background: #0f1117; border-color: #2d3148; }
    .ci.active { background: #1e2035; border-color: #6366f1; }
    .ci.urgent { border-left: 3px solid #f87171; }
    .ci-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
    .ci-id { font-size: 13px; font-weight: 500; color: #e2e8f0; font-family: monospace; }
    .badge { background: #7f1d1d; color: #fca5a5; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
    .ci-meta { font-size: 11px; color: #475569; }
    .contact-info { background: rgba(79,142,255,0.1); border: 1px solid rgba(79,142,255,0.3); border-radius: 8px; padding: 6px 10px; margin-top: 6px; font-size: 12px; color: #4f8eff; }
    .sb-bot { padding: 12px 16px; border-top: 1px solid #2d3148; }
    .btn-logout { width: 100%; padding: 8px; background: transparent; border: 1px solid #2d3148; border-radius: 8px; color: #64748b; font-size: 12px; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-logout:hover { border-color: #f87171; color: #f87171; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    .main-hdr { padding: 20px 28px; border-bottom: 1px solid #2d3148; background: #1a1d27; }
    .main-hdr h2 { font-size: 15px; font-weight: 600; color: #f1f5f9; }
    .main-hdr p { font-size: 13px; color: #475569; margin-top: 3px; }
    .msgs-area { flex: 1; overflow-y: auto; padding: 24px 28px; }
    .msgs-area::-webkit-scrollbar { width: 3px; }
    .msgs-area::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }
    .empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #2d3148; }
    .empty-icon { font-size: 52px; margin-bottom: 16px; }
    .empty p { font-size: 15px; }
    .msgs-wrap { display: flex; flex-direction: column; gap: 14px; }
    .msg { display: flex; flex-direction: column; max-width: 72%; }
    .msg.user { align-self: flex-end; }
    .msg.assistant { align-self: flex-start; }
    .msg-who { font-size: 11px; color: #475569; margin-bottom: 4px; padding: 0 4px; }
    .msg.user .msg-who { text-align: right; }
    .msg-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; }
    .msg.user .msg-text { background: #312e81; color: #e0e7ff; border-bottom-right-radius: 3px; }
    .msg.assistant .msg-text { background: #1e2035; color: #cbd5e1; border: 1px solid #2d3148; border-bottom-left-radius: 3px; }
  </style>
</head>
<body>
<div id="login">
  <div class="card">
    <div class="logo">&#129302;</div>
    <h2>Replai Admin</h2>
    <p class="sub">Connectez-vous pour acceder au dashboard</p>
    <div class="pwd-row">
      <input type="password" id="pwd" placeholder="Mot de passe" />
      <span class="eye" id="eyeBtn">&#128065;</span>
    </div>
    <button class="btn-login" id="loginBtn">Se connecter</button>
    <div class="err" id="errMsg">Mot de passe incorrect</div>
  </div>
</div>
<div id="dashboard">
  <div class="layout">
    <div class="sidebar">
      <div class="sb-top">
        <div class="brand">
          <div class="brand-icon">&#129302;</div>
          <span class="brand-name" id="businessName">Replai</span>
        </div>
        <div class="stats">
          <div class="stat"><span class="stat-n" id="totalN">0</span><span class="stat-l">Total</span></div>
          <div class="stat"><span class="stat-n" id="urgentN">0</span><span class="stat-l">Urgents</span></div>
        </div>
      </div>
      <div class="sb-mid">
        <input class="search-input" id="searchInput" placeholder="&#128269; Rechercher..." />
        <button class="btn-refresh" id="refreshBtn">&#8635; Rafraichir</button>
      </div>
      <div class="conv-list" id="convList"></div>
      <div class="sb-bot">
        <button class="btn-logout" id="logoutBtn">Se deconnecter</button>
      </div>
    </div>
    <div class="main">
      <div class="main-hdr">
        <h2 id="hdrTitle">Conversations</h2>
        <p id="hdrSub">Selectionnez une conversation</p>
      </div>
      <div class="msgs-area" id="msgsArea">
        <div class="empty">
          <div class="empty-icon">&#128172;</div>
          <p>Selectionnez une conversation</p>
        </div>
      </div>
    </div>
  </div>
</div>
<script>
var token = localStorage.getItem("wt") || "";
var clientToken = new URLSearchParams(window.location.search).get("token") || "";
var activeId = null;
var allConvs = [];
if (!clientToken) {
  document.body.innerHTML = "<div style='display:flex;align-items:center;justify-content:center;height:100vh;color:#f87171;font-family:Inter,sans-serif'>Token manquant dans l URL</div>";
}
if (token && clientToken) doVerify();
document.getElementById("eyeBtn").onclick = function() {
  var i = document.getElementById("pwd");
  i.type = i.type === "password" ? "text" : "password";
};
document.getElementById("loginBtn").onclick = doLogin;
document.getElementById("pwd").onkeydown = function(e) { if (e.key==="Enter") doLogin(); };
document.getElementById("refreshBtn").onclick = loadConvs;
document.getElementById("logoutBtn").onclick = doLogout;
document.getElementById("searchInput").oninput = function() { renderConvList(filterConvs(this.value)); };
function doVerify() {
  fetch("/admin/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:token,client_token:clientToken})})
  .then(function(r){if(r.ok)r.json().then(function(d){showDash(d.business_name);}); else{token="";localStorage.removeItem("wt");}});
}
function doLogin() {
  var pwd=document.getElementById("pwd").value;
  var err=document.getElementById("errMsg");
  err.style.display="none";
  fetch("/admin/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:pwd,client_token:clientToken})})
  .then(function(r){
    if(r.ok)r.json().then(function(d){token=pwd;localStorage.setItem("wt",pwd);showDash(d.business_name);});
    else err.style.display="block";
  }).catch(function(){err.style.display="block";err.innerText="Erreur reseau";});
}
function showDash(name) {
  document.getElementById("login").style.display="none";
  document.getElementById("dashboard").style.display="block";
  if(name) document.getElementById("businessName").innerText=name;
  loadConvs();
}
function doLogout() {
  localStorage.removeItem("wt"); token="";
  document.getElementById("dashboard").style.display="none";
  document.getElementById("login").style.display="flex";
  document.getElementById("pwd").value="";
}
function loadConvs() {
  fetch("/admin/conversations?client_token="+clientToken,{headers:{"X-Admin-Password":token}})
  .then(function(r){return r.json();}).then(function(data){allConvs=data;renderConvList(data);});
}
function filterConvs(q) {
  if(!q) return allConvs;
  q=q.toLowerCase();
  return allConvs.filter(function(c){return c.id.toLowerCase().includes(q);});
}
function renderConvList(data) {
  var list=document.getElementById("convList");
  list.innerHTML="";
  var urgent=allConvs.filter(function(c){return c.needs_human;}).length;
  document.getElementById("totalN").innerText=allConvs.length;
  document.getElementById("urgentN").innerText=urgent;
  if(!data.length){list.innerHTML="<p style='color:#475569;font-size:13px;text-align:center;padding:20px'>Aucune conversation</p>";return;}
  data.forEach(function(conv){
    var div=document.createElement("div");
    var cls="ci"+(conv.needs_human?" urgent":"")+(conv.id===activeId?" active":"");
    div.className=cls;
    var contact=conv.contact_info?"<div class='contact-info'>&#128222; "+conv.contact_info+"</div>":"";
    div.innerHTML="<div class='ci-top'><span class='ci-id'>#"+conv.id.slice(0,8)+"</span>"+(conv.needs_human?"<span class='badge'>RAPPELER</span>":"")+"</div>"
      +"<div class='ci-meta'>"+conv.created_at+" &middot; "+conv.message_count+" msg</div>"+contact;
    div.onclick=function(){loadConv(conv.id,div);};
    list.appendChild(div);
  });
}
function loadConv(id,el) {
  activeId=id;
  document.querySelectorAll(".ci").forEach(function(x){x.classList.remove("active");});
  if(el) el.classList.add("active");
  document.getElementById("hdrTitle").innerText="Conversation #"+id.slice(0,8);
  document.getElementById("hdrSub").innerText="Historique complet";
  fetch("/admin/conversations/"+id+"?client_token="+clientToken,{headers:{"X-Admin-Password":token}})
  .then(function(r){return r.json();}).then(function(data){
    var area=document.getElementById("msgsArea");
    area.innerHTML="<div class='msgs-wrap' id='msgsWrap'></div>";
    var wrap=document.getElementById("msgsWrap");
    data.forEach(function(msg){
      var div=document.createElement("div");
      div.className="msg "+msg.role;
      var who=msg.role==="user"?"Visiteur":"Assistant IA";
      div.innerHTML="<div class='msg-who'>"+who+"</div><div class='msg-text'>"+msg.content.replace(/\n/g,"<br>")+"</div>";
      wrap.appendChild(div);
    });
    area.scrollTop=area.scrollHeight;
  });
}
</script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=ADMIN_HTML)


@app.post("/admin/login")
def admin_login(data: dict, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.token == data.get("client_token","")).first()
    if not c or c.admin_password != data.get("password",""):
        raise HTTPException(status_code=401)
    return {"ok": True, "business_name": c.business_name}


@app.get("/admin/conversations")
def admin_conversations(client_token: str, request: Request, db: Session = Depends(get_db)):
    password = request.headers.get("X-Admin-Password","")
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c or c.admin_password != password:
        raise HTTPException(status_code=401)
    convs = db.query(Conversation).filter(
        Conversation.client_token == client_token
    ).order_by(Conversation.created_at.desc()).all()
    result = []
    for conv in convs:
        msgs = db.query(MessageModel).filter(MessageModel.conversation_id == conv.id).order_by(MessageModel.created_at).all()
        state = get_state(conv.id, db)
        needs_human = state == STATE_DONE
        contact_info = None
        for i, m in enumerate(msgs):
            if m.role == "assistant" and "prenom" in m.content.lower() and "telephone" in m.content.lower():
                if i + 1 < len(msgs) and msgs[i+1].role == "user":
                    contact_info = msgs[i+1].content
                    break
        result.append({
            "id": conv.id,
            "created_at": str(conv.created_at)[:16] if conv.created_at else "--",
            "message_count": len(msgs),
            "needs_human": needs_human,
            "contact_info": contact_info,
            "state": state
        })
    return result


@app.get("/admin/conversations/{conv_id}")
def admin_conversation_detail(conv_id: str, client_token: str, request: Request, db: Session = Depends(get_db)):
    password = request.headers.get("X-Admin-Password","")
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c or c.admin_password != password:
        raise HTTPException(status_code=401)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.client_token == client_token
    ).first()
    if not conv:
        raise HTTPException(status_code=404)
    msgs = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()
    return [{"role": m.role, "content": m.content} for m in msgs]


@app.post("/contact-human")
def contact_human(req: ContactHumanRequest, db: Session = Depends(get_db)):
    """Bouton 'Parler à un humain' → passe directement à l'état ASKING"""
    conv_id = req.conversation_id or str(uuid.uuid4())
    client_token = req.client_token or ""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        conv = Conversation(id=conv_id, title="Conversation client", client_token=client_token)
        db.add(conv)
        db.commit()
    set_state(conv_id, STATE_ASKING, db)
    save_message(conv_id, "assistant", ASKING_CONTACT, db)
    return bot_reply(ASKING_CONTACT, conv_id, False)


@app.post("/chat")
def chat(msg: ChatRequest, db: Session = Depends(get_db)):
    conv_id = msg.conversation_id or str(uuid.uuid4())
    client_token = msg.client_token or ""
    c = db.query(Client).filter(Client.token == client_token).first()

    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        conv = Conversation(id=conv_id, title="Conversation client", client_token=client_token)
        db.add(conv)
        db.commit()

    save_message(conv_id, "user", msg.message, db)
    state = get_state(conv_id, db)

    # ── ÉTAT ASKING : on récupère les coordonnées ──────────────────────────────
    if state == STATE_ASKING:
        if c:
            send_human_email(conv_id, msg.message, c)
        set_state(conv_id, STATE_DONE, db)
        save_message(conv_id, "assistant", HUMAN_CONFIRMED, db)
        return bot_reply(HUMAN_CONFIRMED, conv_id, True)

    # ── ÉTAT PROPOSED : visiteur répond oui/non ────────────────────────────────
    if state == STATE_PROPOSED:
        if is_affirmative(msg.message):
            set_state(conv_id, STATE_ASKING, db)
            save_message(conv_id, "assistant", ASKING_CONTACT, db)
            return bot_reply(ASKING_CONTACT, conv_id, False)
        else:
            set_state(conv_id, STATE_NORMAL, db)
            save_message(conv_id, "assistant", DECLINED, db)
            return bot_reply(DECLINED, conv_id, False)

    # ── ÉTAT NORMAL ────────────────────────────────────────────────────────────
    # Détection explicite : le visiteur demande directement un humain
    if HUMAN_REGEX.search(msg.message):
        set_state(conv_id, STATE_PROPOSED, db)
        save_message(conv_id, "assistant", HUMAN_PROPOSAL, db)
        return bot_reply(HUMAN_PROPOSAL, conv_id, False)

    # Appel GPT
    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    if c and c.system_prompt:
        base_prompt = c.system_prompt
    else:
        base_prompt = "Tu es un assistant virtuel professionnel."

    if msg.page_content:
        base_prompt += "\n\nCONTENU SUPPLEMENTAIRE DU SITE :\n" + msg.page_content

    base_prompt += (
        "\n\nREGLES :\n"
        "- Reponds dans la meme langue que le visiteur\n"
        "- Reponds uniquement aux questions liees a l activite du business\n"
        "- Sois concis, professionnel et serviable\n"
        "- Si tu ne connais pas la reponse, dis-le simplement"
    )

    messages_for_openai = [{"role": "system", "content": base_prompt}]
    for m in history:
        messages_for_openai.append({"role": m.role, "content": m.content})

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_openai
    )
    reply = response.choices[0].message.content

    # Si GPT propose spontanément un humain → passer à l'état PROPOSED
    if GPT_PROPOSES_HUMAN.search(reply):
        set_state(conv_id, STATE_PROPOSED, db)

    save_message(conv_id, "assistant", reply, db)
    return bot_reply(reply, conv_id, False)


app.mount("/static", StaticFiles(directory="static"), name="static")