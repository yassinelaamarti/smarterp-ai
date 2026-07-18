import json
import logging
from sqlalchemy.orm import Session
from app.models.ai_recommendation import AIRecommendation
from app.schemas.alert import Alert
from app.services.odoo_connector import odoo
from app.config import settings
from groq import Groq

logger = logging.getLogger(__name__)
_client = Groq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """Tu es le moteur d'intelligence decisionnelle de SmartERP AI.
Ta tache est de transformer une alerte ou anomalie active en une recommandation concrete, structuree et actionnable en un clic dans Odoo.

Tu dois repondre EXCLUSIVEMENT sous la forme d'un objet JSON strict avec les champs suivants :
1. "title" : Un titre court et percutant en francais (ex: "Reapprovisionner Customizable Desk", "Reactiver les 12 clients inactifs", "Relancer le lead commercial 'Interest in your products'").
2. "explanation" : Une explication business claire en francais reliant l'anomalie/alerte aux KPIs (ex: "Le stock de ce bureau est descendu a 0, bloquant les ventes futures.").
3. "action_type" : L'une des valeurs strictes suivantes : "restock_order", "send_email_campaign", "create_crm_activity", ou "none".
4. "action_payload" : Un dictionnaire JSON contenant les parametres precis de l'action :
   - Pour "restock_order" : {"product_id": <int>, "quantity": <int>}
   - Pour "send_email_campaign" : {"partner_ids": [<int>], "campaign_subject": "<string>"}
   - Pour "create_crm_activity" : {"lead_id": <int>, "activity_description": "<string>"}
   - Pour "none" : {}
5. "estimated_impact" : Une estimation court-terme de l'impact financier ou operationnel (ex: "+12 000 MAD de ventes potentielles", "Evite une rupture de stock client").

IMPORTANT : Tu dois utiliser UNIQUEMENT des identifiants (IDs) valides figurant dans la liste des items d'Odoo fournie par l'utilisateur. N'invente aucun ID de produit, de partenaire ou de lead.
"""


def generate_recommendations(db: Session, alerts: list[Alert]) -> None:
    """
    Parcourt les alertes actives et genere une recommandation IA pour chaque alerte si elle n'existe pas deja.
    """
    for alert in alerts:
        # Verifier si une recommandation existe deja pour cette source
        source_id = alert.id
        source_type = "anomaly" if alert.is_anomaly else "kpi_alert"

        existing = db.query(AIRecommendation).filter(
            AIRecommendation.source_id == source_id,
            AIRecommendation.source_type == source_type,
            AIRecommendation.status == "pending"
        ).first()

        if existing:
            continue

        # Charger le contexte Odoo selon l'alerte
        odoo_context = ""
        suggested_action_type = "none"

        try:
            if "stock" in alert.kpi_id or "stock" in alert.message.lower():
                # Alerte de stock -> recuperer les produits en stock bas
                products = odoo.search_read(
                    "product.product",
                    [["qty_available", "<", 10], ["type", "=", "product"]],
                    ["id", "name", "qty_available"],
                    limit=5
                )
                odoo_context = f"Produits Odoo en stock bas disponibles pour reapprovisionnement :\n{products}"
                suggested_action_type = "restock_order"

            elif "customer" in alert.kpi_id or "revenue" in alert.kpi_id or "order" in alert.kpi_id:
                # Alerte commerciale/client -> recuperer des partenaires
                partners = odoo.search_read(
                    "res.partner",
                    [],
                    ["id", "name", "email"],
                    limit=5
                )
                odoo_context = f"Partenaires/Clients Odoo disponibles pour campagne de relance :\n{partners}"
                suggested_action_type = "send_email_campaign"

            elif "lead" in alert.kpi_id or "conversion" in alert.kpi_id or "pipeline" in alert.kpi_id:
                # Alerte CRM -> recuperer les leads ou opportunites actives
                leads = odoo.search_read(
                    "crm.lead",
                    [["type", "=", "opportunity"], ["active", "=", True]],
                    ["id", "name"],
                    limit=5
                )
                odoo_context = f"Opportunites/Leads CRM Odoo disponibles pour relance :\n{leads}"
                suggested_action_type = "create_crm_activity"
        except Exception as e:
            logger.error(f"Impossible de recuperer le contexte Odoo pour l'alerte {alert.id}: {e}")

        # Construire le prompt pour l'appel LLM
        user_prompt = f"""Genere une recommandation actionnable pour l'alerte suivante :
Message d'alerte : "{alert.message}"
KPI concerne : "{alert.kpi_id}"
Severite : "{alert.severity}"

Contexte de donnees reelles provenant d'Odoo :
{odoo_context}

Recommandation pour le type d'action attendu : "{suggested_action_type}".
Rappel : renvoie uniquement le JSON strict sans aucun autre texte autour.
"""

        try:
            completion = _client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"}  # Force le mode JSON strict sur Groq
            )

            response_text = completion.choices[0].message.content
            logger.info(f"Reponse brute LLM Recommandation : {response_text}")

            data = json.loads(response_text)

            # Creer la recommandation en DB
            new_rec = AIRecommendation(
                source_type=source_type,
                source_id=source_id,
                title=data.get("title", f"Action pour {alert.kpi_id}"),
                explanation=data.get("explanation", alert.message),
                action_type=data.get("action_type", "none"),
                action_payload=data.get("action_payload", {}),
                estimated_impact=data.get("estimated_impact", "Impact positif attendu"),
                status="pending"
            )

            db.add(new_rec)
            db.commit()
            logger.info(f"Recommandation IA creee avec succes pour la source {source_id} : '{new_rec.title}'")

        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la generation de recommandation pour l'alerte {alert.id}: {e}")
