"""
Lecture des KPIs pour l'API — lit EXCLUSIVEMENT le cache PostgreSQL.

N'appelle jamais Odoo directement : c'est services/kpi_sync.py qui
garde ce cache à jour en arrière-plan.
"""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.kpi_cache import KPICache, RevenueHistoryCache
from app.schemas.kpi import KPI

# Ordre d'affichage souhaité — les 10 KPIs cibles.
# Un nouveau KPI pas encore listé ici s'ajoute simplement à la fin, rien ne casse.
_KPI_ORDER = [
    "revenue", "new_orders", "avg_order_value",
    "stock_alerts", "new_leads", "conversion_rate",
    "pipeline_value", "stock_value", "active_customers", "late_orders",
]


def get_kpis() -> list[KPI]:
    db: Session = SessionLocal()
    try:
        rows = {r.id: r for r in db.query(KPICache).all()}
        ordered = [rows[k] for k in _KPI_ORDER if k in rows]
        ordered += [r for k, r in rows.items() if k not in _KPI_ORDER]
        return [KPI(id=r.id, label=r.label, value=r.value, unit=r.unit) for r in ordered]
    finally:
        db.close()


def get_monthly_revenue_history(months: int = 6) -> list[dict]:
    db: Session = SessionLocal()
    try:
        rows = (
            db.query(RevenueHistoryCache)
            .order_by(RevenueHistoryCache.month.asc())
            .limit(months)
            .all()
        )
        return [{"month": r.month, "label": r.label, "revenue": r.revenue} for r in rows]
    finally:
        db.close()
