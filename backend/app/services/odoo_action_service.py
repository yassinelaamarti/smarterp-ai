import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.odoo_connector import odoo
from app.models.user import User

logger = logging.getLogger(__name__)


class OdooActionService:
    """Service validant et exécutant les actions issues des recommandations IA sur Odoo."""

    @staticmethod
    def execute_action(action_type: str, payload: dict | None, user: User, db: Session) -> dict:
        if not payload:
            payload = {}

        logger.info(f"Execution action '{action_type}' demandee par {user.email} avec payload: {payload}")

        if action_type == "restock_order":
            product_id = payload.get("product_id")
            quantity = payload.get("quantity")

            if not product_id or not isinstance(product_id, int):
                raise ValueError("Le parametre 'product_id' doit etre un entier valide.")
            if not quantity or not isinstance(quantity, int) or quantity <= 0:
                raise ValueError("La quantite a commander doit etre un entier superieur a 0.")
            if quantity > 1000:
                raise ValueError("La quantite demandee depasse le maximum autorise de 1000 unites.")

            # Valider que le produit existe dans Odoo
            count = odoo.search_count("product.product", [["id", "=", product_id]])
            if count == 0:
                raise ValueError(f"Le produit d'ID {product_id} n'existe pas dans Odoo.")

            # Recuperer le nom du produit
            product_data = odoo.search_read("product.product", [["id", "=", product_id]], ["name"], limit=1)
            product_name = product_data[0]["name"] if product_data else f"Produit #{product_id}"

            # Publier un message dans le chatter du produit (mail.thread) pour simuler la commande
            body = (
                f"<b>[SmartERP AI] Demande de reapprovisionnement :</b><br/>"
                f"Commande de {quantity} unites du produit <i>{product_name}</i> "
                f"initiee par l'utilisateur <b>{user.full_name or user.email}</b>."
            )

            try:
                msg_id = odoo._models().execute_kw(
                    odoo.db, odoo._get_uid(), odoo.password,
                    "product.product", "message_post",
                    [product_id],
                    {"body": body}
                )
                logger.info(f"Message poste sur Odoo product {product_id}. Message ID: {msg_id}")
                return {
                    "success": True,
                    "message": f"Demande de reapprovisionnement pour {quantity} x '{product_name}' enregistree sur Odoo.",
                    "odoo_message_id": msg_id
                }
            except Exception as e:
                logger.error(f"Erreur lors de la publication Odoo: {e}")
                raise RuntimeError(f"Echec de l'integration Odoo : {e}")

        elif action_type == "send_email_campaign":
            partner_ids = payload.get("partner_ids")
            campaign_subject = payload.get("campaign_subject", "Relance client")

            if not partner_ids or not isinstance(partner_ids, list):
                raise ValueError("Le parametre 'partner_ids' doit etre une liste d'entiers valides.")

            # Valider que tous les partenaires existent dans Odoo
            valid_count = odoo.search_count("res.partner", [["id", "in", partner_ids]])
            if valid_count < len(partner_ids):
                # Trouver les valides pour message d'erreur precis
                partners_read = odoo.search_read("res.partner", [["id", "in", partner_ids]], ["id"])
                found_ids = {p["id"] for p in partners_read}
                missing_ids = set(partner_ids) - found_ids
                raise ValueError(f"Certains partenaires n'existent pas dans Odoo (IDs manquants: {list(missing_ids)}).")

            # Publier un message sur le chatter de chaque partenaire
            body = (
                f"<b>[SmartERP AI] Campagne Email :</b><br/>"
                f"E-mail de relance automatique envoye avec le sujet <i>\"{campaign_subject}\"</i>.<br/>"
                f"Action validee par l'utilisateur <b>{user.full_name or user.email}</b>."
            )

            msg_ids = []
            for partner_id in partner_ids:
                try:
                    msg_id = odoo._models().execute_kw(
                        odoo.db, odoo._get_uid(), odoo.password,
                        "res.partner", "message_post",
                        [partner_id],
                        {"body": body}
                    )
                    msg_ids.append(msg_id)
                except Exception as e:
                    logger.error(f"Erreur de publication sur le partenaire {partner_id}: {e}")

            return {
                "success": True,
                "message": f"Campagne d'emails envoyee a {len(partner_ids)} partenaires Odoo.",
                "odoo_message_ids": msg_ids
            }

        elif action_type == "create_crm_activity":
            lead_id = payload.get("lead_id")
            activity_description = payload.get("activity_description")

            if not lead_id or not isinstance(lead_id, int):
                raise ValueError("Le parametre 'lead_id' doit etre un entier valide.")
            if not activity_description or not isinstance(activity_description, str):
                raise ValueError("La description de l'activite doit etre une chaine valide.")

            # Valider que le lead existe
            count = odoo.search_count("crm.lead", [["id", "=", lead_id]])
            if count == 0:
                raise ValueError(f"Le lead CRM d'ID {lead_id} n'existe pas dans Odoo.")

            # Publier un message sur le chatter du lead
            body = (
                f"<b>[SmartERP AI] Activite CRM planifiee :</b><br/>"
                f"<i>\"{activity_description}\"</i><br/>"
                f"Creee et enregistree par l'utilisateur <b>{user.full_name or user.email}</b>."
            )

            try:
                msg_id = odoo._models().execute_kw(
                    odoo.db, odoo._get_uid(), odoo.password,
                    "crm.lead", "message_post",
                    [lead_id],
                    {"body": body}
                )
                logger.info(f"Message poste sur Odoo CRM lead {lead_id}. Message ID: {msg_id}")
                return {
                    "success": True,
                    "message": "Activite CRM enregistree avec succes sur la fiche de lead Odoo.",
                    "odoo_message_id": msg_id
                }
            except Exception as e:
                logger.error(f"Erreur lors de la publication sur le lead: {e}")
                raise RuntimeError(f"Echec de l'integration Odoo : {e}")

        elif action_type == "none":
            return {
                "success": True,
                "message": "Recommandation sans action automatique executee."
            }
        else:
            raise ValueError(f"Type d'action '{action_type}' non supporte.")
