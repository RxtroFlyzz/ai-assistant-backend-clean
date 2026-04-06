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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Widget — Admin</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Inter', sans-serif;
      background: #0f1117;
      color: #e2e8f0;
      height: 100vh;
      overflow: hidden;
    }

    /* ===== LOGIN ===== */
    #login {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100vh;
      background: #0f1117;
    }

    .login-card {
      background: #1a1d27;
      border: 1px solid #2d3148;
      border-radius: 16px;
      padding: 48px 40px;
      width: 380px;
      text-align: center;
    }

    .login-logo {
      width: 48px;
      height: 48px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto 24px;
      font-size: 22px;
    }

    .login-card h2 {
      font-size: 22px;
      font-weight: 600;
      color: #f1f5f9;
      margin-bottom: 6px;
    }

    .login-card p {
      font-size: 14px;
      color: #64748b;
      margin-bottom: 32px;
    }

    .login-card input {
      width: 100%;
      padding: 12px 16px;
      background: #0f1117;
      border: 1px solid #2d3148;
      border-radius: 10px;
      color: #f1f5f9;
      font-size: 15px;
      font-family: 'Inter', sans-serif;
      margin-bottom: 12px;
      outline: none;
      transition: border-color 0.2s;
    }

    .login-card input:focus {
      border-color: #6366f1;
    }

    .login-card button {
      width: 100%;
      padding: 12px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      color: white;
      border: none;
      border-radius: 10px;
      font-size: 15px;
      font-weight: 600;
      font-family: 'Inter', sans-serif;
      cursor: pointer;
      transition: opacity 0.2s;
    }

    .login-card button:hover { opacity: 0.9; }

    .error-msg {
      color: #f87171;
      font-size: 13px;
      margin-top: 10px;
    }

    /* ===== DASHBOARD ===== */
    #dashboard {
      display: none;
      height: 100vh;
      flex-direction: row;
    }

    /* SIDEBAR */
    .sidebar {
      width: 280px;
      background: #1a1d27;
      border-right: 1px solid #2d3148;
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }

    .sidebar-header {
      padding: 20px 20px 16px;
      border-bottom: 1px solid #2d3148;
    }

    .sidebar-brand {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
    }

    .brand-icon {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
    }

    .brand-name {
      font-size: 15px;
      font-weight: 600;
      color: #f1f5f9;
    }

    .sidebar-stats {
      display: flex;
      gap: 8px;
    }

    .stat-pill {
      background: #0f1117;
      border: 1px solid #2d3148;
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12px;
      color: #94a3b8;
      flex: 1;
      text-align: center;
    }

    .stat-pill span {
      display: block;
      font-size: 16px;
      font-weight: 600;
      color: #f1f5f9;
    }

    .sidebar-actions {
      padding: 12px 16px;
      border-bottom: 1px solid #2d3148;
    }

    .refresh-btn {
      width: 100%;
      padding: 8px 12px;
      background: #0f1117;
      border: 1px solid #2d3148;
      border-radius: 8px;
      color: #94a3b8;
      font-size: 13px;
      font-family: 'Inter', sans-serif;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: all 0.2s;
    }

    .refresh-btn:hover {
      border-color: #6366f1;
      color: #6366f1;
    }

    .conv-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }

    .conv-list::-webkit-scrollbar { width: 4px; }
    .conv-list::-webkit-scrollbar-track { background: transparent; }
    .conv-list::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }

    .conv-item {
      padding: 12px 14px;
      border-radius: 10px;
      margin-bottom: 4px;
      cursor: pointer;
      transition: background 0.15s;
      border: 1px solid transparent;
    }

    .conv-item:hover {
      background: #0f1117;
      border-color: #2d3148;
    }

    .conv-item.active {
      background: #1e2035;
      border-color: #6366f1;
    }

    .conv-item.urgent {
      border-left: 3px solid #f87171;
    }

    .conv-item-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 4px;
    }

    .conv-id {
      font-size: 13px;
      font-weight: 500;
      color: #e2e8f0;
      font-family: 'Courier New', monospace;
    }

    .badge-human {
      background: #7f1d1d;
      color: #fca5a5;
      font-size: 10px;
      font-weight: 600;
      padding: 2px 7px;
      border-radius: 20px;
      letter-spacing: 0.5px;
    }

    .conv-meta {
      font-size: 11px;
      color: #475569;
      display: flex;
      gap: 8px;
    }

    .sidebar-footer {
      padding: 12px 16px;
      border-top: 1px solid #2d3148;
    }

    .logout-btn {
      width: 100%;
      padding: 8px;
      background: transparent;
      border: 1px solid #2d3148;
      border-radius: 8px;
      color: #64748b;
      font-size: 12px;
      font-family: 'Inter', sans-serif;
      cursor: pointer;
      transition: all 0.2s;
    }

    .logout-btn:hover {
      border-color: #f87171;
      color: #f87171;
    }

    /* MAIN CONTENT */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .main-header {
      padding: 20px 28px;
      border-bottom: 1px solid #2d3148;
      background: #1a1d27;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .main-header h2 {
      font-size: 15px;
      font-weight: 600;
      color: #f1f5f9;
    }

    .main-header p {
      font-size: 13px;
      color: #475569;
      margin-top: 2px;
    }

    .conv-detail {
      flex: 1;
      overflow-y: auto;
      padding: 24px 28px;
    }

    .conv-detail::-webkit-scrollbar { width: 4px; }
    .conv-detail::-webkit-scrollbar-track { background: transparent; }
    .conv-detail::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }

    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      height: 100%;
      color: #334155;
    }

    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }

    .empty-state p {
      font-size: 15px;
    }

    .msg {
      display: flex;
      flex-direction: column;
      margin-bottom: 16px;
      max-width: 75%;
    }

    .msg.user { align-self: flex-end; margin-left: auto; }
    .msg.assistant { align-self: flex-start; }

    .msg-role {
      font-size: 11px;
      font-weight: 500;
      color: #475569;
      margin-bottom: 4px;
      padding: 0 4px;
    }

    .msg.user .msg-role { text-align: right; }

    .msg-bubble {
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 14px;
      line-height: 1.6;
    }

    .msg.user .msg-bubble {
      background: #312e81;
      color: #e0e7ff;
      border-bottom-right-radius: 4px;
    }

    .msg.assistant .msg-bubble {
      background: #1e2035;
      color: #cbd5e1;
      border: 1px solid #2d3148;
      border-bottom-left-radius: 4px;
    }

    .messages-wrapper {
      display: flex;
      flex-direction: column;
    }
  </style>
</head>
<body>

<!-- LOGIN -->
<div id="login">
  <div class="login-card">
    <div class="login-logo">🤖</div>
    <h2>AI Widget Admin</h2>
    <p>Connectez-vous pour accéder au dashboard</p>
    <input type="password" id="pwd" placeholder="Mot de passe" />
    <button onclick="login()">Se connecter</button>
    <p class="error-msg" id="error"></p>
  </div>
</div>

<!-- DASHBOARD -->
<div id="dashboard">
  <div class="sidebar">
    <div class="sidebar-header">
      <div class="sidebar-brand">
        <div class="brand-icon">🤖</div>
        <span class="brand-name">AI Widget</span>
      </div>
      <div class="sidebar-stats">
        <div class="stat-pill"><span id="total-count">—</span>Total</div>
        <div class="stat-pill"><span id="urgent-count">—</span>Urgents</div>
      </div>
    </div>
    <div class="sidebar-actions">
      <button class="refresh-btn" onclick="loadConversations()">↻ Rafraîchir</button>
    </div>
    <div class="conv-list" id="conv-list"></div>
    <div class="sidebar-footer">
      <button class="logout-btn" onclick="logout()">Se déconnecter</button>
    </div>
  </div>

  <div class="main">
    <div class="main-header">
      <div>
        <h2 id="header-title">Conversations</h2>
        <p id="header-sub">Sélectionnez une conversation pour voir les détails</p>
      </div>
    </div>
    <div class="conv-detail" id="conv-detail">
      <div class="empty-state">
        <div class="empty-state-icon">💬</div>
        <p>Sélectionnez une conversation</p>
      </div>
    </div>
  </div>
</div>

<script>
  let token = localStorage.getItem("admin_token") || "";
  let activeId = null;

  if (token) verifyAndShow();

  async function verifyAndShow() {
    const res = await fetch("/admin/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password: token })
    });
    if (res.ok) showDashboard();
    else { token = ""; localStorage.removeItem("admin_token"); }
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
      showDashboard();
    } else {
      document.getElementById("error").innerText = "Mot de passe incorrect";
    }
  }

  function showDashboard() {
    document.getElementById("login").style.display = "none";
    document.getElementById("dashboard").style.display = "flex";
    loadConversations();
  }

  function logout() {
    localStorage.removeItem("admin_token");
    token = "";
    document.getElementById("dashboard").style.display = "none";
    document.getElementById("login").style.display = "flex";
  }

  async function loadConversations() {
    const res = await fetch("/admin/conversations", {
      headers: { "X-Admin-Password": token }
    });
    const data = await res.json();
    const list = document.getElementById("conv-list");
    list.innerHTML = "";

    const urgent = data.filter(c => c.needs_human).length;
    document.getElementById("total-count").innerText = data.length;
    document.getElementById("urgent-count").innerText = urgent;

    if (data.length === 0) {
      list.innerHTML = '<p style="color:#475569;font-size:13px;text-align:center;padding:20px">Aucune conversation</p>';
      return;
    }

    data.forEach(conv => {
      const div = document.createElement("div");
      div.className = "conv-item" + (conv.needs_human ? " urgent" : "") + (conv.id === activeId ? " active" : "");
      div.innerHTML = `
        <div class="conv-item-header">
          <span class="conv-id">#${conv.id.slice(0, 8)}</span>
          ${conv.needs_human ? '<span class="badge-human">HUMAIN</span>' : ''}
        </div>
        <div class="conv-meta">
          <span>${conv.created_at}</span>
          <span>·</span>
          <span>${conv.message_count} messages</span>
        </div>
      `;
      div.onclick = () => loadConversation(conv.id, div);
      list.appendChild(div);
    });
  }

  async function loadConversation(id, el) {
    activeId = id;
    document.querySelectorAll(".conv-item").forEach(i => i.classList.remove("active"));
    if (el) el.classList.add("active");

    document.getElementById("header-title").innerText = "Conversation #" + id.slice(0, 8);
    document.getElementById("header-sub").innerText = "Historique complet de la conversation";

    const res = await fetch(`/admin/conversations/${id}`, {
      headers: { "X-Admin-Password": token }
    });
    const data = await res.json();
    const detail = document.getElementById("conv-detail");
    detail.innerHTML = '<div class="messages-wrapper" id="msgs"></div>';
    const wrapper = document.getElementById("msgs");

    data.forEach(msg => {
      const div = document.createElement("div");
      div.className = `msg ${msg.role}`;
      div.innerHTML = `
        <div class="msg-role">${msg.role === "user" ? "👤 Visiteur" : "🤖 Assistant IA"}</div>
        <div class="msg-bubble">${msg.content.replace(/\n/g, '<br>')}</div>
      `;
      wrapper.appendChild(div);
    });

    detail.scrollTop = detail.scrollHeight;
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
            m.role == "assistant" and "un assistant humain va vous recontacter" in m.content.lower()
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
                "- Tu réponds directement aux questions avec les infos disponibles\n"
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