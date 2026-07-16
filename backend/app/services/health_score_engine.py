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


def compute_health_score() -> HealthScore:
    kpis = get_kpis()
    alerts = evaluate_alerts(kpis)

    score = 100.0
    factors: list[HealthScoreFactor] = []

    critical_count = sum(1 for a in alerts if a.severity == "critical")
    warning_count = sum(1 for a in alerts if a.severity == "warning")

    if critical_count:
        impact = -CRITICAL_ALERT_PENALTY * critical_count
        score += impact
        factors.append(HealthScoreFactor(
            label=f"{critical_count} alerte(s) critique(s) active(s)",
            impact=impact,
        ))

    if warning_count:
        impact = -WARNING_ALERT_PENALTY * warning_count
        score += impact
        factors.append(HealthScoreFactor(
            label=f"{warning_count} alerte(s) d'avertissement active(s)",
            impact=impact,
        ))

    revenue = next((k for k in kpis if k.id == "revenue"), None)
    if revenue and revenue.change_percent is not None:
        if revenue.change_percent < 0:
            impact = -round(min(abs(revenue.change_percent) * 0.5, MAX_REVENUE_PENALTY), 1)
            score += impact
            factors.append(HealthScoreFactor(
                label=f"Chiffre d'affaires en baisse de {abs(revenue.change_percent)}%",
                impact=impact,
            ))
        elif revenue.change_percent > 0:
            impact = round(min(revenue.change_percent * 0.2, MAX_REVENUE_BONUS), 1)
            score += impact
            factors.append(HealthScoreFactor(
                label=f"Chiffre d'affaires en hausse de {revenue.change_percent}%",
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
