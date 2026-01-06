from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models, schemas

# Crée les tables dans la base si elles n'existent pas
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Autoriser l'accès depuis le front-end React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002"],  # ton front-end
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dépendance pour obtenir une session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Routes pour gérer les conversations
@app.post("/conversation/", response_model=schemas.Conversation)
def create_conversation(conv: schemas.ConversationCreate, db: Session = Depends(get_db)):
    db_conv = models.Conversation(name=conv.name)
    db.add(db_conv)
    db.commit()
    db.refresh(db_conv)
    return db_conv

@app.get("/conversation/", response_model=list[schemas.Conversation])
def read_conversations(db: Session = Depends(get_db)):
    return db.query(models.Conversation).all()

# Routes pour les messages
@app.post("/conversation/{conv_id}/message/", response_model=schemas.Message)
def create_message(conv_id: int, msg: schemas.MessageCreate, db: Session = Depends(get_db)):
    db_msg = models.Message(**msg.dict(), conversation_id=conv_id)
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

@app.get("/conversation/{conv_id}/message/", response_model=list[schemas.Message])
def read_messages(conv_id: int, db: Session = Depends(get_db)):
    return db.query(models.Message).filter(models.Message.conversation_id == conv_id).all()
