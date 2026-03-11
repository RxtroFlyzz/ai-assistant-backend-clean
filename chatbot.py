from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import re
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

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

# CORS (widget sur tous les sites)
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
    r"(assistant|humain|conseiller|agent|support|service client|contact|personne)",
    re.IGNORECASE
)

YES_REGEX = re.compile(
    r"^(oui|ok|okay|yes|yep|bien sûr|svp|oui svp)$",
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
# EMAIL (RESEND)
# =========================

def send_human_email(conv_id: str, user_message: str):

    print("📧 === RESEND EMAIL START ===")

    resend_key = os.getenv("RESEND_API_KEY")
    client_email = os.getenv("CLIENT_EMAIL")

    print(f"RESEND_API_KEY present: {bool(resend_key)}")
    print(f"CLIENT_EMAIL: {client_email}")

    if not resend_key or not client_email:
        print("❌ RESEND CONFIG INCOMPLETE")
        return

    try:
        data = json.dumps({
            "from": "AI Widget <onboarding@resend.dev>",
            "to": [client_email],
            "subject": "🔔 Nouveau client à rappeler",
            "html": (
                "<h2>Un visiteur souhaite parler à un humain</h2>"
                f"<p><strong>Conversation ID :</strong> {conv_id}</p>"
                f"<p><strong>Dernier message :</strong> {user_message}</p>"
                "<p>Merci de le recontacter rapidement.</p>"
            )
        }).encode("utf-8")

        req = Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {resend_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        response = urlopen(req)
        result = json.loads(response.read().decode())
        print(f"✅ EMAIL SENT via Resend! ID: {result.get('id', 'unknown')}")

    except URLError as e:
        print(f"❌ RESEND ERROR: {e}")
    except Exception as e:
        print(f"❌ RESEND UNEXPECTED ERROR: {e}")


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
