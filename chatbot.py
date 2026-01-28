from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import os

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

# 🔥 CORS : widget utilisable sur N'IMPORTE QUEL SITE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Création des tables
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
# ROUTE CHAT
# =========================

@app.post("/chat")
def chat(
    msg: ChatRequest,
    db: Session = Depends(get_db)
):
    # 🔹 ID conversation
    conv_id = msg.conversation_id or str(uuid.uuid4())

    # 🔹 Récupération / création conversation
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

    # 🔹 Sauvegarde message utilisateur
    user_message = MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=msg.message
    )
    db.add(user_message)
    db.commit()

    # 🔹 Historique
    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    # =========================
    # CONTEXTE IA (LE CŒUR DU PRODUIT)
    # =========================

    messages_for_openai = []

    # 🔥 CONTENU DU SITE = PRIORITÉ ABSOLUE
    if msg.page_content:
        messages_for_openai.append({
            "role": "system",
            "content": (
                "Tu es l'assistant officiel du site web suivant.\n\n"
                "CONTENU DU SITE :\n"
                f"{msg.page_content}\n\n"
                "RÈGLES STRICTES :\n"
                "- Tu travailles UNIQUEMENT pour ce site\n"
                "- Tu ne te présentes PAS comme une IA générale\n"
                "- Tu réponds uniquement avec les infos du site\n"
                "- Si une information n'est pas présente, dis-le clairement\n"
                "- Ne devine rien\n"
            )
        })

    # 🔹 Historique conversationnel
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

    # 🔹 Sauvegarde réponse IA
    ai_message = MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="assistant",
        content=reply
    )
    db.add(ai_message)
    db.commit()

    return {
        "reply": reply,
        "conversation_id": conv_id
    }

