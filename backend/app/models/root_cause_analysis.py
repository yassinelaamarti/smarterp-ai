import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Text, UUID
from app.database import Base

DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")


class RootCauseAnalysis(Base):
    """
    Stockage des décompositions et explications des causes racines pour les anomalies et KPIs.
    """

    __tablename__ = "root_cause_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id"), nullable=False, default=DEFAULT_TENANT_ID)
    anomaly_id = Column(String, nullable=False, index=True)
    kpi_name = Column(String, nullable=False)
    period_current = Column(String, nullable=False)
    period_previous = Column(String, nullable=False)
    delta_total = Column(Float, nullable=False)
    delta_total_pct = Column(Float, nullable=False)
    breakdown = Column(JSON, nullable=False, default=list)  # [{ "dimension": "...", "segment": "...", "delta": -4200, "contribution_pct": -62.5 }]
    residual_pct = Column(Float, nullable=False, default=0.0)
    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
