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
MAX_INDIVIDUAL_RECOMMENDATIONS = 12

ALLOWED_ACTIONS_PER_DOMAIN = {
    "stock": ["restock_order", "none"],
    "customer": ["send_email_campaign", "none"],
    "revenue": ["send_email_campaign", "none"],
    "crm": ["create_crm_activity", "none"],
    "global_trend": ["none"],
}

SYSTEM_PROMPT = """Tu es un module d'aide à la décision pour un dirigeant PME.
On te donne un signal détecté (anomalie, alerte) avec ses données réelles provenant d'Odoo.
Tu dois répondre UNIQUEMENT sous la forme d'un objet JSON valide et strict, sans aucun autre texte ou mise en forme.

Structure JSON attendue :
{
  "title": string (max 80 caractères, orienté action),
  "explanation": string (2-3 phrases, business-friendly),
  "action_type": string (doit correspondre STRICTEMENT à l'une des valeurs autorisées fournies),
  "action_payload": object,
  "estimated_impact": {
    "label": string,
    "confidence": "low" | "medium" | "high"
  }
}
"""


def _get_allowed_actions_for_domain(domain: str) -> list[str]:
    """Accès direct au dictionnaire des garde-fous."""
    return ALLOWED_ACTIONS_PER_DOMAIN.get(domain, ["none"])


def _compute_priority_score(item: dict) -> float:
    """Calcul unifié de la priorité financière (MAD à risque) cross-domaine."""
    domain = item.get("domain", "global_trend")
    data = item.get("data", {})
    alert = item.get("alert")
    severity = alert.severity if alert else "warning"
    severity_mult = 1.5 if severity == "critical" else 1.0

    if domain == "stock":
        qty = data.get("qty_available", 0)
        price = data.get("lst_price", 0.0) or 0.0
        if qty <= 0:
            return (10000.0 + (10.0 * price)) * severity_mult
        else:
            return ((10.0 - qty) * price) * severity_mult
    elif domain in ("revenue", "customer"):
        kpi_val = data.get("kpi_value") if isinstance(data, dict) else None
        if kpi_val and isinstance(kpi_val, (int, float)) and kpi_val > 0:
            return float(kpi_val) * severity_mult
        base_val = 15000.0 if severity == "critical" else 5000.0
        return base_val * severity_mult
    elif domain == "crm":
        kpi_val = data.get("kpi_value") if isinstance(data, dict) else None
        if kpi_val and isinstance(kpi_val, (int, float)) and kpi_val > 0:
            return float(kpi_val) * severity_mult
        base_val = 10000.0 if severity == "critical" else 3000.0
        return base_val * severity_mult
    else:
        base_val = 5000.0 if severity == "critical" else 1000.0
        return base_val * severity_mult


def generate_recommendations(
    db: Session,
    alerts: list[Alert],
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID
) -> None:
    """Génère les recommandations IA dynamiques avec tri cross-domaine unifié."""
    active_source_ids = set()
    all_anomalies = []

    # 1. Collecte des anomalies de tous les domaines
    for alert in alerts:
        if "stock" in alert.kpi_id or "stock" in alert.message.lower():
            try:
                products = odoo.search_read(
                    "product.product",
                    [["qty_available", "<", 10], ["type", "=", "product"]],
                    ["id", "name", "qty_available", "lst_price"],
                )
                for p in products:
                    all_anomalies.append({
                        "source_id": f"stock_product_{p['id']}",
                        "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                        "domain": "stock",
                        "data": p,
                        "alert": alert
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du stock Odoo: {e}")
        else:
            domain = "global_trend"
            if "customer" in alert.kpi_id or "revenue" in alert.kpi_id:
                domain = "customer"
            elif "lead" in alert.kpi_id or "crm" in alert.kpi_id:
                domain = "crm"

            all_anomalies.append({
                "source_id": f"anomaly_{alert.id}",
                "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                "domain": domain,
                "data": alert.source_data.model_dump() if alert.source_data else {},
                "alert": alert
            })

    # 2. Calcul du score de priorité unifié cross-domaine
    for item in all_anomalies:
        item["priority_score"] = _compute_priority_score(item)

    # 3. Tri unifié par score de priorité décroissant
    all_anomalies_sorted = sorted(all_anomalies, key=lambda x: x["priority_score"], reverse=True)

    # 4. Plafond à 12 cartes individuelles + Résumé overflow
    if len(all_anomalies_sorted) > MAX_INDIVIDUAL_RECOMMENDATIONS:
        individual_to_process = all_anomalies_sorted[:MAX_INDIVIDUAL_RECOMMENDATIONS]
        overflow_items = all_anomalies_sorted[MAX_INDIVIDUAL_RECOMMENDATIONS:]
        
        for item in individual_to_process:
            active_source_ids.add(item["source_id"])

        overflow_source_id = "summary_overflow_anomalies"
        active_source_ids.add(overflow_source_id)
        _process_overflow_summary(db, tenant_id, overflow_source_id, len(overflow_items), overflow_items)
    else:
        individual_to_process = all_anomalies_sorted
        for item in individual_to_process:
            active_source_ids.add(item["source_id"])

    # 5. Traitement des recommandations individuelles
    for item in individual_to_process:
        source_id = item["source_id"]
        source_type = item["source_type"]
        domain = item["domain"]
        allowed_actions = _get_allowed_actions_for_domain(domain)

        _process_single_recommendation(
            db=db,
            tenant_id=tenant_id,
            source_id=source_id,
            source_type=source_type,
            domain=domain,
            item_data=item,
            allowed_actions=allowed_actions
        )

    # 6. Expiration des anomalies résolues ou basculées
    _expire_obsolete_recommendations(db, tenant_id, active_source_ids)


def _process_single_recommendation(
    db: Session,
    tenant_id: uuid.UUID,
    source_id: str,
    source_type: RecommendationSource,
    domain: str,
    item_data: dict,
    allowed_actions: list[str]
):
    existing = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.source_type == source_type,
        AIRecommendation.source_id == source_id,
        AIRecommendation.status == RecommendationStatus.pending
    ).first()

    prompt_allowed = ", ".join([f'"{a}"' for a in allowed_actions])
    user_prompt = f"""Génère une recommandation pour l'anomalie suivante :
Données : {item_data.get('data')}
Domaine : {domain}
Message d'alerte : {item_data['alert'].message}

GARDE-FOU STRICT : Tu dois OBLIGATOIREMENT choisir action_type uniquement parmi cette liste : [{prompt_allowed}].
Toute autre valeur est strictement interdite.
Rappel : réponds UNIQUEMENT sous la forme d'un objet JSON valide et strict.
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
            response_format={"type": "json_object"}
        )

        response_text = completion.choices[0].message.content
        data = json.loads(response_text)

        # Fallback neutre pour estimated_impact
        impact_raw = data.get("estimated_impact", {})
        if isinstance(impact_raw, str):
            estimated_impact = {"label": impact_raw, "confidence": "medium"}
        else:
            estimated_impact = {
                "label": impact_raw.get("label", "Impact non estimé"),
                "confidence": impact_raw.get("confidence", "medium")
            }

        parsed_action_type = data.get("action_type", "none")
        if parsed_action_type not in allowed_actions:
            logger.warning(
                f"Action '{parsed_action_type}' non autorisée pour le domaine '{domain}'. Fallback sur 'none'."
            )
            parsed_action_type = "none"

        try:
            action_enum = RecommendationAction(parsed_action_type)
        except ValueError:
            action_enum = RecommendationAction.none

        if existing:
            existing.title = data.get("title", existing.title)
            existing.explanation = data.get("explanation", existing.explanation)
            existing.action_type = action_enum
            existing.action_payload = data.get("action_payload", {})
            existing.estimated_impact = estimated_impact
            existing.expires_at = datetime.utcnow() + timedelta(days=7)
            db.commit()
            logger.info(f"Recommandation mise à jour en place pour source_id={source_id}")
        else:
            new_rec = AIRecommendation(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                source_type=source_type,
                source_id=source_id,
                title=data.get("title", f"Action pour {source_id}"),
                explanation=data.get("explanation", item_data['alert'].message),
                action_type=action_enum,
                action_payload=data.get("action_payload", {}),
                estimated_impact=estimated_impact,
                status=RecommendationStatus.pending,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            db.add(new_rec)
            db.commit()
            logger.info(f"Recommandation créée avec succès pour source_id={source_id}")

    except Exception as e:
        db.rollback()
        logger.error(f"Erreur lors de la génération de recommandation pour source_id={source_id}: {e}")


def _process_overflow_summary(
    db: Session,
    tenant_id: uuid.UUID,
    overflow_source_id: str,
    overflow_count: int,
    overflow_items: list[dict]
):
    item_descriptions = []
    for item in overflow_items:
        data = item.get("data", {})
        if item.get("domain") == "stock":
            item_descriptions.append(f"{data.get('name', 'Produit')} (Stock: {data.get('qty_available', 0)})")
        else:
            item_descriptions.append(item.get("source_id", "Anomalie"))

    details_str = ", ".join(item_descriptions[:10])
    if len(item_descriptions) > 10:
        details_str += f", et {len(item_descriptions) - 10} autres..."

    title = f"{overflow_count} autres anomalies secondaires à surveiller"
    explanation = (
        f"{overflow_count} anomalies supplémentaires sont actives au-delà des "
        f"{MAX_INDIVIDUAL_RECOMMENDATIONS} alertes prioritaires. Éléments inclus : {details_str}."
    )

    existing = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.source_type == RecommendationSource.anomaly,
        AIRecommendation.source_id == overflow_source_id,
        AIRecommendation.status == RecommendationStatus.pending
    ).first()

    estimated_impact = {"label": f"{overflow_count} anomalies en attente", "confidence": "medium"}

    if existing:
        existing.title = title
        existing.explanation = explanation
        existing.action_type = RecommendationAction.none
        existing.action_payload = {"overflow_count": overflow_count, "items": item_descriptions}
        existing.estimated_impact = estimated_impact
        existing.expires_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
    else:
        new_rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source_type=RecommendationSource.anomaly,
            source_id=overflow_source_id,
            title=title,
            explanation=explanation,
            action_type=RecommendationAction.none,
            action_payload={"overflow_count": overflow_count, "items": item_descriptions},
            estimated_impact=estimated_impact,
            status=RecommendationStatus.pending,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(new_rec)
        db.commit()


def _expire_obsolete_recommendations(db: Session, tenant_id: uuid.UUID, active_source_ids: set[str]):
    pending_recs = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.status == RecommendationStatus.pending
    ).all()

    for rec in pending_recs:
        if rec.source_id not in active_source_ids:
            rec.status = RecommendationStatus.expired
            logger.info(
                f"Recommandation pending '{rec.source_id}' expirée "
                f"(anomalie résolue ou basculée dans l'overflow suite au réordonnancement par priorité)."
            )
    db.commit()
