"""
Lecture des KPIs pour l'API — lit EXCLUSIVEMENT le cache PostgreSQL.

N'appelle jamais Odoo directement : c'est services/kpi_sync.py qui
garde ce cache (et son historique) à jour en arrière-plan.
"""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.kpi_cache import KPICache, KPIHistoryCache, RevenueHistoryCache
from app.schemas.kpi import KPI
from app.services.date_utils import previous_month_str

_KPI_ORDER = [
    "revenue", "new_orders", "avg_order_value",
    "stock_alerts", "new_leads", "conversion_rate",
    "pipeline_value", "stock_value", "active_customers", "late_orders",
]


def _compute_trend(current: float, previous: float | None):
    """Retourne (trend, change_percent), ou (None, None) si pas d'historique."""
    if previous is None or previous == 0:
        return None, None

    change_percent = round((current - previous) / abs(previous) * 100, 1)
    if change_percent > 0.5:
        trend = "up"
    elif change_percent < -0.5:
        trend = "down"
    else:
        trend = "stable"
    return trend, change_percent


def get_kpis() -> list[KPI]:
    db: Session = SessionLocal()
    try:
        rows = {r.id: r for r in db.query(KPICache).all()}
        ordered = [rows[k] for k in _KPI_ORDER if k in rows]
        ordered += [r for k, r in rows.items() if k not in _KPI_ORDER]

        prev_month = previous_month_str()
        history = (
            db.query(KPIHistoryCache)
            .filter(KPIHistoryCache.month == prev_month)
            .all()
        )
        previous_values = {h.kpi_id: h.value for h in history}

        result = []
        for r in ordered:
            trend, change_percent = _compute_trend(r.value, previous_values.get(r.id))
            result.append(KPI(
                id=r.id,
                label=r.label,
                value=r.value,
                unit=r.unit,
                trend=trend,
                change_percent=change_percent,
            ))
        return result
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
