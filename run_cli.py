"""
Krishi Mitra (ಕೃಷಿ ಮಿತ್ರ) — Phase 1 Interactive Terminal CLI
Context-Aware Agriculture Engine: Uses Karnataka agro-climatic zones,
soil characteristics, and crop calendars to dynamically recommend
and preset the most likely default answers based on your previous answers.
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

# -------------------------------------------------------------------------
# KARNATAKA AGRO-CLIMATIC DOMAIN INTELLIGENCE REPOSITORY
# -------------------------------------------------------------------------
DISTRICT_AGRO_DATA = {
    "Mandya": {
        "zone": "Southern Dry Zone (Cauvery Basin)",
        "top_crops": ["Sugarcane / ಕಬ್ಬು", "Paddy / ಭತ್ತ (Rice)", "Ragi / ರಾಗಿ (Finger Millet)"],
        "default_crop": "Sugarcane / ಕಬ್ಬು",
        "default_irrigation": "Canal / ಕಾಲುವೆ ನೀರಾವರಿ",
        "has_water": True,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "None (No damage / ಯಾವುದೇ ಹಾನಿಯಾಗಿಲ್ಲ)",
        "default_need": "Drip / Sprinkler Irrigation Subsidy (ಹನಿ ಅಥವಾ ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ)"
    },
    "Kalaburagi": {
        "zone": "North Eastern Dry Zone (Pulse Bowl)",
        "top_crops": ["Pigeon Pea / ತೊಗರಿ (Togari / Red Gram)", "Jowar / ಜೋಳ (Sorghum)", "Cotton / ಹತ್ತಿ"],
        "default_crop": "Pigeon Pea / ತೊಗರಿ (Togari / Red Gram)",
        "default_irrigation": "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
        "has_water": False,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "Drought / ಬರಗಾಲ (Lack of rain / crop drying)",
        "default_need": "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು"
    },
    "Dharwad": {
        "zone": "Northern Transition Zone",
        "top_crops": ["Soybean / ಸೋಯಾಬೀನ್", "Cotton / ಹತ್ತಿ", "Jowar / ಜೋಳ (Sorghum)", "Maize / ಮೆಕ್ಕೆಜೋಳ"],
        "default_crop": "Cotton / ಹತ್ತಿ",
        "default_irrigation": "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
        "has_water": False,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "Pest or Disease Attack / ಕೀಟಬಾಧೆ ಅಥವಾ ರೋಗ",
        "default_need": "Farm Equipment / Machinery Subsidy (ಟ್ರ್ಯಾಕ್ಟರ್, ಟಿಲ್ಲರ್, ರೋಟವೇಟರ್ ಯಂತ್ರೋಪಕರಣ)"
    },
    "Belagavi": {
        "zone": "Northern Transition Zone (Sugar Belt)",
        "top_crops": ["Sugarcane / ಕಬ್ಬು", "Soybean / ಸೋಯಾಬೀನ್", "Maize / ಮೆಕ್ಕೆಜೋಳ", "Jowar / ಜೋಳ"],
        "default_crop": "Sugarcane / ಕಬ್ಬು",
        "default_irrigation": "Canal / ಕಾಲುವೆ ನೀರಾವರಿ",
        "has_water": True,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "None (No damage / ಯಾವುದೇ ಹಾನಿಯಾಗಿಲ್ಲ)",
        "default_need": "Farm Equipment / Machinery Subsidy (ಟ್ರ್ಯಾಕ್ಟರ್, ಟಿಲ್ಲರ್, ರೋಟವೇಟರ್ ಯಂತ್ರೋಪಕರಣ)"
    },
    "Kolar": {
        "zone": "Eastern Dry Zone (Vegetable & Borewell Hub)",
        "top_crops": ["Vegetables / ತರಕಾರಿಗಳು (Tomato / ಟೊಮ್ಯಾಟೋ)", "Ragi / ರಾಗಿ (Finger Millet)", "Mulberry / ರೇಷ್ಮೆ"],
        "default_crop": "Vegetables / ತರಕಾರಿಗಳು (Tomato / ಟೊಮ್ಯಾಟೋ)",
        "default_irrigation": "Borewell / ಕೊಳವೆಬಾವಿ",
        "has_water": True,
        "default_season": "Rabi / ಹಿಂಗಾರು (Oct - March)",
        "default_calamity": "Drought / ಬರಗಾಲ (Lack of rain / crop drying)",
        "default_need": "Drip / Sprinkler Irrigation Subsidy (ಹನಿ ಅಥವಾ ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ)"
    },
    "Hassan": {
        "zone": "Southern Transition Zone (Malnad Gateway)",
        "top_crops": ["Potato / ಆಲೂಗಡ್ಡೆ", "Ragi / ರಾಗಿ (Finger Millet)", "Paddy / ಭತ್ತ (Rice)", "Maize / ಮೆಕ್ಕೆಜೋಳ"],
        "default_crop": "Potato / ಆಲೂಗಡ್ಡೆ",
        "default_irrigation": "Borewell / ಕೊಳವೆಬಾವಿ",
        "has_water": True,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "Pest or Disease Attack / ಕೀಟಬಾಧೆ ಅಥವಾ ರೋಗ",
        "default_need": "Soil Fertility & Fertilizer Grant (ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಫಲವತ್ತತೆ ಪ್ರೋತ್ಸಾಹಧನ)"
    },
    "Shivamogga": {
        "zone": "Hilly / Malnad Zone",
        "top_crops": ["Paddy / ಭತ್ತ (Rice)", "Arecanut / ಅಡಿಕೆ", "Maize / ಮೆಕ್ಕೆಜೋಳ", "Ginger / ಶುಂಠಿ"],
        "default_crop": "Paddy / ಭತ್ತ (Rice)",
        "default_irrigation": "Canal / ಕಾಲುವೆ ನೀರಾವರಿ",
        "has_water": True,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "Excess Rainfall or Flood / ಅತಿವೃಷ್ಟಿ ಅಥವಾ ಪ್ರವಾಹ",
        "default_need": "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು"
    },
    "Tumakuru": {
        "zone": "Central Dry Zone",
        "top_crops": ["Ragi / ರಾಗಿ (Finger Millet)", "Groundnut / ಶೇಂಗಾ (ಕಡಲೆಕಾಯಿ)", "Coconut / ತೆಂಗು"],
        "default_crop": "Ragi / ರಾಗಿ (Finger Millet)",
        "default_irrigation": "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
        "has_water": False,
        "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
        "default_calamity": "Drought / ಬರಗಾಲ (Lack of rain / crop drying)",
        "default_need": "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು"
    }
}

DEFAULT_FALLBACK = {
    "zone": "Karnataka General Zone",
    "top_crops": ["Ragi / ರಾಗಿ (Finger Millet)", "Pigeon Pea / ತೊಗರಿ (Togari / Red Gram)", "Paddy / ಭತ್ತ (Rice)"],
    "default_crop": "Ragi / ರಾಗಿ (Finger Millet)",
    "default_irrigation": "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
    "has_water": False,
    "default_season": "Kharif / ಮುಂಗಾರು (June - Oct)",
    "default_calamity": "None (No damage / ಯಾವುದೇ ಹಾನಿಯಾಗಿಲ್ಲ)",
    "default_need": "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು"
}


def print_banner():
    print("\n" + "=" * 78)
    print("      🌾 KRISHI MITRA (ಕೃಷಿ ಮಿತ್ರ) — INTELLIGENT AGRI-SCHEME CLI 🌾")
    print("       Context-Aware Agricultural Intelligence for Karnataka Farmers")
    print("=" * 78 + "\n")


def prompt_smart_choice(prompt_text, options, recommended_option=None, contextual_reason=None):
    """
    Renders options with a clear (Recommended) tag next to the dynamically determined default,
    explaining WHY based on the previous answers.
    """
    print(f"\n{prompt_text}")
    if contextual_reason:
        print(f"  💡 Context Hint: {contextual_reason}")

    # Determine default index (1-based)
    default_idx = 1
    if recommended_option:
        for i, opt in enumerate(options, 1):
            if opt.lower().startswith(recommended_option.lower().split(" ")[0]) or recommended_option.lower() in opt.lower():
                default_idx = i
                break

    for idx, opt in enumerate(options, 1):
        rec_tag = "  <-- [RECOMMENDED DEFAULT]" if idx == default_idx else ""
        print(f"  [{idx}] {opt}{rec_tag}")

    while True:
        try:
            raw = input(f"\n👉 Enter choice (1-{len(options)}) [Press Enter for {default_idx}]: ").strip()
            if not raw:
                return options[default_idx - 1]
            choice_num = int(raw)
            if 1 <= choice_num <= len(options):
                return options[choice_num - 1]
            print(f"⚠️  Please enter a number between 1 and {len(options)}.")
        except ValueError:
            print("⚠️  Invalid input. Please enter a valid number.")


def collect_farmer_input():
    print("📝 Please provide your agricultural details.\nEach question suggests smart defaults based on your earlier answers:\n")

    # 1. Farmer Name
    name = input("1. Farmer Name / ರೈತರ ಹೆಸರು [ರೈತ ಮಿತ್ರ]: ").strip() or "ರೈತ ಮಿತ್ರ"

    # 2. District Selection
    district_options = [
        "Mandya (ಮಂಡ್ಯ) - Southern Dry Zone (Cauvery Basin)",
        "Kalaburagi (ಕಲಬುರಗಿ) - North Eastern Dry Zone (Pulse Bowl)",
        "Dharwad (ಧಾರವಾಡ) - Northern Transition Zone",
        "Belagavi (ಬೆಳಗಾವಿ) - Sugar & Transition Zone",
        "Kolar (ಕೋಲಾರ) - Eastern Dry Zone (Vegetable & Borewell Hub)",
        "Hassan (ಹಾಸನ) - Southern Transition Zone (Potato & Malnad Gateway)",
        "Shivamogga (ಶಿವಮೊಗ್ಗ) - Malnad & Canal Zone",
        "Tumakuru (ತುಮಕೂರು) - Central Dry Zone (Ragi & Coconut Belt)",
        "Other District (ಇತರ ಜಿಲ್ಲೆ)"
    ]
    dist_choice = prompt_smart_choice(
        "2. Select Your District / ನಿಮ್ಮ ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ:",
        district_options,
        recommended_option="Mandya",
        contextual_reason="Karnataka's 10 Agro-Climatic Zones determine rainfall and soil type."
    )
    dist_clean = dist_choice.split(" ")[0]
    agro_intel = DISTRICT_AGRO_DATA.get(dist_clean, DEFAULT_FALLBACK)

    print(f"\n  🌱 Zone Identified: {agro_intel['zone']}")

    # 3. Land Size in Acres (Contextual default: 2.5 acres for small-holder state avg)
    default_land = "2.5" if dist_clean in ["Mandya", "Kolar", "Hassan"] else "5.0"
    while True:
        land_str = input(f"\n3. Land Area in Acres / ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ (ಎಕರೆಗಳಲ್ಲಿ) [Recommended: {default_land}]: ").strip() or default_land
        try:
            land_acres = float(land_str)
            if land_acres >= 0:
                break
            print("⚠️  Land area must be a positive number.")
        except ValueError:
            print("⚠️  Invalid number format. Example: 2.5 or 5.0")

    # 4. Land Ownership
    ownership_options = [
        "Owner (ಸ್ವಂತ ಭೂಮಿ - Pahani/RTC in own/family name)",
        "Tenant (ಗೇಣಿ ರೈತ / Tenant farmer)",
        "Joint Family (ಅವಿಭಕ್ತ ಕುಟುಂಬದ ಜಮೀನು)"
    ]
    owner_choice = prompt_smart_choice(
        "4. Land Ownership Type / ಭೂ ಮಾಲೀಕತ್ವ:",
        ownership_options,
        recommended_option="Owner",
        contextual_reason="Most Karnataka government DBT subsidies require recorded ownership."
    )
    ownership = "Owner" if "Owner" in owner_choice else ("Tenant" if "Tenant" in owner_choice else "Joint Family")

    # 5. Crop Selection (Cascading: Filtered & Recommended by District)
    all_crops = [
        "Sugarcane / ಕಬ್ಬು",
        "Pigeon Pea / ತೊಗರಿ (Togari / Red Gram)",
        "Ragi / ರಾಗಿ (Finger Millet)",
        "Paddy / ಭತ್ತ (Rice)",
        "Jowar / ಜೋಳ (Sorghum)",
        "Cotton / ಹತ್ತಿ",
        "Vegetables / ತರಕಾರಿಗಳು (Tomato / ಟೊಮ್ಯಾಟೋ)",
        "Potato / ಆಲೂಗಡ್ಡೆ",
        "Groundnut / ಶೇಂಗಾ (ಕಡಲೆಕಾಯಿ)",
        "Maize / ಮೆಕ್ಕೆಜೋಳ",
        "Arecanut / ಅಡಿಕೆ",
        "Other Crop / ಇತರ ಬೆಳೆ"
    ]
    
    # Put district's top crops at the very top of the list
    sorted_crops = []
    for top_c in agro_intel["top_crops"]:
        for c in all_crops:
            if c.split(" / ")[0].lower() in top_c.lower() and c not in sorted_crops:
                sorted_crops.append(c)
    for c in all_crops:
        if c not in sorted_crops:
            sorted_crops.append(c)

    crop_choice = prompt_smart_choice(
        f"5. Primary Crop Sown in {dist_clean} / ಮುಖ್ಯ ಬೆಳೆ:",
        sorted_crops,
        recommended_option=agro_intel["default_crop"],
        contextual_reason=f"In {dist_clean} ({agro_intel['zone']}), '{agro_intel['default_crop']}' is traditionally predominant."
    )
    
    # Canonical crop mapping
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

    # 6. Sowing Season (Cascading: Crop-dependent)
    season_options = [
        "Kharif / ಮುಂಗಾರು (June - Oct)",
        "Rabi / ಹಿಂಗಾರು (Oct - March)",
        "Summer / ಬೇಸಿಗೆ (Jan - May)"
    ]
    
    # Jowar in North Karnataka is predominantly Rabi; Pigeon Pea / Ragi / Cotton is Kharif
    if "Jowar" in crops[0] and dist_clean in ["Kalaburagi", "Dharwad", "Belagavi"]:
        rec_season = "Rabi / ಹಿಂಗಾರು (Oct - March)"
        season_reason = "Northern Karnataka White Jowar (ಬಿಳಿ ಜೋಳ) is primarily a Rabi crop."
    elif "Vegetables" in crop_choice and dist_clean == "Kolar":
        rec_season = "Rabi / ಹಿಂಗಾರು (Oct - March)"
        season_reason = "Kolar vegetable growers sow post-monsoon for winter yield."
    else:
        rec_season = "Kharif / ಮುಂಗಾರು (June - Oct)"
        season_reason = f"Kharif is the primary monsoon season for {crops[0]} across Karnataka."

    season_choice = prompt_smart_choice(
        "6. Sowing Season / ಬಿತ್ತನೆ ಋತು:",
        season_options,
        recommended_option=rec_season,
        contextual_reason=season_reason
    )
    season = "Kharif" if "Kharif" in season_choice else ("Rabi" if "Rabi" in season_choice else "Summer")

    # 7. Irrigation & Water Source (Cascading: Crop + District)
    irrig_options = [
        "Rainfed / ಒಣಭೂಮಿ - ಕುಷ್ಕಿ (Dependent only on monsoon rain)",
        "Borewell / ಕೊಳವೆಬಾವಿ",
        "Canal / ಕಾಲುವೆ ನೀರಾವರಿ",
        "Open Well / ತೆರೆದ ಬಾವಿ",
        "Farm Pond / ಕೃಷಿ ಹೊಂಡ"
    ]

    # Sugarcane and Paddy strictly require heavy irrigation
    if crops[0] in ["Sugarcane", "Paddy"]:
        rec_irrig = agro_intel["default_irrigation"] if agro_intel["has_water"] else "Canal / ಕಾಲುವೆ ನೀರಾವರಿ"
        irrig_reason = f"{crops[0]} is a water-intensive crop, traditionally requiring Canal or Borewell supply."
    else:
        rec_irrig = agro_intel["default_irrigation"]
        irrig_reason = f"Based on {dist_clean}'s hydrology, '{agro_intel['default_irrigation'].split(' / ')[0]}' is the common source."

    irrig_choice = prompt_smart_choice(
        f"7. Irrigation Facility for {crops[0]} / ನೀರಾವರಿ ಸೌಲಭ್ಯ:",
        irrig_options,
        recommended_option=rec_irrig,
        contextual_reason=irrig_reason
    )
    if "Rainfed" in irrig_choice:
        irrigation_type = "Rainfed"
        has_water = False
    else:
        irrigation_type = irrig_choice.split(" / ")[0]
        has_water = True

    # 8. Natural Calamity / Damage (Cascading: Agro-Climatic Peril History)
    risk_options = [
        "None (No damage / ಯಾವುದೇ ಹಾನಿಯಾಗಿಲ್ಲ)",
        "Drought / ಬರಗಾಲ (Lack of rain / crop drying)",
        "Excess Rainfall or Flood / ಅತಿವೃಷ್ಟಿ ಅಥವಾ ಪ್ರವಾಹ",
        "Pest or Disease Attack / ಕೀಟಬಾಧೆ ಅಥವಾ ರೋಗ"
    ]
    calamity_reason = f"Historical climate hazard in {dist_clean} ({agro_intel['zone']})."
    risk_choice = prompt_smart_choice(
        f"8. Have you faced any crop loss in {dist_clean}? / ಬೆಳೆ ಹಾನಿ:",
        risk_options,
        recommended_option=agro_intel["default_calamity"],
        contextual_reason=calamity_reason
    )
    risk_type = None if "None" in risk_choice else risk_choice.split(" / ")[0]

    # 9. Assistance Needs (Cascading: Based on Irrigation & Land)
    need_options = [
        "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು (PM-KISAN)",
        "Drip / Sprinkler Irrigation Subsidy (ಹನಿ ಅಥವಾ ತುಂತುರು ನೀರಾವರಿ ಸಬ್ಸಿಡಿ)",
        "Farm Equipment / Machinery Subsidy (ಟ್ರ್ಯಾಕ್ಟರ್, ಟಿಲ್ಲರ್, ರೋಟವೇಟರ್ ಯಂತ್ರೋಪಕರಣ)",
        "Soil Fertility & Fertilizer Grant (ಮಣ್ಣು ಸುಧಾರಣೆ ಮತ್ತು ಫಲವತ್ತತೆ ಪ್ರೋತ್ಸಾಹಧನ)"
    ]

    # If farmer has borewell or large land, drip/machinery is natural; if rainfed, general or soil
    if has_water:
        rec_need = agro_intel["default_need"]
        need_reason = f"With active {irrigation_type}, government micro-irrigation or farm implements yield highest ROI."
    else:
        rec_need = "General Scheme Discovery / ಸಾಮಾನ್ಯ ಯೋಜನೆಗಳು ಮತ್ತು ಆದಾಯ ನೆರವು (PM-KISAN)"
        need_reason = "For rainfed holdings, direct income assistance and crop insurance are prime entitlements."

    need_choice = prompt_smart_choice(
        "9. Specific Assistance Needed / ನಿಮಗೆ ಬೇಕಾಗಿರುವ ಮುಖ್ಯ ನೆರವು:",
        need_options,
        recommended_option=rec_need,
        contextual_reason=need_reason
    )

    requested_equipment = None
    if "Equipment" in need_choice:
        equip_options = [
            "Power Tiller (ಪವರ್ ಟಿಲ್ಲರ್)",
            "Rotavator (ರೋಟವೇಟರ್)",
            "Small Tractor (ಸಣ್ಣ ಟ್ರ್ಯಾಕ್ಟರ್)",
            "Power Sprayer (ಪವರ್ ಸ್ಪ್ರೇಯರ್)",
            "Weeder (ಕಳೆ ಕೀಳುವ ಯಂತ್ರ)"
        ]
        rec_equip = "Power Tiller" if land_acres <= 5.0 else "Small Tractor"
        equip_reason = f"For {land_acres} acres, '{rec_equip}' qualifies for the highest 50% subsidy."
        equip_choice = prompt_smart_choice(
            "   Select Equipment / ಬೇಕಾಗಿರುವ ಯಂತ್ರೋಪಕರಣ:",
            equip_options,
            recommended_option=rec_equip,
            contextual_reason=equip_reason
        )
        requested_equipment = equip_choice.split(" ")[0]

    has_shc = False
    soil_defs = []
    if "Soil" in need_choice:
        shc_prompt = prompt_smart_choice(
            "   Do you possess an official Soil Health Card (SHC)? / ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಇದೆಯೇ?:",
            ["Yes (ಹೌದು)", "No (ಇಲ್ಲ)"],
            recommended_option="Yes (ಹೌದು)",
            contextual_reason="Soil Health Cards are mandatory to verify nutrient deficiency for state grants."
        )
        if "Yes" in shc_prompt:
            has_shc = True
            def_options = [
                "Acidic / ಆಮ್ಲೀಯ ಮಣ್ಣು (Common in Malnad / Coastal)",
                "Alkaline or Saline / ಕ್ಷಾರೀಯ ಮಣ್ಣು (Common in North Karnataka Black Soil)",
                "Low Organic Carbon / ಸಾವಯವ ಇಂಗಾಲದ ಕೊರತೆ",
                "Normal / ಸಾಧಾರಣ ಮಣ್ಣು"
            ]
            rec_def = "Alkaline" if dist_clean in ["Kalaburagi", "Belagavi", "Dharwad"] else ("Acidic" if dist_clean in ["Hassan", "Shivamogga"] else "Low Organic Carbon")
            def_choice = prompt_smart_choice(
                "   Detected Soil Condition in your Card / ಮಣ್ಣಿನ ಸ್ಥಿತಿ:",
                def_options,
                recommended_option=rec_def,
                contextual_reason=f"Typical soil profile in {dist_clean}."
            )
            soil_defs = [def_choice.split(" / ")[0]] if "Normal" not in def_choice else []

    availed_drip = False
    if "Drip" in need_choice:
        drip_prior = prompt_smart_choice(
            "   Have you availed micro-irrigation subsidy in the past 3 years? / ಕಳೆದ 3 ವರ್ಷದಲ್ಲಿ ಸಬ್ಸಿಡಿ ಪಡೆದಿದ್ದೀರಾ?:",
            ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"],
            recommended_option="No (ಇಲ್ಲ)",
            contextual_reason="State rules impose a 3-year cooldown between micro-irrigation grants."
        )
        availed_drip = "Yes" in drip_prior

    # 10. Statutory Exclusion Checks
    print("\n10. Statutory Exclusion Verification / ಸರ್ಕಾರದ ಶಾಸನಬದ್ಧ ಪರಿಶೀಲನೆ:")
    tax_choice = prompt_smart_choice(
        "   Are you or your spouse an Income Tax Payee? / ನೀವು ಆದಾಯ ತೆರಿಗೆ ಪಾವತಿದಾರರೇ?:",
        ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"],
        recommended_option="No (ಇಲ್ಲ)",
        contextual_reason="Income tax payees are statutorily excluded from PM-KISAN."
    )
    is_tax_payee = "Yes" in tax_choice

    gov_choice = prompt_smart_choice(
        "   Are you a regular Government Employee or Constitutional Post Holder?:",
        ["No (ಇಲ್ಲ)", "Yes (ಹೌದು)"],
        recommended_option="No (ಇಲ್ಲ)",
        contextual_reason="Public servants are excluded from direct cash transfers."
    )
    is_gov_employee = "Yes" in gov_choice

    # Construct Profile
    profile = FarmerProfile(
        farmer_name=name,
        district=dist_clean,
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
    print(f"  • Sowing Season / ಬಿತ್ತನೆ ಋತು:    {profile.season}")
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
