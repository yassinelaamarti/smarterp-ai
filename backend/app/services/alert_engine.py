"""
Détection d'alertes à partir des KPIs déjà calculés (cache PostgreSQL).

Aucun appel Odoo ici : on réutilise les valeurs et tendances déjà
disponibles via kpi_calculator.get_kpis(), donc cette évaluation
est quasi instantanée.

Deux types de règles :
- Seuils absolus (ex: trop de produits en stock bas)
- Seuils sur tendance (ex: chute du CA par rapport au mois précédent)
"""

from typing import Callable, Optional
from app.schemas.kpi import KPI
from app.schemas.alert import Alert

RuleResult = Optional[tuple[str, str]]  # (severity, message)


def _check_stock_alerts(kpi: KPI) -> RuleResult:
    if kpi.value > 10:
        return "critical", f"{int(kpi.value)} produits en stock critique — réapprovisionnement urgent recommandé."
    if kpi.value > 0:
        return "warning", f"{int(kpi.value)} produit(s) en stock bas à surveiller."
    return None


def _check_late_orders(kpi: KPI) -> RuleResult:
    if kpi.value > 5:
        return "critical", f"{int(kpi.value)} commandes en retard de livraison — risque pour la satisfaction client."
    if kpi.value > 0:
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


_RULES: dict[str, Callable[[KPI], RuleResult]] = {
    "stock_alerts": _check_stock_alerts,
    "late_orders": _check_late_orders,
    "revenue": lambda k: _check_trend_drop(k, -15, -5, "Le chiffre d'affaires"),
    "new_orders": lambda k: _check_trend_drop(k, -30, -20, "Le nombre de nouvelles commandes"),
    "conversion_rate": lambda k: _check_trend_drop(k, -30, -20, "Le taux de conversion"),
    "pipeline_value": lambda k: _check_trend_drop(k, -40, -30, "La valeur du pipeline CRM"),
    "active_customers": lambda k: _check_trend_drop(k, -30, -20, "Le nombre de clients actifs"),
}


def evaluate_alerts(kpis: list[KPI]) -> list[Alert]:
    alerts = []
    for kpi in kpis:
        rule = _RULES.get(kpi.id)
        if not rule:
            continue
        result = rule(kpi)
        if result:
            severity, message = result
            alerts.append(Alert(id=kpi.id, kpi_id=kpi.id, severity=severity, message=message))
    return alerts
