import unittest
from unittest.mock import patch
from app.schemas.kpi import KPI
from app.schemas.alert import Alert
from app.services.alert_engine import evaluate_alerts


class TestAlertEngine(unittest.TestCase):
    def setUp(self):
        self.default_settings = {
            "stock_critical": 10.0,
            "stock_warning": 2.0,
            "late_orders_critical": 5.0,
            "late_orders_warning": 1.0,
            "revenue_critical": -15.0,
            "revenue_warning": -5.0,
            "new_orders_critical": -30.0,
            "new_orders_warning": -20.0,
            "conversion_rate_critical": -30.0,
            "conversion_rate_warning": -20.0,
            "pipeline_value_critical": -40.0,
            "pipeline_value_warning": -30.0,
            "active_customers_critical": -30.0,
            "active_customers_warning": -20.0,
        }

    def test_evaluate_alerts_stock_critical(self):
        kpis = [
            KPI(id="stock_alerts", label="Stock bas", value=12.0)
        ]


        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "critical")
        self.assertIn("stock critique", alerts[0].message)

    def test_evaluate_alerts_stock_no_alert(self):
        kpis = [
            KPI(id="stock_alerts", label="Stock bas", value=0.0)
        ]
        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 0)


    def test_evaluate_alerts_late_orders_critical(self):
        kpis = [
            KPI(id="late_orders", label="Commandes en retard", value=8.0)
        ]
        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "critical")
        self.assertIn("commandes en retard de livraison", alerts[0].message)

    def test_evaluate_alerts_revenue_drop_critical(self):
        kpis = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=-18.5)
        ]
        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "critical")
        self.assertIn("chuté de 18.5%", alerts[0].message)

    def test_evaluate_alerts_revenue_drop_warning(self):
        kpis = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=-8.0)
        ]
        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].severity, "warning")
        self.assertIn("en baisse de 8.0%", alerts[0].message)

    def test_evaluate_alerts_multiple_kpis(self):
        kpis = [
            KPI(id="revenue", label="CA", value=10000.0, change_percent=-25.0),
            KPI(id="stock_alerts", label="Stock bas", value=1.0),
            KPI(id="late_orders", label="Commandes en retard", value=6.0)
        ]
        alerts = evaluate_alerts(kpis, self.default_settings)
        self.assertEqual(len(alerts), 3)
        kpi_ids = {a.kpi_id for a in alerts}
        self.assertEqual(kpi_ids, {"revenue", "stock_alerts", "late_orders"})

    @patch("app.services.alert_engine.current_month_str")
    def test_evaluate_alerts_anomaly_detected(self, mock_current_month_str):
        from unittest.mock import MagicMock, patch
        from app.models.kpi_cache import KPIHistoryCache
        
        mock_current_month_str.return_value = "2026-07"
        
        # Mock DB session
        mock_db = MagicMock()
        
        # Simuler un historique stable autour de 100 pour le CA
        mock_history = [
            KPIHistoryCache(kpi_id="revenue", month="2026-06", value=100.0),
            KPIHistoryCache(kpi_id="revenue", month="2026-05", value=101.0),
            KPIHistoryCache(kpi_id="revenue", month="2026-04", value=99.0),
        ]
        mock_db.query().filter().all.return_value = mock_history
        
        # Valeur actuelle du CA est 150 (gros pic/anomalie !)
        kpis = [
            KPI(id="revenue", label="CA", value=150.0)
        ]
        
        alerts = evaluate_alerts(kpis, self.default_settings, db=mock_db)
        
        # Vérifications
        anomaly_alerts = [a for a in alerts if a.is_anomaly]
        self.assertEqual(len(anomaly_alerts), 1)
        self.assertEqual(anomaly_alerts[0].severity, "critical")
        self.assertIn("anormale détectée", anomaly_alerts[0].message)
        self.assertTrue(anomaly_alerts[0].is_anomaly)

