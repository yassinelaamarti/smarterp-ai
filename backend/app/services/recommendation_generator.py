import json
import logging
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.ai_recommendation import AIRecommendation, RecommendationSource, RecommendationAction, RecommendationStatus
from app.schemas.alert import Alert
from app.services.odoo_connector import odoo
from app.config import settings
from groq import Groq

logger = logging.getLogger(__name__)
_client = Groq(api_key=settings.groq_api_key)

DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")

SYSTEM_PROMPT = """Tu es un module d'aide à la décision pour un dirigeant PME.
On te donne un signal détecté (anomalie, alerte, score de santé) avec ses données réelles provenant d'Odoo.
Tu dois répondre UNIQUEMENT sous la forme d'un objet JSON valide et strict, sans aucun autre texte ou mise en forme (pas de markdown).

Structure JSON attendue :
{
  "title": string (max 80 caractères, orienté action, ex: "Réactiver 17 clients inactifs", "Réapprovisionner Customizable Desk"),
  "explanation": string (2-3 phrases, business-friendly, pas de jargon technique),
  "action_type": "restock_order" | "send_email_campaign" | "create_crm_activity" | "none",
  "action_payload": object (voir schémas ci-dessous),
  "estimated_impact": {
    "label": string (ex: "+12 000 MAD", "Évite une rupture de stock"),
    "confidence": "low" | "medium" | "high"
  }
}

Schémas pour "action_payload" selon "action_type" :
1. Pour "restock_order" :
   {
     "product_id": int (l'ID du produit Odoo à commander),
     "quantity": int (la quantité à commander)
   }
2. Pour "send_email_campaign" :
   {
     "partner_ids": list[int] (les IDs des partenaires Odoo ciblés),
     "template_id": null
   }
3. Pour "create_crm_activity" :
   {
     "partner_id": int (l'ID du partenaire Odoo),
     "assigned_user_id": null,
     "activity_type": "Todo",
     "note": string (description ou instructions pour l'activité CRM)
   }
4. Pour "none" :
   {}

Règles strictes :
- N'invente JAMAIS un product_id, partner_id ou quantité qui n'apparaît pas dans les données fournies.
- Si aucune action fiable n'est déductible des données, utilise action_type="none".
- Si les données fournies ne permettent pas d'identifier un ID réel pour l'action, mets obligatoirement action_type="none".
- estimated_impact doit rester qualitatif si les données ne permettent pas un calcul précis.
"""


def generate_recommendations(db: Session, alerts: list[Alert]) -> None:
    """
    Parcourt les alertes actives et genere une recommandation IA pour chaque alerte si elle n'existe pas deja.
    """
    for alert in alerts:
        # Verifier si une recommandation existe deja pour cette source
        source_id = alert.id
        if alert.kpi_id == "health_score":
            source_type = RecommendationSource.health_score
        elif alert.is_anomaly:
            source_type = RecommendationSource.anomaly
        else:
            source_type = RecommendationSource.kpi_alert

        existing = db.query(AIRecommendation).filter(
            AIRecommendation.source_id == source_id,
            AIRecommendation.source_type == source_type,
            AIRecommendation.status == RecommendationStatus.pending
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
                # Alerte commerciale/client -> recuperer des partenaires avec e-mail
                partners = odoo.search_read(
                    "res.partner",
                    [["email", "!=", False]],
                    ["id", "name", "email"],
                    limit=5
                )
                odoo_context = f"Partenaires/Clients Odoo avec e-mail disponibles pour campagne de relance :\n{partners}"
                suggested_action_type = "send_email_campaign"

            elif "lead" in alert.kpi_id or "conversion" in alert.kpi_id or "pipeline" in alert.kpi_id:
                # Alerte CRM -> recuperer les opportunites ou partenaires actifs
                partners = odoo.search_read(
                    "res.partner",
                    [],
                    ["id", "name"],
                    limit=5
                )
                odoo_context = f"Partenaires/Clients Odoo pour lesquels creer une activite CRM de suivi :\n{partners}"
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
                response_format={"type": "json_object"}  # Force le mode JSON strict
            )

            response_text = completion.choices[0].message.content
            logger.info(f"Reponse brute LLM Recommandation : {response_text}")

            data = json.loads(response_text)

            # Extraire et valider l'impact estimé
            impact_raw = data.get("estimated_impact", {})
            if isinstance(impact_raw, str):
                estimated_impact = {"label": impact_raw, "confidence": "medium"}
            else:
                estimated_impact = {
                    "label": impact_raw.get("label", "Impact positif attendu"),
                    "confidence": impact_raw.get("confidence", "medium")
                }

            # Valider le type d'action par rapport à l'Enum
            action_type_str = data.get("action_type", "none")
            try:
                action_type = RecommendationAction(action_type_str)
            except ValueError:
                action_type = RecommendationAction.none

            # Creer la recommandation en DB
            new_rec = AIRecommendation(
                id=uuid.uuid4(),
                tenant_id=DEFAULT_TENANT_ID,
                source_type=source_type,
                source_id=source_id,
                title=data.get("title", f"Action pour {alert.kpi_id}"),
                explanation=data.get("explanation", alert.message),
                action_type=action_type,
                action_payload=data.get("action_payload", {}),
                estimated_impact=estimated_impact,
                status=RecommendationStatus.pending,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )

            db.add(new_rec)
            db.commit()
            logger.info(f"Recommandation IA creee avec succes pour la source {source_id} : '{new_rec.title}'")

        except Exception as e:
            db.rollback()
            logger.error(f"Erreur lors de la generation de recommandation pour l'alerte {alert.id}: {e}")
