from fastapi import APIRouter, HTTPException
from app.schemas.kpi import KPI
from app.services.kpi_calculator import get_kpis

router = APIRouter(prefix="/api/kpis", tags=["KPIs"])


@router.get("/", response_model=list[KPI])
def list_kpis():
    """Retourne les KPIs du dashboard, calculés en direct depuis Odoo."""
    try:
        return get_kpis()
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur lors de la lecture des données Odoo : {e}",
        )
