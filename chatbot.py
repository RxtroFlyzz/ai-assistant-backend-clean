from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001"],
    allow_credentials=True,
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

# =========================
# ROUTE CHAT
# =========================

@app.post("/chat")
def chat(
    msg: ChatRequest,
    db: Session = Depends(get_db)
):
    conv_id = msg.conversation_id or str(uuid.uuid4())

    conversation = db.query(Conversation).filter(
        Conversation.id == conv_id
    ).first()

    if not conversation:
        conversation = Conversation(
            id=conv_id,
            title="Nouvelle conversation"
        )
        db.add(conversation)
        db.commit()

    user_message = MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role="user",
        content=msg.message
    )
    db.add(user_message)
    db.commit()

    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    messages_for_openai = [
        {"role": m.role, "content": m.content}
        for m in history
    ]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_openai
    )

    reply = response.choices[0].message.content

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


