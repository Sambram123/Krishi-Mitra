"""
Krishi Mitra — Deterministic Scheme Eligibility Engine
Zero-hallucination, auditable rule evaluator for Karnataka agricultural schemes.
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
    status: str  # "ELIGIBLE", "CONDITIONALLY_ELIGIBLE", "INELIGIBLE"
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
        """Evaluates farmer profile against all 5 benchmark schemes."""
        results = [
            self.evaluate_pm_kisan(profile),
            self.evaluate_pmfby(profile),
            self.evaluate_demo_micro_irrigation(profile),
            self.evaluate_demo_agri_equipment(profile),
            self.evaluate_demo_soil_improvement(profile)
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

    def evaluate_demo_micro_irrigation(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["demo_micro_irrigation"]
        audit: List[str] = []
        disqualifications: List[str] = []

        # Land boundaries: 0.5 to 12.5 acres
        if 0.5 <= profile.land_acres <= 12.5:
            audit.append(f"Passed: Land area of {profile.land_acres} acres is within permitted range (0.5 to 12.5 acres).")
        else:
            disqualifications.append(f"Exclusion: Land size ({profile.land_acres} acres) outside permitted demo bounds (0.5 to 12.5 acres).")

        # Water source requirement
        if profile.has_water_source or profile.irrigation_type in ["Borewell", "Canal", "Open Well"]:
            audit.append(f"Passed: Water source verified ({profile.irrigation_type or 'Borewell/Well'}).")
        else:
            disqualifications.append("Exclusion: Micro-irrigation subsidy requires an existing functional water source (Borewell/Well/Canal).")

        # Subsidy cooldown check
        if profile.availed_drip_subsidy_last_3_years:
            disqualifications.append("Exclusion: Applicant previously availed micro-irrigation subsidy within the 3-year cooldown window.")
        else:
            audit.append("Passed: No subsidy availed in preceding 3 years.")

        if not disqualifications:
            # Determine subsidy percentage
            if profile.land_acres <= 5.0:
                subsidy_pct = scheme["benefit"]["small_marginal_subsidy_pct"]
                category = "ಸಣ್ಣ/ಅತಿ ಸಣ್ಣ ರೈತ (Small/Marginal Farmer)"
            else:
                subsidy_pct = scheme["benefit"]["general_farmer_subsidy_pct"]
                category = "ಇತರ ರೈತ (General Farmer)"

            status = "ELIGIBLE"
            audit.append(f"Subsidy Determination: Categorized as {category} based on {profile.land_acres} acres -> {subsidy_pct}% subsidy.")
            summary_kn = f"ಅರ್ಹರು [ಡೆಮೊ]: ನಿಮ್ಮ {profile.land_acres} ಎಕರೆ ಜಮೀನಿಗೆ ಶೇಕಡಾ {subsidy_pct} ರಷ್ಟು ಹನಿ/ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಲಭ್ಯವಿದೆ."
            summary_en = f"Eligible [Demo]: Qualifies for {subsidy_pct}% micro-irrigation subsidy based on {profile.land_acres} acres holding."
        else:
            status = "INELIGIBLE"
            summary_kn = "ಅನರ್ಹರು [ಡೆಮೊ]: ಹನಿ ನೀರಾವರಿ ಯೋಜನೆಯ ನಿಬಂಧನೆಗಳು ಪೂರ್ಣಗೊಂಡಿಲ್ಲ."
            summary_en = "Ineligible [Demo]: Does not meet criteria for micro-irrigation assistance."

        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=True,
            status=status,
            benefit_summary_kn=summary_kn,
            benefit_summary_en=summary_en,
            audit_trail=audit,
            disqualification_reasons=disqualifications,
            required_documents=scheme["required_documents"],
            disclaimer_kn=scheme["disclaimer_kn"]
        )

    def evaluate_demo_agri_equipment(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["demo_agri_equipment"]
        audit: List[str] = []
        disqualifications: List[str] = []

        # Min landholding check (1.0 acre)
        if profile.land_acres >= 1.0:
            audit.append(f"Passed: Land size of {profile.land_acres} acres satisfies minimum mechanization floor (>= 1.0 acre).")
        else:
            disqualifications.append(f"Exclusion: Farm mechanization requires minimum 1.0 acre holding (current: {profile.land_acres} acres).")

        # Equipment request check
        qualifying = scheme["eligibility_rules"]["qualifying_equipment"]
        req_equip = profile.requested_equipment
        
        matched_equip = None
        if req_equip:
            for q in qualifying:
                if req_equip.lower() in q.lower() or q.lower() in req_equip.lower():
                    matched_equip = q
                    break

        if matched_equip:
            audit.append(f"Passed: Requested implement '{matched_equip}' is in the approved subsidy gazette.")
        elif req_equip:
            disqualifications.append(f"Exclusion: Requested implement '{req_equip}' is not in approved list ({', '.join(qualifying)}).")
        else:
            # Conditionally eligible if equipment not explicitly requested yet
            audit.append("Note: Farmer qualifies for mechanization support; implement selection pending.")

        if not disqualifications:
            subsidy_pct = scheme["benefit"]["subsidy_pct"]
            max_cap = scheme["benefit"]["max_subsidy_inr"]
            status = "ELIGIBLE"
            equip_name = matched_equip or "ಕೃಷಿ ಯಂತ್ರೋಪಕರಣ"
            summary_kn = f"ಅರ್ಹರು [ಡೆಮೊ]: {equip_name} ಖರೀದಿಗೆ ಗರಿಷ್ಠ ₹{max_cap:,.0f} ವರೆಗೆ ಶೇಕಡಾ {subsidy_pct} ಸಬ್ಸಿಡಿ ಪಡೆಯಲು ಅರ್ಹರಾಗಿದ್ದೀರಿ."
            summary_en = f"Eligible [Demo]: Qualifies for 50% subsidy up to Rs. {max_cap:,.0f} for approved implement ({equip_name})."
        else:
            status = "INELIGIBLE"
            summary_kn = "ಅನರ್ಹರು [ಡೆಮೊ]: ಯಂತ್ರೋಪಕರಣ ಸಹಾಯ ಯೋಜನೆಯ ಷರತ್ತುಗಳು ಪೂರೈಕೆಯಾಗಿಲ್ಲ."
            summary_en = "Ineligible [Demo]: Does not meet farm equipment assistance conditions."

        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=True,
            status=status,
            benefit_summary_kn=summary_kn,
            benefit_summary_en=summary_en,
            audit_trail=audit,
            disqualification_reasons=disqualifications,
            required_documents=scheme["required_documents"],
            disclaimer_kn=scheme["disclaimer_kn"]
        )

    def evaluate_demo_soil_improvement(self, profile: FarmerProfile) -> EvaluationResult:
        scheme = self.schemes_map["demo_soil_improvement"]
        audit: List[str] = []
        disqualifications: List[str] = []

        # Soil health card possession
        if profile.has_soil_health_card:
            audit.append("Passed: Possesses official Soil Health Card (SHC) report.")
        else:
            disqualifications.append("Exclusion: Soil improvement incentive requires a verified Soil Health Card issued by Agri Department.")

        # Land limit check (<= 5.0 acres)
        if 0 < profile.land_acres <= 5.0:
            audit.append(f"Passed: Land size of {profile.land_acres} acres is within small farmer soil grant limit (<= 5.0 acres).")
        else:
            disqualifications.append(f"Exclusion: Soil grant is restricted to holdings <= 5.0 acres (current: {profile.land_acres} acres).")

        # Deficiency check
        qualifying_defs = scheme["eligibility_rules"]["qualifying_deficiencies"]
        matched_defs = [d for d in profile.soil_deficiencies if any(qd.lower() in d.lower() or d.lower() in qd.lower() for qd in qualifying_defs)]

        if matched_defs:
            audit.append(f"Passed: Documented soil deficiency matched: {', '.join(matched_defs)}.")
        elif profile.has_soil_health_card:
            disqualifications.append("Exclusion: Soil parameters are within normal threshold; no registered organic carbon or mineral deficiency.")

        if not disqualifications:
            # Benefit calculation: Rs. 5,000 per hectare (1 hectare = ~2.47 acres), capped at 2 hectares (Rs. 10,000)
            hectares = profile.land_acres / 2.471
            grant_amount = min(hectares * 5000, 10000)
            status = "ELIGIBLE"
            summary_kn = f"ಅರ್ಹರು [ಡೆಮೊ]: ಮಣ್ಣು ಸುಧಾರಣೆಗೆ ಸುಮಾರು ₹{grant_amount:,.0f} ಪ್ರೋತ್ಸಾಹಧನ ಮತ್ತು ಜೈವಿಕ ಗೊಬ್ಬರ ಸಹಾಯಧನ ಲಭ್ಯವಿದೆ."
            summary_en = f"Eligible [Demo]: Qualifies for Rs. {grant_amount:,.0f} soil fertility incentive based on documented deficiency."
        else:
            status = "INELIGIBLE"
            summary_kn = "ಅನರ್ಹರು [ಡೆಮೊ]: ಮಣ್ಣು ಸುಧಾರಣೆ ಪ್ರೋತ್ಸಾಹಧನ ಯೋಜನೆಯ ಮಾನದಂಡಗಳು ಅನ್ವಯಿಸುವುದಿಲ್ಲ."
            summary_en = "Ineligible [Demo]: Soil improvement grant requirements not satisfied."

        return EvaluationResult(
            scheme_id=scheme["id"],
            scheme_name_kn=scheme["name_kn"],
            scheme_name_en=scheme["name_en"],
            is_demo=True,
            status=status,
            benefit_summary_kn=summary_kn,
            benefit_summary_en=summary_en,
            audit_trail=audit,
            disqualification_reasons=disqualifications,
            required_documents=scheme["required_documents"],
            disclaimer_kn=scheme["disclaimer_kn"]
        )
