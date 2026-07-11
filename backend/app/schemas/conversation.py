from datetime import datetime
from pydantic import BaseModel


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationDetail(ConversationOut):
    messages: list[MessageOut] = []


class SendMessageRequest(BaseModel):
    message: str


class SendMessageResponse(BaseModel):
    conversation_id: int
    reply: str
