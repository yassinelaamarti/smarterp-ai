import uuid
from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.root_cause_analysis import RootCauseAnalysis, DEFAULT_TENANT_ID
from app.services.root_cause_analysis import compute_root_cause_data, generate_rca_explanation
from app.services.kpi_calculator import get_kpis

router = APIRouter(prefix="/api", tags=["Root Cause Analysis"])


class BreakdownItemSchema(BaseModel):
    dimension: str
    segment: str
    delta: float
    contribution_pct: float


class RootCauseResponseSchema(BaseModel):
    id: str
    tenant_id: str
    anomaly_id: str
    kpi_name: str
    period_current: str
    period_previous: str
    delta_total: float
    delta_total_pct: float
    breakdown: list[BreakdownItemSchema]
    residual_pct: float
    explanation: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/anomalies/{anomaly_id}/root-cause")
def get_root_cause_for_anomaly(anomaly_id: str, db: Session = Depends(get_db)):
    """
    Retourne la décomposition et l'explication des causes racines pour une anomalie.
    Utilise le cache PostgreSQL s'il existe déjà pour cette anomalie, sinon le calcule et le sauvegarde.
    """
    existing = db.query(RootCauseAnalysis).filter(RootCauseAnalysis.anomaly_id == anomaly_id).first()
    if existing:
        return _format_rca_record(existing)

    # Récupérer les infos sur le KPI correspondant si possible
    kpis = get_kpis()
    kpi_match = next((k for k in kpis if k.id == anomaly_id or k.id == anomaly_id.replace("anomaly_", "")), None)

    kpi_id = kpi_match.id if kpi_match else anomaly_id.replace("anomaly_", "")
    cur_val = kpi_match.value if kpi_match else 0.0
    change_pct = kpi_match.change_percent if kpi_match else -8.0

    rca_data = compute_root_cause_data(
        kpi_id=kpi_id,
        current_value=cur_val,
        change_percent=change_pct
    )
    explanation = generate_rca_explanation(rca_data)

    new_rca = RootCauseAnalysis(
        tenant_id=DEFAULT_TENANT_ID,
        anomaly_id=anomaly_id,
        kpi_name=rca_data["kpi_name"],
        period_current=rca_data["period_current"],
        period_previous=rca_data["period_previous"],
        delta_total=rca_data["delta_total"],
        delta_total_pct=rca_data["delta_total_pct"],
        breakdown=rca_data["breakdown"],
        residual_pct=rca_data["residual_pct"],
        explanation=explanation
    )
    db.add(new_rca)
    db.commit()
    db.refresh(new_rca)

    return _format_rca_record(new_rca)


def _format_rca_record(record: RootCauseAnalysis) -> dict:
    return {
        "id": str(record.id),
        "tenant_id": str(record.tenant_id),
        "anomaly_id": record.anomaly_id,
        "kpi_name": record.kpi_name,
        "period_current": record.period_current,
        "period_previous": record.period_previous,
        "delta_total": record.delta_total,
        "delta_total_pct": record.delta_total_pct,
        "breakdown": record.breakdown,
        "residual_pct": record.residual_pct,
        "explanation": record.explanation or "",
        "created_at": record.created_at.isoformat() if record.created_at else ""
    }
