from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
 
 
class Client(Base):
    __tablename__ = "clients"
 
    token = Column(String, primary_key=True, index=True)
    business_name = Column(String, default="Mon Business")
    admin_password = Column(String, nullable=False)
    client_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    conversations = relationship(
        "Conversation",
        back_populates="client",
        cascade="all, delete"
    )
 
 
class Conversation(Base):
    __tablename__ = "conversations"
 
    id = Column(String, primary_key=True, index=True)
    client_token = Column(String, ForeignKey("clients.token"), nullable=True)
    title = Column(String, default="Nouvelle conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
 
    client = relationship("Client", back_populates="conversations")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete"
    )
 
 
class Message(Base):
    __tablename__ = "messages"
 
    id = Column(String, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
 
    conversation = relationship("Conversation", back_populates="messages")