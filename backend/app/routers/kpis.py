from fastapi import APIRouter, HTTPException, Query
from app.schemas.kpi import KPI
from app.schemas.revenue import RevenuePoint
from app.services.kpi_calculator import get_kpis, get_monthly_revenue_history

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("/", response_model=list[KPI])
def list_kpis():
    """Retourne les KPIs du dashboard, calculés en direct depuis Odoo."""
    try:
        return get_kpis()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la lecture des données Odoo : {e}")


@router.get("/revenue-history", response_model=list[RevenuePoint])
def revenue_history(months: int = Query(default=6, ge=1, le=24)):
    """Chiffre d'affaires mensuel sur les `months` derniers mois (pour le graphique)."""
    try:
        return get_monthly_revenue_history(months)
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur lors de la lecture des données Odoo : {e}")
