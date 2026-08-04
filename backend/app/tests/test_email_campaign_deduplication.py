import uuid
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.models.ai_recommendation import AIRecommendation, RecommendationAction, RecommendationStatus
from app.schemas.alert import Alert, AlertSourceData
from app.services.recommendation_generator import generate_recommendations

class TestEmailCampaignDeduplication(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db = Session()
        self.tenant_id = uuid.uuid4()

        tenant = Tenant(id=self.tenant_id, name="Test Tenant")
        user = User(id=1, email="admin@smarterp.ai", hashed_password="pw")
        self.db.add(tenant)
        self.db.add(user)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    @patch("app.services.recommendation_generator.odoo")
    @patch("app.services.recommendation_generator._client")
    def test_email_campaign_overlap_fusion_and_subtraction(self, mock_groq, mock_odoo):
        """
        Test de l'Étape 3 :
        Simule 4 anomalies email avec des chevauchements variés (100%, 60%, 10% <= 50%) :
        - Anomaly A: [1..10] -> Crée Segment 1
        - Anomaly B: [1..10] -> 100% overlap -> Fusionne dans Segment 1
        - Anomaly C: [5..14] -> 6/10 = 60% overlap -> Fusionne dans Segment 1 (Union = 1..14)
        - Anomaly D: [14..23] -> 1/10 = 10% overlap (<= 50%) -> Crée Segment 2 (Soustraction: [15..23])

        Vérifications :
        1. Les chevauchements > 50% sont fusionnés en 1 seule carte multi-causes.
        2. Aucun partner_id n'apparaît dans plus d'une recommandation pending à la fin du cycle.
        """
        anomalies_data = [
            ("anomaly_revenue_drop", "revenue", list(range(1, 11))),          # 1..10
            ("anomaly_new_orders", "new_orders", list(range(1, 11))),          # 1..10 (100% overlap)
            ("anomaly_active_customers", "active_customers", list(range(5, 15))), # 5..14 (60% overlap)
            ("anomaly_conversion_rate", "conversion_rate", list(range(14, 24)))  # 14..23 (10% overlap)
        ]

        alerts = [
            Alert(
                id=aid,
                kpi_id=kpi,
                message=f"Alerte sur {kpi}",
                severity="critical",
                is_anomaly=True,
                timestamp=datetime.utcnow(),
                source_data=AlertSourceData(
                    kpi_label=kpi,
                    kpi_value=100.0,
                    model="res.partner",
                    domain="[]",
                    formula="test",
                    threshold_info="test",
                    partner_ids=pids
                )
            )
            for aid, kpi, pids in anomalies_data
        ]

        # Mock LLM response to simulate batch recommendation creation
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="""
            {
                "recommendations": [
                    {
                        "entity_key": "email_campaign_segment_1",
                        "title": "Réactiver les clients inactifs — CA, commandes et clients actifs en baisse",
                        "explanation": "Multiples anomalies détectées.",
                        "action_type": "send_email_campaign",
                        "action_payload": {},
                        "estimated_impact": {"label": "+20 000 MAD", "confidence": "high"}
                    },
                    {
                        "entity_key": "email_campaign_segment_2",
                        "title": "Réactiver les clients inactifs — Taux de conversion en baisse",
                        "explanation": "Anomalie conversion.",
                        "action_type": "send_email_campaign",
                        "action_payload": {},
                        "estimated_impact": {"label": "+10 000 MAD", "confidence": "medium"}
                    }
                ]
            }
            """))
        ]
        mock_groq.chat.completions.create.return_value = mock_completion
        mock_odoo.search_read.return_value = []

        # Execute recommendation generation
        generate_recommendations(self.db, alerts, tenant_id=self.tenant_id)

        # Retrieve pending email campaign recommendations
        recs = self.db.query(AIRecommendation).filter(
            AIRecommendation.tenant_id == self.tenant_id,
            AIRecommendation.status == RecommendationStatus.pending,
            AIRecommendation.action_type == RecommendationAction.send_email_campaign
        ).all()

        # 1. Vérification du nombre de cartes (Seulement 2 cartes créées)
        self.assertEqual(len(recs), 2, f"Attendu 2 recommandations uniques, mais obtenu {len(recs)}")

        # 2. Récupération des partner_ids des deux cartes
        card1_pids = set(recs[0].action_payload.get("partner_ids", []))
        card2_pids = set(recs[1].action_payload.get("partner_ids", []))

        # 3. Vérification d'absence TOTALE de doublons (Intersection nulle)
        intersection = card1_pids & card2_pids
        self.assertEqual(
            len(intersection), 0,
            f"ERREUR : Des partner_ids en double ont été trouvés entre cartes : {intersection}"
        )

        # 4. Vérification de l'UNION et de la soustraction exacte
        all_pids = card1_pids | card2_pids
        self.assertEqual(all_pids, set(range(1, 24)), "Tous les clients de 1 à 23 doivent être couverts sans perte.")

        # Vérifier que le segment fusionné (>50%) contient bien 1..14 (14 clients)
        segment1_rec = next(r for r in recs if len(r.action_payload.get("partner_ids", [])) == 14)
        self.assertEqual(set(segment1_rec.action_payload["partner_ids"]), set(range(1, 15)))

        # Vérifier que le segment soustrait (<=50%) contient bien 15..23 (9 clients, 14 soustrait)
        segment2_rec = next(r for r in recs if len(r.action_payload.get("partner_ids", [])) == 9)
        self.assertEqual(set(segment2_rec.action_payload["partner_ids"]), set(range(15, 24)))

        # 5. Vérifier que la carte fusionnée a un titre multi-causes
        self.assertIn("—", segment1_rec.title)
