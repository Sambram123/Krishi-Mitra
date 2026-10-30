"""
Krishi Mitra — Dialect and Land Unit Normalization
Pure Python deterministic normalizer for rural Kannada crop names, land units, and agricultural jargon.
Zero LLM dependencies — all mathematical conversions and canonical dictionaries are explicit.
"""

from typing import List, Optional, Dict, Any, Set
from backend.nlu.schemas import LandSize, ExtractOut

# Exact canonical crop names aligned with backend/rules_engine.py and data/schemes_dataset.json
CROP_CANONICAL_MAP: Dict[str, str] = {
    # Pigeon Pea / Red Gram / Togari
    "togari": "Pigeon Pea (Togari)",
    "ತೊಗರಿ": "Pigeon Pea (Togari)",
    "togari bele": "Pigeon Pea (Togari)",
    "ತೊಗರಿ ಬೇಳೆ": "Pigeon Pea (Togari)",
    "pigeon pea": "Pigeon Pea (Togari)",
    "red gram": "Pigeon Pea (Togari)",
    "tur": "Pigeon Pea (Togari)",

    # Jowar / Sorghum / Jola
    "jola": "Jowar",
    "ಜೋಳ": "Jowar",
    "jowar": "Jowar",
    "sorghum": "Jowar",

    # Ragi / Finger Millet
    "ragi": "Ragi",
    "ರಾಗಿ": "Ragi",
    "finger millet": "Ragi",

    # Sugarcane / Kabbu
    "kabbu": "Sugarcane",
    "ಕಬ್ಬು": "Sugarcane",
    "sugarcane": "Sugarcane",

    # Paddy / Rice / Bhattha
    "paddy": "Paddy",
    "rice": "Paddy",
    "bhattha": "Paddy",
    "ಭತ್ತ": "Paddy",

    # Cotton / Hatti
    "cotton": "Cotton",
    "hatti": "Cotton",
    "ಹತ್ತಿ": "Cotton",

    # Groundnut / Kadalekayi
    "groundnut": "Groundnut",
    "kadalekayi": "Groundnut",
    "ಕಡಲೆಕಾಯಿ": "Groundnut",
    "peanut": "Groundnut",

    # Maize / Mekke Jola
    "maize": "Maize",
    "mekke jola": "Maize",
    "ಮೆಕ್ಕೆ ಜೋಳ": "Maize",
    "corn": "Maize",
}

# District name bilingual synonym map for evidence verification
DISTRICT_SYNONYMS: Dict[str, Set[str]] = {
    "kalaburagi": {"kalaburagi", "gulbarga", "ಕಲಬುರಗಿ", "ಗುಲ್ಬರ್ಗ"},
    "belagavi": {"belagavi", "belgaum", "ಬೆಳಗಾವಿ"},
    "dharwad": {"dharwad", "ಧಾರವಾಡ"},
    "mandya": {"mandya", "ಮಂಡ್ಯ"},
    "mysuru": {"mysuru", "mysore", "ಮೈಸೂರು"},
    "tumakuru": {"tumakuru", "tumkur", "ತುಮಕೂರು"},
    "hassan": {"hassan", "ಹಾಸನ"},
    "ballari": {"ballari", "bellary", "ಬಳ್ಳಾರಿ"},
    "raichur": {"raichur", "ರಾಯಚೂರು"},
    "koppal": {"koppal", "ಕೊಪ್ಪಳ"},
    "vijayapura": {"vijayapura", "bijapur", "ವಿಜಯಪುರ"},
    "bagalkote": {"bagalkote", "bagalkot", "ಬಾಗಲಕೋಟೆ"},
    "haveri": {"haveri", "ಹಾವೇರಿ"},
    "gadag": {"gadag", "ಗದಗ"},
    "shivamogga": {"shivamogga", "shimoga", "ಶಿವಮೊಗ್ಗ"},
    "chikkamagaluru": {"chikkamagaluru", "ಚಿಕ್ಕಮಗಳೂರು"},
    "chitradurga": {"chitradurga", "ಚಿತ್ರದುರ್ಗ"},
    "davanagere": {"davanagere", "ದಾವಣಗೆರೆ"},
    "kolar": {"kolar", "ಕೋಲಾರ"},
    "chikkaballapura": {"chikkaballapura", "ಚಿಕ್ಕಬಳ್ಳಾಪುರ"},
    "ramanagara": {"ramanagara", "ರಾಮನಗರ"},
    "bengaluru": {"bengaluru", "bangalore", "ಬೆಂಗಳೂರು"},
    "udupi": {"udupi", "ಉಡುಪಿ"},
    "dakshina kannada": {"dakshina kannada", "ದಕ್ಷಿಣ ಕನ್ನಡ", "ಮಂಗಳೂರು", "mangalore"},
    "uttara kannada": {"uttara kannada", "ಉತ್ತರ ಕನ್ನಡ", "ಕಾರವಾರ", "karwar"},
    "kodagu": {"kodagu", "ಕೊಡಗು", "coorg"},
    "chamarajanagar": {"chamarajanagar", "ಚಾಮರಾಜನಗರ"},
    "yadgir": {"yadgir", "ಯಾದಗಿರಿ"},
}

# Irrigation source to water availability mapping
IRRIGATION_TO_WATER_SOURCE: Dict[str, bool] = {
    "Rainfed": False,
    "None": False,
    "Borewell": True,
    "Canal": True,
    "Open Well": True,
}


def normalize_land_size(land_size: LandSize) -> float:
    """
    Converts spoken land units to normalized acres with exact Python floating-point math.
    1 gunta = 0.025 acre (1/40th acre)
    1 hectare = 2.471 acres
    1 acre = 1.0 acre
    """
    unit = land_size.unit.lower()
    val = float(land_size.value)
    if unit == "gunta":
        return val * 0.025
    elif unit == "hectare":
        return val * 2.471
    elif unit == "acre":
        return val
    else:
        raise ValueError(f"Unsupported land unit: {land_size.unit}")


def canonicalize_crop(local_name: str) -> str:
    """Maps a local Kannada or English crop synonym to its canonical catalog name."""
    if not local_name:
        return local_name
    cleaned = local_name.strip().lower()
    return CROP_CANONICAL_MAP.get(cleaned, local_name.strip())


def canonicalize_crops(crops_local: List[str]) -> List[str]:
    """Canonicalizes a list of crop names, deduplicating while preserving order."""
    seen = set()
    result = []
    for c in crops_local:
        canonical = canonicalize_crop(c)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result


def is_land_size_sane(acres: float) -> bool:
    """Enforces sanity guardrail: acres must fall within [0.01, 100.0]."""
    return 0.01 <= acres <= 100.0


def check_district_evidence(district: str, transcript: str) -> bool:
    """Checks if a district (or its Kannada/English synonyms) appears in the transcript."""
    cleaned = district.strip().lower()
    transcript_clean = transcript.lower()

    if cleaned in transcript_clean:
        return True

    # Check synonyms
    for canon_dist, syns in DISTRICT_SYNONYMS.items():
        if cleaned == canon_dist or cleaned in syns:
            if any(s in transcript_clean for s in syns):
                return True

    return False


def extraction_to_farmer_profile_fields(extract: ExtractOut) -> Dict[str, Any]:
    """
    Converts an ExtractOut schema instance to a dictionary of field updates
    compatible with backend.rules_engine.FarmerProfile.
    """
    fields: Dict[str, Any] = {}

    if extract.district:
        fields["district"] = extract.district

    if extract.land_size:
        acres = normalize_land_size(extract.land_size)
        if is_land_size_sane(acres):
            fields["land_acres"] = acres

    if extract.ownership_type and extract.ownership_type != "Unknown":
        fields["ownership"] = extract.ownership_type

    if extract.crops_local:
        canon_crops = canonicalize_crops(extract.crops_local)
        if canon_crops:
            fields["crops"] = canon_crops

    if extract.irrigation_source:
        fields["irrigation_type"] = extract.irrigation_source
        fields["has_water_source"] = IRRIGATION_TO_WATER_SOURCE.get(extract.irrigation_source, False)

    return fields
