from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import ai_agent
from app.services.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/chat", tags=["Agent IA"])


@router.post("/", response_model=ChatResponse)
def chat(payload: ChatRequest, current_user: User = Depends(get_current_active_user)):
    """Envoie un message à l'agent IA, avec le contexte des KPIs actuels injecté automatiquement."""
    try:
        history = [{"role": m.role, "content": m.content} for m in payload.history]
        reply = ai_agent.ask(payload.message, history)
        return ChatResponse(reply=reply)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur de l'agent IA : {e}")
