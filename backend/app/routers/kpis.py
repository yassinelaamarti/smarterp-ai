from fastapi import APIRouter, HTTPException, Query, Depends
from app.database import SessionLocal
from app.schemas.kpi import KPI, AISummaryResponse
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

@router.get("/{kpi_id}/history")
def kpi_detailed_history(kpi_id: str, period: str = Query("month", regex="^(week|month|trimester)$"), current_user: User = Depends(get_current_active_user)):
    """Historique détaillé d'un KPI spécifique pour un affichage graphique approfondi."""
    from app.services.kpi_history_service import get_kpi_history
    return get_kpi_history(kpi_id, period)

@router.get("/{kpi_id}/context")
def kpi_context(kpi_id: str, period: str = Query("month", regex="^(week|month|trimester)$"), current_user: User = Depends(get_current_active_user)):
    """Données contextuelles spécifiques au KPI (entonnoir, alertes, objectifs, etc.)"""
    from app.services.kpi_context_service import get_kpi_context
    return get_kpi_context(kpi_id, period)


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


@router.get("/ai-summary", response_model=AISummaryResponse)
def get_ai_summary(current_user: User = Depends(get_current_active_user)):
    """Génère une synthèse décisionnelle rédigée par l'agent IA à partir des KPIs."""
    try:
        from app.services.ai_agent import generate_dashboard_summary
        summary_text = generate_dashboard_summary()
        return AISummaryResponse(summary=summary_text)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de la génération de la synthèse par l'agent IA : {e}"
        )

