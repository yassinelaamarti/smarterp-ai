import uuid
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Literal


class AIRecommendationSchema(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    source_type: Literal["anomaly", "health_score", "kpi_alert"]
    source_id: str
    title: str
    explanation: str
    action_type: Literal["restock_order", "send_email_campaign", "create_crm_activity", "none"]
    action_payload: Optional[dict[str, Any]] = None
    estimated_impact: Optional[dict[str, Any]] = None  # ex: {"label": "+12 000 MAD", "confidence": "medium"}
    status: Literal["pending", "executed", "dismissed", "failed"]
    executed_by: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True
