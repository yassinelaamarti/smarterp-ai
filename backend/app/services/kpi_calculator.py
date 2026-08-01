"""
Lecture des KPIs pour l'API — lit EXCLUSIVEMENT le cache PostgreSQL.

N'appelle jamais Odoo directement : c'est services/kpi_sync.py qui
garde ce cache (et son historique) à jour en arrière-plan.
"""

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.kpi_cache import KPICache, KPIHistoryCache, RevenueHistoryCache
from app.schemas.kpi import KPI, KPISourceData
from app.services.date_utils import previous_month_str

_KPI_ORDER = [
    "revenue", "new_orders", "avg_order_value",
    "stock_alerts", "new_leads", "conversion_rate",
    "pipeline_value", "stock_value", "active_customers", "late_orders",
]

_KPI_SOURCE_META = {
    "revenue": {
        "model": "sale.order",
        "domain": "[('state', 'in', ['sale', 'done']), ('date_order', '>=', aujourd'hui - 30j)]",
        "formula": "Somme de amount_total des commandes sur la fenêtre glissante de 30 jours"
    },
    "new_orders": {
        "model": "sale.order",
        "domain": "[('date_order', '>=', aujourd'hui - 30j)]",
        "formula": "Nombre total de commandes passées sur les 30 derniers jours"
    },
    "avg_order_value": {
        "model": "sale.order",
        "domain": "Calculé à partir du CA (30j) et du Nombre de commandes (30j)",
        "formula": "Chiffre d'affaires (30j) / Nombre de commandes (30j)"
    },
    "stock_alerts": {
        "model": "product.product",
        "domain": "[('qty_available', '<', 5), ('type', '=', 'product')]",
        "formula": "Nombre d'articles de type stockable dont la quantité en stock est inférieure à 5"
    },
    "new_leads": {
        "model": "crm.lead",
        "domain": "[('create_date', '>=', aujourd'hui - 30j), ('type', '=', 'lead')]",
        "formula": "Nombre total de pistes (leads) commerciales créées sur les 30 derniers jours"
    },
    "conversion_rate": {
        "model": "crm.lead",
        "domain": "[('create_date', '>=', aujourd'hui - 30j), ('type', '=', 'opportunity')]",
        "formula": "(Opportunités gagnées 30j / Total opportunités créées 30j) * 100"
    },
    "pipeline_value": {
        "model": "crm.lead",
        "domain": "[('type', '=', 'opportunity'), ('active', '=', True), ('stage_id.is_won', '=', False)]",
        "formula": "Somme des revenus attendus (expected_revenue) de toutes les opportunités ouvertes"
    },
    "stock_value": {
        "model": "product.product",
        "domain": "[('type', '=', 'product')]",
        "formula": "Somme de (quantité disponible * coût unitaire standard) pour tous les articles stockables"
    },
    "active_customers": {
        "model": "sale.order",
        "domain": "[('date_order', '>=', aujourd'hui - 30j)]",
        "formula": "Nombre de clients uniques (partner_id distincts) ayant passé au moins une commande sur 30 jours"
    },
    "late_orders": {
        "model": "stock.picking",
        "domain": "[('picking_type_id.code', '=', 'outgoing'), ('state', 'not in', ['done', 'cancel']), ('scheduled_date', '<', aujourd'hui)]",
        "formula": "Nombre de bons de livraison clients non encore livrés dont la date de livraison prévue est dépassée"
    }
}


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
        # Filtre STRICTEMENT sur la liste canonique des 10 KPIs, exclut les orphelins obsolètes
        ordered = [rows[k] for k in _KPI_ORDER if k in rows]

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
            meta = _KPI_SOURCE_META.get(r.id)
            source_data = None
            if meta:
                source_data = KPISourceData(
                    model=meta["model"],
                    domain=meta["domain"],
                    formula=meta["formula"]
                )
            result.append(KPI(
                id=r.id,
                label=r.label,
                value=r.value,
                unit=r.unit,
                trend=trend,
                change_percent=change_percent,
                source_data=source_data
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
