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

        # Cas 2 : Quantité trop élevée (> 1000)
        with self.assertRaises(ValueError) as ctx:
            OdooActionService.execute_action(
                "restock_order",
                {"product_id": 12, "quantity": 1050},
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
        self.assertEqual(res[0]["delta"], -5.5)

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

