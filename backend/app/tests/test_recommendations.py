import uuid
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.ai_recommendation import AIRecommendation
from app.models.user import User
from app.schemas.alert import Alert
from app.services.odoo_action_service import OdooActionService
from app.services.recommendation_generator import generate_recommendations


class TestRecommendations(unittest.TestCase):
    def setUp(self):
        # Créer un mock pour la session de base de données
        self.db = MagicMock(spec=Session)
        
        # Créer un mock pour l'utilisateur
        self.user = User(
            id=42,
            email="test_operator@smarterp.ai",
            full_name="Opérateur Test",
            is_active=True
        )

    @patch("app.services.odoo_action_service.odoo")
    def test_execute_action_restock_order_invalid_quantity(self, mock_odoo):
        # Cas 1 : Quantité négative
        with self.assertRaises(ValueError) as ctx:
            OdooActionService.execute_action(
                "restock_order",
                {"product_id": 12, "quantity": -5},
                self.user,
                self.db
            )
        self.assertIn("quantite a commander doit etre un entier superieur a 0", str(ctx.exception))

        # Cas 2 : Quantité trop élevée (> 10000)
        with self.assertRaises(ValueError) as ctx:
            OdooActionService.execute_action(
                "restock_order",
                {"product_id": 12, "quantity": 15000},
                self.user,
                self.db
            )

        self.assertIn("quantite demandee depasse le maximum autorise", str(ctx.exception))

    @patch("app.services.odoo_action_service.odoo")
    def test_execute_action_restock_order_product_not_found(self, mock_odoo):
        # Simuler que le produit n'existe pas dans Odoo
        mock_odoo.search_count.return_value = 0

        with self.assertRaises(ValueError) as ctx:
            OdooActionService.execute_action(
                "restock_order",
                {"product_id": 999, "quantity": 10},
                self.user,
                self.db
            )
        self.assertIn("n'existe pas dans Odoo", str(ctx.exception))
        mock_odoo.search_count.assert_called_once_with("product.product", [["id", "=", 999]])

    @patch("app.services.odoo_action_service.odoo")
    def test_execute_action_restock_order_success(self, mock_odoo):
        # Simuler que le produit existe
        mock_odoo.search_count.return_value = 1
        mock_odoo.search_read.return_value = [{"id": 12, "name": "Desk Organizer"}]
        
        # Mock de create et execute_kw
        mock_odoo.create.return_value = 1001
        mock_odoo._models().execute_kw.return_value = 1001

        res = OdooActionService.execute_action(
            "restock_order",
            {"product_id": 12, "quantity": 50},
            self.user,
            self.db
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["odoo_message_id"], 1001)
        self.assertIn("Desk Organizer", res["message"])

    @patch("app.services.odoo_action_service.odoo")
    def test_execute_action_send_email_campaign_success(self, mock_odoo):
        # Simuler que tous les partenaires existent (2 partenaires)
        mock_odoo.search_count.return_value = 2
        mock_odoo.search_read.return_value = [
            {"id": 10, "name": "Partenaire 10", "email": "p10@example.com"},
            {"id": 11, "name": "Partenaire 11", "email": "p11@example.com"}
        ]
        mock_odoo._models().execute_kw.return_value = 2001

        res = OdooActionService.execute_action(
            "send_email_campaign",
            {"partner_ids": [10, 11], "campaign_subject": "Offre Spéciale"},
            self.user,
            self.db
        )

        self.assertTrue(res["success"])
        self.assertEqual(len(res["odoo_message_ids"]), 2)
        self.assertIn("envoyee a 2 partenaires Odoo", res["message"])

    @patch("app.services.odoo_action_service.odoo")
    def test_execute_action_create_crm_activity_success(self, mock_odoo):
        # Simuler que le lead existe
        mock_odoo.search_count.return_value = 1
        mock_odoo.create.return_value = 3001
        mock_odoo._models().execute_kw.return_value = 3001

        res = OdooActionService.execute_action(
            "create_crm_activity",
            {"lead_id": 5, "activity_description": "Appeler pour négociation"},
            self.user,
            self.db
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["odoo_message_id"], 3001)
        self.assertIn("Activite CRM enregistree avec succes", res["message"])

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_generate_recommendations_stock_success(self, mock_groq_client, mock_odoo):
        # Mock de la réponse Odoo
        mock_odoo.search_read.return_value = [{"id": 1, "name": "Customizable Desk", "qty_available": 2}]

        # Mock de la complétion Groq
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Reapprovisionner Customizable Desk",
                "explanation": "Le stock de Customizable Desk est en dessous du seuil critique.",
                "action_type": "restock_order",
                "action_payload": {"product_id": 1, "quantity": 50},
                "estimated_impact": "+10 000 MAD"
            }
            """))
        ]
        mock_groq_client.chat.completions.create.return_value = mock_completion

        # Simuler l'absence de recommandation existante en DB
        self.db.query().filter().first.return_value = None

        # Alerte à traiter
        alert = Alert(
            id="stock_alerts",
            kpi_id="stock_alerts",
            message="Le stock du produit Customizable Desk est critique (2 unités)",
            severity="critical",
            is_anomaly=False,
            timestamp=datetime.utcnow()
        )

        # Générer
        generate_recommendations(self.db, [alert])

        # Vérifier que add et commit ont été appelés sur la DB
        self.assertTrue(self.db.add.called)
        self.assertTrue(self.db.commit.called)
        
        # Inspecter la recommandation ajoutée
        added_rec = self.db.add.call_args[0][0]
        self.assertIsInstance(added_rec, AIRecommendation)
        self.assertEqual(added_rec.title, "Reapprovisionner Customizable Desk")
        self.assertEqual(added_rec.action_type, "restock_order")
        self.assertEqual(added_rec.action_payload, {"product_id": 1, "quantity": 50})
        self.assertEqual(added_rec.estimated_impact, {"label": "+10 000 MAD", "confidence": "medium"})

    @patch("app.services.root_cause_analysis.odoo")
    def test_rca_real_revenue_success(self, mock_odoo):
        from app.services.root_cause_analysis import get_root_cause_analysis
        
        # Simuler 2 commandes courantes
        mock_odoo.search_read.side_effect = [
            # sale.order courantes
            [
                {"id": 1, "amount_total": 1000.0, "partner_id": [10, "Client A"], "user_id": [2, "Commercial X"]},
                {"id": 2, "amount_total": 2000.0, "partner_id": [11, "Client B"], "user_id": [3, "Commercial Y"]}
            ],
            # sale.order précédentes
            [
                {"id": 3, "amount_total": 5000.0, "partner_id": [10, "Client A"], "user_id": [2, "Commercial X"]}
            ],
            # res.partner
            [
                {"id": 10, "state_id": [5, "Casablanca"]},
                {"id": 11, "state_id": [6, "Rabat"]}
            ],
            # sale.order.line courantes
            [
                {"product_id": [100, "Desk"], "price_subtotal": 1000.0},
                {"product_id": [101, "Chair"], "price_subtotal": 2000.0}
            ],
            # sale.order.line précédentes
            [
                {"product_id": [100, "Desk"], "price_subtotal": 5000.0}
            ]
        ]
        
        res = get_root_cause_analysis("revenue", 3000.0, -40.0)
        self.assertTrue(len(res) > 0)
        # Vérifier que les dimensions contiennent Produit, Commercial, Région
        dimensions = {r["dimension"] for r in res}
        self.assertTrue("Produit" in dimensions or "Commercial" in dimensions or "Région" in dimensions)

    @patch("app.services.root_cause_analysis.odoo")
    def test_rca_simulated_fallback_on_exception(self, mock_odoo):
        from app.services.root_cause_analysis import get_root_cause_analysis
        # Simuler une panne Odoo XML-RPC
        mock_odoo.search_read.side_effect = Exception("Odoo XML-RPC error")

        res = get_root_cause_analysis("revenue", 10000.0, -10.0)
        # Devrait retourner les données simulées
        self.assertEqual(len(res), 3)
        self.assertEqual(res[0]["dimension"], "Région")
        self.assertEqual(res[0]["segment"], "Casablanca-Settat")
        self.assertTrue(res[0]["delta"] < 0)

    def test_alert_engine_rca_integration(self):
        from app.services.alert_engine import evaluate_alerts
        from app.schemas.kpi import KPI, KPISourceData
        
        kpis = [
            KPI(
                id="revenue",
                label="CA",
                value=8000.0,
                unit="MAD",
                trend="down",
                change_percent=-20.0,
                source_data=KPISourceData(model="sale.order", domain="[]", formula="")
            )
        ]
        
        alerts = evaluate_alerts(kpis)
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        # Le message doit contenir le texte formaté des causes racine
        self.assertIn("dont ", alert.message)
        self.assertIsNotNone(alert.source_data.root_causes)
        self.assertTrue(len(alert.source_data.root_causes) > 0)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_action_type_guardrail_enforcement(self, mock_groq_client, mock_odoo):
        from app.services.recommendation_generator import generate_recommendations
        from app.models.ai_recommendation import RecommendationAction

        mock_odoo.search_read.return_value = [{"id": 5, "name": "Produit X", "qty_available": 1, "lst_price": 100.0}]
        # Le LLM tente d'imposer un send_email_campaign sur du stock
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Email pour stock",
                "explanation": "Test guardrail",
                "action_type": "send_email_campaign",
                "action_payload": {},
                "estimated_impact": "+500 MAD"
            }
            """))
        ]
        mock_groq_client.chat.completions.create.return_value = mock_completion
        self.db.query().filter().first.return_value = None

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert])

        added_rec = self.db.add.call_args[0][0]
        # Le garde-fou doit forcer 'none' au lieu de 'send_email_campaign'
        self.assertEqual(added_rec.action_type, RecommendationAction.none)

    @patch("app.services.recommendation_generator.odoo")
    def test_auto_expiration_of_resolved_anomalies(self, mock_odoo):
        from app.services.recommendation_generator import generate_recommendations, RecommendationStatus
        mock_odoo.search_read.return_value = [] # Aucun stock bas

        existing_rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            source_type="anomaly",
            source_id="stock_product_99",
            title="Old Rec",
            explanation="Old",
            action_type="restock_order",
            status=RecommendationStatus.pending
        )
        self.db.query().filter().all.return_value = [existing_rec]

        generate_recommendations(self.db, [])
        # L'anomalie stock_product_99 ayant disparu, elle doit être marquée expired
        self.assertEqual(existing_rec.status, RecommendationStatus.expired)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_in_place_update_for_existing_pending_recommendation(self, mock_groq_client, mock_odoo):
        from app.services.recommendation_generator import generate_recommendations, RecommendationStatus

        mock_odoo.search_read.return_value = [{"id": 12, "name": "Produit 12", "qty_available": 1, "lst_price": 500.0}]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Mise a jour commande",
                "explanation": "Quantite encore plus faible",
                "action_type": "restock_order",
                "action_payload": {"product_id": 12, "quantity": 100},
                "estimated_impact": "+5 000 MAD"
            }
            """))
        ]
        mock_groq_client.chat.completions.create.return_value = mock_completion

        existing_rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            source_type="anomaly",
            source_id="stock_product_12",
            title="Ancien Titre",
            explanation="Ancienne explication",
            action_type="restock_order",
            action_payload={"product_id": 12, "quantity": 50},
            status=RecommendationStatus.pending
        )
        self.db.query().filter().first.return_value = existing_rec

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas 12", severity="critical", is_anomaly=True, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert])

        # Verifier que add N'A PAS été appelé (mise à jour en place)
        self.assertFalse(self.db.add.called)
        self.assertEqual(existing_rec.title, "Mise a jour commande")
        self.assertEqual(existing_rec.action_payload["quantity"], 100)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_no_anomaly_appears_both_individual_and_overflow(self, mock_groq_client, mock_odoo):
        from app.services.recommendation_generator import generate_recommendations, MAX_INDIVIDUAL_RECOMMENDATIONS

        # Générer 20 produits en stock bas
        products = [{"id": i, "name": f"Product {i}", "qty_available": 1, "lst_price": 100.0} for i in range(1, 21)]
        mock_odoo.search_read.return_value = products

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Commander Produit",
                "explanation": "Stock bas",
                "action_type": "restock_order",
                "action_payload": {},
                "estimated_impact": "+100 MAD"
            }
            """))
        ]
        mock_groq_client.chat.completions.create.return_value = mock_completion
        self.db.query().filter().first.return_value = None

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Multiples stock bas", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())
        
        added_recs = []
        self.db.add.side_effect = lambda rec: added_recs.append(rec)

        generate_recommendations(self.db, [alert])

        # Extraire les source_ids des cartes individuelles et de la carte d'overflow
        individual_ids = [r.source_id for r in added_recs if r.source_id != "summary_overflow_anomalies"]
        overflow_rec = next((r for r in added_recs if r.source_id == "summary_overflow_anomalies"), None)

        self.assertIsNotNone(overflow_rec)
        self.assertEqual(len(individual_ids), MAX_INDIVIDUAL_RECOMMENDATIONS)

        overflow_items_list = overflow_rec.action_payload.get("items", [])
        # Vérifier qu'aucune carte individuelle n'est énumérée dans l'overflow
        for ind_id in individual_ids:
            prod_id_str = ind_id.replace("stock_product_", "")
            matching = [item for item in overflow_items_list if f"Product {prod_id_str} " in item]
            self.assertEqual(len(matching), 0, f"L'anomalie {ind_id} ne doit pas figurer dans l'overflow.")


