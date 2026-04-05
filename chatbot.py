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
    r"^(oui|ok|okay|yes|yep|bien sûr|svp|oui svp)$",
    re.IGNORECASE
)

HUMAN_PROPOSAL = (
    "Ces informations ne sont pas disponibles.\n\n"
    "Souhaitez-vous être mis en relation avec un assistant humain ?"
)

HUMAN_CONFIRMED = (
    "Parfait 😊\n\n"
    "Un assistant humain va vous recontacter très rapidement."
)

def send_human_email(conv_id: str, user_message: str):
    print("📧 === RESEND EMAIL START ===")
    client_email = os.getenv("CLIENT_EMAIL")
    print(f"CLIENT_EMAIL: {client_email}")
    if not client_email:
        print("❌ CLIENT_EMAIL MANQUANT")
        return
    try:
        params = {
            "from": "AI Widget <noreply@gianluca-ai.fr>",
            "to": [client_email],
            "subject": "🔔 Nouveau client à rappeler",
            "html": (
                "<h2>Un visiteur souhaite parler à un humain</h2>"
                f"<p><strong>Conversation ID :</strong> {conv_id}</p>"
                f"<p><strong>Dernier message :</strong> {user_message}</p>"
                "<p>Merci de le recontacter rapidement.</p>"
            )
        }
        email = resend.Emails.send(params)
        print(f"✅ EMAIL SENT! ID: {email['id']}")
    except Exception as e:
        print(f"❌ RESEND ERROR: {e}")


# =========================
# ADMIN
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Admin - AI Widget</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; background: #f5f5f5; }
    #login { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; }
    #login input { padding: 10px; font-size: 16px; margin-bottom: 10px; width: 300px; border: 1px solid #ddd; border-radius: 6px; }
    #login button { padding: 10px 20px; background: #000; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; width: 300px; }
    #dashboard { display: none; padding: 20px; }
    h1 { margin-bottom: 20px; }
    .conv-list { display: flex; gap: 20px; }
    .conv-sidebar { width: 340px; flex-shrink: 0; }
    .conv-item { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin-bottom: 10px; cursor: pointer; }
    .conv-item:hover { border-color: #000; }
    .conv-item.urgent { border-left: 4px solid #e74c3c; }
    .conv-item .date { font-size: 12px; color: #999; margin-top: 4px; }
    .conv-item .badge { background: #e74c3c; color: white; font-size: 11px; padding: 2px 6px; border-radius: 4px; }
    .conv-detail { flex: 1; background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; min-height: 400px; }
    .msg { margin-bottom: 12px; padding: 10px; border-radius: 6px; }
    .msg.user { background: #f0f0f0; }
    .msg.assistant { background: #e8f4fd; }
    .msg .role { font-weight: bold; font-size: 12px; margin-bottom: 4px; }
    #no-selection { color: #999; text-align: center; margin-top: 100px; }
    .error { color: red; font-size: 14px; margin-top: 8px; }
    #refresh-btn { margin-left: 20px; padding: 6px 14px; background: #fff; border: 1px solid #ddd; border-radius: 6px; cursor: pointer; font-size: 14px; }
    #refresh-btn:hover { background: #f0f0f0; }
  </style>
</head>
<body>
<div id="login">
  <h2 style="margin-bottom:20px">🔐 Admin AI Widget</h2>
  <input type="password" id="pwd" placeholder="Mot de passe" />
  <button onclick="login()">Connexion</button>
  <p class="error" id="error"></p>
</div>
<div id="dashboard">
  <h1>📊 Dashboard Admin <button id="refresh-btn" onclick="loadConversations()">🔄 Rafraîchir</button></h1>
  <div class="conv-list">
    <div class="conv-sidebar" id="conv-list"></div>
    <div class="conv-detail" id="conv-detail">
      <p id="no-selection">← Sélectionne une conversation</p>
    </div>
  </div>
</div>
<script>
  let token = localStorage.getItem("admin_token") || "";

  if (token) {
    verifyAndShow();
  }

  async function verifyAndShow() {
    const res = await fetch("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: token })
    });
    if (res.ok) {
      document.getElementById("login").style.display = "none";
      document.getElementById("dashboard").style.display = "block";
      loadConversations();
    } else {
      token = "";
      localStorage.removeItem("admin_token");
    }
  }

  async function login() {
    const pwd = document.getElementById("pwd").value;
    const res = await fetch("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: pwd })
    });
    if (res.ok) {
      token = pwd;
      localStorage.setItem("admin_token", pwd);
      document.getElementById("login").style.display = "none";
      document.getElementById("dashboard").style.display = "block";
      loadConversations();
    } else {
      document.getElementById("error").innerText = "Mot de passe incorrect";
    }
  }

  async function loadConversations() {
    const res = await fetch("/admin/conversations", {
      headers: { "X-Admin-Password": token }
    });
    const data = await res.json();
    const list = document.getElementById("conv-list");
    list.innerHTML = "";
    data.forEach(conv => {
      const div = document.createElement("div");
      div.className = "conv-item" + (conv.needs_human ? " urgent" : "");
      div.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center">
          <strong>${conv.id.slice(0, 8)}...</strong>
          ${conv.needs_human ? '<span class="badge">🔴 Humain</span>' : ''}
        </div>
        <div class="date">${conv.created_at} · ${conv.message_count} messages</div>
      `;
      div.onclick = () => loadConversation(conv.id);
      list.appendChild(div);
    });
  }

  async function loadConversation(id) {
    const res = await fetch(`/admin/conversations/${id}`, {
      headers: { "X-Admin-Password": token }
    });
    const data = await res.json();
    const detail = document.getElementById("conv-detail");
    detail.innerHTML = `<h3 style="margin-bottom:16px">Conversation ${id.slice(0,8)}...</h3>`;
    data.forEach(msg => {
      const div = document.createElement("div");
      div.className = `msg ${msg.role}`;
      div.innerHTML = `<div class="role">${msg.role === "user" ? "👤 Visiteur" : "🤖 IA"}</div>${msg.content}`;
      detail.appendChild(div);
    });
  }

  document.getElementById("pwd").addEventListener("keydown", e => {
    if (e.key === "Enter") login();
  });
</script>
</body>
</html>
""")

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
            "assistant humain" in m.content.lower() or "parler à un humain" in m.content.lower()
            for m in messages
        )
        result.append({
            "id": conv.id,
            "created_at": str(conv.created_at)[:16] if conv.created_at else "—",
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


# =========================
# ROUTES CHAT
# =========================

@app.post("/contact-human")
def contact_human(req: ContactHumanRequest, db: Session = Depends(get_db)):
    conv_id = req.conversation_id or str(uuid.uuid4())
    conversation = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conversation:
        conversation = Conversation(id=conv_id, title="Conversation client")
        db.add(conversation)
        db.commit()
    send_human_email(conv_id, "Le visiteur a cliqué sur le bouton 'Parler à un humain'")
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
                f"{msg.page_content}\n\n"
                "RÈGLES :\n"
                "- Tu travailles uniquement pour ce site\n"
                "- Tu n'inventes rien\n"
                "- Si info absente → propose humain"
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
