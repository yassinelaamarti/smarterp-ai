from fastapi import APIRouter
from app.schemas.alert import Alert
from app.services.kpi_calculator import get_kpis
from app.services.alert_engine import evaluate_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alertes"])


@router.get("/", response_model=list[Alert])
def list_alerts():
    """Évalue les alertes à partir des KPIs actuellement en cache (rapide, pas d'appel Odoo)."""
    kpis = get_kpis()
    return evaluate_alerts(kpis)
