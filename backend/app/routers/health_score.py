from fastapi import APIRouter
from app.schemas.health_score import HealthScore
from app.services.health_score_engine import compute_health_score

router = APIRouter(prefix="/api/health-score", tags=["Score de santé"])


@router.get("/", response_model=HealthScore)
def get_health_score():
    """Retourne le score de santé global (0-100) avec le détail de son calcul."""
    return compute_health_score()
