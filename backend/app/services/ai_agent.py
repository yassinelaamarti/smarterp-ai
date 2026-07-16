"""
Agent IA conversationnel — répond en français aux questions du manager
sur ses données métier, en s'appuyant sur les KPIs actuellement en cache
(pas besoin de recontacter Odoo : le contexte vient du cache PostgreSQL,
déjà à jour grâce à kpi_sync.py).
"""

from groq import Groq

from app.config import settings
from app.services.kpi_calculator import get_kpis
from app.services.health_score_engine import compute_health_score
from app.services.alert_engine import evaluate_alerts
from app.database import SessionLocal
from app.models.alert_setting import AlertSetting

_client = Groq(api_key=settings.groq_api_key)

_SYSTEM_PROMPT_TEMPLATE = """Tu es l'assistant analytique de SmartERP AI, une plateforme connectée à Odoo 17 \
utilisée par une PME marocaine.

RÈGLES STRICTES (à respecter absolument) :
1. Réponds toujours en français, de façon claire et concise.
2. N'utilise QUE les chiffres et indicateurs listés ci-dessous (y compris le score de santé global, ses facteurs, et les alertes/anomalies). N'invente JAMAIS une valeur, \
un pourcentage, un nom de client ou de produit qui n'y figure pas.
3. Si la question porte sur une donnée absente de cette liste (un client précis, \
un produit précis, une période non couverte, etc.), dis explicitement que tu ne \
disposes pas de cette information, plutôt que de deviner ou d'extrapoler.
4. Tu peux proposer des recommandations générales et raisonnables basées sur les \
tendances observées, mais distingue clairement un fait chiffré d'une recommandation.
5. Intègre et commente le score de santé global (0-100) ainsi que les alertes et anomalies actives détectées pour justifier tes analyses de santé ou tes diagnostics si l'utilisateur te pose des questions sur la situation de l'entreprise ou sur une alerte spécifique.

Voici le score de santé global de l'entreprise, ses facteurs d'explication, les alertes/anomalies détectées par l'IA et les indicateurs clés (KPIs) actuels de l'entreprise, seules données fiables \
à ta disposition :
{context}
"""


def _build_context() -> str:
    # 1. Récupérer le score de santé global
    try:
        health = compute_health_score()
        health_str = f"Score de santé global : {health.score}/100 - {health.label}\n"
        health_str += "Facteurs influençant le score :\n"
        for factor in health.factors:
            sign = "+" if factor.impact > 0 else ""
            health_str += f"  * {factor.label} ({sign}{factor.impact} pts)\n"
    except Exception as e:
        health_str = f"Score de santé global : Non disponible (erreur: {e})\n"

    # 2. Récupérer les KPIs
    kpis = get_kpis()
    if not kpis:
        kpis_str = "(aucun KPI disponible pour le moment)"
    else:
        lines = []
        for kpi in kpis:
            line = f"- {kpi.label} : {kpi.value} {kpi.unit or ''}".strip()
            if kpi.trend and kpi.change_percent is not None:
                arrow = {"up": "↑", "down": "↓", "stable": "→"}[kpi.trend]
                line += f" ({arrow} {kpi.change_percent}% vs mois précédent)"
            lines.append(line)
        kpis_str = "\n".join(lines)

    # 3. Récupérer les alertes et anomalies actives
    try:
        db = SessionLocal()
        settings_db = db.query(AlertSetting).all()
        settings_dict = {s.key: s.value for s in settings_db}
        alerts = evaluate_alerts(kpis, settings_dict, db=db)
        if alerts:
            alerts_lines = []
            for alert in alerts:
                type_label = "[ANOMALIE IA]" if alert.is_anomaly else "[SEUIL DÉPASSÉ]"
                alerts_lines.append(f"  * {type_label} (Sévérité: {alert.severity}) : {alert.message}")
            alerts_str = "Alertes et Anomalies actives :\n" + "\n".join(alerts_lines) + "\n"
        else:
            alerts_str = "Alertes et Anomalies actives : Aucune alerte ou anomalie active.\n"
    except Exception as e:
        alerts_str = f"Alertes et Anomalies actives : Non disponible (erreur: {e})\n"
    finally:
        if 'db' in locals():
            db.close()

    return f"{health_str}\n{alerts_str}\nIndicateurs clés (KPIs) :\n{kpis_str}"



def ask(message: str, history: list[dict] | None = None) -> str:
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=_build_context())

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    completion = _client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.2,  # bas volontairement : on privilégie la fiabilité à la créativité
        max_tokens=700,
    )
    return completion.choices[0].message.content


def generate_dashboard_summary() -> str:
    """Génère un rapport de synthèse analytique et décisionnel complet basé sur les KPIs actuels."""
    context = _build_context()
    
    prompt = """En tant qu'expert en business intelligence et conseiller stratégique pour PME, rédige un rapport de synthèse analytique et décisionnel basé sur le score de santé global et les indicateurs de performance (KPIs) de l'entreprise.

Ton rapport doit être rédigé en français, avec un ton professionnel, structuré, persuasif et orienté vers l'action. Utilise uniquement les données chiffrées fournies dans le contexte ci-dessous. Ne crée aucune donnée imaginaire.

Structure ton rapport de la manière suivante avec des titres clairs en Markdown :
1. **Synthèse de Performance Globale** : Un résumé exécutif clair de la santé générale de l'entreprise. Commente et explique explicitement le score de santé global (0-100) et ses facteurs d'impact (positifs et négatifs).
2. **Analyse Détaillée par Axe** :
   - **Performance Financière & Commerciale** (CA, Commandes, Panier Moyen, Leads, Conversion, Pipeline)
   - **Performance Opérationnelle** (Alertes stock, Valorisation, Commandes en retard)
3. **Risques & Points de Vigilance** : Identification claire des menaces (retards de livraison, ruptures de stocks, baisse de tendance) avec leur criticité.
4. **Recommandations Stratégiques Actionnables** : 3 à 4 actions concrètes et réalistes à court terme pour améliorer la situation commerciale ou opérationnelle.

Voici les indicateurs actuels :
{context}
"""
    messages = [
        {"role": "system", "content": "Tu es le conseiller stratégique virtuel de SmartERP AI. Tu rédiges des rapports décisionnels professionnels en français."},
        {"role": "user", "content": prompt.format(context=context)}
    ]
    
    completion = _client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.3,
        max_tokens=1500,
    )
    return completion.choices[0].message.content


