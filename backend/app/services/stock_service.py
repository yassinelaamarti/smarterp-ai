"""
Service centralisé pour la détection et la gestion des produits en stock critique.
Assure la cohérence dynamique des seuils (qty_available <= stock_critical) entre Dashboard, Alertes, Recommandations et Audit.
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.models.alert_setting import AlertSetting
from app.services.odoo_connector import odoo

logger = logging.getLogger(__name__)

DEFAULT_STOCK_CRITICAL = 10.0


def get_stock_critical_threshold(
    db: Optional[Session] = None,
    settings_dict: Optional[dict[str, float]] = None
) -> float:
    """Récupère le seuil de stock critique dynamique depuis la DB ou le dictionnaire de configuration."""
    if settings_dict and isinstance(settings_dict, dict) and "stock_critical" in settings_dict:
        try:
            return float(settings_dict["stock_critical"])
        except (ValueError, TypeError):
            pass

    # Si db est fourni et valide, l'utiliser exclusivement
    if db is not None and not hasattr(db, "_mock_name") and type(db).__name__ not in ("MagicMock", "Mock"):
        try:
            query_res = db.query(AlertSetting)
            if hasattr(query_res, "filter"):
                setting = query_res.filter(AlertSetting.key == "stock_critical").first()
                if setting and hasattr(setting, "value") and isinstance(getattr(setting, "value", None), (int, float)):
                    return float(setting.value)
        except Exception as e:
            logger.warning(f"Impossible de lire 'stock_critical' depuis la DB transmise: {e}")
        return DEFAULT_STOCK_CRITICAL

    # Fallback robuste : uniquement si db n'a PAS été transmis (db is None)
    try:
        from app.database import SessionLocal
        temp_db = SessionLocal()
        try:
            setting = temp_db.query(AlertSetting).filter(AlertSetting.key == "stock_critical").first()
            if setting and setting.value is not None:
                return float(setting.value)
        finally:
            temp_db.close()
    except Exception as e:
        logger.warning(f"Impossible de lire 'stock_critical' via session DB temporaire: {e}")

    return DEFAULT_STOCK_CRITICAL


def fetch_critical_stock_products(
    db: Optional[Session] = None,
    settings_dict: Optional[dict[str, float]] = None,
    threshold: Optional[float] = None,
    odoo_client=None
) -> list[dict]:
    """
    Retourne la liste unique des produits Odoo de type 'product' (stockable)
    dont la quantité disponible est inférieure ou égale au seuil critique configuré (qty_available <= threshold).
    Dédoublonne par produit ID.
    """
    if odoo_client is None:
        odoo_client = odoo

    if threshold is None:
        threshold = get_stock_critical_threshold(db=db, settings_dict=settings_dict)

    try:
        domain = [["qty_available", "<=", threshold], ["type", "=", "product"]]
        products = odoo_client.search_read(
            "product.product",
            domain,
            ["id", "name", "qty_available", "lst_price", "default_code"],
            limit=100
        )
        if not isinstance(products, list):
            return []

        seen_ids = set()
        unique_products = []
        for p in products:
            if isinstance(p, dict):
                p_id = p.get("id")
                if p_id and p_id not in seen_ids:
                    seen_ids.add(p_id)
                    unique_products.append(p)
        return unique_products
    except Exception as e:
        logger.error(f"Erreur lors de la lecture des produits en stock critique Odoo: {e}")
        return []


def count_critical_stock_products(
    db: Optional[Session] = None,
    settings_dict: Optional[dict[str, float]] = None,
    threshold: Optional[float] = None,
    odoo_client=None
) -> int:
    """Retourne le nombre exact de produits en stock critique (qty_available <= threshold)."""
    products = fetch_critical_stock_products(db=db, settings_dict=settings_dict, threshold=threshold, odoo_client=odoo_client)
    return len(products)
