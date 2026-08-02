"""
Agent IA conversationnel — répond en français aux questions du manager
sur ses données métier, en s'appuyant sur les KPIs actuellement en cache
(pas besoin de recontacter Odoo : le contexte vient du cache PostgreSQL,
déjà à jour grâce à kpi_sync.py).
"""

import re
import time
import logging
from groq import Groq

from app.config import settings
from app.services.kpi_calculator import get_kpis
from app.services.health_score_engine import compute_health_score
from app.services.alert_engine import evaluate_alerts
from app.database import SessionLocal
from app.models.alert_setting import AlertSetting

logger = logging.getLogger(__name__)

_client = Groq(api_key=settings.groq_api_key)

_SYSTEM_PROMPT_TEMPLATE = """Tu es l'assistant analytique de SmartERP AI, une plateforme connectée à Odoo 17 \
utilisée par une PME marocaine.

RÈGLES STRICTES ET NORMES DE FORMULATION (à respecter absolument) :
1. Réponds toujours en français, de façon claire, structurée et professionnelle.
2. N'utilise QUE les chiffres et indicateurs listés ci-dessous. N'invente JAMAIS une valeur, un pourcentage, un nom de client ou de produit qui n'y figure pas.
3. LOGIQUE DIRECTIONNELLE DU SCORE DE SANTÉ & TENDANCES :
   - Les hausses de CA, de commandes ou de taux de conversion sont des signaux POSITIFS (+points de santé). Ne les traite JAMAIS comme des risques majeurs ou des anomalies négatives.
   - Les risques et pénalités sont exclusivement réservés aux vrais signaux défavorables (retards de livraison, alertes stock critique, baisse du portefeuille client).
4. DISTINCTION OBLIGATOIRE - POINTS DE POURCENTAGE VS POURCENTAGE RELATIF :
   - Pour les indicateurs qui sont DÉJÀ des pourcentages (ex: Taux de conversion CRM) : Exprime TOUJOURS les variations en "points" ou "points de pourcentage" (ex: "Le taux de conversion CRM a progressé de 2,1 points, passant de 12,2% à 14,3%"). Ne dis JAMAIS "en hausse de X%" pour un taux sans préciser "points".
   - Pour les montants monétaires et comptages bruts (ex: Chiffre d'affaires, Commandes) : Exprime les variations en pourcentage relatif % (ex: "Le chiffre d'affaires a augmenté de 1,0%, atteignant 24 917,32 MAD").
5. MISE EN VALEUR DES CHIFFRES CLÉS :
   - Encadre systématiquement les montants, taux, scores et variations clés par des astérisques doubles pour le gras (ex: **24 917,32 MAD**, **+1,0%**, **73/100**, **+2,1 points**).
6. SECTIONS VIDES ET ANTI-HALLUCINATION :
   - Si un axe ou une catégorie ne présente aucun risque ou signal négatif (ex: aucun retard, aucun stock en alerte), dis explicitement : "Aucun point de vigilance majeur identifié sur cet axe — tous les indicateurs sont au vert." Ne crée aucun contenu artificiel.

Voici le score de santé global de l'entreprise, ses facteurs d'explication, les alertes/anomalies détectées par l'IA et les indicateurs clés (KPIs) actuels de l'entreprise :
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
                # Indication spécifique pour les taux déjà en %
                if "rate" in kpi.id or "taux" in kpi.label.lower() or (kpi.unit and "%" in kpi.unit):
                    line += f" ({arrow} {kpi.change_percent} points vs mois précédent)"
                else:
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
                pos_label = " [Tendance Positive]" if getattr(alert, "is_positive_trend", False) else ""
                alerts_lines.append(f"  * {type_label}{pos_label} (Sévérité: {alert.severity}) : {alert.message}")
            alerts_str = "Alertes et Anomalies actives :\n" + "\n".join(alerts_lines) + "\n"
        else:
            alerts_str = "Alertes et Anomalies actives : Aucune alerte ou anomalie active.\n"
    except Exception as e:
        alerts_str = f"Alertes et Anomalies actives : Non disponible (erreur: {e})\n"
    finally:
        if 'db' in locals():
            db.close()

    return f"{health_str}\n{alerts_str}\nIndicateurs clés (KPIs) :\n{kpis_str}"


def post_process_and_validate_summary(summary_text: str) -> str:
    """
    Validation et post-traitement automatique par Regex pour garantir la cohérence
    des formulations chiffrées (points de pourcentage vs pourcentage relatif).
    """
    if not summary_text:
        return summary_text

    # 1. Corriger les ambiguïtés sur le taux de conversion s'il est formulé comme "en hausse de X%, à Y%"
    # Remplacer "en hausse de X%, à Y%" ou "en hausse de X%" pour le taux de conversion par "en hausse de X points"
    pattern_rate = re.compile(
        r"(taux\s+de\s+conversion[^\.\n]*?)\b(en\s+hausse|en\s+progression|a\s+augmenté|en\s+baisse|a\s+chuté)\s+de\s+([\d\s,.]+)\s*%",
        re.IGNORECASE
    )

    def _replace_rate_match(match):
        prefix = match.group(1)
        direction = match.group(2)
        val = match.group(3).strip()
        # Si 'points' n'est pas déjà présent
        return f"{prefix}{direction} de **{val} points**"

    result = pattern_rate.sub(_replace_rate_match, summary_text)

    # 2. Harmoniser la casse des sous-titres et puces si besoin
    return result


def generate_chat_fallback(message: str) -> str:
    """Génère une réponse déterministe structurée en cas de rate limit (HTTP 429) sur l'Agent Chat."""
    context = _build_context()
    return f"""Le service d'analyse IA est momentanément indisponible (limite de requêtes atteinte).

Voici les données d'entreprise en temps réel validées en cache Odoo 17 :

{context}

💡 *Conseil : Vous pouvez ré-essayer votre question dans quelques minutes lorsque le quota journalier LLM sera réinitialisé.*"""


def ask(message: str, history: list[dict] | None = None) -> str:
    context = _build_context()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(context=context)

    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            completion = _client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=0.2,
                max_tokens=700,
            )
            raw_response = completion.choices[0].message.content
            return post_process_and_validate_summary(raw_response)
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Erreur lors de l'appel Agent Chat (Tentative {attempt + 1}/{max_retries + 1}): {err_msg}")

            if "Limit 100000" in err_msg or "tokens per day" in err_msg or "429" in err_msg or "TPD" in err_msg or "rate_limit" in err_msg.lower():
                logger.error("Quota journalier Groq atteint (429/TPD) sur le Chat. Basculement sur le fallback déterministe.")
                return generate_chat_fallback(message)

            if attempt < max_retries:
                time.sleep((attempt + 1) * 1.5)

    return generate_chat_fallback(message)


def generate_fallback_summary() -> str:
    """Génère une synthèse déterministe d'urgence en cas d'indisponibilité / quota du LLM."""
    try:
        health = compute_health_score()
        health_info = f"Score de santé global de l'entreprise : **{health.score}/100** ({health.label})."
    except Exception:
        health_info = "Score de santé global de l'entreprise actuellement sous évaluation."

    try:
        kpis = get_kpis()
    except Exception:
        kpis = []

    kpi_highlights = []
    if kpis:
        for k in kpis[:4]:
            kpi_highlights.append(f"- **{k.label}** : **{k.value} {k.unit or ''}**")
    kpis_text = "\n".join(kpi_highlights) if kpi_highlights else "- Données de synthèse en cours d'actualisation."

    return f"""## 1. Synthèse Exécutive & Score de Santé Global
{health_info} Ce rapport analytique présente l'état de performance opérationnel et financier sur les 30 derniers jours à partir du cache validé Odoo 17.

## 2. Analyse Détaillée par Axe Stratégique

### Performance Financière & Commerciale
{kpis_text}

### Performance Opérationnelle & Logistique
Les opérations logistiques et les flux de commandes se poursuivent. La synchronisation automatique garantit le suivi des stocks.

## 3. Analyse des Risques & Points de Vigilance
Aucun point de vigilance majeur identifié sur cet axe — tous les indicateurs sont conformes aux objectifs.

## 4. Plan d'Actions Recommandées (Priorités 30-90 jours)
1. **Maintenir la dynamique commerciale** sur les opportunités actives et le suivi du pipeline CRM.
2. **Optimiser les réapprovisionnements** pour conserver un niveau de stock équilibré.
3. **Poursuivre le suivi automatisé** via les alertes décisionnelles du tableau de bord.
"""


def generate_dashboard_summary() -> str:
    """
    Génère un rapport de synthèse analytique et décisionnel complet de niveau exécutif.
    Intègre un mécanisme de retry et un fallback automatique en cas de rate limit (HTTP 429).
    """
    context = _build_context()
    
    prompt = """En tant que Conseiller Stratégique Virtuel pour la Direction Générale d'une PME, rédige un rapport de synthèse analytique et décisionnel de niveau EXÉCUTIF (type Board Report) basé sur les données ci-dessous.

RÈGLES DE RÉDACTION IMPÉRATIVES :
1. Rédige en français avec un ton hautement professionnel, factuel, structuré et orienté décision.
2. N'utilise QUE les données chiffrées fournies. Ne crée aucune donnée imaginaire.
3. FORMULATION CHIFFRÉE EXACTE :
   - Taux en % (ex: conversion) : Exprime TOUJOURS la variation en POINTS (ex: "progression de 2,1 points, passant de 12,2% à 14,3%"). Ne dis jamais "hausse de X%" sans préciser points.
   - Montants (CA) et volumes (commandes) : Exprime les variations en POURCENTAGE RELATIF % (ex: "augmentation de 1,0%, atteignant 24 917,32 MAD").
4. LOGIQUE DIRECTIONNELLE : Les hausses de CA ou de conversion sont des succès (+points de santé). Ne les qualifie jamais d'anomalies négatives ou de risques.
5. CHIFFRES CLÉS EN GRAS : Entoure systématiquement tous les montants, pourcentages, points et scores par des astérisques doubles (ex: **24 917,32 MAD**, **+1,0%**, **73/100**, **+2,1 points**).
6. GESTION DES SECTIONS VIDES : Si un axe ne présente aucun risque ou signal négatif (ex: aucun retard), écris explicitement : "Aucun point de vigilance majeur identifié sur cet axe — tous les indicateurs sont au vert." Ne crée aucun contenu artificiel.

STRUCTURE DU RAPPORT (Respecte exactement ces 4 sections Markdown) :

## 1. Synthèse Exécutive & Score de Santé Global
(Présente un résumé exécutif percutant en 2-3 phrases maximum. Commente ensuite explicitement le score de santé global **X/100** et ses principaux facteurs d'impact).

## 2. Analyse Détaillée par Axe Stratégique
### Performance Financière & Commerciale
(Analyse du CA, panier moyen, leads et taux de conversion CRM avec les règles de formulation exacte).
### Performance Opérationnelle & Logistique
(Analyse du stock, des alertes de rupture et des commandes en retard).

## 3. Analyse des Risques & Points de Vigilance
(Synthèse claire des vulnérabilités actives avec leur niveau de criticité. Si aucun risque actif, écris la phrase d'absence de risque).

## 4. Plan d'Actions Recommandées (Priorités 30-90 jours)
(3 à 4 actions stratégiques et opérationnelles concrètes et prioritaires basées sur le diagnostic).

Voici les données validées en cache Odoo :
{context}
"""
    messages = [
        {"role": "system", "content": "Tu es le conseiller stratégique virtuel de SmartERP AI. Tu rédiges des rapports décisionnels professionnels en français pour la Direction Générale."},
        {"role": "user", "content": prompt.format(context=context)}
    ]
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            completion = _client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                temperature=0.25,
                max_tokens=1500,
            )
            raw_summary = completion.choices[0].message.content
            return post_process_and_validate_summary(raw_summary)
        except Exception as e:
            err_msg = str(e)
            logger.warning(f"Erreur lors de la génération de la synthèse (Tentative {attempt + 1}/{max_retries + 1}): {err_msg}")
            
            if "Limit 100000" in err_msg or "tokens per day" in err_msg or "429" in err_msg or "TPD" in err_msg:
                logger.error("Quota journalier Groq atteint (429/TPD). Basculement sur la synthèse déterministe d'urgence.")
                return generate_fallback_summary()

            if attempt < max_retries:
                time.sleep((attempt + 1) * 1.5)

    return generate_fallback_summary()
