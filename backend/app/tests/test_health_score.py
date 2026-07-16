import unittest
from unittest.mock import patch
from app.schemas.kpi import KPI
from app.schemas.alert import Alert
from app.services.health_score_engine import compute_health_score


class TestHealthScoreEngine(unittest.TestCase):

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_perfect_condition(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=0.0)
        ]
        mock_evaluate_alerts.return_value = []

        # Act
        health = compute_health_score()

        # Assert
        self.assertEqual(health.score, 100)
        self.assertEqual(health.label, "Excellente santé")
        self.assertEqual(len(health.factors), 1)
        self.assertEqual(health.factors[0].label, "Aucun signal notable détecté")

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_finance_critical_alert(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=-20.0)
        ]
        mock_evaluate_alerts.return_value = [
            Alert(id="revenue", kpi_id="revenue", severity="critical", message="Baisse critique du CA")
        ]

        # Act
        health = compute_health_score()

        # Assert
        # Finance critical penalty = -20
        self.assertEqual(health.score, 80)
        self.assertEqual(health.label, "Excellente santé")  # score >= 80 is Excelente santé
        self.assertEqual(len(health.factors), 1)
        self.assertEqual(health.factors[0].impact, -20)
        self.assertIn("[Finance]", health.factors[0].label)

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_operations_warning_alert(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="stock_alerts", label="Stock bas", value=5.0)
        ]
        mock_evaluate_alerts.return_value = [
            Alert(id="stock_alerts", kpi_id="stock_alerts", severity="warning", message="Stock bas")
        ]

        # Act
        health = compute_health_score()

        # Assert
        # Operations warning penalty = -5
        self.assertEqual(health.score, 95)
        self.assertEqual(len(health.factors), 1)
        self.assertEqual(health.factors[0].impact, -5)
        self.assertIn("[Opérations]", health.factors[0].label)

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_crm_critical_alert(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="pipeline_value", label="Pipeline CRM", value=50000.0, change_percent=-45.0)
        ]
        mock_evaluate_alerts.return_value = [
            Alert(id="pipeline_value", kpi_id="pipeline_value", severity="critical", message="Baisse du CRM")
        ]

        # Act
        health = compute_health_score()

        # Assert
        # CRM critical penalty = -10
        self.assertEqual(health.score, 90)
        self.assertEqual(len(health.factors), 1)
        self.assertEqual(health.factors[0].impact, -10)
        self.assertIn("[CRM]", health.factors[0].label)

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_revenue_bonus(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="revenue", label="CA", value=12000.0, change_percent=10.0)
        ]
        mock_evaluate_alerts.return_value = []

        # Act
        health = compute_health_score()

        # Assert
        # base (100) + bonus (min(10.0 * 0.2, 5) = 2.0) = 102 -> capped at 100
        self.assertEqual(health.score, 100)
        # However, check that the bonus factor is added
        self.assertEqual(len(health.factors), 1)
        self.assertEqual(health.factors[0].impact, 2.0)
        self.assertIn("Chiffre d'affaires en hausse de 10.0%", health.factors[0].label)

    @patch("app.services.health_score_engine.get_kpis")
    @patch("app.services.health_score_engine.evaluate_alerts")
    def test_health_score_multiple_alerts(self, mock_evaluate_alerts, mock_get_kpis):
        # Arrange
        mock_get_kpis.return_value = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=-20.0),
            KPI(id="stock_alerts", label="Stock bas", value=15.0),
            KPI(id="pipeline_value", label="Pipeline CRM", value=50000.0, change_percent=-45.0)
        ]
        mock_evaluate_alerts.return_value = [
            Alert(id="revenue", kpi_id="revenue", severity="critical", message="Baisse critique du CA"),
            Alert(id="stock_alerts", kpi_id="stock_alerts", severity="critical", message="Stock critique"),
            Alert(id="pipeline_value", kpi_id="pipeline_value", severity="critical", message="Baisse du CRM")
        ]

        # Act
        health = compute_health_score()

        # Assert
        # Penalties: Finance critical (-20) + Operations critical (-15) + CRM critical (-10) = -45
        # Expected score: 100 - 45 = 55
        self.assertEqual(health.score, 55)
        self.assertEqual(health.label, "Vigilance requise")
        self.assertEqual(len(health.factors), 3)
