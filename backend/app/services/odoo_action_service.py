import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.odoo_connector import odoo
from app.models.user import User


logger = logging.getLogger(__name__)


class OdooActionValidationError(ValueError):
    """Exception levée en cas d'échec de validation d'une action Odoo."""
    pass


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
            if quantity is None and "quantity_to_order" in payload:
                quantity = payload.get("quantity_to_order")


            if not product_id or not isinstance(product_id, int):
                raise OdooActionValidationError("Le parametre 'product_id' doit etre un entier valide.")
            if not quantity or not isinstance(quantity, int) or quantity <= 0:
                raise OdooActionValidationError("La quantite a commander doit etre un entier superieur a 0.")
            if quantity > 10000:
                raise OdooActionValidationError("La quantite demandee depasse le maximum autorise de 10000 unites.")


            # Valider que le produit existe dans Odoo
            count = odoo.search_count("product.product", [["id", "=", product_id]])
            if count == 0:
                raise OdooActionValidationError(f"Le produit d'ID {product_id} n'existe pas dans Odoo.")

            # Récupérer le nom du produit
            product_data = odoo.search_read("product.product", [["id", "=", product_id]], ["name"], limit=1)
            product_name = product_data[0]["name"] if product_data else f"Produit #{product_id}"

            # Récupérer le fournisseur par défaut
            supplier_id = OdooActionService._get_default_supplier_id(product_id)

            # Créer le bon de commande d'achat (purchase.order) en état Brouillon (draft)
            try:
                vals = {
                    "partner_id": supplier_id,
                    "state": "draft",
                    "order_line": [
                        [0, 0, {
                            "product_id": product_id,
                            "product_qty": quantity,
                            "name": product_name,
                            "price_unit": 0.0
                        }]
                    ]
                }
                purchase_order_id = odoo.create("purchase.order", vals)
                logger.info(f"Purchase Order cree en draft dans Odoo. ID: {purchase_order_id}")
                
                return {
                    "success": True,
                    "message": f"Bon de commande draft #{purchase_order_id} pour {quantity} x '{product_name}' cree sur Odoo.",
                    "odoo_id": purchase_order_id,
                    "model": "purchase.order",
                    "odoo_message_id": purchase_order_id  # Pour compatibilité de test
                }
            except Exception as e:
                logger.error(f"Erreur lors de la creation du purchase order: {e}")
                raise RuntimeError(f"Echec de l'integration Odoo : {e}")

        elif action_type == "send_email_campaign":
            partner_ids = payload.get("partner_ids")
            template_id = payload.get("template_id")
            campaign_subject = payload.get("campaign_subject", "Relance client")

            if not partner_ids or not isinstance(partner_ids, list):
                raise OdooActionValidationError("Le parametre 'partner_ids' doit etre une liste d'entiers valides.")

            # Valider que tous les partenaires existent dans Odoo
            valid_count = odoo.search_count("res.partner", [["id", "in", partner_ids]])
            if valid_count < len(partner_ids):
                partners_read = odoo.search_read("res.partner", [["id", "in", partner_ids]], ["id"])
                found_ids = {p["id"] for p in partners_read}
                missing_ids = set(partner_ids) - found_ids
                raise OdooActionValidationError(f"Certains partenaires n'existent pas dans Odoo (IDs manquants: {list(missing_ids)}).")

            # Récupérer les informations des partenaires (et valider l'adresse email)
            partners_data = odoo.search_read("res.partner", [["id", "in", partner_ids]], ["name", "email"])
            for partner in partners_data:
                if not partner.get("email"):
                    raise OdooActionValidationError(f"Le partenaire '{partner['name']}' (ID: {partner['id']}) n'a pas d'adresse email renseignee dans Odoo.")

            # Tenter de charger le template de mail si template_id est fourni
            subject = campaign_subject
            body_html = "<p>Bonjour,</p><p>Nous vous contactons dans le cadre de notre campagne de relance.</p>"
            if template_id:
                try:
                    tmpl = odoo.search_read("mail.template", [["id", "=", template_id]], ["subject", "body_html"], limit=1)
                    if tmpl:
                        subject = tmpl[0].get("subject") or subject
                        body_html = tmpl[0].get("body_html") or body_html
                except Exception as e:
                    logger.warning(f"Impossible de lire le template de mail {template_id} dans Odoo: {e}")

            # Récupérer l'adresse email de la société dans Odoo (res.company) ou de la payload
            email_from = payload.get("email_from")
            if not email_from:
                try:
                    company_data = odoo.search_read("res.company", [], ["name", "email"], limit=1)
                    if company_data and company_data[0].get("email"):
                        comp_name = company_data[0].get("name") or "Entreprise"
                        comp_email = company_data[0]["email"]
                        email_from = f'"{comp_name}" <{comp_email}>'
                except Exception as e:
                    logger.warning(f"Impossible de lire l'email de la societe dans Odoo: {e}")

            # Créer les e-mails dans la file d'attente d'Odoo (mail.mail avec state='outgoing')
            mail_ids = []
            for partner in partners_data:
                try:
                    mail_vals = {
                        "subject": subject,
                        "body_html": body_html,
                        "email_to": partner["email"],
                        "recipient_ids": [[6, 0, [partner["id"]]]],
                        "state": "outgoing"
                    }
                    if email_from:
                        mail_vals["email_from"] = email_from

                    mail_id = odoo.create("mail.mail", mail_vals)
                    mail_ids.append(mail_id)
                except Exception as e:
                    logger.error(f"Erreur de creation de mail pour le partenaire {partner['id']}: {e}")
                    raise RuntimeError(f"Echec de creation d'email dans Odoo : {e}")

            return {
                "success": True,
                "message": f"Campagne d'emails envoyee a {len(partner_ids)} partenaires Odoo.",
                "odoo_message_ids": mail_ids,
                "model": "mail.mail"
            }

        elif action_type == "create_crm_activity":
            partner_id = payload.get("partner_id") or payload.get("lead_id")  # support des deux clés pour la compatibilité
            assigned_user_id = payload.get("assigned_user_id")
            activity_type = payload.get("activity_type", "Todo")
            note = payload.get("note", payload.get("activity_description", "Activité SmartERP AI"))

            if not partner_id or not isinstance(partner_id, int):
                raise OdooActionValidationError("Le parametre 'partner_id' ou 'lead_id' doit etre un entier valide.")
            if not note or not isinstance(note, str):
                raise OdooActionValidationError("La note ou description d'activite doit etre une chaine valide.")

            # Si assigned_user_id n'est pas fourni, on prend l'utilisateur Odoo actif correspondant au username
            if not assigned_user_id:
                # Fallback à l'ID 1 ou premier utilisateur actif
                users_odoo = odoo.search_read("res.users", [["active", "=", True]], ["id"], limit=1)
                assigned_user_id = users_odoo[0]["id"] if users_odoo else 1

            # Vérifier que l'utilisateur assigné existe et est actif
            user_exists = odoo.search_count("res.users", [["id", "=", assigned_user_id], ["active", "=", True]])
            if not user_exists:
                raise OdooActionValidationError(f"L'utilisateur Odoo assigne (ID: {assigned_user_id}) n'existe pas ou n'est pas actif.")

            # Trouver ou créer le lead/opportunité correspondant au partenaire
            # On vérifie d'abord si l'ID fourni est déjà un crm.lead
            is_lead = odoo.search_count("crm.lead", [["id", "=", partner_id]])
            if is_lead > 0:
                lead_id = partner_id
            else:
                # Sinon on cherche un lead lié à ce partner_id
                leads = odoo.search_read("crm.lead", [["partner_id", "=", partner_id], ["active", "=", True]], ["id"], limit=1)
                if leads:
                    lead_id = leads[0]["id"]
                else:
                    # Créer un lead en draft pour ce partenaire
                    partner_info = odoo.search_read("res.partner", [["id", "=", partner_id]], ["name"], limit=1)
                    partner_name = partner_info[0]["name"] if partner_info else f"Partenaire #{partner_id}"
                    lead_id = odoo.create("crm.lead", {
                        "name": f"Opportunite IA - {partner_name}",
                        "partner_id": partner_id,
                        "type": "opportunity",
                        "user_id": assigned_user_id
                    })

            # Récupérer l'ir.model ID pour crm.lead
            try:
                model_data = odoo.search_read("ir.model", [["model", "=", "crm.lead"]], ["id"], limit=1)
                res_model_id = model_data[0]["id"] if model_data else None
                if not res_model_id:
                    raise OdooActionValidationError("Impossible de trouver le modele 'crm.lead' dans Odoo.")

                # Récupérer l'activity_type_id correspondant
                activity_type_id = None
                if activity_type:
                    act_types = odoo.search_read("mail.activity.type", [["name", "ilike", activity_type]], ["id"], limit=1)
                    if act_types:
                        activity_type_id = act_types[0]["id"]
                if not activity_type_id:
                    # Fallback sur le premier type disponible
                    act_types = odoo.search_read("mail.activity.type", [], ["id"], limit=1)
                    activity_type_id = act_types[0]["id"] if act_types else 1

                # Créer l'activité Odoo
                activity_id = odoo.create("mail.activity", {
                    "res_id": lead_id,
                    "res_model_id": res_model_id,
                    "activity_type_id": activity_type_id,
                    "summary": "Suivi SmartERP AI",
                    "note": note,
                    "user_id": assigned_user_id
                })

                return {
                    "success": True,
                    "message": "Activite CRM enregistree avec succes sur la fiche de lead Odoo.",
                    "odoo_id": activity_id,
                    "model": "mail.activity",
                    "odoo_message_id": activity_id  # Pour compatibilité de test
                }
            except Exception as e:
                logger.error(f"Erreur lors de la creation de l'activite CRM: {e}")
                raise RuntimeError(f"Echec de creation d'activite CRM dans Odoo : {e}")

        elif action_type == "create_follow_up_activity":
            from datetime import timedelta
            order_id = payload.get("order_id")
            note = payload.get("note", payload.get("summary", "Relance commande en retard — SmartERP AI"))

            if not order_id or not isinstance(order_id, int):
                raise OdooActionValidationError("Le parametre 'order_id' doit etre un entier valide.")

            # Valider l'existence de la commande dans Odoo
            orders = odoo.search_read("sale.order", [["id", "=", order_id]], ["id", "name", "user_id", "partner_id"])
            if not orders:
                raise OdooActionValidationError(f"La commande d'ID {order_id} n'existe pas dans Odoo.")

            order = orders[0]
            order_name = order.get("name", f"S000{order_id}")

            # RÈGLE STRICTE : user_id (commercial assigné à la commande). AUCUN fallback arbitraire.
            assigned_user = order.get("user_id")
            if not assigned_user or not isinstance(assigned_user, (list, tuple)):
                raise OdooActionValidationError(f"La commande '{order_name}' (ID: {order_id}) n'a aucun commercial (user_id) assigne dans Odoo — action non réalisable automatiquement.")

            assigned_user_id = assigned_user[0]
            assigned_user_name = assigned_user[1] if len(assigned_user) > 1 else f"User #{assigned_user_id}"

            # Vérifier que l'utilisateur assigné existe et est actif dans Odoo
            user_active = odoo.search_count("res.users", [["id", "=", assigned_user_id], ["active", "=", True]])
            if not user_active:
                raise OdooActionValidationError(f"Le commercial assigne a la commande '{order_name}' (User ID: {assigned_user_id}) n'est pas un utilisateur actif dans Odoo.")

            # Récupérer l'ir.model ID pour sale.order
            model_data = odoo.search_read("ir.model", [["model", "=", "sale.order"]], ["id"], limit=1)
            res_model_id = model_data[0]["id"] if model_data else None
            if not res_model_id:
                raise OdooActionValidationError("Impossible de trouver le modele 'sale.order' dans Odoo.")

            # Récupérer le type d'activité Odoo
            act_types = odoo.search_read("mail.activity.type", [], ["id"], limit=1)
            activity_type_id = act_types[0]["id"] if act_types else 1

            deadline_str = payload.get("date_deadline") or (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            try:
                activity_id = odoo.create("mail.activity", {
                    "res_id": order_id,
                    "res_model_id": res_model_id,
                    "activity_type_id": activity_type_id,
                    "summary": f"Relance livraison — Commande {order_name}",
                    "note": note,
                    "user_id": assigned_user_id,
                    "date_deadline": deadline_str
                })

                logger.info(f"Activite mail.activity #{activity_id} creee pour commande {order_name} et assignee a {assigned_user_name}.")

                return {
                    "success": True,
                    "message": f"Activite de relance enregistree sur Odoo pour la commande {order_name} et assignee a {assigned_user_name}.",
                    "odoo_id": activity_id,
                    "model": "mail.activity",
                    "odoo_message_id": activity_id
                }
            except Exception as e:
                logger.error(f"Erreur lors de la creation de l'activite sur la commande {order_name}: {e}")
                raise RuntimeError(f"Echec de creation d'activite Odoo : {e}")

        elif action_type == "none":
            return {
                "success": True,
                "message": "Recommandation sans action automatique executee."
            }
        else:
            raise OdooActionValidationError(f"Type d'action '{action_type}' non supporte.")

    @staticmethod
    def _get_default_supplier_id(product_id: int) -> int:
        """Trouve le fournisseur du produit ou retourne le premier partenaire disponible."""
        try:
            prod = odoo.search_read("product.product", [["id", "=", product_id]], ["product_tmpl_id"], limit=1)
            if prod and prod[0].get("product_tmpl_id"):
                tmpl_id = prod[0]["product_tmpl_id"][0]
                supplier_info = odoo.search_read("product.supplierinfo", [["product_tmpl_id", "=", tmpl_id]], ["partner_id"], limit=1)
                if supplier_info and supplier_info[0].get("partner_id"):
                    return supplier_info[0]["partner_id"][0]
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche du fournisseur pour le produit {product_id}: {e}")

        # Fallback
        try:
            partners = odoo.search_read("res.partner", [], ["id"], limit=1)
            if partners:
                return partners[0]["id"]
        except Exception as e:
            logger.error(f"Impossible de recuperer un partenaire Odoo : {e}")

        raise OdooActionValidationError("Aucun partenaire (fournisseur) trouve dans Odoo pour lier a la commande.")
