from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey
from app.database import Base


class AIRecommendation(Base):
    """Représente une recommandation IA actionnable par l'utilisateur."""

    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=True)
    source_type = Column(String, nullable=False)  # anomaly | health_score | kpi_alert
    source_id = Column(String, nullable=False)  # ex: "stock_alerts" ou "anomaly_revenue"
    title = Column(String, nullable=False)
    explanation = Column(String, nullable=False)
    action_type = Column(String, nullable=False)  # restock_order | send_email_campaign | create_crm_activity | none
    action_payload = Column(JSON, nullable=True)  # ex: {"product_id": 36, "quantity": 50}
    estimated_impact = Column(String, nullable=True)  # ex: "+12 000 MAD potentiels"
    status = Column(String, default="pending", nullable=False)  # pending | executed | dismissed
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
