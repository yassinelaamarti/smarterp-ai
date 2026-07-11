from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.conversation import Conversation, ChatMessageDB
from app.schemas.conversation import (
    ConversationOut,
    ConversationDetail,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services.auth import get_current_active_user
from app.services import ai_agent

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])


def _get_owned_conversation(db: Session, conversation_id: int, user: User) -> Conversation:
    """Récupère une conversation en vérifiant qu'elle appartient bien à l'utilisateur courant."""
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return conversation


def _derive_title(message: str) -> str:
    trimmed = message.strip()
    if not trimmed:
        return "Nouvelle conversation"
    return trimmed[:42] + "…" if len(trimmed) > 42 else trimmed


@router.get("/", response_model=list[ConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Liste les conversations de l'utilisateur connecté, les plus récentes en premier."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )


@router.post("/", response_model=ConversationOut, status_code=201)
def create_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conversation = Conversation(user_id=current_user.id, title="Nouvelle conversation")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return _get_owned_conversation(db, conversation_id, current_user)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    conversation = _get_owned_conversation(db, conversation_id, current_user)
    db.delete(conversation)
    db.commit()


@router.post("/{conversation_id}/messages", response_model=SendMessageResponse)
def send_message(
    conversation_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Envoie un message dans une conversation existante, sauvegarde la question
    ET la réponse de l'agent IA, puis renvoie la réponse."""
    conversation = _get_owned_conversation(db, conversation_id, current_user)

    # Historique déjà en base, pour donner du contexte à l'agent IA
    history = [{"role": m.role, "content": m.content} for m in conversation.messages]

    user_message = ChatMessageDB(
        conversation_id=conversation.id, role="user", content=payload.message
    )
    db.add(user_message)

    if conversation.title == "Nouvelle conversation" and not conversation.messages:
        conversation.title = _derive_title(payload.message)

    db.commit()

    try:
        reply = ai_agent.ask(payload.message, history)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur de l'agent IA : {e}")

    assistant_message = ChatMessageDB(
        conversation_id=conversation.id, role="assistant", content=reply
    )
    db.add(assistant_message)
    db.commit()

    return SendMessageResponse(conversation_id=conversation.id, reply=reply)
