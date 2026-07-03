"""
Synchronisation : va chercher les données fraîches dans Odoo
(via odoo_kpi_reader.py) et les écrit dans le cache PostgreSQL.

sync_all() est appelé :
- une fois au démarrage du backend
- puis périodiquement en arrière-plan (voir main.py)
- ou manuellement via POST /api/kpis/sync
"""

import logging
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.kpi_cache import KPICache, RevenueHistoryCache
from app.services import odoo_kpi_reader

logger = logging.getLogger(__name__)


def sync_kpis(db: Session) -> None:
    kpis = odoo_kpi_reader.get_kpis()
    for kpi in kpis:
        db.merge(KPICache(id=kpi.id, label=kpi.label, value=kpi.value, unit=kpi.unit))
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
        sync_kpis(db)
        sync_revenue_history(db)
        logger.info("Synchronisation terminée avec succès.")
    except Exception:
        logger.exception("Échec de la synchronisation Odoo -> cache (le cache existant est conservé)")
    finally:
        db.close()
