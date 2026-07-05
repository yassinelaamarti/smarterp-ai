"""
Agent IA conversationnel — répond en français aux questions du manager
sur ses données métier, en s'appuyant sur les KPIs actuellement en cache
(pas besoin de recontacter Odoo : le contexte vient du cache PostgreSQL,
déjà à jour grâce à kpi_sync.py).
"""

from groq import Groq

from app.config import settings
from app.services.kpi_calculator import get_kpis

_client = Groq(api_key=settings.groq_api_key)

_SYSTEM_PROMPT_TEMPLATE = """Tu es l'assistant analytique de SmartERP AI, une plateforme connectée à Odoo 17 \
utilisée par une PME marocaine.

Réponds toujours en français, de façon claire, concise et orientée action. \
Tu peux proposer des recommandations concrètes basées sur les chiffres ci-dessous.

Voici les indicateurs clés (KPIs) actuels de l'entreprise :
{context}

Si une question porte sur une donnée que tu n'as pas dans cette liste, dis-le \
honnêtement plutôt que d'inventer un chiffre."""


def _build_context() -> str:
    kpis = get_kpis()
    if not kpis:
        return "(aucune donnée disponible pour le moment)"

    lines = []
    for kpi in kpis:
        line = f"- {kpi.label} : {kpi.value} {kpi.unit or ''}".strip()
        if kpi.trend and kpi.change_percent is not None:
            arrow = {"up": "↑", "down": "↓", "stable": "→"}[kpi.trend]
            line += f" ({arrow} {kpi.change_percent}% vs mois précédent)"
        lines.append(line)
    return "\n".join(lines)


def ask(message: str, history: list[dict] | None = None) -> str:
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=_build_context())

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    completion = _client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.3,
        max_tokens=600,
    )
    return completion.choices[0].message.content
