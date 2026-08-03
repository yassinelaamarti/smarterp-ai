import logging
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.database import SessionLocal
from app.services.stock_service import fetch_critical_stock_products
from app.models.ai_recommendation import AIRecommendation, RecommendationSource, RecommendationAction, RecommendationStatus
from app.models.alert_setting import AlertSetting
from app.schemas.alert import Alert
from app.services.odoo_connector import odoo
from groq import Groq

logger = logging.getLogger(__name__)

_client = Groq(api_key=settings.groq_api_key)

DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
MAX_INDIVIDUAL_RECOMMENDATIONS = 12

# Indicateur global pour bascule proactive si le quota TPD quotidien Groq est épuisé
_groq_quota_exhausted = False

SYSTEM_BATCH_PROMPT = """Tu es l'assistant IA décisionnel de SmartERP AI pour dirigeants de PME.
Ta mission est d'analyser les anomalies d'entreprise (stock, ventes, trésorerie, CRM) et de générer pour CHAQUE entité fournie une recommandation d'action ultra-pertinente, concrète et quantifiée.

RÈGLES D'ACTION STRICTES SELON LE DOMAINE :
1. Domaine "stock" (rupture, stock bas) :
   - Tu peux proposer action_type = "restock_order"
   - Le champ action_payload DOIT contenir "product_id" (entier) et "quantity" (entier suggéré pour réapprovisionner).
2. Domaine "customer_inactive" (baisse de CA, attrition client) :
   - Tu peux proposer action_type = "send_email_campaign"
   - Le champ action_payload DOIT contenir "segment_id" ou "customer_ids" et "template".
3. Domaine "crm" (opportunités stagnantes, pipeline en baisse) :
   - Tu peux proposer action_type = "create_crm_activity"
   - Le champ action_payload DOIT contenir "lead_id" et "summary".
4. Si aucune action automatique n'est possible :
   - Tu DOIS retourner action_type = "none" et action_payload = {}.

FORMAT JSON ATTENDU (STRICT) :
{
  "recommendations": [
    {
      "entity_key": "identifiant_exact_de_lentite",
      "title": "Titre court et percutant de l'action",
      "explanation": "Explication claire de la cause et du risque si rien n'est fait",
      "action_type": "restock_order | send_email_campaign | create_crm_activity | none",
      "action_payload": {},
      "estimated_impact": {"label": "+15 000 MAD de CA préservé", "confidence": "high | medium | low"}
    }
  ]
}
"""

ALLOWED_ACTIONS_PER_DOMAIN = {
    "stock": ["restock_order", "none"],
    "late_orders": ["create_follow_up_activity", "none"],
    "customer": ["send_email_campaign", "none"],
    "customer_inactive": ["send_email_campaign", "none"],
    "crm": ["send_email_campaign", "create_crm_activity", "none"],
}

# Mapping explicite et exhaustif des KPIs vers leurs domaines métiers respectifs
KPI_TO_DOMAIN = {
    # Performance Commerciale & CA
    "revenue": "revenue_trend",
    "new_orders": "revenue_trend",
    "avg_order_value": "revenue_trend",

    # Stock Agrégé (anomalies globales sans entité produit physique)
    "stock_alerts": "global_trend",
    "stock_value": "global_trend",

    # CRM & Portefeuille Client
    "new_leads": "crm",
    "conversion_rate": "crm",
    "pipeline_value": "crm",
    "active_customers": "crm",

    # Opérations & Logistique
    "late_orders": "global_trend",
    "unpaid_invoices": "global_trend",
    "unpaid_invoices_count": "global_trend",
}

# Libellés lisibles des KPIs pour les fallbacks non-stock
KPI_LABELS = {
    "revenue": "Chiffre d'affaires",
    "new_orders": "Nouvelles commandes",
    "avg_order_value": "Panier moyen",
    "stock_alerts": "Alertes stock bas",
    "stock_value": "Valorisation du stock",
    "new_leads": "Nouveaux leads CRM",
    "conversion_rate": "Taux de conversion CRM",
    "pipeline_value": "Pipeline CRM",
    "active_customers": "Clients actifs",
    "late_orders": "Commandes en retard",
    "unpaid_invoices": "Factures impayées",
    "unpaid_invoices_count": "Factures impayées",
}


def _get_allowed_actions_for_domain(domain: str) -> list[str]:
    return ALLOWED_ACTIONS_PER_DOMAIN.get(domain, ["none"])


def _fetch_target_partner_ids_for_campaign(entity_key: str = None, data: dict = None) -> list[int]:
    """
    Récupère de manière déterministe les partner_ids Odoo réels pour les campagnes d'emails.
    Critère métier :
    - Clients (res.partner) possédant un email valide (email != False).
    - Exclut les clients ayant passé une commande validée (sale.order état 'sale'/'done')
      au cours des 60 derniers jours (cibles d'attrition et de réactivation).
    - Fallback : Si moins de 3 clients répondent au seuil de 60j, sélectionne les clients les plus anciens avec email.
    """
    try:
        cutoff = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d 00:00:00")
        recent_orders = odoo.search_read(
            "sale.order",
            [["date_order", ">=", cutoff], ["state", "in", ["sale", "done"]]],
            ["partner_id"]
        ) or []
        recent_pids = {o["partner_id"][0] for o in recent_orders if o.get("partner_id")}

        all_partners = odoo.search_read(
            "res.partner",
            [["email", "!=", False]],
            ["id", "name", "email"]
        ) or []

        inactive_pids = [p["id"] for p in all_partners if p["id"] not in recent_pids]
        if len(inactive_pids) >= 3:
            return inactive_pids[:10]

        return [p["id"] for p in all_partners[:10]]
    except Exception as e:
        logger.error(f"Erreur lors de la recherche Odoo des partner_ids pour campagne email : {e}")
        return []


def _resolve_domain_from_entity_key(entity_key: str, data: dict = None, alert: Alert = None) -> str:
    """Détermine le domaine métier de manière déterministe par entité concrète ou mapping explicite de KPI."""
    # Règle 1 : Entités physiques/concrètes identifiées (IDs dans les données ou préfixes d'entités)
    if entity_key.startswith("product_") or (data and ("qty_available" in data or "product_id" in data)):
        return "stock"
    if entity_key.startswith("late_order_") or entity_key.startswith("order_") or (data and ("order_id" in data or "picking_id" in data)):
        return "late_orders"
    if entity_key.startswith("partner_") or (data and ("customer_id" in data or "partner_id" in data)):
        return "customer_inactive"
    if entity_key.startswith("lead_") or (data and ("lead_id" in data or "opportunity_id" in data)):
        return "crm"

    # Règle 2 : Extraction et dictionnaire de correspondance exacte KPI_TO_DOMAIN
    clean_kpi_id = None
    if alert and hasattr(alert, "kpi_id") and alert.kpi_id:
        clean_kpi_id = alert.kpi_id
    elif data and "kpi_id" in data:
        clean_kpi_id = data["kpi_id"]
    else:
        clean_kpi_id = entity_key
        while clean_kpi_id.startswith("anomaly_"):
            clean_kpi_id = clean_kpi_id[8:]
        for suffix in ["_drop", "_increase", "_alerts", "_critical", "_warning"]:
            if clean_kpi_id.endswith(suffix) and clean_kpi_id not in KPI_TO_DOMAIN:
                clean_kpi_id = clean_kpi_id[:-len(suffix)]

    if clean_kpi_id in KPI_TO_DOMAIN:
        return KPI_TO_DOMAIN[clean_kpi_id]

    logger.warning(
        f"Avertissement : kpi_id ou entity_key inconnu '{entity_key}' (clean_kpi_id: '{clean_kpi_id}'). "
        f"Fallback sur domain 'global_trend'."
    )
    return "global_trend"




def _compute_priority_score(entity_item: dict) -> float:
    """Calcule le score de priorité unifié intégrant l'impact financier réel."""
    score = 50.0

    causes = entity_item.get("causes", [entity_item])
    for c in causes:
        alert = c.get("alert")
        if alert:
            if alert.severity == "critical":
                score += 40.0
            elif alert.severity == "warning":
                score += 20.0
            elif alert.severity == "info":
                score += 5.0

            if alert.is_anomaly and not getattr(alert, "is_positive_trend", False):
                score += 10.0


    domain = entity_item.get("domain") or _resolve_domain_from_entity_key(entity_item.get("entity_key", ""))
    if domain == "stock":
        score += 15.0
    elif domain in ("customer", "customer_inactive", "crm"):
        score += 10.0

    data = entity_item.get("data", {})
    financial_impact = 0.0
    if domain == "stock":
        qty = data.get("qty_available", 0)
        price = data.get("lst_price", 100.0)
        qty_gap = max(0, 10 - qty)
        financial_impact = qty_gap * price
    elif domain in ("customer", "customer_inactive", "crm", "revenue_trend", "global_trend"):
        financial_impact = abs(data.get("amount", data.get("value", data.get("revenue_loss", 0.0))))

    score += min(financial_impact / 100.0, 50.0)
    return round(score, 2)


def _entity_needs_llm(db: Session, tenant_id: uuid.UUID, entity_item: dict) -> bool:
    """Vérifie si une entité a réellement besoin d'un appel LLM (nouvelle ou données modifiées de > 15%)."""
    entity_key = entity_item["entity_key"]
    existing = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.entity_key == entity_key,
        AIRecommendation.status.in_([RecommendationStatus.pending, RecommendationStatus.acknowledged])
    ).first()

    if not existing:
        return True

    # Si c'était un fallback générique indisponible, réessayer
    if existing.title.startswith("Analyse IA temporairement indisponible"):
        return True

    domain = entity_item["domain"]
    data = entity_item.get("data", {})

    if domain == "stock":
        old_qty = existing.action_payload.get("quantity")
        new_qty = data.get("qty_available", 0)
        if old_qty is None:
            return True
        if abs(new_qty - old_qty) >= max(2, old_qty * 0.15):
            return True
        return False
    elif domain in ("customer", "customer_inactive", "crm", "revenue_trend", "global_trend"):
        old_val = existing.action_payload.get("value", 0)
        new_val = data.get("amount", data.get("value", 0))
        if old_val == 0 or abs(new_val - old_val) / max(abs(old_val), 1.0) >= 0.15:
            return True
        return False

    return False


def _generate_fallback_data(db: Session, entity_item: dict) -> dict:
    """Génère un fallback intelligent (Option 1 pour le stock concrétisé, Option 2 avec libellé KPI pour le non-stock)."""
    entity_key = entity_item["entity_key"]
    domain = entity_item["domain"]
    data = entity_item.get("data", {})

    causes = entity_item.get("causes", [entity_item])
    first_alert = causes[0].get("alert") if causes else None

    clean_kpi_id = None
    if first_alert and hasattr(first_alert, "kpi_id") and first_alert.kpi_id:
        clean_kpi_id = first_alert.kpi_id
    elif "kpi_id" in data:
        clean_kpi_id = data["kpi_id"]
    else:
        clean_kpi_id = entity_key
        while clean_kpi_id.startswith("anomaly_"):
            clean_kpi_id = clean_kpi_id[8:]
        for suffix in ["_drop", "_increase", "_alerts", "_critical", "_warning"]:
            if clean_kpi_id.endswith(suffix) and clean_kpi_id not in KPI_LABELS:
                clean_kpi_id = clean_kpi_id[:-len(suffix)]

    kpi_label = KPI_LABELS.get(clean_kpi_id, "Anomalie")

    if domain == "stock":
        critical_setting = db.query(AlertSetting).filter(AlertSetting.key == "stock_critical").first()
        critical_threshold = critical_setting.value if critical_setting else 10.0

        qty_available = data.get("qty_available", 0)
        product_id = data.get("id")
        product_name = data.get("name", entity_key)
        lst_price = data.get("lst_price", 100.0)

        if qty_available >= critical_threshold:
            return {
                "title": f"Aucune action requise pour {product_name}",
                "explanation": f"Le produit {product_name} dispose d'un stock suffisant ({int(qty_available)} unité(s)).",
                "action_type": "none",
                "action_payload": {},
                "estimated_impact": {"label": "Stock suffisant", "confidence": "high"}
            }

        suggested_qty = max(int(critical_threshold - qty_available + 5), 5)
        estimated_impact_value = suggested_qty * lst_price

        return {
            "title": f"Réapprovisionner {product_name}",
            "explanation": (
                f"Stock critique détecté ({int(qty_available)} unité(s) disponible(s), seuil fixé à {int(critical_threshold)}). "
                f"Quantité suggérée automatiquement en l'absence d'analyse IA détaillée — à ajuster si besoin avant validation."
            ),
            "action_type": "restock_order",
            "action_payload": {"product_id": product_id, "quantity": suggested_qty},
            "estimated_impact": {"label": f"+{int(estimated_impact_value):,} MAD préservé", "confidence": "medium"}
        }
    elif domain == "late_orders":
        order_id = data.get("order_id")
        user_id = data.get("user_id")
        order_name = data.get("order_name", f"S000{order_id}" if order_id else "Commande")

        if order_id:
            return {
                "title": f"Planifier une relance pour la commande {order_name}",
                "explanation": f"La commande {order_name} accuse un retard de livraison. Une activité de suivi doit être créée sur Odoo pour le commercial assigné.",
                "action_type": "create_follow_up_activity",
                "action_payload": {
                    "order_id": order_id,
                    "user_id": user_id,
                    "summary": f"Relance livraison — Commande {order_name}",
                    "note": f"La commande {order_name} accuse un retard de livraison par rapport à la date planifiée. Merci de contacter le client et d'actualiser la livraison."
                },
                "estimated_impact": {"label": "Livraison accélérée", "confidence": "high"}
            }
        else:
            return {
                "title": "Commandes en retard de livraison",
                "explanation": "Des retards de livraison sont détectés sur plusieurs commandes. Veuillez auditer la logistique.",
                "action_type": "none",
                "action_payload": {},
                "estimated_impact": {"label": "Impact non estimé", "confidence": "low"}
            }
    else:
        return {
            "title": f"Analyse IA temporairement indisponible — {kpi_label}",
            "explanation": "Le service d'analyse est momentanément surchargé. Cette anomalie reste surveillée et sera réanalysée automatiquement au prochain cycle.",
            "action_type": "none",
            "action_payload": {},
            "estimated_impact": {"label": "Impact non estimé", "confidence": "low"}
        }


def _execute_batch_llm_call(entities_batch: list[dict], db: Session) -> dict[str, dict]:
    """Exécute un SEUL appel API LLM en mode batch pour toutes les entités du lot avec retries et fallback."""
    global _groq_quota_exhausted

    results = {}
    if not entities_batch:
        return results

    if _groq_quota_exhausted:
        logger.warning("Quota TPD Groq épuisé. Basculement proactif immédiat en fallback calculé.")
        for item in entities_batch:
            results[item["entity_key"]] = _generate_fallback_data(db, item)
        return results

    entities_descriptions = []
    for item in entities_batch:
        ekey = item["entity_key"]
        domain = item["domain"]
        data = item.get("data", {})
        allowed_actions = _get_allowed_actions_for_domain(domain)
        causes = item.get("causes", [])

        alert_msgs = []
        for c in causes:
            a = c.get("alert")
            if a:
                if c.get("source_type") == RecommendationSource.anomaly:
                    alert_msgs.append(f"Anomalie Z-Score: {a.message}")
                else:
                    alert_msgs.append(f"Alerte Seuil: {a.message}")
        causes_text = " | ".join(alert_msgs) if alert_msgs else "Alerte détectée"

        desc = (
            f"- Entité: {ekey}\n"
            f"  Domain: {domain}\n"
            f"  Données: {data}\n"
            f"  Causes: {causes_text}\n"
            f"  Allowed_actions: {allowed_actions}"
        )
        entities_descriptions.append(desc)

    user_batch_prompt = (
        f"Génère une recommandation pour CHAQUE entité ci-dessous ({len(entities_batch)} entités) :\n\n"
        + "\n\n".join(entities_descriptions)
        + "\n\nRéponds UNIQUEMENT sous la forme d'un objet JSON respectant le format requis."
    )

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Envoi d'un appel LLM BATCH pour {len(entities_batch)} entités (Tentative {attempt + 1})...")
            completion = _client.chat.completions.create(
                model=settings.groq_model,
                messages=[
                    {"role": "system", "content": SYSTEM_BATCH_PROMPT},
                    {"role": "user", "content": user_batch_prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )

            response_text = completion.choices[0].message.content
            parsed = json.loads(response_text)

            rec_list = parsed.get("recommendations", [])
            if not rec_list and isinstance(parsed, dict):
                if "entity_key" in parsed:
                    rec_list = [parsed]
                elif "title" in parsed:
                    rec_list = []
                    for item in entities_batch:
                        item_rec = dict(parsed)
                        item_rec["entity_key"] = item["entity_key"]
                        rec_list.append(item_rec)

            for rec_data in rec_list:
                ekey = rec_data.get("entity_key")
                if ekey:
                    results[ekey] = rec_data

            for item in entities_batch:
                ekey = item["entity_key"]
                if ekey not in results:
                    logger.warning(f"Entité {ekey} absente de la réponse batch LLM. Utilisation du fallback.")
                    results[ekey] = _generate_fallback_data(db, item)

            return results

        except Exception as err:
            err_msg = str(err)
            logger.warning(f"Erreur lors de l'appel LLM Batch (Tentative {attempt + 1}/{max_retries + 1}): {err_msg}")

            if "Limit 100000" in err_msg or "tokens per day" in err_msg or "TPD" in err_msg:
                logger.error("Quota journalier Groq (100k TPD) totalement atteint. Activation du fallback proactif.")
                _groq_quota_exhausted = True
                break

            if attempt < max_retries:
                sleep_time = (attempt + 1) * 2
                logger.info(f"Pause de {sleep_time}s avant retry (Backoff exponentiel)...")
                time.sleep(sleep_time)

    for item in entities_batch:
        results[item["entity_key"]] = _generate_fallback_data(db, item)

    return results


def generate_recommendations(
    db: Session,
    alerts: list[Alert],
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID
) -> None:
    """Génère les recommandations IA dynamiques en mode BATCH optimisé."""
    active_entity_keys = set()
    all_anomalies = []

    # 1. Collecte des anomalies de tous les domaines
    for alert in alerts:
        if "stock" in alert.kpi_id or "stock" in alert.message.lower():
            try:
                products = fetch_critical_stock_products(db=db, odoo_client=odoo)
                for p in products:
                    all_anomalies.append({
                        "source_id": f"stock_product_{p['id']}",
                        "entity_key": f"product_{p['id']}",
                        "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                        "domain": "stock",
                        "data": p,
                        "alert": alert
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la lecture du stock Odoo: {e}")
        elif "late_orders" in alert.kpi_id or "retard" in alert.message.lower():
            try:
                from datetime import date
                now_str = date.today().strftime("%Y-%m-%d 23:59:59")
                late_pickings = odoo.search_read(
                    "stock.picking",
                    [
                        ["picking_type_id.code", "=", "outgoing"],
                        ["state", "not in", ["done", "cancel"]],
                        ["scheduled_date", "<", now_str],
                        ["company_id", "=", settings.odoo_company_id],
                    ],
                    ["id", "name", "origin", "partner_id", "user_id"],
                    limit=10
                ) or []

                found_late_orders = False
                for pick in late_pickings:
                    origin = pick.get("origin")
                    if origin:
                        orders = odoo.search_read("sale.order", [["name", "=", origin]], ["id", "name", "user_id", "partner_id"], limit=1)
                        if orders:
                            ord_obj = orders[0]
                            o_id = ord_obj["id"]
                            u_id = ord_obj["user_id"][0] if ord_obj.get("user_id") else None
                            found_late_orders = True

                            all_anomalies.append({
                                "source_id": f"late_order_{o_id}",
                                "entity_key": f"late_order_{o_id}",
                                "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                                "domain": "late_orders",
                                "data": {
                                    "order_id": o_id,
                                    "user_id": u_id,
                                    "order_name": ord_obj.get("name"),
                                    "picking_name": pick.get("name")
                                },
                                "alert": alert
                            })

                if not found_late_orders:
                    ekey = alert.id if alert.id.startswith("anomaly_") or alert.id.startswith("kpi_") else f"anomaly_{alert.id}"
                    all_anomalies.append({
                        "source_id": ekey,
                        "entity_key": ekey,
                        "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                        "domain": "global_trend",
                        "data": alert.source_data.model_dump() if alert.source_data else {},
                        "alert": alert
                    })
            except Exception as e:
                logger.error(f"Erreur lors de la recherche des commandes en retard Odoo: {e}")
        else:
            ekey = alert.id if alert.id.startswith("anomaly_") or alert.id.startswith("kpi_") else f"anomaly_{alert.id}"
            domain = _resolve_domain_from_entity_key(ekey)

            all_anomalies.append({
                "source_id": ekey,
                "entity_key": ekey,
                "source_type": RecommendationSource.anomaly if alert.is_anomaly else RecommendationSource.kpi_alert,
                "domain": domain,
                "data": alert.source_data.model_dump() if alert.source_data else {},
                "alert": alert
            })


    # 1.5 Fusion par entity_key et détermination déterministe du domaine
    grouped_by_entity = {}
    for item in all_anomalies:
        ekey = item["entity_key"]
        resolved_domain = _resolve_domain_from_entity_key(ekey, item["data"])

        if ekey not in grouped_by_entity:
            grouped_by_entity[ekey] = {
                "entity_key": ekey,
                "source_id": item["source_id"],
                "source_type": item["source_type"],
                "domain": resolved_domain,
                "data": item["data"],
                "causes": [item]
            }
        else:
            prev_domain = grouped_by_entity[ekey]["domain"]
            if prev_domain != resolved_domain and prev_domain != "global_trend":
                logger.warning(
                    f"Avertissement : conflit potentiel de domaine pour {ekey} ({prev_domain} vs {resolved_domain}). "
                    f"Domaine déterministe conservé : {resolved_domain}"
                )
            grouped_by_entity[ekey]["domain"] = resolved_domain
            grouped_by_entity[ekey]["causes"].append(item)
            if item["source_type"] == RecommendationSource.anomaly:
                grouped_by_entity[ekey]["source_type"] = RecommendationSource.anomaly

    unique_items = list(grouped_by_entity.values())

    # 2. Calcul du score de priorité unifié cross-domaine avec impact financier
    for item in unique_items:
        item["priority_score"] = _compute_priority_score(item)

    # 3. Tri unifié par score de priorité décroissant
    all_anomalies_sorted = sorted(unique_items, key=lambda x: x["priority_score"], reverse=True)

    # 4. Plafond à 12 cartes individuelles + Résumé overflow
    if len(all_anomalies_sorted) > MAX_INDIVIDUAL_RECOMMENDATIONS:
        individual_to_process = all_anomalies_sorted[:MAX_INDIVIDUAL_RECOMMENDATIONS]
        overflow_items = all_anomalies_sorted[MAX_INDIVIDUAL_RECOMMENDATIONS:]

        for item in individual_to_process:
            active_entity_keys.add(item["entity_key"])

        overflow_source_id = "summary_overflow_anomalies"
        overflow_entity_key = overflow_source_id
        active_entity_keys.add(overflow_entity_key)
        _process_overflow_summary(db, tenant_id, overflow_source_id, len(overflow_items), overflow_items)
    else:
        individual_to_process = all_anomalies_sorted
        for item in individual_to_process:
            active_entity_keys.add(item["entity_key"])

    # 5. Filtrage des entités nécessitant un appel LLM (Cache / Inchangées)
    entities_needing_llm = []
    for item in individual_to_process:
        if _entity_needs_llm(db, tenant_id, item):
            entities_needing_llm.append(item)
        else:
            logger.info(f"Entité {item['entity_key']} inchangée : réutilisation de la recommandation existante sans appel LLM.")

    # 6. Exécution de l'appel BATCH LLM unique pour le lot nécessitant une mise à jour
    batch_llm_results = {}
    if entities_needing_llm:
        batch_llm_results = _execute_batch_llm_call(entities_needing_llm, db)

    # 7. Persistance en DB des recommandations individuelles
    for item in individual_to_process:
        ekey = item["entity_key"]
        domain = item["domain"]
        allowed_actions = _get_allowed_actions_for_domain(domain)

        rec_data = batch_llm_results.get(ekey)
        if not rec_data:
            existing = db.query(AIRecommendation).filter(
                AIRecommendation.tenant_id == tenant_id,
                AIRecommendation.entity_key == ekey,
                AIRecommendation.status.in_([RecommendationStatus.pending, RecommendationStatus.acknowledged])
            ).first()
            if existing:
                if existing.status == RecommendationStatus.acknowledged:
                    existing.status = RecommendationStatus.pending
                existing.expires_at = datetime.utcnow() + timedelta(days=7)
                db.commit()
                continue
            else:
                rec_data = _generate_fallback_data(db, item)

        _save_single_recommendation(
            db=db,
            tenant_id=tenant_id,
            source_id=item["source_id"],
            entity_key=ekey,
            source_type=item["source_type"],
            domain=domain,
            data_dict=rec_data,
            allowed_actions=allowed_actions
        )

    # 8. Expiration des anomalies résolues ou basculées par entity_key
    _expire_obsolete_recommendations(db, tenant_id, active_entity_keys)


def _save_single_recommendation(
    db: Session,
    tenant_id: uuid.UUID,
    source_id: str,
    entity_key: str,
    source_type: RecommendationSource,
    domain: str,
    data_dict: dict,
    allowed_actions: list[str]
):
    existing = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.entity_key == entity_key,
        AIRecommendation.status.in_([RecommendationStatus.pending, RecommendationStatus.acknowledged])
    ).first()

    impact_raw = data_dict.get("estimated_impact", {})
    if isinstance(impact_raw, str):
        estimated_impact = {"label": impact_raw, "confidence": "medium"}
    else:
        estimated_impact = {
            "label": impact_raw.get("label", "Impact non estimé"),
            "confidence": impact_raw.get("confidence", "medium")
        }

    parsed_action_type = data_dict.get("action_type", "none")
    if parsed_action_type not in allowed_actions:
        logger.warning(f"Action '{parsed_action_type}' non autorisée pour le domaine '{domain}'. Fallback sur action autorisée.")
        parsed_action_type = "restock_order" if domain == "stock" else "none"

    try:
        action_enum = RecommendationAction(parsed_action_type)
    except ValueError:
        action_enum = RecommendationAction.none

    # RÈGLE STRICTE : Pour les produits physiques (entity_key.startswith("product_")), si l'action est 'none' (stock suffisant,
    # aucun réapprovisionnement nécessaire), ne PAS générer ni persister de carte du tout.
    if entity_key.startswith("product_") and action_enum == RecommendationAction.none:
        if existing:
            existing.status = RecommendationStatus.expired
            db.commit()
            logger.info(f"Produit {entity_key} avec stock suffisant : carte existante expirée/purgée.")
        return

    action_payload = data_dict.get("action_payload", {}) or {}
    if action_enum == RecommendationAction.send_email_campaign:
        pids = action_payload.get("partner_ids") or action_payload.get("customer_ids")
        if not pids or not isinstance(pids, list) or len(pids) == 0:
            target_pids = _fetch_target_partner_ids_for_campaign(entity_key, data_dict)
            action_payload["partner_ids"] = target_pids
            if "campaign_subject" not in action_payload:
                action_payload["campaign_subject"] = "Campagne de relance & réactivation clients — SmartERP AI"

    if action_enum == RecommendationAction.create_follow_up_activity:
        if not action_payload.get("order_id") and data_dict.get("order_id"):
            action_payload["order_id"] = data_dict["order_id"]
        if not action_payload.get("user_id") and data_dict.get("user_id"):
            action_payload["user_id"] = data_dict["user_id"]

    clean_kpi_id = entity_key
    while clean_kpi_id.startswith("anomaly_"):
        clean_kpi_id = clean_kpi_id[8:]
    kpi_label = KPI_LABELS.get(clean_kpi_id, "Anomalie")
    default_title = f"Analyse IA temporairement indisponible — {kpi_label}" if domain != "stock" else f"Action pour {entity_key}"

    if existing:
        if existing.status == RecommendationStatus.acknowledged:
            existing.status = RecommendationStatus.pending
        existing.title = data_dict.get("title", existing.title)
        existing.explanation = data_dict.get("explanation", existing.explanation)
        existing.source_type = source_type
        existing.action_type = action_enum
        existing.action_payload = action_payload
        existing.estimated_impact = estimated_impact
        existing.expires_at = datetime.utcnow() + timedelta(days=7)
        db.commit()
        logger.info(f"Recommandation mise à jour en place pour entity_key={entity_key}")
    else:
        new_rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            entity_key=entity_key,
            source_type=source_type,
            source_id=source_id,
            title=data_dict.get("title", default_title),
            explanation=data_dict.get("explanation", "Anomalie ou alerte détectée"),
            action_type=action_enum,
            action_payload=action_payload,
            estimated_impact=estimated_impact,
            status=RecommendationStatus.pending,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(new_rec)
        db.commit()
        logger.info(f"Recommandation créée avec succès pour entity_key={entity_key}")


def _process_overflow_summary(
    db: Session,
    tenant_id: uuid.UUID,
    overflow_source_id: str,
    overflow_count: int,
    overflow_items: list[dict]
):
    overflow_entity_key = overflow_source_id
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
        AIRecommendation.entity_key == overflow_entity_key,
        AIRecommendation.status.in_([RecommendationStatus.pending, RecommendationStatus.acknowledged])
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
            entity_key=overflow_entity_key,
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


def _expire_obsolete_recommendations(db: Session, tenant_id: uuid.UUID, active_entity_keys: set[str]):
    pending_recs = db.query(AIRecommendation).filter(
        AIRecommendation.tenant_id == tenant_id,
        AIRecommendation.status == RecommendationStatus.pending
    ).all()

    for rec in pending_recs:
        if rec.entity_key not in active_entity_keys:
            rec.status = RecommendationStatus.expired
            logger.info(f"Recommandation expirée automatiquement : entity_key={rec.entity_key}")

    db.commit()
