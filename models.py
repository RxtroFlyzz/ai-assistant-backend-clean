from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
 
 
class Client(Base):
    __tablename__ = "clients"
 
    token = Column(String, primary_key=True, index=True)
    business_name = Column(String, default="Mon Business")
    admin_password = Column(String, nullable=False)
    client_email = Column(String, nullable=True)
    system_prompt = Column(Text, nullable=True)
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


class Event(Base):
    """Ce que le chat a declenche : clic vers un produit, ajout au panier, commande."""
    __tablename__ = "replai_events"

    id = Column(String, primary_key=True, index=True)
    client_token = Column(String, index=True)
    conversation_id = Column(String, index=True, nullable=True)
    type = Column(String, index=True)          # product_click | add_to_cart | order
    product_id = Column(String, nullable=True)
    variant_id = Column(String, nullable=True)
    value = Column(Float, nullable=True)       # montant (commande ou prix du produit ajoute)
    currency = Column(String, nullable=True)
    ref = Column(String, nullable=True)        # numero de commande (anti-doublon)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class ReportLog(Base):
    """Rapports mensuels deja envoyes (un par client et par mois)."""
    __tablename__ = "replai_reports"

    id = Column(String, primary_key=True)      # token + ":" + "2026-10"
    sent_at = Column(DateTime, default=datetime.utcnow)
