"""
Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ) — Phase 1 Interactive Terminal CLI
Pure manual interactive mode: Enter or choose your agricultural details,
and get auditable scheme eligibility, benefits, reasons, and conditions.
"""

import sys
import os

# Ensure backend package can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from backend.rules_engine import SchemeEvaluator, FarmerProfile


def print_banner():
    print("\n" + "=" * 78)
    print("      🌾 KRISHI MITRA (ಕೃಷಿ ಮಿತ್ರ) — FARMER SCHEME ELIGIBILITY CLI 🌾")
    print("         Enter your agricultural details to find qualifying schemes")
    print("=" * 78 + "\n")


def prompt_choice(prompt_text, options, default_idx=1):
    """Utility to display numbered options and return user's choice."""
    print(f"\n{prompt_text}")
    for idx, opt in enumerate(options, 1):
        def_tag = " (Default)" if idx == default_idx else ""
        print(f"  [{idx}] {opt}{def_tag}")
    
    while True:
        try:
            raw = input(f"👉 Enter choice (1-{len(options)}) [default {default_idx}]: ").strip()
            if not raw:
                return options[default_idx - 1]
            choice_num = int(raw)
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
            print(f"⚠️  Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("⚠️  Invalid input. Please enter a valid number.")


def collect_farmer_input():
    print("📝 Please provide your agricultural details (Press Enter to keep default):\n")

    # 1. Farmer Name
    name = input("1. Farmer Name / ರೈತರ ಹೆಸರು [ರೈತ ಮಿತ್ರ]: ").strip() or "ರೈತ ಮಿತ್ರ"

    # 2. District
    district_options = [
        "Mandya (ಮಂಡ್ಯ)",
        "Kalaburagi (ಕಲಬುರಗಿ)",
        "Hassan (ಹಾಸನ)",
        "Belagavi (ಬೆಳಗಾವಿ)",
        "Kolar (ಕೋಲಾರ)",
        "Shivamogga (ಶಿವಮೊಗ್ಗ)",
        "Dharwad (ಧಾರವಾಡ)",
        "Tumakuru (ತುಮಕೂರು)",
        "Other District (ಇತರ ಜಿಲ್ಲೆ)"
    ]
    dist_choice = prompt_choice("2. Select Your District / ನಿಮ್ಮ ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:", district_options, 1)
    district = dist_choice.split(" ")[0]

    # 3. Land Size in Acres
    while True:
        land_str = input("\n3. Land Area in Acres / ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಎಕರೆಗಳಲ್ಲಿ) [e.g. 2.5]: ").strip() or "2.5"
        try:
            land_acres = float(land_str)
            if land_acres >= 0:
                break
            print("⚠️  Land area must be a positive number.")
        except ValueError:
            print("⚠️  Invalid number format. Example: 2.5 or 3")

    # 4. Land Ownership
    ownership_options = [
        "Owner (ಸ್ವಂತ ಭೂಮಿ - Pahani/RTC in own/family name)",
        "Tenant (ಗೇಣಿ ರೈತ / Tenant farmer)",
        "Joint Family (ಅವಿಭಕ್ತ ಕುಟುಂಬದ ಜಮೀನು)"
    ]
    owner_choice = prompt_choice("4. Land Ownership Type / ಭೂ ಮಾಲೀಕತ್ವ:", ownership_options, 1)
    ownership = "Owner" if "Owner" in owner_choice else ("Tenant" if "Tenant" in owner_choice else "Joint Family")

    # 5. Crop Selection
    crop_options = [
        "Ragi / ರಾಗಿ (Finger Millet)",
        "Pigeon Pea / ತೊಗರಿ (Togari / Red Gram)",
        "Paddy / ಭತ್ತ (Rice)",
        "Jowar / ಜೋಳ (Sorghum)",
        "Sugarcane / ಕಬ್ಬು",
        "Cotton / ಹತ್ತಿ",
        "Groundnut / ಶೇಂಗಾ (ಕಡಲೆಕಾಯಿ)",
        "Maize / ಮೆಕ್ಕೆಜೋಳ",
        "Vegetables / ತರಕಾರಿಗಳು",
        "Other Crop / ಇತರ ಬೆಳೆ"
    ]
    crop_choice = prompt_choice("5. Primary Crop Sown / ಬೆಳೆದಿರುವ ಮುಖ್ಯ ಬೆಳೆ:", crop_options, 1)
    
    # Map to canonical crop name
    if "Ragi" in crop_choice:
        crops = ["Ragi"]
    elif "Pigeon Pea" in crop_choice or "Togari" in crop_choice:
        crops = ["Pigeon Pea (Togari)"]
    elif "Paddy" in crop_choice:
        crops = ["Paddy"]
    elif "Jowar" in crop_choice:
        crops = ["Jowar"]
    elif "Sugarcane" in crop_choice:
        crops = ["Sugarcane"]
    elif "Cotton" in crop_choice:
        crops = ["Cotton"]
    elif "Groundnut" in crop_choice:
        crops = ["Groundnut"]
    elif "Maize" in crop_choice:
        crops = ["Maize"]
    else:
        crops = [crop_choice.split(" / ")[0]]

    # 6. Sowing Season
    season_options = [
        "Kharif / ಮುಂಗಾರು (June - Oct)",
        "Rabi / ಹಿಂಗಾರು (Oct - March)",
        "Summer / ಬೇಸಿಗೆ (Jan - May)"
    ]
    season_choice = prompt_choice("6. Sowing Season / ಬಿತ್ತನೆ ಋತು:", season_options, 1)
    season = "Kharif" if "Kharif" in season_choice else ("Rabi" if "Rabi" in season_choice else "Summer")

    # 7. Irrigation & Water Source
    irrig_options = [
        "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
        "Borewell / ಕೊಳವೆಬಾವಿ",
        "Canal / ಕಾಲುವೆ ನೀರಾವರಿ",
        "Open Well / ತೆರೆದ ಬಾವಿ",
        "Farm Pond / ಕೃಷಿ ಹೊಂಡ"
    ]
    irrig_choice = prompt_choice("7. Irrigation & Water Source / ನೀರಾವರಿ ಸೌಲಭ್ಯ:", irrig_options, 1)
    if "Rainfed" in irrig_choice:
        irrigation_type = "Rainfed"
        has_water = False
    else:
        irrigation_type = irrig_choice.split(" / ")[0]
        has_water = True

    # 8. Have you faced any crop loss or natural calamity this season?
    risk_options = [
        "None (No damage / ಯಾವುದೇ ಹಾನಿಯಾಗಿಲ್ಲ)",
        "Drought / ಬರಗಾಲ (Lack of rain / crop drying)",
        "Excess Rainfall or Flood / ಅತಿವೃಷ್ಟಿ ಅಥವಾ ಪ್ರವಾಹ",
        "Pest or Disease Attack / ಕೀಟಬಾಧೆ ಅಥವಾ ರೋಗ"
    ]
    risk_choice = prompt_choice("8. Crop Loss / Natural Calamity / ಬೆಳೆ ಹಾನಿ:", risk_options, 1)
    risk_type = None if "None" in risk_choice else risk_choice.split(" / ")[0]

    # 9. Assistance Needs (Subsidy intent)
    need_options = [
        "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು",
        "Drip / Sprinkler Irrigation Subsidy (ಹನಿ ಅಥವಾ ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ)",
        "Farm Equipment / Machinery Subsidy (ಟ್ರ್ಯಾಕ್ಟರ್, ಟಿಲ್ಲರ್, ರೋಟವೇಟರ್ ಯಂತ್ರೋಪಕರಣ)",
        "Soil Fertility & Fertilizer Grant (ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಫಲವತ್ತತೆ ಪ್ರೋತ್ಸಾಹಧನ)"
    ]
    need_choice = prompt_choice("9. Specific Assistance Needed / ನಿಮಗೆ ಬೇಕಾಗಿರುವ ಮುಖ್ಯ ನೆರವು:", need_options, 1)
    
    requested_equipment = None
    if "Equipment" in need_choice:
        equip_options = [
            "Power Tiller (ಪವರ್ ಟಿಲ್ಲರ್)",
            "Rotavator (ರೋಟವೇಟರ್)",
            "Small Tractor (ಸಣ್ಣ ಟ್ರ್ಯಾಕ್ಟರ್)",
            "Power Sprayer (ಪವರ್ ಸ್ಪ್ರೇಯರ್)",
            "Weeder (ಕಳೆ ಕೀಳುವ ಯಂತ್ರ)"
        ]
        equip_choice = prompt_choice("   Select Equipment Needed / ಬೇಕಾಗಿರುವ ಉಪಕರಣ:", equip_options, 1)
        requested_equipment = equip_choice.split(" ")[0]

    has_shc = False
    soil_defs = []
    if "Soil" in need_choice:
        shc_prompt = prompt_choice("   Do you have an official Soil Health Card (SHC)? / ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಇದೆಯೇ?:", ["Yes (ಹೌದು)", "No (ಇಲ್ಲ)"], 1)
        if "Yes" in shc_prompt:
            has_shc = True
            def_options = [
                "Acidic / ಆಮ್ಲೀಯ ಮಣ್ಣು (Low pH)",
                "Alkaline or Saline / ಕ್ಷಾರೀಯ ಮಣ್ಣು",
                "Low Organic Carbon / ಸಾವಯವ ಇಂಗಾಲದ ಕೊರತೆ",
                "Normal / ಸಾಧಾರಣ ಮಣ್ಣು"
            ]
            def_choice = prompt_choice("   Detected Soil Condition / ಮಣ್ಣಿನ ಸ್ಥಿತಿ:", def_options, 1)
            soil_defs = [def_choice.split(" / ")[0]] if "Normal" not in def_choice else []

    # 10. Prior Drip Subsidy check (if asking for drip)
    availed_drip = False
    if "Drip" in need_choice:
        drip_prior = prompt_choice("   Have you availed micro-irrigation subsidy in the past 3 years? / ಕಳೆದ 3 ವರ್ಷದಲ್ಲಿ ಹನಿ ನೀರಾವರಿ ಸಬ್ಸಿಡಿ ಪಡೆದಿದ್ದೀರಾ?:", ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"], 1)
        availed_drip = "Yes" in drip_prior

    # 11. Exclusion checks
    print("\n10. Statutory Exclusion Verification / ಸರ್ಕಾರದ ಶಾಸನಬದ್ಧ ಪರಿಶೀಲನೆ:")
    tax_choice = prompt_choice("   Are you or your spouse an Income Tax Payee? / ನೀವು ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿದಾರರೇ?:", ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"], 1)
    is_tax_payee = "Yes" in tax_choice

    gov_choice = prompt_choice("   Are you a regular Government Employee or Constitutional Post Holder?:", ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"], 1)
    is_gov_employee = "Yes" in gov_choice

    # Construct FarmerProfile
    profile = FarmerProfile(
        farmer_name=name,
        district=district,
        land_acres=land_acres,
        ownership=ownership,
        crops=crops,
        season=season,
        risk_type=risk_type,
        irrigation_type=irrigation_type,
        has_water_source=has_water,
        availed_drip_subsidy_last_3_years=availed_drip,
        requested_equipment=requested_equipment,
        has_soil_health_card=has_shc,
        soil_deficiencies=soil_defs,
        is_income_tax_payee=is_tax_payee,
        is_government_employee=is_gov_employee
    )

    return profile


def display_comprehensive_evaluation(profile: FarmerProfile, evaluator: SchemeEvaluator):
    print("\n" + "=" * 78)
    print("📊 YOUR INPUT PROFILE SUMMARY / ನಿಮ್ಮ ವಿವರಗಳು:")
    print("=" * 78)
    print(f"  • Farmer Name / ಹೆಸರು:         {profile.farmer_name}")
    print(f"  • District / ಜಿಲ್ಲೆ:             {profile.district}")
    print(f"  • Landholding / ವಿಸ್ತೀರ್ಣ:        {profile.land_acres} Acres ({profile.ownership})")
    print(f"  • Primary Crop / ಬೆಳೆ:          {', '.join(profile.crops)}")
    print(f"  • Season / ಬಿತ್ತನೆ ಋತು:          {profile.season}")
    print(f"  • Water Source / ನೀರಾವರಿ:       {profile.irrigation_type} ({'Water Available' if profile.has_water_source else 'No Water Source'})")
    if profile.risk_type:
        print(f"  • Reported Damage / ಹಾನಿ:       {profile.risk_type}")
    if profile.requested_equipment:
        print(f"  • Requested Implement:          {profile.requested_equipment}")
    if profile.has_soil_health_card:
        print(f"  • Soil Health Status:           Deficiencies: {', '.join(profile.soil_deficiencies) if profile.soil_deficiencies else 'None'}")
    print(f"  • Income Tax Payee / ತೆರಿಗೆ:    {'YES' if profile.is_income_tax_payee else 'NO'}")
    print("=" * 78)

    print("\n⏳ EVALUATING YOUR ELIGIBILITY AGAINST GOVERNMENT CRITERIA...\n")
    results = evaluator.evaluate_all(profile)

    eligible_schemes = [r for r in results if r.status == "ELIGIBLE"]
    ineligible_schemes = [r for r in results if r.status != "ELIGIBLE"]

    # 1. ELIGIBLE SCHEMES SECTION
    print("*" * 78)
    print(f" 🎉 QUALIFYING SCHEMES ({len(eligible_schemes)} SCHEMES FOUND)")
    print("*" * 78)

    if not eligible_schemes:
        print("  None of the 5 reference schemes matched your specific input profile.")
    else:
        for idx, r in enumerate(eligible_schemes, 1):
            demo_badge = " [DEMO TEST CASE]" if r.is_demo else " [OFFICIAL GOVERNMENT SCHEME]"
            print(f"\n{idx}. {r.scheme_name_kn} ({r.scheme_name_en}){demo_badge}")
            print(f"   🟢 Status: {r.status} (ಅರ್ಹರು)")
            print(f"   💰 Financial Benefit (Kannada): {r.benefit_summary_kn}")
            print(f"   💰 Financial Benefit (English): {r.benefit_summary_en}")
            
            if r.disclaimer_kn:
                print(f"   ⚠️  ಪ್ರಮುಖ ಸೂಚನೆ: {r.disclaimer_kn}")

            print("   🔍 Why You Are Eligible (Auditable Reasons):")
            for a in r.audit_trail:
                print(f"      ✔ {a}")

            print("   📄 Required Documents & Application Steps:")
            for doc in r.required_documents:
                mandatory_str = "[Mandatory / ಕಡ್ಡಾಯ]" if doc.get("mandatory") else "[Optional / ಐಚ್ಛಿಕ]"
                print(f"      • {doc['name_kn']} ({doc['name_en']}) {mandatory_str}")
                print(f"        -> Where to get / ಎಲ್ಲಿಂದ ಪಡೆಯಬೇಕು: {doc.get('source_kn', 'ಸಂಬಂಧಪಟ್ಟ ಇಲಾಖೆ')}")
            print("-" * 78)

    # 2. INELIGIBLE SCHEMES WITH EXACT EXCLUSION REASONS
    if ineligible_schemes:
        print("\n" + "-" * 78)
        print(f" ❌ INELIGIBLE SCHEMES & CONDITIONS FAILED ({len(ineligible_schemes)} SCHEMES)")
        print("-" * 78)
        for idx, r in enumerate(ineligible_schemes, 1):
            demo_badge = " [DEMO]" if r.is_demo else " [REAL]"
            print(f"\n• {r.scheme_name_kn} ({r.scheme_name_en}){demo_badge}")
            print(f"  🔴 Status: {r.status} (ಅನರ್ಹರು)")
            print(f"  Reason / ಷರತ್ತು ಉಲ್ಲಂಘನೆ:")
            for d in r.disqualification_reasons:
                print(f"     ✖ {d}")
            print("  Conditions that passed:")
            for a in r.audit_trail:
                print(f"     ✔ {a}")

    print("\n" + "=" * 78)
    print("📌 WHAT TO DO NEXT / ಮುಂದಿನ ಕ್ರಮಗಳು:")
    print("  1. Carry the mandatory documents listed above to your local 'Grama One' (ಗ್ರಾಮ ಒನ್) center.")
    print("  2. Ensure your Aadhaar is linked with your Bank Passbook (NPCI seeding) for Direct Benefit Transfer.")
    print("  3. For insurance claims (PMFBY), notify within 72 hours of crop loss.")
    print("=" * 78 + "\n")


def main():
    print_banner()
    evaluator = SchemeEvaluator()

    while True:
        profile = collect_farmer_input()
        display_comprehensive_evaluation(profile, evaluator)

        try:
            again = input("🔄 Do you want to test with another farmer profile? (y/n) [y]: ").strip().lower()
            if again in ['n', 'no', 'exit', 'quit', 'q']:
                print("\nಧನ್ಯವಾದಗಳು! (Exiting Krishi Mitra CLI)\n")
                break
        except (EOFError, KeyboardInterrupt):
            print("\nಧನ್ಯವಾದಗಳು! (Exiting Krishi Mitra CLI)\n")
            break


if __name__ == "__main__":
    main()
