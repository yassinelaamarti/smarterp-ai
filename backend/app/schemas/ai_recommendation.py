from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Literal


class AIRecommendationSchema(BaseModel):
    id: int
    tenant_id: Optional[str] = None
    source_type: Literal["anomaly", "health_score", "kpi_alert"]
    source_id: str
    title: str
    explanation: str
    action_type: Literal["restock_order", "send_email_campaign", "create_crm_activity", "none"]
    action_payload: Optional[dict[str, Any]] = None
    estimated_impact: Optional[str] = None
    status: Literal["pending", "executed", "dismissed"]
    executed_by: Optional[int] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AIRecommendationAuditSchema(BaseModel):
    id: int
    source_type: str
    title: str
    action_type: str
    action_payload: Optional[dict[str, Any]] = None
    estimated_impact: Optional[str] = None
    status: str
    executed_by_name: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
