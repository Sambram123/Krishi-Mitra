"""
Krishi Mitra — Automated Test Suite for Deterministic Rule Evaluator
Tests rule boundaries, statutory exclusions, real scheme status, and catalogue sources.
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

    def test_all_catalog_entries_are_real_government_programs(self):
        self.assertEqual(len(self.evaluator.schemes_map), 5)
        self.assertTrue(all(not scheme["is_demo"] for scheme in self.evaluator.dataset["schemes"]))
        self.assertTrue(all(scheme.get("sources") for scheme in self.evaluator.dataset["schemes"]))
        self.assertNotIn("90%", self.evaluator.schemes_map["pmksy_pdmc"]["benefit"]["description_en"])
        self.assertNotIn("50%", self.evaluator.schemes_map["smam"]["benefit"]["description_en"])
        self.assertIn("not a", self.evaluator.schemes_map["soil_health_card"]["benefit"]["description_en"])

    def test_real_agriculture_programs_are_not_asserted_as_approved(self):
        results = {
            result.scheme_id: result
            for result in self.evaluator.evaluate_all(FarmerProfile(
                land_acres=3,
                irrigation_type="Borewell",
                requested_equipment="Power Tiller",
            ))
        }
        for scheme_id in ("pmksy_pdmc", "smam"):
            self.assertEqual(results[scheme_id].status, "CONDITIONALLY_ELIGIBLE")
            self.assertFalse(results[scheme_id].is_demo)
            self.assertFalse(results[scheme_id].disqualification_reasons)

    def test_soil_health_card_is_not_misrepresented_as_a_cash_grant(self):
        result = self.evaluator.evaluate_soil_health_card(FarmerProfile(has_soil_health_card=True))
        self.assertEqual(result.status, "INFORMATIONAL")
        self.assertFalse(result.is_demo)
        self.assertIn("not a", result.benefit_summary_en)
        self.assertFalse(result.disqualification_reasons)


if __name__ == "__main__":
    unittest.main()
