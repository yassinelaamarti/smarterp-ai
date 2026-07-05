from pydantic import BaseModel
from typing import Literal


class ChatMessageIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessageIn] = []


class ChatResponse(BaseModel):
    reply: str
