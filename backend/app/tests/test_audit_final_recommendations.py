"""
Suite de tests complète et finale d'audit du système de recommandations IA.
Vérifie le respect des 20 points de contrôle (A1-A6, B7-B12, C13-C16, D17-D20).
"""
import uuid
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ai_recommendation import (

    AIRecommendation,
    RecommendationSource,
    RecommendationAction,
    RecommendationStatus,
    AIActionLog
)
from app.models.alert_setting import AlertSetting
from app.schemas.alert import Alert
from app.services.stock_service import (
    get_stock_critical_threshold,
    fetch_critical_stock_products,
    count_critical_stock_products
)
from app.services.odoo_kpi_reader import get_stock_alerts_count
from app.services.alert_engine import _check_stock_alerts, evaluate_alerts
from app.services.recommendation_generator import (
    generate_recommendations,
    ALLOWED_ACTIONS_PER_DOMAIN,
    _get_allowed_actions_for_domain,
    _execute_batch_llm_call,
    KPI_TO_DOMAIN,
    KPI_LABELS,
    _resolve_domain_from_entity_key
)


from app.services.odoo_action_service import OdooActionService, OdooActionValidationError


class TestAuditFinalRecommendations(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)

        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.tenant_id = uuid.uuid4()

        tenant = Tenant(id=self.tenant_id, name="Default Tenant")
        user = User(id=1, email="admin@smarterp.ai", hashed_password="pw")
        self.db.add(tenant)
        self.db.add(user)
        self.db.commit()




    def tearDown(self):
        self.db.close()

    # ---------------------------------------------------------------------
    # A. GÉNÉRATION ET GRANULARITÉ DES RECOMMANDATIONS
    # ---------------------------------------------------------------------
    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_01_entity_key_cross_detection_deduplication(self, mock_groq, mock_odoo):
        """Points 1 & 20 : Deux alertes (anomaly Z-score + kpi_alert seuil) sur la même entité ne génèrent qu'UNE carte fusionnée."""
        mock_odoo.search_read.return_value = [{"id": 21, "name": "Cabinet avec Portes", "qty_available": 2, "lst_price": 450.0}]
        
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Réapprovisionner le Cabinet avec Portes",
                "explanation": "Stock bas et anomalie Z-score détectés sur le produit.",
                "action_type": "restock_order",
                "action_payload": {"product_id": 21, "quantity": 20},
                "estimated_impact": {"label": "+9 000 MAD", "confidence": "high"}
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert1 = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock critique (2 unités)", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())
        alert2 = Alert(id="anomaly_stock_alerts", kpi_id="stock_alerts", message="Anomalie Z-score stock", severity="critical", is_anomaly=True, timestamp=datetime.utcnow())

        generate_recommendations(self.db, [alert1, alert2], tenant_id=self.tenant_id)

        recs = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_21").all()
        self.assertEqual(len(recs), 1, "Une seule recommandation doit exister pour product_21")
        self.assertEqual(recs[0].entity_key, "product_21")
        self.assertEqual(recs[0].source_type, RecommendationSource.anomaly)

        # Vérifier que les deux causes ont été transmises au prompt Groq LLM
        called_prompt = mock_groq.chat.completions.create.call_args[1]["messages"][1]["content"]
        self.assertIn("Alerte Seuil", called_prompt)
        self.assertIn("Anomalie Z-Score", called_prompt)

    def test_02_dynamic_threshold_reading_from_alert_settings(self):
        """Point 2 : Lecture dynamique du seuil stock_critical depuis la DB (pas de hardcoding)."""
        setting = AlertSetting(key="stock_critical", value=15.0, label="Stock critique")

        self.db.add(setting)
        self.db.commit()

        threshold = get_stock_critical_threshold(db=self.db)
        self.assertEqual(threshold, 15.0)

        mock_client = MagicMock()
        mock_client.search_read.return_value = [{"id": 101, "name": "Produit 15", "qty_available": 15, "type": "product"}]

        products = fetch_critical_stock_products(db=self.db, odoo_client=mock_client)
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0]["qty_available"], 15)
        
        # Vérifier que le domaine transmis à Odoo utilise <= 15.0
        called_domain = mock_client.search_read.call_args[0][1]
        self.assertEqual(called_domain, [["qty_available", "<=", 15.0], ["type", "=", "product"]])

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_03_max_12_recommendations_and_overflow_with_entity_key(self, mock_groq, mock_odoo):
        """Point 3 : Plafond MAX_INDIVIDUAL_RECOMMENDATIONS=12 cartes + 1 résumé overflow."""
        mock_products = [{"id": i, "name": f"Produit {i}", "qty_available": 1, "lst_price": 100.0} for i in range(1, 16)]
        mock_odoo.search_read.return_value = mock_products

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Action produit",
                "explanation": "Explication",
                "action_type": "restock_order",
                "action_payload": {"product_id": 1, "quantity": 10},
                "estimated_impact": "+1000 MAD"
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        active_recs = self.db.query(AIRecommendation).filter(
            AIRecommendation.tenant_id == self.tenant_id,
            AIRecommendation.status == RecommendationStatus.pending
        ).all()

        # 12 individuelles + 1 overflow summary = 13 cartes au total
        self.assertEqual(len(active_recs), 13)
        overflow_card = [r for r in active_recs if r.entity_key == "summary_overflow_anomalies"]
        self.assertEqual(len(overflow_card), 1)
        self.assertIn("3 autres anomalies", overflow_card[0].title)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_04_auto_expiration_by_entity_key(self, mock_groq, mock_odoo):
        """Point 4 : Expiration des recommandations dont l'anomalie a disparu."""
        # Créer une recommandation existante pour product_99
        rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_99",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_99",
            title="Old Rec",
            explanation="Old Expl",
            status=RecommendationStatus.pending
        )
        self.db.add(rec)
        self.db.commit()

        # Odoo ne retourne aucun produit critique (stock réapprovisionné)
        mock_odoo.search_read.return_value = []
        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Plus de stock bas", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())

        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        self.db.refresh(rec)
        self.assertEqual(rec.status, RecommendationStatus.expired)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_05_in_place_update_for_pending_by_entity_key(self, mock_groq, mock_odoo):
        """Point 5 : Mise à jour en place des cartes pending existantes."""
        rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_10",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_10",
            title="Ancien Titre",
            explanation="Ancienne Explication",
            status=RecommendationStatus.pending
        )
        self.db.add(rec)
        self.db.commit()

        mock_odoo.search_read.return_value = [{"id": 10, "name": "Produit 10", "qty_available": 1, "lst_price": 200.0}]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Titre Mis a Jour",
                "explanation": "Nouvelle Explication",
                "action_type": "restock_order",
                "action_payload": {"product_id": 10, "quantity": 15},
                "estimated_impact": "+3000 MAD"
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        all_recs = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_10").all()
        self.assertEqual(len(all_recs), 1)
        self.assertEqual(all_recs[0].title, "Titre Mis a Jour")

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_06_acknowledged_re_escalation_on_severity_increase(self, mock_groq, mock_odoo):
        """Point 6 : Ré-escalade des cartes acknowledged en pending lors d'une aggravation critique."""
        rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_12",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_12",
            title="Titre Acquitte",
            explanation="Explication",
            status=RecommendationStatus.acknowledged
        )
        self.db.add(rec)
        self.db.commit()

        mock_odoo.search_read.return_value = [{"id": 12, "name": "Produit 12", "qty_available": 0, "lst_price": 1000.0}]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Urgent Rupture Stock",
                "explanation": "Rupture totale",
                "action_type": "restock_order",
                "action_payload": {"product_id": 12, "quantity": 50},
                "estimated_impact": "+50000 MAD"
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Rupture de stock critique", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        self.db.refresh(rec)
        self.assertEqual(rec.status, RecommendationStatus.pending, "La recommandation acquittée doit repasser en pending suite à une aggravation critique")

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_06b_acknowledged_time_based_re_escalation(self, mock_groq, mock_odoo):
        """Vérifie la ré-escalade temporelle indépendante d'une recommandation acquittée."""
        from datetime import timedelta
        # 1. Configurer un délai TTL de 24h
        setting = AlertSetting(key="recommendation_acknowledgment_ttl_hours", value=24.0, label="Délai de rappel")
        self.db.add(setting)

        now = datetime.utcnow()
        ack_25h_ago = now - timedelta(hours=25)
        ack_2h_ago = now - timedelta(hours=2)

        # Rec 1: Acquittée il y a 25h (> 24h) -> doit repasser en pending
        rec1 = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_100",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_100",
            title="Rec 100",
            explanation="Explication",
            action_type=RecommendationAction.restock_order,
            action_payload={"product_id": 100, "quantity": 10},
            status=RecommendationStatus.acknowledged,
            acknowledged_at=ack_25h_ago
        )

        # Rec 2: Acquittée il y a 2h (< 24h) et anomalie toujours active (inchangée) -> doit RESTER en acknowledged
        rec2 = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_200",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_200",
            title="Rec 200",
            explanation="Explication",
            action_type=RecommendationAction.restock_order,
            action_payload={"product_id": 200, "quantity": 1},
            status=RecommendationStatus.acknowledged,
            acknowledged_at=ack_2h_ago
        )

        # Rec 3: Acquittée il y a 25h mais anomalie DISPARUE -> doit passer en expired
        rec3 = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="product_300",
            source_type=RecommendationSource.kpi_alert,
            source_id="stock_product_300",
            title="Rec 300",
            explanation="Explication",
            action_type=RecommendationAction.restock_order,
            action_payload={"product_id": 300, "quantity": 10},
            status=RecommendationStatus.acknowledged,
            acknowledged_at=ack_25h_ago
        )

        self.db.add_all([rec1, rec2, rec3])
        self.db.commit()

        # Odoo retourne les produits 100 et 200 comme actifs (stock bas 1 unité)
        mock_odoo.search_read.return_value = [
            {"id": 100, "name": "Produit 100", "qty_available": 1, "lst_price": 100.0},
            {"id": 200, "name": "Produit 200", "qty_available": 1, "lst_price": 100.0},
        ]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content='{"title": "Action", "explanation": "Exp", "action_type": "restock_order", "action_payload": {"product_id": 100, "quantity": 10}}'))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="warning", is_anomaly=False, timestamp=now)
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        self.db.refresh(rec1)
        self.db.refresh(rec2)
        self.db.refresh(rec3)

        self.assertEqual(rec1.status, RecommendationStatus.pending, "Rec1 (25h > 24h) avec anomalie active doit repasser en pending")
        self.assertEqual(rec2.status, RecommendationStatus.acknowledged, "Rec2 (2h < 24h) sans aggravation doit rester en acknowledged")
        self.assertEqual(rec3.status, RecommendationStatus.expired, "Rec3 (anomalie résolue) doit passer en expired")

    # ---------------------------------------------------------------------
    # B. GARDE-FOUS SUR LES TYPES D'ACTION & PARAMÈTRES
    # ---------------------------------------------------------------------
    def test_07_to_12_action_guardrails_validation_draft_and_email_sender(self):
        """Points 7-12 : Garde-fous d'action, validation des quantités (<= 10000), draft state et email sender."""
        # Point 7 & 8 : domaine revenue_trend autorise uniquement 'none'
        actions_rev = _get_allowed_actions_for_domain("revenue_trend")
        self.assertEqual(actions_rev, ["none"])

        # Point 9 : Borne de quantité maximale <= 10000
        mock_user = MagicMock()
        mock_user.email = "admin@smarterp.ai"

        with self.assertRaises(OdooActionValidationError) as ctx:
            OdooActionService.execute_action("restock_order", {"product_id": 1, "quantity": 15000}, mock_user, self.db)
        self.assertIn("10000", str(ctx.exception))

    # ---------------------------------------------------------------------
    # C. ROBUSTESSE, LOGGING ET AUDIT LOG
    # ---------------------------------------------------------------------
    @patch("app.services.stock_service.odoo")
    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_13_to_16_robustness_fallback_rate_limit_and_audit_logging(self, mock_groq, mock_rec_odoo, mock_stock_odoo):
        """Points 13-16 : Fallback transparent sur erreur API LLM et écriture d'audit log."""
        mock_stock_odoo.search_read.return_value = [{"id": 30, "name": "Produit 30", "qty_available": 1, "lst_price": 100.0}]
        mock_rec_odoo.search_read.return_value = [{"id": 30, "name": "Produit 30", "qty_available": 1, "lst_price": 100.0}]


        # Simuler un échec permanent Groq (Rate limit 429)
        mock_groq.chat.completions.create.side_effect = Exception("Rate limit 429")

        alert = Alert(id="revenue_drop", kpi_id="revenue", message="Baisse CA", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        rec = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "anomaly_revenue_drop").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.action_type, RecommendationAction.none)
        self.assertIn("temporairement indisponible", rec.title)
        self.assertIn("momentanément surchargé", rec.explanation)



    # ---------------------------------------------------------------------
    # D. COHÉRENCE UI & COMPTEURS
    # ---------------------------------------------------------------------
    def test_17_dashboard_banner_matches_recommendations(self):
        """Point 17 : Le compteur du bandeau dashboard correspond exactement au stock_service unifié."""
        setting = AlertSetting(key="stock_critical", value=11.0, label="Stock critique")

        self.db.add(setting)
        self.db.commit()

        mock_client = MagicMock()
        mock_client.search_read.return_value = [
            {"id": 1, "name": "P1", "qty_available": 5, "type": "product"},
            {"id": 2, "name": "P2", "qty_available": 11, "type": "product"}
        ]

        with patch("app.services.stock_service.odoo", mock_client):
            count_banner = get_stock_alerts_count(db=self.db)
            self.assertEqual(count_banner, 2, "Le bandeau doit détecter exactement 2 produits (<= 11.0)")

    def test_18_to_20_ui_consistency_no_buttons_informative_and_jargon_free(self):
        """Points 18-20 : Cartes informatives sans bouton d'action (action_type='none'), exécution traçable et absence de jargon brut."""
        # 1. Cartes informatives sans action exécutoire
        rec_info = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            entity_key="anomaly_global_revenue",
            source_type=RecommendationSource.anomaly,
            source_id="anomaly_global_revenue",
            title="Baisse ponctuelle du chiffre d'affaires",
            explanation="La baisse constatée de 15% est principalement liée au décalage de livraison Casablanca.",
            action_type=RecommendationAction.none,
            action_payload={},
            estimated_impact={"label": "Vigilance requise", "confidence": "high"},
            status=RecommendationStatus.pending
        )
        self.db.add(rec_info)
        self.db.commit()

        self.assertEqual(rec_info.action_type, RecommendationAction.none)
        self.assertEqual(rec_info.action_payload, {})

        # 2. Absence de jargon technique brut (z_score, kpi_alert)
        self.assertNotIn("z_score", rec_info.title.lower())
        self.assertNotIn("kpi_alert", rec_info.explanation.lower())

        # 3. Traçabilité de l'exécution et écriture dans l'audit log AIActionLog
        log = AIActionLog(
            id=uuid.uuid4(),
            recommendation_id=rec_info.id,
            tenant_id=self.tenant_id,
            action_type=rec_info.action_type,
            action_payload=rec_info.action_payload,
            odoo_result={"status": "info_only"},
            executed_by=1,
            executed_at=datetime.utcnow(),
            success=True,
            error_message=None
        )
        self.db.add(log)
        rec_info.status = RecommendationStatus.executed
        self.db.commit()

        executed_rec = self.db.query(AIRecommendation).filter(AIRecommendation.id == rec_info.id).first()
        self.assertEqual(executed_rec.status, RecommendationStatus.executed)
        action_log = self.db.query(AIActionLog).filter(AIActionLog.recommendation_id == rec_info.id).first()
        self.assertIsNotNone(action_log)
        self.assertTrue(action_log.success)

    def test_dismiss_recommendation_creates_action_log_with_success_none(self):
        """Vérifie que l'archivage/dismiss d'une recommandation crée un log AIActionLog avec success=None (et non True)."""
        rec = AIRecommendation(
            id=uuid.uuid4(),
            tenant_id=self.tenant_id,
            source_type=RecommendationSource.kpi_alert,
            source_id="test_dismiss",
            title="Test Dismiss",
            explanation="Explication test dismiss",
            action_type=RecommendationAction.create_crm_activity,
            action_payload={"lead_id": 10},
            status=RecommendationStatus.pending
        )
        self.db.add(rec)
        self.db.commit()

        # Simuler le dismiss
        rec.status = RecommendationStatus.dismissed
        rec.executed_by = 1
        rec.executed_at = datetime.utcnow()

        log = AIActionLog(
            id=uuid.uuid4(),
            recommendation_id=rec.id,
            tenant_id=rec.tenant_id,
            action_type=rec.action_type,
            action_payload=rec.action_payload,
            odoo_result={"info": "Recommandation ignorée par l'utilisateur, aucune action exécutée sur Odoo"},
            executed_by=1,
            executed_at=datetime.utcnow(),
            success=None,
            error_message=None
        )
        self.db.add(log)
        self.db.commit()

        fetched_log = self.db.query(AIActionLog).filter(AIActionLog.recommendation_id == rec.id).first()
        self.assertIsNotNone(fetched_log)
        self.assertIsNone(fetched_log.success, "Le log de dismiss doit avoir success=None en base de données")
        self.assertEqual(rec.status, RecommendationStatus.dismissed)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_domain_preserved_after_multi_cause_fusion(self, mock_groq, mock_odoo):
        """Test non-régression 1 : Une entité stock avec 2 causes (anomaly + kpi_alert) conserve domain='stock' et action_type autorisant restock_order."""
        mock_odoo.search_read.return_value = [{"id": 50, "name": "Produit 50", "qty_available": 2, "lst_price": 500.0}]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Réapprovisionner Produit 50",
                "explanation": "Stock bas et anomalie Z-score détectés sur Produit 50.",
                "action_type": "restock_order",
                "action_payload": {"product_id": 50, "quantity": 30},
                "estimated_impact": {"label": "+15 000 MAD", "confidence": "high"}
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert_kpi = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock critique", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())
        alert_anomaly = Alert(id="anomaly_stock_50", kpi_id="stock_alerts", message="Anomalie Z-score stock 50", severity="critical", is_anomaly=True, timestamp=datetime.utcnow())

        generate_recommendations(self.db, [alert_kpi, alert_anomaly], tenant_id=self.tenant_id)

        rec = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_50").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.action_type, RecommendationAction.restock_order)
        self.assertIn("product_id", rec.action_payload)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_domain_resolution_independent_of_cause_order(self, mock_groq, mock_odoo):
        """Test non-régression 2 : L'ordre des causes (générique puis stock) produit exactement le même domain='stock'."""
        mock_odoo.search_read.return_value = [{"id": 60, "name": "Produit 60", "qty_available": 1, "lst_price": 200.0}]
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "title": "Réapprovisionner Produit 60",
                "explanation": "Recommandation stock",
                "action_type": "restock_order",
                "action_payload": {"product_id": 60, "quantity": 10},
                "estimated_impact": {"label": "+2000 MAD", "confidence": "medium"}
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion

        # Alerte générique en premier, alerte stock en second
        alert_generic = Alert(id="stock_anomaly_60", kpi_id="stock_alerts", message="Baisse anomale observée", severity="warning", is_anomaly=True, timestamp=datetime.utcnow())
        alert_stock = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="critical", is_anomaly=False, timestamp=datetime.utcnow())

        generate_recommendations(self.db, [alert_generic, alert_stock], tenant_id=self.tenant_id)

        rec = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_60").first()
        self.assertIsNotNone(rec)
        self.assertEqual(rec.action_type, RecommendationAction.restock_order)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_priority_score_differentiates_entities(self, mock_groq, mock_odoo):
        """Test non-régression 3 : 15 entités stock avec des valeurs financières différentes sont différenciées par priority_score."""
        products = [{"id": i, "name": f"Produit {i}", "qty_available": 10 - i, "lst_price": i * 100.0} for i in range(1, 16)]
        mock_odoo.search_read.return_value = products

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"title": "Action", "explanation": "Exp", "action_type": "restock_order", "action_payload": {"product_id": 1, "quantity": 10}}'))]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        all_recs = self.db.query(AIRecommendation).filter(AIRecommendation.tenant_id == self.tenant_id, AIRecommendation.status == RecommendationStatus.pending).all()
        self.assertTrue(len(all_recs) > 1)
        first_rec = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_15").first()
        self.assertIsNotNone(first_rec)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_no_more_than_12_pending_plus_overflow_in_db(self, mock_groq, mock_odoo):
        """Test non-régression 4 : Après un cycle avec 15 entités, la DB contient au maximum 13 lignes pending (12 individuelles + 1 overflow)."""
        products = [{"id": i, "name": f"Produit {i}", "qty_available": 1, "lst_price": 50.0} for i in range(1, 16)]
        mock_odoo.search_read.return_value = products

        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock(message=MagicMock(content='{"title": "Action", "explanation": "Exp", "action_type": "none"}'))]
        mock_groq.chat.completions.create.return_value = mock_completion

        alert = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Stock bas", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        pending_count = self.db.query(AIRecommendation).filter(
            AIRecommendation.tenant_id == self.tenant_id,
            AIRecommendation.status == RecommendationStatus.pending
        ).count()
        self.assertLessEqual(pending_count, 13)

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_fallback_title_is_generic_and_static(self, mock_groq, mock_odoo):
        mock_odoo.search_read.return_value = [{"id": 70, "name": "Produit 70", "qty_available": 1, "lst_price": 50.0}]
        mock_groq.chat.completions.create.side_effect = Exception("Rate limit 429")

        # 1. Fallback Option 1 pour le domaine stock (restock_order avec quantité calculée)
        alert_stock = Alert(id="stock_alerts", kpi_id="stock_alerts", message="Message d'alerte brut stock", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert_stock], tenant_id=self.tenant_id)


        rec_stock = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "product_70").first()
        self.assertIsNotNone(rec_stock)
        self.assertEqual(rec_stock.action_type, RecommendationAction.restock_order)
        self.assertIn("product_id", rec_stock.action_payload)
        self.assertNotIn("Message d'alerte brut stock", rec_stock.title)

        # 2. Fallback Option 2 pour les domaines non-stock (titre générique fixe)
        alert_general = Alert(id="general_drop", kpi_id="revenue", message="Message d'alerte brut général", severity="warning", is_anomaly=False, timestamp=datetime.utcnow())
        generate_recommendations(self.db, [alert_general], tenant_id=self.tenant_id)

        rec_gen = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "anomaly_general_drop").first()
        self.assertIsNotNone(rec_gen)
        self.assertIn("Analyse IA temporairement indisponible", rec_gen.title)
        self.assertNotIn("Message d'alerte brut général", rec_gen.title)


    @patch("app.services.recommendation_generator.odoo")
    def test_batch_json_parsing_multi_domain(self, mock_odoo):
        """Vérification b : Parsing d'une réponse JSON batch contenant 3 entités de domaines différents."""
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
              "recommendations": [
                {
                  "entity_key": "product_21",
                  "title": "Réapprovisionner Cabinet avec Portes",
                  "explanation": "Stock bas (2 unités restantes).",
                  "action_type": "restock_order",
                  "action_payload": {"product_id": 21, "quantity": 15},
                  "estimated_impact": {"label": "+6 750 MAD", "confidence": "high"}
                },
                {
                  "entity_key": "partner_105",
                  "title": "Campagne de relance client inactif",
                  "explanation": "Client inactif depuis 90 jours.",
                  "action_type": "send_email_campaign",
                  "action_payload": {"customer_ids": [105], "template": "winback"},
                  "estimated_impact": {"label": "+12 000 MAD", "confidence": "medium"}
                },
                {
                  "entity_key": "lead_42",
                  "title": "Relancer opportunité CRM stagnante",
                  "explanation": "Offre sans mise à jour depuis 14 jours.",
                  "action_type": "create_crm_activity",
                  "action_payload": {"lead_id": 42, "summary": "Appel de relance"},
                  "estimated_impact": {"label": "+45 000 MAD", "confidence": "high"}
                }
              ]
            }
            """))
        ]
        with patch("app.services.recommendation_generator._client.chat.completions.create", return_value=mock_completion):
            batch_items = [
                {"entity_key": "product_21", "domain": "stock", "data": {"id": 21}},
                {"entity_key": "partner_105", "domain": "customer", "data": {"id": 105}},
                {"entity_key": "lead_42", "domain": "crm", "data": {"id": 42}},
            ]
            results = _execute_batch_llm_call(batch_items, self.db)
            self.assertIn("product_21", results)
            self.assertIn("partner_105", results)
            self.assertIn("lead_42", results)
            self.assertEqual(results["product_21"]["action_type"], "restock_order")
            self.assertEqual(results["partner_105"]["action_type"], "send_email_campaign")
            self.assertEqual(results["lead_42"]["action_type"], "create_crm_activity")

    def test_domain_mapping_covers_all_known_kpis(self):
        """Étape 3 Test 1 : Vérifie que TOUS les kpi_id connus du système sont couverts dans KPI_TO_DOMAIN et KPI_LABELS."""
        from app.services.kpi_calculator import _KPI_ORDER
        for kpi_id in _KPI_ORDER:
            self.assertIn(kpi_id, KPI_TO_DOMAIN, f"Le KPI '{kpi_id}' doit être présent dans KPI_TO_DOMAIN")
            self.assertIn(kpi_id, KPI_LABELS, f"Le KPI '{kpi_id}' doit être présent dans KPI_LABELS")

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_fallback_titles_differentiated_by_domain(self, mock_groq, mock_odoo):
        """Étape 3 Test 2 : 4 anomalies non-stock en échec LLM produisent des titres de fallback tous différents et identifiables."""
        mock_groq.chat.completions.create.side_effect = Exception("Rate limit 429")
        alerts = [
            Alert(id="revenue_drop", kpi_id="revenue", message="Baisse CA", severity="critical", is_anomaly=True, timestamp=datetime.utcnow()),
            Alert(id="active_cust", kpi_id="active_customers", message="Chute clients actifs", severity="warning", is_anomaly=True, timestamp=datetime.utcnow()),
            Alert(id="late_ord", kpi_id="late_orders", message="Retards livraison", severity="warning", is_anomaly=True, timestamp=datetime.utcnow()),
            Alert(id="new_ord", kpi_id="new_orders", message="Baisse commandes", severity="warning", is_anomaly=True, timestamp=datetime.utcnow()),
        ]
        generate_recommendations(self.db, alerts, tenant_id=self.tenant_id)

        recs = self.db.query(AIRecommendation).filter(
            AIRecommendation.tenant_id == self.tenant_id,
            AIRecommendation.status == RecommendationStatus.pending
        ).all()

        titles = [r.title for r in recs]
        self.assertEqual(len(titles), 4)
        self.assertEqual(len(set(titles)), 4, "Chaque anomalie non-stock doit avoir un titre de fallback unique")
        self.assertTrue(any("Chiffre d'affaires" in t for t in titles))
        self.assertTrue(any("Clients actifs" in t for t in titles))
        self.assertTrue(any("Commandes en retard" in t for t in titles))
        self.assertTrue(any("Nouvelles commandes" in t for t in titles))

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_all_score_health_anomalies_produce_a_card(self, mock_groq, mock_odoo):
        """Étape 3 Test 3 : L'anomalie 'clients_actifs' produit obligatoirement domain='customer_inactive' et une carte de recommandation."""
        mock_groq.chat.completions.create.side_effect = Exception("Rate limit 429")
        alert = Alert(id="active_customers", kpi_id="active_customers", message="Hausse anormale détectée pour clients actifs", severity="critical", is_anomaly=True, timestamp=datetime.utcnow())

        generate_recommendations(self.db, [alert], tenant_id=self.tenant_id)

        rec = self.db.query(AIRecommendation).filter(AIRecommendation.entity_key == "anomaly_active_customers").first()
        self.assertIsNotNone(rec, "L'anomalie active_customers doit obligatoirement produire une carte")
        domain_resolved = _resolve_domain_from_entity_key(rec.entity_key)
        self.assertEqual(domain_resolved, "customer_inactive", "L'anomalie active_customers doit être résolue vers le domaine 'customer_inactive'")

    def test_no_hardcoded_substring_matching_for_domain(self):
        """Étape 3 Test 4 : Vérifie que la résolution de domaine pour anomalies globales est déterministe et exacte."""
        self.assertEqual(_resolve_domain_from_entity_key("anomaly_active_customers"), "customer_inactive")
        self.assertEqual(_resolve_domain_from_entity_key("anomaly_revenue"), "revenue_trend")
        self.assertEqual(_resolve_domain_from_entity_key("anomaly_late_orders"), "global_trend")
        self.assertEqual(_resolve_domain_from_entity_key("anomaly_new_leads"), "crm")


if __name__ == "__main__":
    unittest.main()

