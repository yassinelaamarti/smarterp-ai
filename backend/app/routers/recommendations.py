from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ai_recommendation import AIRecommendation
from app.models.user import User
from app.schemas.ai_recommendation import AIRecommendationSchema, AIRecommendationAuditSchema
from app.services.auth import get_current_active_user
from app.services.odoo_action_service import OdooActionService
from datetime import datetime

router = APIRouter(prefix="/api/recommendations", tags=["Recommandations IA"])


@router.get("/", response_model=list[AIRecommendationSchema])
def list_pending_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Recupere toutes les recommandations IA en attente d'execution."""
    return (
        db.query(AIRecommendation)
        .filter(AIRecommendation.status == "pending")
        .order_by(AIRecommendation.created_at.desc())
        .all()
    )


@router.get("/audit", response_model=list[AIRecommendationAuditSchema])
def get_recommendations_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Recupere l'historique complet d'audit des recommandations executees ou ignorees."""
    recs = (
        db.query(AIRecommendation)
        .filter(AIRecommendation.status.in_(["executed", "dismissed"]))
        .order_by(AIRecommendation.executed_at.desc())
        .all()
    )

    audit_data = []
    for r in recs:
        username = None
        if r.executed_by:
            user = db.query(User).filter(User.id == r.executed_by).first()
            if user:
                username = user.full_name or user.email

        audit_data.append({
            "id": r.id,
            "source_type": r.source_type,
            "title": r.title,
            "action_type": r.action_type,
            "action_payload": r.action_payload,
            "estimated_impact": r.estimated_impact,
            "status": r.status,
            "executed_by_name": username,
            "executed_at": r.executed_at,
            "created_at": r.created_at
        })

    return audit_data


@router.post("/{rec_id}/execute")
def execute_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Execute l'action recommandee dans Odoo apres validation stricte des parametres."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvee.")

    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cette recommandation a deja ete traitee (statut: {rec.status}).")

    try:
        # Executer l'action via le service de validation et d'integration Odoo
        res = OdooActionService.execute_action(rec.action_type, rec.action_payload, current_user, db)

        # Mettre a jour le statut en DB
        rec.status = "executed"
        rec.executed_by = current_user.id
        rec.executed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "message": res.get("message", "Action executee sur Odoo avec succes."),
            "odoo_response": res
        }
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur interne lors de l'execution sur Odoo : {e}")


@router.post("/{rec_id}/dismiss")
def dismiss_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ignore et archive la recommandation sans l'executer."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvee.")

    if rec.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cette recommandation a deja ete traitee (statut: {rec.status}).")

    rec.status = "dismissed"
    rec.executed_by = current_user.id
    rec.executed_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Recommandation ignoree avec succes."}
