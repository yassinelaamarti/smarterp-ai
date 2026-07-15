import unittest
from unittest.mock import patch
from datetime import date
from app.services.date_utils import current_month_str, previous_month_str


class TestDateUtils(unittest.TestCase):
    @patch("app.services.date_utils.date")
    def test_current_month_str(self, mock_date):
        mock_date.today.return_value = date(2026, 7, 15)
        self.assertEqual(current_month_str(), "2026-07")

    @patch("app.services.date_utils.date")
    def test_previous_month_str_regular_month(self, mock_date):
        # Juillet -> Juin
        mock_date.today.return_value = date(2026, 7, 15)
        self.assertEqual(previous_month_str(), "2026-06")

    @patch("app.services.date_utils.date")
    def test_previous_month_str_january(self, mock_date):
        # Janvier -> Décembre de l'année précédente
        mock_date.today.return_value = date(2026, 1, 15)
        self.assertEqual(previous_month_str(), "2025-12")
