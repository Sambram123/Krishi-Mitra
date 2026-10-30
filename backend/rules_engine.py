"""
Krishi Mitra — deterministic, auditable screening for Karnataka agriculture schemes.
Evaluates official government schemes (PM-KISAN, PMFBY) and synthetic benchmark schemes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import os

@dataclass
class FarmerProfile:
    # Basic Demographics & Land
    farmer_name: str = "ರೈತ ಮಿತ್ರ"
    district: str = "General"
    land_acres: float = 0.0
    ownership: str = "Owner"  # "Owner", "Tenant", "Joint Family"
    
    # Crop & Season
    crops: List[str] = field(default_factory=list)  # e.g. ["Ragi", "Pigeon Pea (Togari)"]
    season: str = "Kharif"  # "Kharif", "Rabi", "Summer"
    risk_type: Optional[str] = None  # "Drought", "Excess Rain", "Pest Attack", etc.
    
    # Irrigation & Water Source
    irrigation_type: str = "Rainfed"  # "Rainfed", "Borewell", "Canal", "Open Well"
    has_water_source: bool = False
    availed_drip_subsidy_last_3_years: bool = False
    
    # Mechanization & Needs
    requested_equipment: Optional[str] = None  # "Power Tiller", "Rotavator", "Sprayer", etc.
    equipment_cost_inr: float = 0.0
    
    # Soil Health
    has_soil_health_card: bool = False
    soil_deficiencies: List[str] = field(default_factory=list)  # ["Acidic", "Low Organic Carbon"]
    
    # Official Exclusion Checks
    is_income_tax_payee: bool = False
    is_institutional_landholder: bool = False
    is_constitutional_post_holder: bool = False
    is_government_employee: bool = False


@dataclass
class EvaluationResult:
    scheme_id: str
    scheme_name_kn: str
    scheme_name_en: str
    is_demo: bool
    status: str  # Eligibility screen or INFORMATIONAL for non-benefit services.
    benefit_summary_kn: str
    benefit_summary_en: str
    audit_trail: List[str]
    disqualification_reasons: List[str]
    required_documents: List[Dict[str, Any]]
    disclaimer_kn: Optional[str] = None


class SchemeEvaluator:
    def __init__(self, dataset_path: Optional[str] = None):
        if dataset_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dataset_path = os.path.join(base_dir, "data", "schemes_dataset.json")
        
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)
        
        self.schemes_map = {s["id"]: s for s in self.dataset["schemes"]}

    def evaluate_all(self, profile: FarmerProfile) -> List[EvaluationResult]:
        """Evaluate applicable schemes and return source-backed informational programs."""
        results = [
            self.evaluate_pm_kisan(profile),
            self.evaluate_pmfby(profile),
            self.evaluate_pmksy_pdmc(profile),
            self.evaluate_smam(profile),
            self.evaluate_soil_health_card(profile),
        ]
        return results

    def evaluate_pm_kisan(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["pm_kisan"]
        audit: List[str] = []
        disqualifications: List[str] = []
        
        # Landholder check
        if profile.ownership in ["Owner", "Joint Family Owner"] and profile.land_acres > 0.0:
            audit.append(f"Passed: Valid cultivable landholding of {profile.land_acres} acres under {profile.ownership} title.")
        else:
            disqualifications.append("Exclusion: Applicant must be a recorded landholder with cultivable land in Pahani/RTC.")

        # Mandatory Exclusion Checks
        if profile.is_income_tax_payee:
            disqualifications.append("Exclusion: Individuals who paid Income Tax in the previous assessment year are not eligible.")
        if profile.is_institutional_landholder:
            disqualifications.append("Exclusion: Institutional landholders are excluded from PM-KISAN benefits.")
        if profile.is_constitutional_post_holder:
            disqualifications.append("Exclusion: Present or former constitutional post holders / public representatives are excluded.")
        if profile.is_government_employee:
            disqualifications.append("Exclusion: Regular serving or retired government officers/employees are excluded.")

        if not disqualifications:
            status = "ELIGIBLE"
            audit.append("Passed: Cleared all statutory negative exclusions under Central PM-KISAN guidelines.")
            summary_kn = "ಅರ್ಹರು: ವಾರ್ಷಿಕ ₹6,000 (ಪ್ರತಿ 4 ತಿಂಗಳಿಗೆ ₹2,000) ನೇರ ಬ್ಯಾಂಕ್ ಜಮೆ ಪಡೆಯಲು ನೀವು ಅರ್ಹರಾಗಿದ್ದೀರಿ."
            summary_en = "Eligible: You qualify for Rs. 6,000 annual direct benefit transfer in 3 installments."
        else:
            status = "INELIGIBLE"
            summary_kn = "ಅನರ್ಹರು: ಸರ್ಕಾರದ ನಿಯಮಾವಳಿಗಳ ಪ್ರಕಾರ ನೀವು ಪಿಎಂ-ಕಿಸಾನ್ ಯೋಜನೆಗೆ ಅರ್ಹರಾಗಿರುವುದಿಲ್ಲ."
            summary_en = "Ineligible: Does not satisfy statutory criteria for PM-KISAN income assistance."

        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=False,
            status=status,
            benefit_summary_kn=summary_kn,
            benefit_summary_en=summary_en,
            audit_trail=audit,
            disqualification_reasons=disqualifications,
            required_documents=scheme["required_documents"]
        )

    def evaluate_pmfby(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["pmfby"]
        audit: List[str] = []
        disqualifications: List[str] = []
        
        notified_crops = scheme["eligibility_rules"]["notified_crops"]
        qualifying_calamities = scheme["eligibility_rules"]["qualifying_calamities"]

        # Crop matching (supports partial/case-insensitive matching)
        matched_crops = []
        for c in profile.crops:
            for nc in notified_crops:
                if c.lower() in nc.lower() or nc.lower() in c.lower():
                    matched_crops.append(nc)
        
        if matched_crops:
            audit.append(f"Passed: Cultivating notified insurance crop(s): {', '.join(set(matched_crops))}.")
        else:
            disqualifications.append(f"Exclusion: Crop(s) ({', '.join(profile.crops) or 'None'}) are not currently notified under PMFBY.")

        # Season check
        if profile.season in scheme["eligibility_rules"]["notified_seasons"]:
            audit.append(f"Passed: Crop sown during notified {profile.season} season.")
        else:
            disqualifications.append(f"Exclusion: Season '{profile.season}' is not a notified crop insurance window.")

        # Risk / Damage check
        if profile.risk_type:
            matched_risk = any(profile.risk_type.lower() in q.lower() or q.lower() in profile.risk_type.lower() for q in qualifying_calamities)
            if matched_risk:
                audit.append(f"Passed: Reported peril '{profile.risk_type}' is a notified non-preventable natural risk.")
            else:
                audit.append(f"Note: Reported peril '{profile.risk_type}' requires field-level survey by Joint Inspection Committee.")

        if not disqualifications:
            status = "ELIGIBLE"
            summary_kn = f"ಅರ್ಹರು: ನಿಮ್ಮ {', '.join(set(matched_crops))} ಬೆಳೆಗೆ ಸಂರಕ್ಷಣೆ ಬೆಳೆ ವಿಮೆ ಅಡಿಯಲ್ಲಿ ಪರಿಹಾರ ಪಡೆಯಲು ಅರ್ಹರಾಗಿದ್ದೀರಿ."
            summary_en = f"Eligible: Covered under PMFBY crop insurance for {', '.join(set(matched_crops))} against natural yield loss."
        else:
            status = "INELIGIBLE"
            summary_kn = "ಅನರ್ಹರು: ಪ್ರಸ್ತುತ ಬೆಳೆ ಅಥವಾ ಋತುವು ವಿಮಾ ವ್ಯಾಪ್ತಿಗೆ ಹೊಂದಾಣಿಕೆಯಾಗುವುದಿಲ್ಲ."
            summary_en = "Ineligible: Crop or season does not fall within notified PMFBY insurance coverage."

        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=False,
            status=status,
            benefit_summary_kn=summary_kn,
            benefit_summary_en=summary_en,
            audit_trail=audit,
            disqualification_reasons=disqualifications,
            required_documents=scheme["required_documents"]
        )

    def evaluate_pmksy_pdmc(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["pmksy_pdmc"]
        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=False,
            status="CONDITIONALLY_ELIGIBLE",
            benefit_summary_kn=scheme["benefit"]["description_kn"],
            benefit_summary_en=scheme["benefit"]["description_en"],
            audit_trail=[
                "The official PMKSY portal describes Per Drop More Crop as support for farm-level water-use efficiency through micro irrigation.",
                "Karnataka's current beneficiary criteria, assistance rate, eligible cost, and application window were not verified.",
            ],
            disqualification_reasons=[],
            required_documents=scheme["required_documents"],
        )

    def evaluate_smam(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["smam"]
        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=False,
            status="CONDITIONALLY_ELIGIBLE",
            benefit_summary_kn=scheme["benefit"]["description_kn"],
            benefit_summary_en=scheme["benefit"]["description_en"],
            audit_trail=[
                "The official Farm Machinery DBT portal describes government assistance for procurement of agricultural machinery.",
                "The current Karnataka equipment list, applicant category, assistance rate, application window, and fund availability were not verified.",
            ],
            disqualification_reasons=[],
            required_documents=scheme["required_documents"],
        )

    def evaluate_soil_health_card(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["soil_health_card"]
        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=False,
            status="INFORMATIONAL",
            benefit_summary_kn=scheme["benefit"]["description_kn"],
            benefit_summary_en=scheme["benefit"]["description_en"],
            audit_trail=[
                "This is a soil-testing and advisory service, not an individual cash-subsidy eligibility determination.",
                "Confirm local sample collection and service availability with the district soil-testing facility.",
            ],
            disqualification_reasons=[],
            required_documents=scheme["required_documents"],
        )
