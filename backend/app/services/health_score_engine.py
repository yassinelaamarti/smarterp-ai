"""
Calcule un score de santé global (0-100) à partir des KPIs et alertes déjà
disponibles en cache — aucun nouvel appel Odoo, calcul quasi instantané.

Principe : on part de 100, et chaque signal négatif (alerte, tendance en
baisse) retire des points ; chaque signal positif (tendance en hausse) en
ajoute un peu. Le détail (factors) est renvoyé pour que l'utilisateur (et
l'agent IA) puissent expliquer précisément d'où vient le score.
"""

from app.schemas.health_score import HealthScore, HealthScoreFactor
from app.services.kpi_calculator import get_kpis
from app.services.alert_engine import evaluate_alerts

CRITICAL_ALERT_PENALTY = 15
WARNING_ALERT_PENALTY = 5
MAX_REVENUE_PENALTY = 15
MAX_REVENUE_BONUS = 5


KPI_CATEGORIES = {
    "revenue": "finance",
    "new_orders": "finance",
    "stock_alerts": "operations",
    "late_orders": "operations",
    "conversion_rate": "crm",
    "pipeline_value": "crm",
    "active_customers": "crm",
}

CATEGORY_PENALTIES = {
    "finance": {"critical": 20, "warning": 8, "label": "Finance"},
    "operations": {"critical": 15, "warning": 5, "label": "Opérations"},
    "crm": {"critical": 10, "warning": 3, "label": "CRM"},
}

DEFAULT_PENALTIES = {"critical": 15, "warning": 5, "label": "Général"}


from app.database import SessionLocal

def compute_health_score() -> HealthScore:
    db = SessionLocal()
    try:
        kpis = get_kpis()
        alerts = evaluate_alerts(kpis, db=db)
    finally:
        db.close()

    score = 100.0
    factors: list[HealthScoreFactor] = []

    # Calcul des pénalités basées sur les catégories d'alertes actives
    for alert in alerts:
        kpi_id = alert.kpi_id
        severity = alert.severity  # 'critical' or 'warning'
        
        category = KPI_CATEGORIES.get(kpi_id)
        penalties = CATEGORY_PENALTIES.get(category, DEFAULT_PENALTIES) if category else DEFAULT_PENALTIES
        penalty_value = penalties.get(severity, 5)
        
        impact = -penalty_value
        score += impact
        
        cat_label = penalties["label"]
        factors.append(HealthScoreFactor(
            label=f"[{cat_label}] {alert.message}",
            impact=impact,
        ))

    # Bonus/Pénalité sur l'évolution du Chiffre d'Affaires (CA)
    revenue = next((k for k in kpis if k.id == "revenue"), None)
    if revenue and revenue.change_percent is not None:
        if revenue.change_percent < 0:
            # La baisse est déjà capturée par l'alerte de baisse du CA si elle dépasse les seuils,
            # mais on peut ajouter un ajustement fin ou un bonus en cas de hausse.
            pass
        elif revenue.change_percent > 0:
            impact = round(min(revenue.change_percent * 0.2, MAX_REVENUE_BONUS), 1)
            score += impact
            factors.append(HealthScoreFactor(
                label=f"[Finance] Chiffre d'affaires en hausse de {revenue.change_percent}%",
                impact=impact,
            ))

    score_int = max(0, min(100, round(score)))

    if score_int >= 80:
        label = "Excellente santé"
    elif score_int >= 60:
        label = "Bonne santé, à surveiller"
    elif score_int >= 40:
        label = "Vigilance requise"
    else:
        label = "Situation critique"

    if not factors:
        factors.append(HealthScoreFactor(label="Aucun signal notable détecté", impact=0))

    return HealthScore(score=score_int, label=label, factors=factors)

