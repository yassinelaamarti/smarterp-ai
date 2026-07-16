import unittest
from unittest.mock import MagicMock, patch
import datetime

from app.models.user import User
from app.services.report_scheduler import (
    generate_pdf_report,
    check_and_send_scheduled_reports
)

class TestReportScheduler(unittest.TestCase):
    def test_generate_pdf_report(self):
        summary_text = (
            "# Rapport decisionnel\n\n"
            "## 1. Synthese Generale\n"
            "Tout va bien. **Le chiffre d'affaires** est excellent.\n"
            "- Point A\n"
            "- Point B\n"
        )
        pdf_bytes = generate_pdf_report(summary_text)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    @patch("app.services.report_scheduler.send_single_report")
    def test_check_and_send_scheduled_reports_eligibility(self, mock_send):
        mock_send.return_value = True
        
        # Mock de session
        db = MagicMock()
        
        today = datetime.date.today()
        
        # Utilisateur 1 : Quotidien, jamais envoyé -> doit envoyer
        user_daily_new = User(
            email="daily_new@smarterp.ai",
            report_schedule="daily",
            last_report_sent=None
        )
        
        # Utilisateur 2 : Quotidien, envoyé aujourd'hui -> ne doit pas envoyer
        user_daily_sent_today = User(
            email="daily_sent@smarterp.ai",
            report_schedule="daily",
            last_report_sent=today.strftime("%Y-%m-%d")
        )
        
        # Utilisateur 3 : Hebdomadaire, envoyé il y a 7 jours -> doit envoyer
        seven_days_ago = today - datetime.timedelta(days=7)
        user_weekly_due = User(
            email="weekly_due@smarterp.ai",
            report_schedule="weekly",
            last_report_sent=seven_days_ago.strftime("%Y-%m-%d")
        )
        
        # Utilisateur 4 : Hebdomadaire, envoyé il y a 2 jours -> ne doit pas envoyer
        two_days_ago = today - datetime.timedelta(days=2)
        user_weekly_not_due = User(
            email="weekly_not_due@smarterp.ai",
            report_schedule="weekly",
            last_report_sent=two_days_ago.strftime("%Y-%m-%d")
        )
        
        db.query().filter().all.return_value = [
            user_daily_new,
            user_daily_sent_today,
            user_weekly_due,
            user_weekly_not_due
        ]
        
        check_and_send_scheduled_reports(db)
        
        # send_single_report doit être appelé exactement 2 fois
        self.assertEqual(mock_send.call_count, 2)
        
        # last_report_sent doit être mis à jour à aujourd'hui
        self.assertEqual(user_daily_new.last_report_sent, today.strftime("%Y-%m-%d"))
        self.assertEqual(user_weekly_due.last_report_sent, today.strftime("%Y-%m-%d"))
        
        # Ne doit pas avoir changé pour les autres
        self.assertEqual(user_daily_sent_today.last_report_sent, today.strftime("%Y-%m-%d"))
        self.assertEqual(user_weekly_not_due.last_report_sent, two_days_ago.strftime("%Y-%m-%d"))
