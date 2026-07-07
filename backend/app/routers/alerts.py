from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alert_setting import AlertSetting
from app.schemas.alert import Alert
from app.services.kpi_calculator import get_kpis
from app.services.alert_engine import evaluate_alerts

router = APIRouter(prefix="/api/alerts", tags=["Alertes"])


@router.get("/", response_model=list[Alert])
def list_alerts(db: Session = Depends(get_db)):
    """Évalue les alertes à partir des KPIs actuellement en cache (rapide, pas d'appel Odoo)."""
    kpis = get_kpis()
    settings_db = db.query(AlertSetting).all()
    settings_dict = {s.key: s.value for s in settings_db}
    return evaluate_alerts(kpis, settings_dict)

