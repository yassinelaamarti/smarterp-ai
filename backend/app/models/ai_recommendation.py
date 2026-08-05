import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, JSON, DateTime, ForeignKey, Text, Boolean, Enum, UUID, Integer, Index, text
from app.database import Base


class RecommendationSource(str, enum.Enum):
    anomaly = "anomaly"
    health_score = "health_score"
    kpi_alert = "kpi_alert"


class RecommendationAction(str, enum.Enum):
    restock_order = "restock_order"
    send_email_campaign = "send_email_campaign"
    create_crm_activity = "create_crm_activity"
    create_follow_up_activity = "create_follow_up_activity"
    none = "none"


class RecommendationStatus(str, enum.Enum):
    pending = "pending"
    executed = "executed"
    dismissed = "dismissed"
    failed = "failed"
    expired = "expired"
    acknowledged = "acknowledged"


class AIRecommendation(Base):
    """Représente une recommandation IA actionnable par l'utilisateur."""

    __tablename__ = "ai_recommendation"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False)
    source_type = Column(Enum(RecommendationSource), nullable=False)
    source_id = Column(String, nullable=False)  # ex: "stock_alerts" ou "anomaly_revenue"
    title = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    action_type = Column(Enum(RecommendationAction), nullable=False, default=RecommendationAction.none)
    action_payload = Column(JSON, nullable=False, default=dict)  # ex: {"product_id": 36, "quantity": 50}
    estimated_impact = Column(JSON, nullable=True)  # ex: {"label": "+12 000 DH", "confidence": "medium"}
    status = Column(Enum(RecommendationStatus), default=RecommendationStatus.pending, nullable=False)
    entity_key = Column(String(255), nullable=True, index=True)
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    failure_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index(
            "uq_pending_recommendation_per_anomaly",
            "tenant_id",
            "source_type",
            "source_id",
            unique=True,
            postgresql_where=text("status = 'pending'")
        ),
    )


class AIActionLog(Base):
    """Table d'audit pour tracer l'exécution ou le rejet des recommandations IA."""

    __tablename__ = "ai_action_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(UUID(as_uuid=True), nullable=False)  # clé de recommandation
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    action_type = Column(Enum(RecommendationAction), nullable=False)
    action_payload = Column(JSON, nullable=False, default=dict)
    odoo_result = Column(JSON, nullable=True)  # réponse brute de l'ERP Odoo
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    success = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
