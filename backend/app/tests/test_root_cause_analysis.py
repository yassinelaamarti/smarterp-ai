import unittest
from unittest.mock import MagicMock, patch

from app.services.root_cause_analysis import (
    compute_root_cause_data,
    generate_rca_explanation,
    _run_real_rca_decomposition
)


class TestRootCauseAnalysis(unittest.TestCase):

    def test_mathematical_coherence_sum(self):
        """Vérifier que la somme des contribution_pct du top 3 + residual_pct englobe exactement 100.0%."""
        res = compute_root_cause_data("revenue", current_value=50000.0, change_percent=-8.5)

        breakdown = res["breakdown"]
        residual_pct = res["residual_pct"]

        sum_top3 = sum(item["contribution_pct"] for item in breakdown)
        total_sum = round(sum_top3 + residual_pct, 1)

        self.assertAlmostEqual(total_sum, 100.0, delta=0.5)
        self.assertGreaterEqual(residual_pct, 0.0)
        self.assertLessEqual(len(breakdown), 3)

    def test_zero_division_safety(self):
        """Vérifier l'absence de crash en cas de division par zéro (previous = 0 ou current = 0)."""
        # Case 1: current = 0, change_percent = None
        res1 = compute_root_cause_data("revenue", current_value=0.0, change_percent=None)
        self.assertIsNotNone(res1)
        self.assertIn("breakdown", res1)

        # Case 2: change_percent = 0
        res2 = compute_root_cause_data("new_orders", current_value=0.0, change_percent=0.0)
        self.assertIsNotNone(res2)
        self.assertIn("breakdown", res2)

    @patch("app.services.root_cause_analysis.odoo")
    def test_full_outer_join_missing_segment(self, mock_odoo):
        """Vérifier qu'un produit vendu le mois dernier mais à 0 ce mois-ci (FULL OUTER JOIN) est capturé."""
        # Configurer les dates
        cur_orders = [
            {"id": 1, "amount_total": 1000.0, "partner_id": [10, "Client A"], "user_id": [1, "Marc"]}
        ]
        prev_orders = [
            {"id": 2, "amount_total": 1000.0, "partner_id": [10, "Client A"], "user_id": [1, "Marc"]},
            {"id": 3, "amount_total": 3000.0, "partner_id": [11, "Client B"], "user_id": [2, "Karim"]}
        ]

        def search_read_side_effect(model, domain, fields):
            if model == "sale.order":
                if ">=" in str(domain) and "<" not in str(domain):
                    return cur_orders
                else:
                    return prev_orders
            elif model == "res.partner":
                return [{"id": 10, "state_id": [1, "Casablanca"]}, {"id": 11, "state_id": [2, "Rabat"]}]
            elif model == "sale.order.line":
                if domain == [["order_id", "in", [1]]]:
                    return [{"product_id": [101, "Produit A"], "price_subtotal": 1000.0}]
                else:
                    return [
                        {"product_id": [101, "Produit A"], "price_subtotal": 1000.0},
                        {"product_id": [102, "Produit B Disparu"], "price_subtotal": 3000.0}
                    ]
            return []

        mock_odoo.search_read.side_effect = search_read_side_effect

        res = _run_real_rca_decomposition("revenue", 1000.0, -75.0, "Mois en cours", "Mois précédent")

        self.assertIsNotNone(res)
        breakdown = res["breakdown"]

        # Le produit B qui a fait 0 ce mois-ci doit apparaître avec une baisse de -3000.0
        product_b = next((item for item in breakdown if item["segment"] == "Produit B Disparu"), None)
        self.assertIsNotNone(product_b, "Le produit à 0 ventes cette semaine doit être capturé par le FULL OUTER JOIN !")
        self.assertEqual(product_b["delta"], -3000.0)

    @patch("app.services.root_cause_analysis.Groq")
    def test_llm_explanation_generation(self, mock_groq_class):
        """Vérifier que la génération de l'explication LLM produit un texte valide sans crash."""
        mock_client = MagicMock()
        mock_completion = MagicMock()
        mock_completion.choices[0].message.content = (
            "La baisse du chiffre d'affaires s'explique par la région Casablanca, suivie du produit X et du commercial Marc Demo. "
            "Ces 3 facteurs représentent l'essentiel de la baisse."
        )
        mock_client.chat.completions.create.return_value = mock_completion
        mock_groq_class.return_value = mock_client

        rca_data = compute_root_cause_data("revenue", current_value=40000.0, change_percent=-8.0)
        explanation = generate_rca_explanation(rca_data)

        self.assertIsNotNone(explanation)
        self.assertTrue(len(explanation) > 10)


if __name__ == "__main__":
    unittest.main()
