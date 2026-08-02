"""
Calcule un score de santé global (0-100) à partir des KPIs et alertes déjà
disponibles en cache — aucun nouvel appel Odoo, calcul quasi instantané.

Méthodologie avec rendements décroissants :
1. Déduplication par KPI (conserve le signal le plus sévère pour chaque KPI).
2. Tri des pénalités par ordre de gravité décroissante.
3. Application de coefficients d'amortissement dégressifs (100%, 70%, 50%, 35%, 25%, 15%)
   pour éviter qu'un cumul d'anomalies mineures n'écrase artificiellement le score à 0.
"""

from app.schemas.health_score import HealthScore, HealthScoreFactor
from app.services.kpi_calculator import get_kpis
from app.services.alert_engine import evaluate_alerts
from app.database import SessionLocal

CRITICAL_ALERT_PENALTY = 15
WARNING_ALERT_PENALTY = 5
MAX_REVENUE_PENALTY = 15
MAX_REVENUE_BONUS = 5

# Mapping exhaustif de tous les KPIs vers leur domaine métier principal
KPI_CATEGORIES = {
    # Finance
    "revenue": "finance",
    "new_orders": "finance",
    "unpaid_invoices": "finance",
    # Opérations
    "stock_alerts": "operations",
    "stock_value": "operations",
    "late_orders": "operations",
    # CRM & Clients
    "conversion_rate": "crm",
    "pipeline_value": "crm",
    "active_customers": "crm",
    "new_leads": "crm",
}

CATEGORY_PENALTIES = {
    "finance": {"critical": 20, "warning": 8, "label": "Finance"},
    "operations": {"critical": 15, "warning": 5, "label": "Opérations"},
    "crm": {"critical": 10, "warning": 3, "label": "CRM"},
}

DEFAULT_PENALTIES = {"critical": 15, "warning": 5, "label": "Général"}

# Facteurs de pondération dégressive par rang de gravité (Pondération à rendements décroissants)
DEGRESSIVE_WEIGHTS = [1.0, 0.70, 0.50, 0.35, 0.25, 0.15]


def compute_health_score() -> HealthScore:
    db = SessionLocal()
    try:
        kpis = get_kpis()
        raw_alerts = evaluate_alerts(kpis, db=db)
    finally:
        db.close()

    # ÉTAPE 1 : Déduplication par KPI (Conserver uniquement le signal le plus sévère pour chaque KPI)
    dedup_map = {}
    for alert in raw_alerts:
        kpi_id = alert.kpi_id
        if kpi_id not in dedup_map:
            dedup_map[kpi_id] = alert
        else:
            existing = dedup_map[kpi_id]
            # Priorité à critical sur warning, puis aux anomalies IA
            if alert.severity == "critical" and existing.severity != "critical":
                dedup_map[kpi_id] = alert
            elif alert.severity == existing.severity and alert.is_anomaly:
                dedup_map[kpi_id] = alert

    dedup_alerts = list(dedup_map.values())

    # ÉTAPE 2 : Préparation et calcul de la pénalité de base pour chaque alerte
    penalty_items = []
    for alert in dedup_alerts:
        category = KPI_CATEGORIES.get(alert.kpi_id)
        penalties = CATEGORY_PENALTIES.get(category, DEFAULT_PENALTIES) if category else DEFAULT_PENALTIES
        base_val = penalties.get(alert.severity, 5)

        penalty_items.append({
            "alert": alert,
            "base_penalty": base_val,
            "cat_label": penalties["label"],
        })

    # Trier par pénalité de base décroissante (les alertes les plus lourdes en premier)
    penalty_items.sort(key=lambda x: x["base_penalty"], reverse=True)

    # ÉTAPE 3 : Application des coefficients d'amortissement dégressifs
    score = 100.0
    factors: list[HealthScoreFactor] = []

    for i, item in enumerate(penalty_items):
        weight = DEGRESSIVE_WEIGHTS[i] if i < len(DEGRESSIVE_WEIGHTS) else 0.15
        impact = round(-item["base_penalty"] * weight, 1)
        score += impact

        factors.append(HealthScoreFactor(
            label=f"[{item['cat_label']}] {item['alert'].message}",
            impact=impact,
        ))

    # ÉTAPE 4 : Prise en compte du Bonus sur l'évolution du Chiffre d'Affaires
    revenue = next((k for k in kpis if k.id == "revenue"), None)
    if revenue and revenue.change_percent is not None and revenue.change_percent > 0:
        impact = round(min(revenue.change_percent * 0.2, MAX_REVENUE_BONUS), 1)
        score += impact
        factors.append(HealthScoreFactor(
            label=f"[Finance] Chiffre d'affaires en hausse de {revenue.change_percent}%",
            impact=impact,
        ))

    # ÉTAPE 5 : Tri des facteurs par impact (les pénalités les plus importantes en premier)
    factors.sort(key=lambda f: f.impact)

    # Plafonnement final entre 0 et 100
    score_int = max(0, min(100, round(score)))

    # Attribution du libellé de statut
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
