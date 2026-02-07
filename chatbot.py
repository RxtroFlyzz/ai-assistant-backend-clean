from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import re
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
from openai import OpenAI

from database import SessionLocal, engine
from models import Base, Conversation, Message as MessageModel

# =========================
# INIT
# =========================

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

# =========================
# DB
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SCHEMA
# =========================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    page_content: Optional[str] = None

# =========================
# REGEX
# =========================

HUMAN_REGEX = re.compile(
    r"(assistant|humain|conseiller|agent|support|service client|personne|quelqu'un|contact)",
    re.IGNORECASE
)

YES_REGEX = re.compile(
    r"^(oui|ok|okay|d'accord|yes|yep|bien sûr|svp|oui svp)$",
    re.IGNORECASE
)

# =========================
# TEXTES
# =========================

HUMAN_PROPOSAL = (
    "Ces informations ne sont pas disponibles.\n\n"
    "Souhaitez-vous être mis en relation avec un assistant humain ?"
)

HUMAN_CONFIRMED = (
    "Parfait 😊\n\n"
    "Un assistant humain va vous recontacter très rapidement."
)

# =========================
# EMAIL
# =========================

def send_human_email(conv_id: str, user_message: str):

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    smtp_from = os.getenv("SMTP_FROM")
    client_email = os.getenv("CLIENT_EMAIL")

    # Vérification config
    if not all([
        smtp_host,
        smtp_port,
        smtp_user,
        smtp_pass,
        smtp_from,
        client_email
    ]):
        print("❌ SMTP CONFIG INCOMPLETE")
        return

    try:
        msg = EmailMessage()

        msg["Subject"] = "📞 Nouveau client à rappeler"
        msg["From"] = smtp_from
        msg["To"] = client_email

        msg.set_content(f"""
Un visiteur souhaite parler à un assistant humain.

Conversation ID :
{conv_id}

Dernier message :
{user_message}

Merci de le recontacter rapidement.
""")

        with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        print("✅ EMAIL SENT")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# =========================
# ROUTE CHAT
# =========================

@app.post("/chat")
def chat(msg: ChatRequest, db: Session = Depends(get_db)):

    # ID conversation
    conv_id = msg.conversation_id or str(uuid.uuid4())

    # Conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id
    ).first()

    if not conversation:
        conversation = Conversation(
            id=conv_id,
            title="Conversation client"
        )
        db.add(conversation)
        db.commit()

    # Message user
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=msg.message
    ))
    db.commit()

    # =========================
    # CONFIRMATION HUMAIN
    # =========================

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

            return {
                "reply": HUMAN_CONFIRMED,
                "conversation_id": conv_id,
                "needs_human": True
            }

    # =========================
    # DEMANDE HUMAIN DIRECTE
    # =========================

    if HUMAN_REGEX.search(msg.message):

        db.add(MessageModel(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="assistant",
            content=HUMAN_PROPOSAL
        ))
        db.commit()

        return {
            "reply": HUMAN_PROPOSAL,
            "conversation_id": conv_id,
            "needs_human": True
        }

    # =========================
    # HISTORIQUE
    # =========================

    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    messages_for_openai = []

    # =========================
    # CONTEXTE SITE
    # =========================

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
        messages_for_openai.append({
            "role": m.role,
            "content": m.content
        })

    # =========================
    # OPENAI
    # =========================

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_openai
    )

    reply = response.choices[0].message.content

    # Save AI msg
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=reply
    ))
    db.commit()

    return {
        "reply": reply,
        "conversation_id": conv_id,
        "needs_human": False
    }
