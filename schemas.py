from pydantic import BaseModel
from typing import List, Optional


class MessageCreate(BaseModel):
    role: str
    content: str


class MessageRead(BaseModel):
    id: int
    role: str
    content: str

    class Config:
        orm_mode = True


class ConversationCreate(BaseModel):
    title: Optional[str] = "Nouvelle conversation"


class ConversationRead(BaseModel):
    id: int
    title: str
    messages: List[MessageRead] = []

    class Config:
        orm_mode = True
