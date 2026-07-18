"""
Synchronisation : va chercher les données fraîches dans Odoo
(via odoo_kpi_reader.py) et les écrit dans le cache PostgreSQL.

sync_all() est appelé :
- une fois au démarrage du backend
- puis périodiquement en arrière-plan (voir main.py)
- ou manuellement via POST /api/kpis/sync
"""

import logging
import random
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.kpi_cache import KPICache, KPIHistoryCache, RevenueHistoryCache
from app.services import odoo_kpi_reader
from app.services.date_utils import current_month_str, previous_month_str
from app.schemas.kpi import KPI

logger = logging.getLogger(__name__)


def sync_kpis(db: Session) -> list[KPI]:
    kpis = odoo_kpi_reader.get_kpis()
    for kpi in kpis:
        db.merge(KPICache(id=kpi.id, label=kpi.label, value=kpi.value, unit=kpi.unit))
    db.commit()
    return kpis


def sync_kpi_history(db: Session, kpis: list[KPI]) -> None:
    """Archive la valeur actuelle de chaque KPI pour le mois en cours.
    C'est cet historique qui permettra, le mois prochain, de calculer les tendances."""
    month = current_month_str()
    for kpi in kpis:
        db.merge(KPIHistoryCache(kpi_id=kpi.id, month=month, value=kpi.value))
    db.commit()


def sync_revenue_history(db: Session, months: int = 6) -> None:
    history = odoo_kpi_reader.get_monthly_revenue_history(months)
    for point in history:
        db.merge(RevenueHistoryCache(
            month=point["month"],
            label=point["label"],
            revenue=point["revenue"],
        ))
    db.commit()


def sync_all() -> None:
    """Rafraîchit tout le cache depuis Odoo. Ne lève jamais d'exception :
    en cas d'échec, le cache existant reste tel quel et l'erreur est juste loggée."""
    db = SessionLocal()
    try:
        logger.info("Synchronisation Odoo -> cache PostgreSQL en cours...")
        kpis = sync_kpis(db)
        sync_kpi_history(db, kpis)
        sync_revenue_history(db)
        
        # Générer et actualiser les recommandations IA actionnables en fonction des alertes
        try:
            from app.services.kpi_calculator import get_kpis as get_kpis_from_calculator
            from app.services.alert_engine import evaluate_alerts
            from app.services.recommendation_generator import generate_recommendations
            from app.models.alert_setting import AlertSetting
            
            settings_db = db.query(AlertSetting).all()
            settings_dict = {s.key: s.value for s in settings_db}
            
            fresh_kpis = get_kpis_from_calculator()
            alerts = evaluate_alerts(fresh_kpis, settings_dict, db=db)
            
            if alerts:
                logger.info(f"Génération automatique de recommandations pour {len(alerts)} alertes/anomalies...")
                generate_recommendations(db, alerts)
        except Exception as e:
            logger.error(f"Échec de la génération automatique des recommandations : {e}")

        logger.info("Synchronisation terminée avec succès.")
    except Exception:
        logger.exception("Échec de la synchronisation Odoo -> cache (le cache existant est conservé)")
    finally:
        db.close()


def seed_demo_previous_month(db: Session) -> None:
    """
    ⚠️ UNIQUEMENT POUR TESTER/DÉMONTRER LES TENDANCES EN LOCAL.

    Crée un historique factice du mois précédent (valeurs actuelles +/- une
    variation aléatoire), pour voir immédiatement les badges de tendance (↑/↓)
    sans attendre qu'un vrai mois calendaire s'écoule. À ne jamais appeler
    en production — les vraies tendances se construiront naturellement, mois
    après mois, via sync_kpi_history().
    """
    month = previous_month_str()
    current_rows = db.query(KPICache).all()
    for row in current_rows:
        factor = random.uniform(0.82, 1.18)
        db.merge(KPIHistoryCache(kpi_id=row.id, month=month, value=round(row.value * factor, 2)))
    db.commit()


def seed_demo_history(db: Session, months: int = 6) -> None:
    """
    Génère un historique factice sur plusieurs mois passés pour tous les KPIs actuels,
    permettant de tester l'analyse de tendance et la détection d'anomalies statistiques.
    """
    current_rows = db.query(KPICache).all()
    if not current_rows:
        return
        
    import datetime
    today = datetime.date.today()
    
    for row in current_rows:
        base_value = row.value
        # Si c'est le CA ou les commandes en retard, on décale l'historique
        # pour provoquer une anomalie statistique sur la valeur actuelle.
        if row.id == "revenue":
            # Valeur actuelle élevée -> historique bas
            historical_base = base_value * 0.5  # la valeur actuelle sera un pic à +100%
        elif row.id == "late_orders":
            # Valeur actuelle élevée (ex: 12) -> historique très bas (ex: 1)
            historical_base = 1.0
        else:
            historical_base = base_value
            
        for i in range(1, months + 1):
            total_months = today.month - 1 - i
            year = today.year + total_months // 12
            month_idx = total_months % 12 + 1
            month_str = f"{year:04d}-{month_idx:02d}"
            
            factor = random.uniform(0.9, 1.1)
            val = historical_base * factor
            db.merge(KPIHistoryCache(kpi_id=row.id, month=month_str, value=round(val, 2)))
            
    db.commit()

