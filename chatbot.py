from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import re
import resend

from dotenv import load_dotenv
from openai import OpenAI

from database import SessionLocal, engine
from models import Base, Conversation, Message as MessageModel

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    page_content: Optional[str] = None

class ContactHumanRequest(BaseModel):
    conversation_id: Optional[str] = None

HUMAN_REGEX = re.compile(
    r"(assistant|humain|conseiller|agent|support|service client|contact|personne)",
    re.IGNORECASE
)

YES_REGEX = re.compile(
    r"^(oui|ok|okay|yes|yep|svp)$",
    re.IGNORECASE
)

HUMAN_PROPOSAL = "Ces informations ne sont pas disponibles. Souhaitez-vous etre mis en relation avec un assistant humain ?"

HUMAN_CONFIRMED = "Parfait. Un assistant humain va vous recontacter tres rapidement."

def send_human_email(conv_id: str, user_message: str):
    print("EMAIL START")
    client_email = os.getenv("CLIENT_EMAIL")
    if not client_email:
        return
    try:
        params = {
            "from": "AI Widget <noreply@gianluca-ai.fr>",
            "to": [client_email],
            "subject": "Nouveau client a rappeler",
            "html": (
                "<h2>Un visiteur souhaite parler a un humain</h2>"
                "<p><strong>Conversation ID :</strong> " + conv_id + "</p>"
                "<p><strong>Dernier message :</strong> " + user_message + "</p>"
                "<p>Merci de le recontacter rapidement.</p>"
            )
        }
        email = resend.Emails.send(params)
        print("EMAIL SENT: " + email['id'])
    except Exception as e:
        print("EMAIL ERROR: " + str(e))


ADMIN_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Widget Admin</title>
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
    .sb-mid { padding: 12px 16px; border-bottom: 1px solid #2d3148; }
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
    <h2>AI Widget Admin</h2>
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
          <span class="brand-name">AI Widget</span>
        </div>
        <div class="stats">
          <div class="stat"><span class="stat-n" id="totalN">0</span><span class="stat-l">Total</span></div>
          <div class="stat"><span class="stat-n" id="urgentN">0</span><span class="stat-l">Urgents</span></div>
        </div>
      </div>
      <div class="sb-mid">
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
var activeId = null;

if (token) { doVerify(); }

document.getElementById("eyeBtn").addEventListener("click", function() {
  var inp = document.getElementById("pwd");
  inp.type = inp.type === "password" ? "text" : "password";
});

document.getElementById("loginBtn").addEventListener("click", doLogin);

document.getElementById("pwd").addEventListener("keydown", function(e) {
  if (e.key === "Enter") { doLogin(); }
});

document.getElementById("refreshBtn").addEventListener("click", loadConvs);
document.getElementById("logoutBtn").addEventListener("click", doLogout);

function doVerify() {
  fetch("/admin/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({password: token})
  }).then(function(r) {
    if (r.ok) { showDash(); } else { token = ""; localStorage.removeItem("wt"); }
  });
}

function doLogin() {
  var pwd = document.getElementById("pwd").value;
  var err = document.getElementById("errMsg");
  err.style.display = "none";
  fetch("/admin/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({password: pwd})
  }).then(function(r) {
    if (r.ok) {
      token = pwd;
      localStorage.setItem("wt", pwd);
      showDash();
    } else {
      err.style.display = "block";
    }
  }).catch(function() {
    err.style.display = "block";
    document.getElementById("errMsg").innerText = "Erreur reseau";
  });
}

function showDash() {
  document.getElementById("login").style.display = "none";
  document.getElementById("dashboard").style.display = "block";
  loadConvs();
}

function doLogout() {
  localStorage.removeItem("wt");
  token = "";
  document.getElementById("dashboard").style.display = "none";
  document.getElementById("login").style.display = "flex";
  document.getElementById("pwd").value = "";
}

function loadConvs() {
  fetch("/admin/conversations", {
    headers: {"X-Admin-Password": token}
  }).then(function(r) { return r.json(); }).then(function(data) {
    var list = document.getElementById("convList");
    list.innerHTML = "";
    var urgent = 0;
    for (var i = 0; i < data.length; i++) {
      if (data[i].needs_human) urgent++;
    }
    document.getElementById("totalN").innerText = data.length;
    document.getElementById("urgentN").innerText = urgent;
    if (data.length === 0) {
      list.innerHTML = "<p style='color:#475569;font-size:13px;text-align:center;padding:20px'>Aucune conversation</p>";
      return;
    }
    for (var j = 0; j < data.length; j++) {
      (function(conv) {
        var div = document.createElement("div");
        var cls = "ci";
        if (conv.needs_human) cls += " urgent";
        if (conv.id === activeId) cls += " active";
        div.className = cls;
        div.innerHTML = "<div class='ci-top'><span class='ci-id'>#" + conv.id.slice(0,8) + "</span>" +
          (conv.needs_human ? "<span class='badge'>HUMAIN</span>" : "") + "</div>" +
          "<div class='ci-meta'>" + conv.created_at + " &middot; " + conv.message_count + " msg</div>";
        div.addEventListener("click", function() { loadConv(conv.id, div); });
        list.appendChild(div);
      })(data[j]);
    }
  });
}

function loadConv(id, el) {
  activeId = id;
  var items = document.getElementsByClassName("ci");
  for (var i = 0; i < items.length; i++) { items[i].classList.remove("active"); }
  if (el) el.classList.add("active");
  document.getElementById("hdrTitle").innerText = "Conversation #" + id.slice(0,8);
  document.getElementById("hdrSub").innerText = "Historique complet";
  fetch("/admin/conversations/" + id, {
    headers: {"X-Admin-Password": token}
  }).then(function(r) { return r.json(); }).then(function(data) {
    var area = document.getElementById("msgsArea");
    area.innerHTML = "<div class='msgs-wrap' id='msgsWrap'></div>";
    var wrap = document.getElementById("msgsWrap");
    for (var i = 0; i < data.length; i++) {
      var msg = data[i];
      var div = document.createElement("div");
      div.className = "msg " + msg.role;
      var who = msg.role === "user" ? "Visiteur" : "Assistant IA";
      var txt = msg.content.replace(/\n/g, "<br>");
      div.innerHTML = "<div class='msg-who'>" + who + "</div><div class='msg-text'>" + txt + "</div>";
      wrap.appendChild(div);
    }
    area.scrollTop = area.scrollHeight;
  });
}
</script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=ADMIN_HTML)

@app.post("/admin/login")
def admin_login(data: dict, request: Request):
    if data.get("password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Mot de passe incorrect")
    return {"ok": True}

@app.get("/admin/conversations")
def admin_conversations(request: Request, db: Session = Depends(get_db)):
    if request.headers.get("X-Admin-Password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    conversations = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    result = []
    for conv in conversations:
        messages = db.query(MessageModel).filter(MessageModel.conversation_id == conv.id).all()
        needs_human = any(
            m.role == "assistant" and "assistant humain va vous recontacter" in m.content.lower()
            for m in messages
        )
        result.append({
            "id": conv.id,
            "created_at": str(conv.created_at)[:16] if conv.created_at else "--",
            "message_count": len(messages),
            "needs_human": needs_human
        })
    return result

@app.get("/admin/conversations/{conv_id}")
def admin_conversation_detail(conv_id: str, request: Request, db: Session = Depends(get_db)):
    if request.headers.get("X-Admin-Password") != ADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    messages = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()
    return [{"role": m.role, "content": m.content} for m in messages]


@app.post("/contact-human")
def contact_human(req: ContactHumanRequest, db: Session = Depends(get_db)):
    conv_id = req.conversation_id or str(uuid.uuid4())
    conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversation:
        conversation = Conversation(id=conv_id, title="Conversation client")
        db.add(conversation)
        db.commit()
    send_human_email(conv_id, "Le visiteur a clique sur le bouton Parler a un humain")
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=HUMAN_CONFIRMED
    ))
    db.commit()
    return {"reply": HUMAN_CONFIRMED, "conversation_id": conv_id, "needs_human": True}

@app.post("/chat")
def chat(msg: ChatRequest, db: Session = Depends(get_db)):
    conv_id = msg.conversation_id or str(uuid.uuid4())
    conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversation:
        conversation = Conversation(id=conv_id, title="Conversation client")
        db.add(conversation)
        db.commit()
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=msg.message
    ))
    db.commit()
    last_ai = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id,
        MessageModel.role == "assistant"
    ).order_by(MessageModel.created_at.desc()).first()
    if last_ai and "assistant humain" in last_ai.content.lower():
        if YES_REGEX.match(msg.message.strip().lower()):
            send_human_email(conv_id, msg.message)
            db.add(MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conv_id,
                role="assistant",
                content=HUMAN_CONFIRMED
            ))
            db.commit()
            return {"reply": HUMAN_CONFIRMED, "conversation_id": conv_id, "needs_human": True}
    if HUMAN_REGEX.search(msg.message):
        db.add(MessageModel(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="assistant",
            content=HUMAN_PROPOSAL
        ))
        db.commit()
        return {"reply": HUMAN_PROPOSAL, "conversation_id": conv_id, "needs_human": True}
    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()
    messages_for_openai = []
    if msg.page_content:
        messages_for_openai.append({
            "role": "system",
            "content": (
                "Tu es l'assistant officiel du site web.\n\n"
                "CONTENU DU SITE :\n"
                + msg.page_content +
                "\n\nREGLES :\n"
                "- Tu travailles uniquement pour ce site\n"
                "- Tu reponds directement aux questions avec les infos disponibles\n"
                "- Tu n'inventes JAMAIS d'informations qui ne sont pas dans le contenu\n"
                "- Tu proposes un humain UNIQUEMENT si la question est totalement hors sujet ou si le visiteur le demande explicitement"
            )
        })
    for m in history:
        messages_for_openai.append({"role": m.role, "content": m.content})
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_openai
    )
    reply = response.choices[0].message.content
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=reply
    ))
    db.commit()
    return {"reply": reply, "conversation_id": conv_id, "needs_human": False}

app.mount("/static", StaticFiles(directory="static"), name="static")