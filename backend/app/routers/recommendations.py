import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.ai_recommendation import AIRecommendation, AIActionLog, RecommendationStatus
from app.models.user import User
from app.schemas.ai_recommendation import AIRecommendationSchema, AIRecommendationAuditSchema
from app.services.auth import get_current_active_user
from app.services.odoo_action_service import OdooActionService, OdooActionValidationError

router = APIRouter(prefix="/api/recommendations", tags=["Recommandations IA"])


@router.get("/", response_model=list[AIRecommendationSchema])
def list_recommendations(
    tenant_id: Optional[uuid.UUID] = None,
    status: str = "pending",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Récupère les recommandations IA filtrées par tenant et statut (par défaut en attente)."""
    if not tenant_id:
        tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    now = datetime.utcnow()
    query = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.status == status
    )

    # N'affiche pas les recommandations expirées si le statut recherché est "pending"
    if status == "pending":
        query = query.filter(
            (AIRecommendation.expires_at == None) | (AIRecommendation.expires_at >= now)
        )

    return query.order_by(AIRecommendation.created_at.desc()).all()


@router.get("/audit", response_model=list[AIRecommendationAuditSchema])
def get_recommendations_audit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Récupère l'historique complet d'audit des actions tentées, réussies ou échouées."""
    results = (
        db.query(AIActionLog, AIRecommendation, User)
        .outerjoin(AIRecommendation, AIActionLog.recommendation_id == AIRecommendation.id)
        .join(User, AIActionLog.executed_by == User.id)
        .order_by(AIActionLog.executed_at.desc())
        .all()
    )

    audit_data = []
    for log, rec, user in results:
        title = rec.title if rec else f"Action {log.action_type.value}"
        source_type = rec.source_type.value if rec else "anomaly"
        estimated_impact = rec.estimated_impact if rec else None
        created_at = rec.created_at if rec else log.executed_at
        status = rec.status.value if rec else ("executed" if log.success else "failed")

        audit_data.append({
            "id": log.id,
            "recommendation_id": log.recommendation_id,
            "source_type": source_type,
            "title": title,
            "action_type": log.action_type.value,
            "action_payload": log.action_payload,
            "odoo_result": log.odoo_result,
            "estimated_impact": estimated_impact,
            "status": status,
            "executed_by_name": user.full_name or user.email,
            "executed_at": log.executed_at,
            "created_at": created_at,
            "success": log.success,
            "error_message": log.error_message
        })

    return audit_data


@router.post("/{rec_id}/execute")
def execute_recommendation(
    rec_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Exécute l'action recommandée sur Odoo, applique les validations, et consigne le résultat dans l'audit log."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée.")

    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cette recommandation a déjà été traitée (statut: {rec.status.value}).")

    try:
        # Enrichir le payload avec le titre et l'explication de la recommandation pour garantir le contexte à toutes les actions
        exec_payload = {
            **(rec.action_payload or {}),
            "recommendation_title": rec.title,
            "recommendation_explanation": rec.explanation,
            "title": rec.title,
            "explanation": rec.explanation
        }
        res = OdooActionService.execute_action(rec.action_type.value, exec_payload, current_user, db)

        # Créer le log d'audit en succès
        log = AIActionLog(
            id=uuid.uuid4(),
            recommendation_id=rec.id,
            tenant_id=rec.tenant_id,
            action_type=rec.action_type,
            action_payload=rec.action_payload,
            odoo_result=res,
            executed_by=current_user.id,
            executed_at=datetime.utcnow(),
            success=True,
            error_message=None
        )
        db.add(log)

        # Mettre à jour le statut en DB
        rec.status = RecommendationStatus.executed
        rec.executed_by = current_user.id
        rec.executed_at = datetime.utcnow()
        db.commit()

        return {
            "status": "success",
            "message": res.get("message", "Action exécutée sur Odoo avec succès."),
            "odoo_response": res
        }

    except Exception as e:
        db.rollback()
        # Créer le log d'audit en échec
        log = AIActionLog(
            id=uuid.uuid4(),
            recommendation_id=rec.id,
            tenant_id=rec.tenant_id,
            action_type=rec.action_type,
            action_payload=rec.action_payload,
            odoo_result=None,
            executed_by=current_user.id,
            executed_at=datetime.utcnow(),
            success=False,
            error_message=str(e)
        )
        db.add(log)

        # Mettre à jour le statut en échec
        rec.status = RecommendationStatus.failed
        rec.executed_by = current_user.id
        rec.executed_at = datetime.utcnow()
        rec.failure_reason = str(e)
        db.commit()

        if isinstance(e, OdooActionValidationError):
            raise HTTPException(status_code=400, detail=str(e))
        else:
            raise HTTPException(status_code=500, detail=f"Erreur interne lors de l'exécution sur Odoo : {e}")


@router.post("/{rec_id}/dismiss")
def dismiss_recommendation(
    rec_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Ignore et archive la recommandation sans l'exécuter, en consignant l'action dans le log d'audit."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée.")

    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cette recommandation a déjà été traitée (statut: {rec.status.value}).")

    # Mettre à jour la recommandation
    rec.status = RecommendationStatus.dismissed
    rec.executed_by = current_user.id
    rec.executed_at = datetime.utcnow()

    # Créer le log d'audit pour le rejet
    log = AIActionLog(
        id=uuid.uuid4(),
        recommendation_id=rec.id,
        tenant_id=rec.tenant_id,
        action_type=rec.action_type,
        action_payload=rec.action_payload,
        odoo_result={"info": "Recommandation ignorée par l'utilisateur"},
        executed_by=current_user.id,
        executed_at=datetime.utcnow(),
        success=True,
        error_message=None
    )
    db.add(log)
    db.commit()

    return {"status": "success", "message": "Recommandation ignorée avec succès."}


@router.post("/{rec_id}/acknowledge")
def acknowledge_recommendation(
    rec_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Marque une recommandation informative comme lue/vue (statut: acknowledged)."""
    rec = db.query(AIRecommendation).filter(AIRecommendation.id == rec_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée.")

    if rec.status != RecommendationStatus.pending:
        raise HTTPException(status_code=400, detail=f"Cette recommandation a déjà été traitée (statut: {rec.status.value}).")

    rec.status = RecommendationStatus.acknowledged
    rec.executed_by = current_user.id
    rec.executed_at = datetime.utcnow()

    log = AIActionLog(
        id=uuid.uuid4(),
        recommendation_id=rec.id,
        tenant_id=rec.tenant_id,
        action_type=rec.action_type,
        action_payload=rec.action_payload,
        odoo_result={"info": "Recommandation marquée comme lue/vue par l'utilisateur"},
        executed_by=current_user.id,
        executed_at=datetime.utcnow(),
        success=True,
        error_message=None
    )
    db.add(log)
    db.commit()

    return {"status": "success", "message": "Recommandation marquée comme lue avec succès."}

