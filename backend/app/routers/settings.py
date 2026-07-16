from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert_setting import AlertSetting
from app.schemas.settings import AlertSettingSchema, AlertSettingsUpdate, ReportScheduleSchema
from app.services.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/settings", tags=["Configuration"])


@router.get("/", response_model=list[AlertSettingSchema])
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Récupère tous les paramètres de configuration des seuils d'alertes."""
    settings = db.query(AlertSetting).order_by(AlertSetting.key).all()
    return settings


@router.put("/", response_model=list[AlertSettingSchema])
def update_settings(
    payload: AlertSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Met à jour les paramètres de configuration en base de données."""
    try:
        updated_settings = []
        for setting in payload.settings:
            db_setting = db.query(AlertSetting).filter(AlertSetting.key == setting.key).first()
            if db_setting:
                db_setting.value = setting.value
                db_setting.label = setting.label
                updated_settings.append(db_setting)
            else:
                # Si le paramètre n'existe pas, on le crée
                new_setting = AlertSetting(
                    key=setting.key,
                    value=setting.value,
                    label=setting.label
                )
                db.add(new_setting)
                updated_settings.append(new_setting)
        
        db.commit()
        # Rafraîchir
        for s in updated_settings:
            db.refresh(s)
            
        return updated_settings
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour des paramètres : {e}"
        )


@router.get("/report-schedule", response_model=ReportScheduleSchema)
def get_report_schedule(current_user: User = Depends(get_current_active_user)):
    """Récupère la configuration de planification de rapports pour l'utilisateur connecté."""
    return {
        "report_schedule": current_user.report_schedule or "none",
        "report_email": current_user.report_email or current_user.email
    }


@router.put("/report-schedule", response_model=ReportScheduleSchema)
def update_report_schedule(
    payload: ReportScheduleSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Met à jour la configuration de planification de rapports pour l'utilisateur connecté."""
    try:
        current_user.report_schedule = payload.report_schedule
        current_user.report_email = payload.report_email
        db.commit()
        db.refresh(current_user)
        return {
            "report_schedule": current_user.report_schedule,
            "report_email": current_user.report_email
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la mise à jour de la planification : {e}"
        )


@router.post("/report-schedule/trigger-test")
def trigger_test_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Génère et envoie immédiatement un rapport de test à l'utilisateur connecté."""
    from app.services.report_scheduler import send_single_report
    success = send_single_report(db, current_user)
    if success:
        return {"status": "success", "message": "Rapport de test généré et envoyé (ou simulé) avec succès."}
    else:
        raise HTTPException(
            status_code=500,
            detail="Erreur lors du déclenchement du rapport de test."
        )

