from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime

from app.database import Base


class KPICache(Base):
    """Dernière valeur connue de chaque KPI (une ligne par KPI)."""

    __tablename__ = "kpi_cache"

    id = Column(String, primary_key=True)  # ex: "revenue", "new_orders"
    label = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RevenueHistoryCache(Base):
    """Chiffre d'affaires en cache, un enregistrement par mois."""

    __tablename__ = "revenue_history_cache"

    month = Column(String, primary_key=True)  # ex: "2026-07"
    label = Column(String, nullable=False)     # ex: "juil. 2026"
    revenue = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
