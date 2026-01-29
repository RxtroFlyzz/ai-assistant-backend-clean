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
# REGEX & TEXTES
# =========================

HUMAN_REGEX = re.compile(
    r"(assistant|humain|conseiller|agent|support|service client|personne|quelqu'un)",
    re.IGNORECASE
)

YES_REGEX = re.compile(
    r"^(oui|ok|okay|d'accord|yes|yep|bien sûr|svp)$",
    re.IGNORECASE
)

HUMAN_PROPOSAL = (
    "Ces informations ne sont pas fournies sur le site.\n\n"
    "Souhaitez-vous être mis en relation avec un assistant humain ?"
)

HUMAN_CONFIRMED = (
    "Parfait 😊\n\n"
    "Un assistant humain va vous recontacter très rapidement."
)

# =========================
# EMAIL
# =========================

def send_human_email(user_message: str):
    msg = EmailMessage()
    msg["Subject"] = "🔔 Nouveau client à contacter"
    msg["From"] = os.getenv("SMTP_FROM")
    msg["To"] = os.getenv("CLIENT_EMAIL")

    msg.set_content(
        f"""
Un visiteur souhaite parler à un assistant humain.

Message :
{user_message}

Connectez-vous pour le recontacter.
"""
    )

    with smtplib.SMTP(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT"))) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.send_message(msg)

# =========================
# ROUTE CHAT
# =========================

@app.post("/chat")
def chat(msg: ChatRequest, db: Session = Depends(get_db)):

    conv_id = msg.conversation_id or str(uuid.uuid4())

    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id
    ).first()

    if not conversation:
        conversation = Conversation(
            id=conv_id,
            title="Conversation site client"
        )
        db.add(conversation)
        db.commit()

    # Message utilisateur
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
        if YES_REGEX.match(msg.message.strip()):
            send_human_email(msg.message)

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

    if msg.page_content:
        messages_for_openai.append({
            "role": "system",
            "content": (
                "Tu es l'assistant officiel du site web.\n\n"
                "CONTENU DU SITE :\n"
                f"{msg.page_content}\n\n"
                "RÈGLES STRICTES :\n"
                "- Tu travailles UNIQUEMENT pour ce site\n"
                "- Tu ne te présentes JAMAIS comme une IA générale\n"
                "- Tu n'inventes RIEN\n"
                "- Si info absente → propose assistant humain"
            )
        })

    for m in history:
        messages_for_openai.append({
            "role": m.role,
            "content": m.content
        })

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

    return {
        "reply": reply,
        "conversation_id": conv_id,
        "needs_human": False
    }
