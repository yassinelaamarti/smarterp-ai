"""
Détection d'alertes à partir des KPIs déjà calculés (cache PostgreSQL).

Aucun appel Odoo ici : on réutilise les valeurs et tendances déjà
disponibles via kpi_calculator.get_kpis(), donc cette évaluation
est quasi instantanée.

Deux types de règles :
- Seuils absolus (ex: trop de produits en stock bas)
- Seuils sur tendance (ex: chute du CA par rapport au mois précédent)
"""

from typing import Optional
from app.schemas.kpi import KPI
from app.schemas.alert import Alert

RuleResult = Optional[tuple[str, str]]  # (severity, message)


def _check_stock_alerts(kpi: KPI, settings: dict[str, float]) -> RuleResult:
    critical = settings.get("stock_critical", 10.0)
    warning = settings.get("stock_warning", 0.0)
    if kpi.value > critical:
        return "critical", f"{int(kpi.value)} produits en stock critique — réapprovisionnement urgent recommandé."
    if kpi.value > warning:
        return "warning", f"{int(kpi.value)} produit(s) en stock bas à surveiller."
    return None


def _check_late_orders(kpi: KPI, settings: dict[str, float]) -> RuleResult:
    critical = settings.get("late_orders_critical", 5.0)
    warning = settings.get("late_orders_warning", 0.0)
    if kpi.value > critical:
        return "critical", f"{int(kpi.value)} commandes en retard de livraison — risque pour la satisfaction client."
    if kpi.value > warning:
        return "warning", f"{int(kpi.value)} commande(s) en retard de livraison."
    return None


def _check_trend_drop(kpi: KPI, critical_at: float, warning_at: float, label: str) -> RuleResult:
    """critical_at / warning_at sont des seuils négatifs, ex: -15 pour -15%."""
    if kpi.change_percent is None:
        return None
    if kpi.change_percent <= critical_at:
        return "critical", f"{label} a chuté de {abs(kpi.change_percent)}% par rapport au mois précédent."
    if kpi.change_percent <= warning_at:
        return "warning", f"{label} est en baisse de {abs(kpi.change_percent)}% par rapport au mois précédent."
    return None


from sqlalchemy.orm import Session
from app.models.kpi_cache import KPIHistoryCache
from app.services.date_utils import current_month_str

def evaluate_alerts(kpis: list[KPI], settings: dict[str, float] | None = None, db: Session | None = None) -> list[Alert]:
    if settings is None:
        settings = {
            "stock_critical": 10.0,
            "stock_warning": 0.0,
            "late_orders_critical": 5.0,
            "late_orders_warning": 0.0,
            "revenue_critical": -15.0,
            "revenue_warning": -5.0,
            "new_orders_critical": -30.0,
            "new_orders_warning": -20.0,
            "conversion_rate_critical": -30.0,
            "conversion_rate_warning": -20.0,
            "pipeline_value_critical": -40.0,
            "pipeline_value_warning": -30.0,
            "active_customers_critical": -30.0,
            "active_customers_warning": -20.0,
        }

    alerts = []
    for kpi in kpis:
        if kpi.id == "stock_alerts":
            result = _check_stock_alerts(kpi, settings)
        elif kpi.id == "late_orders":
            result = _check_late_orders(kpi, settings)
        elif kpi.id == "revenue":
            result = _check_trend_drop(kpi, settings.get("revenue_critical", -15.0), settings.get("revenue_warning", -5.0), "Le chiffre d'affaires")
        elif kpi.id == "new_orders":
            result = _check_trend_drop(kpi, settings.get("new_orders_critical", -30.0), settings.get("new_orders_warning", -20.0), "Le nombre de nouvelles commandes")
        elif kpi.id == "conversion_rate":
            result = _check_trend_drop(kpi, settings.get("conversion_rate_critical", -30.0), settings.get("conversion_rate_warning", -20.0), "Le taux de conversion")
        elif kpi.id == "pipeline_value":
            result = _check_trend_drop(kpi, settings.get("pipeline_value_critical", -40.0), settings.get("pipeline_value_warning", -30.0), "La valeur du pipeline CRM")
        elif kpi.id == "active_customers":
            result = _check_trend_drop(kpi, settings.get("active_customers_critical", -30.0), settings.get("active_customers_warning", -20.0), "Le nombre de clients actifs")
        else:
            continue

        if result:
            severity, message = result
            alerts.append(Alert(id=kpi.id, kpi_id=kpi.id, severity=severity, message=message, is_anomaly=False))

    # Détection d'anomalies statistiques par l'IA
    if db is not None:
        cur_month = current_month_str()
        for kpi in kpis:
            # Récupérer l'historique des mois précédents uniquement (exclure le mois en cours)
            history_records = (
                db.query(KPIHistoryCache)
                .filter(KPIHistoryCache.kpi_id == kpi.id, KPIHistoryCache.month != cur_month)
                .all()
            )
            history_values = [r.value for r in history_records]

            if len(history_values) >= 3:
                import math
                n = len(history_values)
                mean = sum(history_values) / n
                variance = sum((x - mean) ** 2 for x in history_values) / n
                std_dev = math.sqrt(variance)

                if std_dev > 0:
                    z_score = (kpi.value - mean) / std_dev
                    # Seuil d'anomalie à 1.8 pour les petits échantillons de démo
                    if abs(z_score) >= 1.8:
                        severity = "critical" if abs(z_score) >= 2.2 else "warning"
                        direction = "Hausse" if z_score > 0 else "Baisse"
                        message = f"[Anomalie IA] {direction} anormale détectée pour {kpi.label.lower()} : la valeur actuelle ({kpi.value} {kpi.unit or ''}) s'écarte significativement de l'historique (Z-score: {z_score:+.2f}, moyenne: {mean:.1f})."
                        alerts.append(Alert(
                            id=f"anomaly_{kpi.id}",
                            kpi_id=kpi.id,
                            severity=severity,
                            message=message,
                            is_anomaly=True
                        ))

    return alerts


