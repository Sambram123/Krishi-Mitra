"""
Krishi Mitra — Automated Test Suite for Deterministic Rule Evaluator
Tests positive eligibility, statutory exclusions, boundary conditions, and demo flags.
"""

import unittest
from backend.rules_engine import SchemeEvaluator, FarmerProfile

class TestKrishiMitraRuleEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = SchemeEvaluator()

    # -------------------------------------------------------------
    # PM-KISAN (Real Scheme) Tests
    # -------------------------------------------------------------
    def test_pm_kisan_eligible(self):
        """Verifies legitimate small landholder is eligible for PM-KISAN."""
        profile = FarmerProfile(
            farmer_name="Basavaraj",
            land_acres=2.5,
            ownership="Owner",
            crops=["Ragi"],
            is_income_tax_payee=False
        )
        res = self.evaluator.evaluate_pm_kisan(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertFalse(res.is_demo)
        self.assertEqual(len(res.disqualification_reasons), 0)
        self.assertTrue(any("6,000" in res.benefit_summary_kn for _ in [1]))
        self.assertEqual(len(res.required_documents), 3)

    def test_pm_kisan_taxpayer_exclusion(self):
        """Verifies statutory exclusion for Income Tax Payers."""
        profile = FarmerProfile(
            farmer_name="City Return Farmer",
            land_acres=5.0,
            ownership="Owner",
            crops=["Paddy"],
            is_income_tax_payee=True  # Disqualifier
        )
        res = self.evaluator.evaluate_pm_kisan(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("Income Tax" in reason for reason in res.disqualification_reasons))

    def test_pm_kisan_institutional_exclusion(self):
        """Verifies institutional landholders are excluded."""
        profile = FarmerProfile(
            land_acres=20.0,
            ownership="Owner",
            is_institutional_landholder=True
        )
        res = self.evaluator.evaluate_pm_kisan(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("Institutional" in r for r in res.disqualification_reasons))

    # -------------------------------------------------------------
    # PMFBY (Real Scheme - Crop Insurance) Tests
    # -------------------------------------------------------------
    def test_pmfby_eligible_drought_loss(self):
        """Verifies crop loss compensation for notified crop during Kharif."""
        profile = FarmerProfile(
            farmer_name="Sharanappa Patil",
            land_acres=3.0,
            crops=["Pigeon Pea (Togari)"],
            season="Kharif",
            risk_type="Drought"
        )
        res = self.evaluator.evaluate_pmfby(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertFalse(res.is_demo)
        self.assertTrue(any("Pigeon Pea (Togari)" in trail for trail in res.audit_trail))

    def test_pmfby_unnotified_crop_rejection(self):
        """Verifies non-notified crops (e.g. Vanilla / Rubber) are excluded."""
        profile = FarmerProfile(
            land_acres=4.0,
            crops=["Vanilla"],
            season="Kharif"
        )
        res = self.evaluator.evaluate_pmfby(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("not currently notified" in r for r in res.disqualification_reasons))

    # -------------------------------------------------------------
    # Demo Micro-Irrigation Support (Synthetic Test Case) Tests
    # -------------------------------------------------------------
    def test_demo_micro_irrigation_small_farmer_90pct(self):
        """Verifies small farmers (<= 5 acres) with water source get 90% subsidy."""
        profile = FarmerProfile(
            land_acres=3.0,
            irrigation_type="Borewell",
            has_water_source=True,
            availed_drip_subsidy_last_3_years=False
        )
        res = self.evaluator.evaluate_demo_micro_irrigation(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertTrue(res.is_demo)
        self.assertIn("90", res.benefit_summary_kn)
        self.assertIsNotNone(res.disclaimer_kn)

    def test_demo_micro_irrigation_large_farmer_70pct(self):
        """Verifies larger farmers (> 5 acres, <= 12.5 acres) get 70% subsidy."""
        profile = FarmerProfile(
            land_acres=8.0,
            irrigation_type="Canal",
            has_water_source=True,
            availed_drip_subsidy_last_3_years=False
        )
        res = self.evaluator.evaluate_demo_micro_irrigation(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertIn("70", res.benefit_summary_kn)

    def test_demo_micro_irrigation_no_water_exclusion(self):
        """Verifies failure when farmer lacks water source."""
        profile = FarmerProfile(
            land_acres=4.0,
            irrigation_type="Rainfed",
            has_water_source=False
        )
        res = self.evaluator.evaluate_demo_micro_irrigation(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("water source" in r.lower() for r in res.disqualification_reasons))

    def test_demo_micro_irrigation_cooldown_exclusion(self):
        """Verifies 3-year cooldown exclusion."""
        profile = FarmerProfile(
            land_acres=2.5,
            has_water_source=True,
            availed_drip_subsidy_last_3_years=True  # Excluded
        )
        res = self.evaluator.evaluate_demo_micro_irrigation(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("cooldown" in r.lower() or "3-year" in r.lower() for r in res.disqualification_reasons))

    # -------------------------------------------------------------
    # Demo Agricultural Equipment Assistance (Synthetic Test Case) Tests
    # -------------------------------------------------------------
    def test_demo_agri_equipment_eligible(self):
        """Verifies 50% subsidy up to Rs 1,00,000 for approved equipment."""
        profile = FarmerProfile(
            land_acres=4.0,
            requested_equipment="Power Tiller"
        )
        res = self.evaluator.evaluate_demo_agri_equipment(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertTrue(res.is_demo)
        self.assertIn("100,000", res.benefit_summary_en)
        self.assertIn("50", res.benefit_summary_en)

    def test_demo_agri_equipment_under_min_acres(self):
        """Verifies rejection if landholding < 1.0 acre minimum."""
        profile = FarmerProfile(
            land_acres=0.5,
            requested_equipment="Rotavator"
        )
        res = self.evaluator.evaluate_demo_agri_equipment(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("minimum 1.0 acre" in r for r in res.disqualification_reasons))

    # -------------------------------------------------------------
    # Demo Soil Improvement Support (Synthetic Test Case) Tests
    # -------------------------------------------------------------
    def test_demo_soil_improvement_eligible(self):
        """Verifies soil health incentive with Soil Health Card deficiency."""
        profile = FarmerProfile(
            land_acres=4.0,
            has_soil_health_card=True,
            soil_deficiencies=["Acidic", "Low Organic Carbon"]
        )
        res = self.evaluator.evaluate_demo_soil_improvement(profile)
        self.assertEqual(res.status, "ELIGIBLE")
        self.assertTrue(res.is_demo)
        self.assertTrue(any("Acidic" in t for t in res.audit_trail))

    def test_demo_soil_improvement_missing_card(self):
        """Verifies rejection when farmer does not have Soil Health Card."""
        profile = FarmerProfile(
            land_acres=3.0,
            has_soil_health_card=False
        )
        res = self.evaluator.evaluate_demo_soil_improvement(profile)
        self.assertEqual(res.status, "INELIGIBLE")
        self.assertTrue(any("Soil Health Card" in r for r in res.disqualification_reasons))


if __name__ == "__main__":
    unittest.main()
