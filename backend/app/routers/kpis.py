from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import SessionLocal
from app.schemas.kpi import KPI
from app.schemas.revenue import RevenuePoint
from app.services.kpi_calculator import get_kpis, get_monthly_revenue_history
from app.services.kpi_sync import sync_all, seed_demo_previous_month
from app.services.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("/", response_model=list[KPI])
def list_kpis(current_user: User = Depends(get_current_active_user)):
    """Retourne les KPIs depuis le cache PostgreSQL, avec tendance vs mois précédent si disponible."""
    kpis = get_kpis()
    if not kpis:
        raise HTTPException(
            status_code=503,
            detail="Cache vide — la première synchronisation n'a pas encore eu lieu. Réessaie dans quelques secondes, ou POST /api/kpis/sync.",
        )
    return kpis


@router.get("/revenue-history", response_model=list[RevenuePoint])
def revenue_history(months: int = Query(default=6, ge=1, le=24), current_user: User = Depends(get_current_active_user)):
    """Historique du CA depuis le cache PostgreSQL."""
    return get_monthly_revenue_history(months)


@router.post("/sync", status_code=202)
def trigger_sync(current_user: User = Depends(get_current_active_user)):
    """Force une synchronisation immédiate avec Odoo (utile pour tester ou pour une démo)."""
    sync_all()
    return {"status": "synced"}


@router.post("/seed-demo-history", status_code=202)
def trigger_seed_demo_history(current_user: User = Depends(get_current_active_user)):
    """
    ⚠️ DEV/DÉMO UNIQUEMENT.
    Crée un historique factice du mois précédent pour voir immédiatement les
    badges de tendance (↑/↓), sans attendre qu'un vrai mois s'écoule.
    Ne jamais appeler cette route en production.
    """
    db = SessionLocal()
    try:
        seed_demo_previous_month(db)
    finally:
        db.close()
    return {"status": "demo history seeded"}
