import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
from app.models.ai_recommendation import RecommendationSource, RecommendationAction, RecommendationStatus


class AIRecommendationSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    source_type: RecommendationSource
    source_id: str
    title: str
    explanation: str
    action_type: RecommendationAction
    action_payload: Optional[dict[str, Any]] = None
    estimated_impact: Optional[dict[str, Any]] = None  # ex: {"label": "+12 000 MAD", "confidence": "medium"}
    status: RecommendationStatus
    executed_by: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class AIRecommendationAuditSchema(BaseModel):
    id: uuid.UUID
    recommendation_id: uuid.UUID
    source_type: str
    title: str
    action_type: str
    action_payload: Optional[dict[str, Any]] = None
    estimated_impact: Optional[dict[str, Any]] = None
    status: str
    executed_by_name: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    success: bool
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

