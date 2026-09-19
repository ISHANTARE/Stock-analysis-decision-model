"""
Unit & Integration Test Suite for Quantamental Stock Decision Engine.
"""

import unittest
from src.market_data import normalize_ticker, format_currency_value
from src.financial_engine import compute_health_metrics, compute_valuation_scenarios
from src.decision_engine import synthesize_decision


class TestStockEngine(unittest.TestCase):

    def test_ticker_normalization(self):
        # Indian bluechip auto-resolution
        res = normalize_ticker("RELIANCE")
        self.assertEqual(res["symbol"], "RELIANCE.NS")
        self.assertEqual(res["market"], "IN")

        res_tcs = normalize_ticker("TCS")
        self.assertEqual(res_tcs["symbol"], "TCS.NS")

        # Explicit Indian exchange suffix
        res_bse = normalize_ticker("INFY.BO")
        self.assertEqual(res_bse["symbol"], "INFY.BO")
        self.assertEqual(res_bse["market"], "IN")
        self.assertEqual(res_bse["exchange"], "BSE")

        # Global US stock
        res_us = normalize_ticker("NVDA")
        self.assertEqual(res_us["symbol"], "NVDA")
        self.assertEqual(res_us["market"], "GLOBAL")

    def test_currency_formatting(self):
        # Indian Crore formatting
        self.assertEqual(format_currency_value(16500000000000, "INR"), "₹16.50 Lakh Cr")
        self.assertEqual(format_currency_value(500000000, "INR"), "₹50.00 Cr")

        # US formatting
        self.assertEqual(format_currency_value(3000000000000, "USD"), "$3.00 Trillion")
        self.assertEqual(format_currency_value(500000000, "USD"), "$500.00 Million")

    def test_valuation_scenarios(self):
        dummy_state = {
            "current_price": 1000.0,
            "financial_metrics": {
                "revenue_growth_yoy": 0.15,
                "pe_forward": 25.0
            }
        }
        scenarios = compute_valuation_scenarios(dummy_state)
        bull = scenarios["bull_case"]["target_price"]
        base = scenarios["base_case"]["target_price"]
        bear = scenarios["bear_case"]["target_price"]

        self.assertGreater(bull, base)
        self.assertGreater(base, bear)
        self.assertGreater(bear, 0)

    def test_forensic_veto_trigger(self):
        dummy_state = {
            "ticker": "TEST.NS",
            "company_name": "Test Company",
            "market": "IN",
            "currency": "INR",
            "current_price": 100.0
        }
        health_metrics = {"health_status": "HEALTHY_SAFE_ZONE", "altman_z_score": 3.5}
        valuation_scenarios = {
            "bull_case": {"target_price": 200.0, "upside_pct": 100.0},
            "base_case": {"target_price": 150.0, "upside_pct": 50.0},
            "bear_case": {"target_price": 120.0, "upside_pct": 20.0}
        }
        # Jev reports high forensic risk (noul = 0.85)
        high_risk_jev = {
            "overall_confidence": 0.85,
            "guidance_trajectory": {
                "choice": "accelerating",
                "probabilities": {"accelerating": 0.80, "steady": 0.15, "decelerating": 0.05}
            },
            "management_conviction": {"score": 2.5},
            "economic_moat": {"score": 2.8},
            "forensic_governance_risk": {"noul": 0.85},  # > 0.60 VETO THRESHOLD
            "macro_policy_tailwinds": {"choice": "strong_tailwinds"}
        }

        decision = synthesize_decision(
            stock_state=dummy_state,
            health_metrics=health_metrics,
            valuation_scenarios=valuation_scenarios,
            jev_eval=high_risk_jev
        )

        # Must trigger hard veto regardless of 100% upside
        self.assertEqual(decision["action"], "STRONG_SELL_OR_AVOID")
        self.assertTrue(decision["is_vetoed"])


if __name__ == "__main__":
    unittest.main()
