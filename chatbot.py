from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os
import re

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
# DB DEPENDENCY
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
# OUTILS
# =========================

HUMAN_REGEX = re.compile(
    r"(assistant|conseiller|humain|personne|agent|support|service client|parler).*",
    re.IGNORECASE
)

NO_INFO_REGEX = re.compile(
    r"(ne (mentionne|fournit|précise) pas|aucune information|non disponible)",
    re.IGNORECASE
)

HUMAN_REPLY = (
    "Ces informations ne sont pas fournies sur le site.\n\n"
    "Souhaitez-vous que je vous redirige vers un assistant humain "
    "qui puisse vous aider ?"
)

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

    # Sauvegarde message utilisateur
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=msg.message
    ))
    db.commit()

    # =========================
    # 🔴 DÉCLENCHEUR 1 : HUMAIN DEMANDÉ
    # =========================

    if HUMAN_REGEX.search(msg.message):
        db.add(MessageModel(
            id=str(uuid.uuid4()),
            conversation_id=conv_id,
            role="assistant",
            content=HUMAN_REPLY
        ))
        db.commit()

        return {
            "reply": HUMAN_REPLY,
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
                "- Tu ne dis JAMAIS que tu es une IA générale\n"
                "- Tu ne réponds QUE si l'information est présente\n"
                "- Sinon dis que l'information n'est pas fournie\n"
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

    # =========================
    # 🔴 DÉCLENCHEUR 2 : INFO ABSENTE → HUMAIN
    # =========================

    if NO_INFO_REGEX.search(reply):
        reply = HUMAN_REPLY
        needs_human = True
    else:
        needs_human = False

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
        "needs_human": needs_human
    }

