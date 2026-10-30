"""Local HTTP API for the Krishi Mitra web application."""

from __future__ import annotations

import base64
import binascii
from dataclasses import asdict
from io import BytesIO
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import math
import os
from pathlib import Path
import re
import time
import uuid
from typing import Any, Callable
from urllib.parse import urlparse

import httpx
from groq import APIConnectionError as GroqConnectionError
from groq import APIStatusError as GroqStatusError
from groq import APITimeoutError as GroqTimeoutError
from groq import Groq
from sarvamai import SarvamAI
from sarvamai.core.api_error import ApiError as SarvamApiError

from backend.rules_engine import FarmerProfile, SchemeEvaluator


ROOT = Path(__file__).resolve().parent.parent
MAX_REQUEST_BYTES = 64 * 1024
MAX_VOICE_AUDIO_BYTES = 4 * 1024 * 1024
MAX_VOICE_REQUEST_BYTES = 6 * 1024 * 1024
SARVAM_REQUEST_TIMEOUT_SECONDS = 15
GROQ_REQUEST_TIMEOUT_SECONDS = 25
GROQ_CHAT_MODEL = "openai/gpt-oss-120b"
PROFILE_DEFAULTS: dict[str, Any] = {
    "farmer_name": None,
    "district": None,
    "land_acres": None,
    "ownership": None,
    "crops": [],
    "season": None,
    "risk_type": None,
    "irrigation_type": None,
    "has_water_source": None,
    "availed_drip_subsidy_last_3_years": None,
    "requested_equipment": None,
    "equipment_cost_inr": None,
    "has_soil_health_card": None,
    "soil_deficiencies": [],
    "is_income_tax_payee": None,
    "is_institutional_landholder": None,
    "is_constitutional_post_holder": None,
    "is_government_employee": None,
}
BOOLEAN_FIELDS = {
    "has_water_source",
    "availed_drip_subsidy_last_3_years",
    "has_soil_health_card",
    "is_income_tax_payee",
    "is_institutional_landholder",
    "is_constitutional_post_holder",
    "is_government_employee",
}
LIST_FIELDS = {"crops", "soil_deficiencies"}
EVALUATOR = SchemeEvaluator()
LOGGER = logging.getLogger("krishi_mitra")


def _load_environment_file() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        name, separator, value = line.partition("=")
        name = name.strip()
        if separator and name and not name.startswith("#"):
            os.environ.setdefault(name, value.strip().strip("\"'"))


_load_environment_file()


class APIError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status


def _clean_string(value: Any, field: str) -> str | None:
    if not isinstance(value, str):
        raise APIError(400, f"'{field}' must be text.")
    value = value.strip()
    if not value:
        return None
    if len(value) > 160:
        raise APIError(400, f"'{field}' is too long.")
    return value


def normalize_profile_patch(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise APIError(400, "Farmer profile must be an object.")

    patch: dict[str, Any] = {}
    for field, value in raw.items():
        if field not in PROFILE_DEFAULTS or value is None:
            continue
        if field in BOOLEAN_FIELDS:
            if not isinstance(value, bool):
                raise APIError(400, f"'{field}' must be true or false.")
            patch[field] = value
        elif field in LIST_FIELDS:
            if not isinstance(value, list) or len(value) > 10:
                raise APIError(400, f"'{field}' must be a list of at most 10 items.")
            items = [_clean_string(item, field) for item in value]
            patch[field] = [item for item in items if item]
        elif field in {"land_acres", "equipment_cost_inr"}:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise APIError(400, f"'{field}' must be a number.")
            number = float(value)
            if not math.isfinite(number) or number < 0 or number > 1_000_000:
                raise APIError(400, f"'{field}' is outside the supported range.")
            patch[field] = number
        else:
            text = _clean_string(value, field)
            if text is not None:
                patch[field] = text
    return patch


def merge_profile(current: Any, patch: Any) -> dict[str, Any]:
    if not isinstance(current, dict):
        raise APIError(400, "Farmer profile must be an object.")
    merged = dict(PROFILE_DEFAULTS)
    merged.update(normalize_profile_patch(current))
    merged.update(normalize_profile_patch(patch))
    return merged


def _deterministic_extract(message: str) -> dict[str, Any]:
    text = message.lower()
    patch: dict[str, Any] = {}

    number_words = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "ಒಂದು": 1, "ಎರಡು": 2, "ಮೂರು": 3, "ಮೂರ್": 3, "ನಾಲ್ಕು": 4, "ಐದು": 5,
    }
    acres_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:acres?|ಎಕರೆ|ಎಕರೆಗಳು)", text, re.IGNORECASE
    )
    if acres_match:
        patch["land_acres"] = float(acres_match.group(1))
    else:
        for word, count in number_words.items():
            matches_word = (
                word in text
                if any("\u0c80" <= char <= "\u0cff" for char in word)
                else bool(re.search(rf"\b{re.escape(word)}\b", text))
            )
            if matches_word and re.search(r"(?:acre|ಎಕರೆ)", text):
                patch["land_acres"] = float(count)
                break

    districts = {
        "kalaburagi": ("kalaburagi", "ಕಲಬುರಗಿ", "gulbarga", "ಗುಲ್ಬರ್ಗಾ"),
        "mandya": ("mandya", "ಮಂಡ್ಯ"),
        "belagavi": ("belagavi", "ಬೆಳಗಾವಿ", " ಬೆಳಗಾವಿ"),
        "dharwad": ("dharwad", "ಧಾರವಾಡ"),
        "kolar": ("kolar", "ಕೋಲಾರ"),
        "hassan": ("hassan", "ಹಾಸನ"),
        "shivamogga": ("shivamogga", "ಶಿವಮೊಗ್ಗ"),
        "tumakuru": ("tumakuru", "ತುಮಕೂರು"),
    }
    for district, aliases in districts.items():
        if any(alias in text for alias in aliases):
            patch["district"] = district.title()
            break

    crop_aliases = {
        "Ragi": ("ragi", "ರಾಗಿ"),
        "Pigeon Pea (Togari)": ("pigeon pea", "togari", "ತೊಗರಿ"),
        "Jowar": ("jowar", "jola", "ಜೋಳ"),
        "Paddy": ("paddy", "rice", "ಭತ್ತ", "ಅಕ್ಕಿ"),
        "Cotton": ("cotton", "ಹತ್ತಿ"),
        "Groundnut": ("groundnut", "peanut", "ಶೇಂಗಾ"),
        "Sugarcane": ("sugarcane", "sugar cane", "ಕಬ್ಬು"),
        "Maize": ("maize", "corn", "ಮೆಕ್ಕೆಜೋಳ"),
        "Soybean": ("soybean", "ಸೋಯಾಬೀನ್"),
    }
    for crop, aliases in crop_aliases.items():
        if any(alias in text for alias in aliases):
            patch["crops"] = [crop]
            break

    if any(term in text for term in ("kharif", "ಖರೀಫ್")):
        patch["season"] = "Kharif"
    elif any(term in text for term in ("rabi", "ರಬಿ")):
        patch["season"] = "Rabi"
    elif any(term in text for term in ("summer", "ಬೇಸಿಗೆ")):
        patch["season"] = "Summer"

    if any(term in text for term in ("borewell", "bore well", "ಬೋರ್ವೆಲ್", "ಕೊಳವೆಬಾವಿ")):
        patch.update(irrigation_type="Borewell", has_water_source=True)
    elif any(term in text for term in ("canal", "ಕಾಲುವೆ")):
        patch.update(irrigation_type="Canal", has_water_source=True)
    elif any(term in text for term in ("open well", "ಬಾವಿ")):
        patch.update(irrigation_type="Open Well", has_water_source=True)
    elif any(term in text for term in ("rainfed", "dryland", "ಕುಷ್ಕಿ", "ಮಳೆ ಆಶ್ರಿತ")):
        patch.update(irrigation_type="Rainfed", has_water_source=False)

    if any(term in text for term in ("drought", " ಬರ", "ಬರಗಾಲ")):
        patch["risk_type"] = "Drought"
    elif any(term in text for term in ("excess rain", "flood", "ನೆರೆ", "ಅತಿವೃಷ್ಟಿ")):
        patch["risk_type"] = "Excess Rain"
    elif any(term in text for term in ("pest", "ಕೀಟ", "ರೋಗಬಾಧೆ")):
        patch["risk_type"] = "Pest Attack"

    if any(term in text for term in ("tenant", "sharecropper", "ಗೇಣಿದಾರ", "ಬಾಡಿಗೆದಾರ")):
        patch["ownership"] = "Tenant"
    elif any(term in text for term in ("joint family", "ಜಂಟಿ ಕುಟುಂಬ")):
        patch["ownership"] = "Joint Family Owner"
    elif any(term in text for term in ("my land", "own land", "ನನ್ನ ಜಮೀನು", "ನಮ್ಮ ಜಮೀನು")):
        patch["ownership"] = "Owner"

    equipment = {
        "Power Tiller": ("power tiller", "ಪವರ್ ಟಿಲ್ಲರ್"),
        "Rotavator": ("rotavator", "ರೋಟಾವೇಟರ್"),
        "Tractor": ("tractor", "ಟ್ರ್ಯಾಕ್ಟರ್"),
        "Sprayer": ("sprayer", "ಸ್ಪ್ರೇಯರ್"),
    }
    for name, aliases in equipment.items():
        if any(alias in text for alias in aliases):
            patch["requested_equipment"] = name
            break

    if any(term in text for term in ("soil health card", "soil card", "ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್")):
        patch["has_soil_health_card"] = not any(
            term in text for term in ("no soil health card", "don't have soil", "ಕಾರ್ಡ್ ಇಲ್ಲ")
        )

    exclusion_phrases = {
        "is_income_tax_payee": ("income tax", "ಆದಾಯ ತೆರಿಗೆ"),
        "is_institutional_landholder": ("institutional landholder", "ಸಂಸ್ಥಾಗತ ಭೂಮಾಲೀಕ"),
        "is_constitutional_post_holder": ("constitutional post", "ಜನಪ್ರತಿನಿಧಿ", "ಸಾಂವಿಧಾನಿಕ ಹುದ್ದೆ"),
        "is_government_employee": ("government employee", "government pension", "ಸರ್ಕಾರಿ ನೌಕರ"),
    }
    for field, phrases in exclusion_phrases.items():
        if any(phrase in text for phrase in phrases):
            negated = any(
                marker in text
                for marker in ("not ", "don't ", "do not ", "no ", "ಅಲ್ಲ", "ಇಲ್ಲ")
            )
            patch[field] = not negated

    return normalize_profile_patch(patch)


def _profile_to_model(profile: dict[str, Any]) -> FarmerProfile:
    values = {key: value for key, value in profile.items() if value is not None}
    if values.get("land_acres") is None:
        values["land_acres"] = 0.0
    values.setdefault("crops", [])
    values.setdefault("soil_deficiencies", [])
    return FarmerProfile(**values)


def _eligibility_results(profile: dict[str, Any]) -> list[dict[str, Any]]:
    farmer = _profile_to_model(profile)
    results = EVALUATOR.evaluate_all(farmer)
    missing_by_scheme = {
        "pm_kisan": [
            field for field in (
                "land_acres", "ownership", "is_income_tax_payee",
                "is_institutional_landholder", "is_constitutional_post_holder",
                "is_government_employee",
            ) if profile.get(field) is None
        ],
        "pmfby": [
            field for field in ("district", "crops", "season")
            if not profile.get(field)
        ],
        "pmksy_pdmc": [
            field for field in ("district", "land_acres", "irrigation_type")
            if profile.get(field) is None
        ],
        "smam": [
            field for field in ("district", "requested_equipment")
            if profile.get(field) is None
        ],
        "soil_health_card": [
            field for field in ("district",)
            if profile.get(field) is None
        ],
    }

    serialized: list[dict[str, Any]] = []
    for result in results:
        item = asdict(result)
        missing = missing_by_scheme[result.scheme_id]
        definitely_ineligible = bool(result.disqualification_reasons)
        if result.scheme_id == "pm_kisan":
            definitely_ineligible = (
                profile.get("ownership") == "Tenant"
                or (
                    profile.get("land_acres") is not None
                    and profile["land_acres"] <= 0
                )
                or any(profile.get(field) is True for field in (
                    "is_income_tax_payee", "is_institutional_landholder",
                    "is_constitutional_post_holder", "is_government_employee",
                ))
            )
        elif result.scheme_id == "pmfby":
            definitely_ineligible = (
                bool(profile.get("crops"))
                and result.disqualification_reasons
                and ("not currently notified" in result.disqualification_reasons[0]
                     or ("Season '" in result.disqualification_reasons[0]))
            )

        if missing and not definitely_ineligible and result.scheme_id in {"pm_kisan", "pmfby"}:
            item["status"] = "CONDITIONALLY_ELIGIBLE"
            item["missing_information"] = missing
            item["benefit_summary_en"] = (
                "Potentially eligible based on the details provided; answer the follow-up "
                "questions before relying on this screening."
            )
            item["benefit_summary_kn"] = (
                "ನೀಡಿದ ಮಾಹಿತಿಯ ಆಧಾರದಲ್ಲಿ ಷರತ್ತುಬದ್ಧ ಸಾಧ್ಯತೆ ಇದೆ; ಮುಂದಿನ ಪ್ರಶ್ನೆಗಳಿಗೆ "
                "ಉತ್ತರಿಸಿದ ನಂತರವೇ ಈ ಪರಿಶೀಲನೆಯನ್ನು ಪರಿಗಣಿಸಿ."
            )
        else:
            item["missing_information"] = missing

        if result.scheme_id == "pmfby" and item["status"] == "ELIGIBLE":
            item["status"] = "CONDITIONALLY_ELIGIBLE"
            item["benefit_summary_en"] = (
                "The crop and season match the reference rules. District notification, "
                "insurance enrollment, and claim assessment must still be confirmed."
            )
            item["benefit_summary_kn"] = (
                "ಬೆಳೆ ಮತ್ತು ಋತು ಮಾದರಿ ನಿಯಮಗಳಿಗೆ ಹೊಂದಿವೆ. ಜಿಲ್ಲೆ/ಹೋಬಳಿ ಅಧಿಸೂಚನೆ, "
                "ವಿಮೆ ನೋಂದಣಿ ಮತ್ತು ಹಾನಿ ಪರಿಶೀಲನೆ ಇನ್ನೂ ದೃಢಪಡಿಸಬೇಕು."
            )
        if result.scheme_id == "pm_kisan" and item["status"] == "ELIGIBLE":
            item["status"] = "CONDITIONALLY_ELIGIBLE"
            item["benefit_summary_en"] = (
                "The details provided match the listed screening criteria. Official "
                "land records, beneficiary status, and current exclusions still need "
                "verification by the department."
            )
            item["benefit_summary_kn"] = (
                "ನೀಡಿದ ವಿವರಗಳು ಪ್ರಾಥಮಿಕ ಮಾನದಂಡಗಳಿಗೆ ಹೊಂದಿವೆ. ಇಲಾಖೆಯು ಭೂ ದಾಖಲೆ, "
                "ಫಲಾನುಭವಿ ಸ್ಥಿತಿ ಮತ್ತು ಪ್ರಸ್ತುತ ಅನರ್ಹತೆಗಳನ್ನು ಇನ್ನೂ ದೃಢಪಡಿಸಬೇಕು."
            )
        item["disclaimer_en"] = (
            "This is an informational screening, not an official eligibility decision. "
            "Confirm current rules and application status with the relevant department."
        )
        scheme = EVALUATOR.schemes_map[result.scheme_id]
        item["sources"] = scheme.get("sources", [])
        item["last_researched"] = scheme.get("last_researched")
        serialized.append(item)
    return serialized


def _missing_chat_slots(profile: dict[str, Any], message: str) -> list[str]:
    text = message.lower()
    labels = []
    if any(term in text for term in (
        "pmksy", "per drop more crop", "micro irrigation", "drip", "sprinkler",
        "irrigation", "ಹನಿ", "ತುಂತುರು", "ನೀರಾವರಿ",
    )):
        if profile.get("district") is None:
            labels.append("district / ಜಿಲ್ಲೆ")
        if profile.get("land_acres") is None:
            labels.append("land size in acres / ಎಕರೆ")
        if profile.get("irrigation_type") is None:
            labels.append("water source / ನೀರಿನ ಮೂಲ")
    elif any(term in text for term in (
        "smam", "machinery", "mechanization", "tiller", "rotavator",
        "tractor", "sprayer", "ಯಂತ್ರ", "ಟಿಲ್ಲರ್", "ಟ್ರ್ಯಾಕ್ಟರ್",
    )):
        if profile.get("district") is None:
            labels.append("district / ಜಿಲ್ಲೆ")
        if profile.get("requested_equipment") is None:
            labels.append("equipment needed / ಬೇಕಾದ ಯಂತ್ರೋಪಕರಣ")
    elif any(term in text for term in ("soil", "ಮಣ್ಣು", "soil health", "ಮಣ್ಣಿನ")):
        if profile.get("district") is None:
            labels.append("district / ಜಿಲ್ಲೆ")
        labels.append("whether you need a soil test or help understanding an existing report / ಮಣ್ಣು ಪರೀಕ್ಷೆ ಬೇಕೇ ಅಥವಾ ವರದಿ ಅರ್ಥೈಸಲು ಸಹಾಯ ಬೇಕೇ")
    elif any(term in text for term in ("pm-kisan", "pm kisan", "ಕಿಸಾನ್")):
        if profile.get("land_acres") is None:
            labels.append("land size in acres / ಎಕರೆ")
        if profile.get("ownership") is None:
            labels.append("recorded land ownership / ಜಮೀನಿನ ಮಾಲೀಕತ್ವ")
        exclusion_fields = (
            "is_income_tax_payee", "is_institutional_landholder",
            "is_constitutional_post_holder", "is_government_employee",
        )
        if any(profile.get(field) is None for field in exclusion_fields):
            labels.append("PM-KISAN exclusion details (tax, institutional land, public office, government service)")
    elif any(term in text for term in ("pmfby", "crop insurance", "insurance", "crop loss", "compensation", "ವಿಮೆ", "ಬೆಳೆ ನಷ್ಟ", "ಪರಿಹಾರ")):
        if profile.get("district") is None:
            labels.append("district / ಜಿಲ್ಲೆ")
        if not profile.get("crops"):
            labels.append("crop / ಬೆಳೆ")
        if profile.get("season") is None:
            labels.append("sowing season / ಬಿತ್ತನೆ ಋತು")
        if profile.get("risk_type") is None:
            labels.append("crop damage or peril / ಬೆಳೆ ಹಾನಿ")
    return labels


def _is_scheme_query(message: str) -> bool:
    text = message.casefold()
    return any(term in text for term in (
        "scheme", "yojana", "ಸರ್ಕಾರಿ ಯೋಜನೆ", "ಸರ್ಕಾರದ ಯೋಜನೆ", "ಯೋಜನೆ",
        "subsidy", "ಸಬ್ಸಿಡಿ", "eligible", "eligibility", "ಅರ್ಹತೆ", "ಅರ್ಹ",
        "government support", "government assistance", "government benefit",
        "government benefits", "financial assistance", "scheme application",
        "apply for subsidy", "grant", "pm-kisan", "pm kisan",
        "pmfby", "pmksy", "crop insurance", "insurance claim", "ಬೆಳೆ ವಿಮೆ",
        "ಪರಿಹಾರ", "ಸರ್ಕಾರಿ ನೆರವು", "ಸಹಾಯಧನ",
    ))


def _validated_chat_history(payload: dict[str, Any]) -> list[dict[str, str]]:
    history = payload.get("history", [])
    if not isinstance(history, list) or len(history) > 8:
        raise APIError(400, "Chat history must contain no more than 8 messages.")

    messages = []
    for item in history:
        if (
            not isinstance(item, dict)
            or item.get("role") not in {"user", "assistant"}
            or not isinstance(item.get("content"), str)
            or not item["content"].strip()
            or len(item["content"]) > 2500
        ):
            raise APIError(400, "Chat history contains an invalid message.")
        messages.append({
            "role": item["role"],
            "content": item["content"].strip(),
        })
    return messages


def _local_chat_reply(language: str, missing: list[str]) -> str:
    if missing:
        question = missing[0]
        if language == "kn":
            return f"ನಿಮ್ಮ ಪ್ರಶ್ನೆಗೆ ಸಹಾಯ ಮಾಡಲು ಪ್ರಯತ್ನಿಸುತ್ತೇನೆ. ಮೊದಲು, ದಯವಿಟ್ಟು {question} ತಿಳಿಸಿ."
        return f"I can help with that. First, could you tell me your {question}?"
    if language == "kn":
        return "ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗೆ ಸಹಾಯ ಮಾಡಲು ನಾನು ಇಲ್ಲಿದ್ದೇನೆ. ನಿಮ್ಮ ಬೆಳೆ ಮತ್ತು ಜಿಲ್ಲೆಯ ಬಗ್ಗೆ ಹೇಳಿದರೆ, ನಿಮ್ಮ ಪರಿಸ್ಥಿತಿಗೆ ತಕ್ಕಂತೆ ಮಾರ್ಗದರ್ಶನ ನೀಡುತ್ತೇನೆ."
    return "I’m here to help with your farming question. Tell me which crop you’re growing and your district, and I can tailor the guidance to your farm."


def handle_chat(payload: dict[str, Any], request_id: str = "local") -> dict[str, Any]:
    message = payload.get("message")
    language = payload.get("language", "en")
    if not isinstance(message, str) or not message.strip() or len(message) > 4000:
        raise APIError(400, "Message must contain 1-4000 characters.")
    if language not in {"en", "kn"}:
        raise APIError(400, "Language must be 'en' or 'kn'.")

    message = message.strip()
    history = _validated_chat_history(payload)
    current = merge_profile(payload.get("profile", {}), {})
    profile = merge_profile(current, _deterministic_extract(message))
    results = _eligibility_results(profile)
    show_evaluations = _is_scheme_query(message)
    missing = _missing_chat_slots(profile, message) if show_evaluations else []
    groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
    sarvam_api_key = os.environ.get("SARVAM_API_KEY", "").strip()
    audio = None
    scheme_context = [
        {
            "scheme": result["scheme_name_en"],
            "status": result["status"],
            "benefit_summary": result["benefit_summary_en"],
            "missing_information": result.get("missing_information", []),
        }
        for result in results
    ] if show_evaluations else []
    context = {
        "farmer_profile": profile,
        "preliminary_programme_screening": (
            scheme_context if show_evaluations else
            "Not requested in this message. Do not introduce government schemes."
        ),
        "scheme_follow_up_information": missing,
    }
    system_prompt = (
        "You are Krishi Mitra, a warm, natural, concise agricultural information "
        "assistant for farmers in Karnataka. Respond in "
        f"{'Kannada' if language == 'kn' else 'Indian English'}. "
        "Answer the farmer's actual question first in everyday spoken language; "
        "handle broad farming questions, not only scheme eligibility. Use the recent "
        "conversation to understand follow-ups. For general crop-care guidance, be "
        "practical and note briefly when advice depends on local conditions. For "
        "government schemes, use only the supplied screening context; never invent "
        "current rates, application dates, funding, or availability, and never promise "
        "eligibility or approval. Clearly call scheme results preliminary and direct "
        "official decisions to the department. After answering, ask one brief, relevant "
        "question to learn a useful farm detail or move a scheme check forward. Ask only "
        "for information not already present in the profile or recent conversation, and "
        "never ask for multiple details at once. If no useful follow-up is needed, do not "
        "add a filler question. Keep the whole reply to at most four short sentences."
    )
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": (
            message
            + "\n\nCurrent farmer and screening context (reference data only): "
            + json.dumps(context, ensure_ascii=False)
        ),
    })
    if groq_api_key:
        try:
            response = _groq_chat_completion(request_id, messages)
            reply = _validated_model_reply(response, "Groq")
            model_mode = f"Groq {GROQ_CHAT_MODEL}"
        except APIError as error:
            LOGGER.warning(
                "request_id=%s route=/api/chat status=local_fallback http_status=%d",
                request_id,
                error.status,
            )
            reply = _local_chat_reply(language, missing)
            model_mode = f"Local assistant (Groq unavailable: {error})"
    else:
        reply = _local_chat_reply(language, missing)
        model_mode = "Local assistant (set GROQ_API_KEY to enable natural chat)"

    if sarvam_api_key:
        speech_language = "kn" if language == "kn" else "en"
        try:
            speech_client = SarvamAI(
                api_subscription_key=sarvam_api_key,
                timeout=SARVAM_REQUEST_TIMEOUT_SECONDS,
            )
            speech = _sarvam_request(
                request_id,
                f"{speech_language} speech synthesis",
                lambda: speech_client.text_to_speech.convert(
                    text=reply,
                    model="bulbul:v4-flash",
                    language_code="kn-IN" if speech_language == "kn" else "en-IN",
                    speaker=(
                        "chaitra_kn_conversation"
                        if speech_language == "kn"
                        else "simran_en_conversation"
                    ),
                    output_audio_codec="wav",
                ),
            )
            audio_segments = getattr(speech, "audios", None)
            if (
                isinstance(audio_segments, list)
                and audio_segments
                and all(isinstance(segment, str) for segment in audio_segments)
            ):
                audio = "".join(audio_segments)
                speech_label = "Kannada" if speech_language == "kn" else "English"
                model_mode += f" + {speech_label} speech"
            else:
                LOGGER.warning(
                    "request_id=%s stage=%s speech synthesis status=invalid_response",
                    request_id,
                    speech_language,
                )
        except APIError as error:
            LOGGER.warning(
                "request_id=%s stage=%s speech synthesis status=text_fallback error=%s",
                request_id,
                speech_language,
                error,
            )

    return {
        "reply": reply,
        "language": language,
        "profile": profile,
        "evaluations": results,
        "show_evaluations": show_evaluations,
        "missing_slots": missing,
        "audio": audio,
        "mime_type": "audio/wav" if audio else None,
        "model_mode": model_mode,
    }


def _sarvam_request(
    request_id: str,
    operation: str,
    request: Callable[[], Any],
) -> Any:
    started_at = time.monotonic()
    LOGGER.info("request_id=%s stage=%s status=started", request_id, operation)
    try:
        result = request()
    except SarvamApiError as error:
        LOGGER.warning(
            "request_id=%s stage=%s status=provider_error http_status=%s duration_ms=%d",
            request_id,
            operation,
            error.status_code,
            round((time.monotonic() - started_at) * 1000),
        )
        if error.status_code in (401, 403):
            raise APIError(503, "Sarvam rejected the configured API key or account.") from error
        if error.status_code == 429:
            raise APIError(503, "Sarvam rate limit reached. Please try again shortly.") from error
        raise APIError(
            502,
            f"Sarvam {operation} failed with HTTP {error.status_code}.",
        ) from error
    except httpx.TimeoutException as error:
        LOGGER.warning(
            "request_id=%s stage=%s status=timeout duration_ms=%d",
            request_id,
            operation,
            round((time.monotonic() - started_at) * 1000),
        )
        raise APIError(504, f"Sarvam {operation} timed out. Please try again.") from error
    except httpx.HTTPError as error:
        LOGGER.warning(
            "request_id=%s stage=%s status=connection_error duration_ms=%d error_type=%s",
            request_id,
            operation,
            round((time.monotonic() - started_at) * 1000),
            type(error).__name__,
        )
        raise APIError(502, f"Could not reach Sarvam for {operation}.") from error
    LOGGER.info(
        "request_id=%s stage=%s status=completed duration_ms=%d",
        request_id,
        operation,
        round((time.monotonic() - started_at) * 1000),
    )
    return result


def _groq_chat_completion(request_id: str, messages: list[dict[str, str]]) -> Any:
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise APIError(503, "Set GROQ_API_KEY in .env to enable natural chat.")
    client = Groq(
        api_key=api_key,
        timeout=GROQ_REQUEST_TIMEOUT_SECONDS,
        max_retries=0,
    )
    started_at = time.monotonic()
    LOGGER.info("request_id=%s stage=Groq chat completion status=started", request_id)
    try:
        response = client.chat.completions.create(
            model=GROQ_CHAT_MODEL,
            messages=messages,
            temperature=0.3,
        )
    except GroqTimeoutError as error:
        LOGGER.warning(
            "request_id=%s stage=Groq chat completion status=timeout duration_ms=%d",
            request_id,
            round((time.monotonic() - started_at) * 1000),
        )
        raise APIError(504, "Groq chat completion timed out. Please try again.") from error
    except GroqStatusError as error:
        LOGGER.warning(
            "request_id=%s stage=Groq chat completion status=provider_error "
            "http_status=%s duration_ms=%d",
            request_id,
            error.status_code,
            round((time.monotonic() - started_at) * 1000),
        )
        if error.status_code in (401, 403):
            raise APIError(503, "Groq rejected the configured API key or account.") from error
        if error.status_code == 429:
            raise APIError(503, "Groq rate limit reached. Please try again shortly.") from error
        raise APIError(
            502,
            f"Groq chat completion failed with HTTP {error.status_code}.",
        ) from error
    except GroqConnectionError as error:
        LOGGER.warning(
            "request_id=%s stage=Groq chat completion status=connection_error duration_ms=%d",
            request_id,
            round((time.monotonic() - started_at) * 1000),
        )
        raise APIError(502, "Could not reach Groq for chat completion.") from error
    LOGGER.info(
        "request_id=%s stage=Groq chat completion status=completed duration_ms=%d",
        request_id,
        round((time.monotonic() - started_at) * 1000),
    )
    return response


def _validated_model_reply(response: Any, provider: str) -> str:
    try:
        reply = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError) as error:
        raise APIError(502, f"{provider} returned an invalid chat response.") from error
    if not isinstance(reply, str) or not reply.strip() or len(reply) > 2500:
        raise APIError(502, f"{provider} returned an invalid chat response.")
    return reply.strip()


def handle_voice_turn(payload: dict[str, Any], request_id: str = "local") -> dict[str, Any]:
    api_key = os.environ.get("SARVAM_API_KEY", "").strip()
    if not api_key:
        raise APIError(503, "Set SARVAM_API_KEY in .env to enable voice chat.")

    encoded_audio = payload.get("audio")
    mime_type = payload.get("mime_type")
    if not isinstance(encoded_audio, str) or not encoded_audio:
        raise APIError(400, "A recorded audio clip is required.")
    if not isinstance(mime_type, str) or mime_type not in {
        "audio/webm", "audio/ogg", "audio/mp4", "audio/wav"
    }:
        raise APIError(400, "Audio must be WebM, Ogg, MP4, or WAV.")
    try:
        audio_bytes = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError) as error:
        raise APIError(400, "Audio data must be valid base64.") from error
    if not audio_bytes:
        raise APIError(400, "The recorded audio clip is empty.")
    if len(audio_bytes) > MAX_VOICE_AUDIO_BYTES:
        raise APIError(413, "Audio clips must be no larger than 4 MB.")
    recording_duration_ms = payload.get("recording_duration_ms")
    if (
        not isinstance(recording_duration_ms, int)
        or isinstance(recording_duration_ms, bool)
        or not 0 <= recording_duration_ms <= 26_000
    ):
        recording_duration_ms = "unknown"
    LOGGER.info(
        "request_id=%s voice_audio_bytes=%d mime_type=%s recording_duration_ms=%s",
        request_id,
        len(audio_bytes),
        mime_type,
        recording_duration_ms,
    )

    language = payload.get("language", "en")
    if not isinstance(language, str) or language not in {"en", "kn"}:
        raise APIError(400, "Language must be 'en' or 'kn'.")
    current_profile = merge_profile(payload.get("profile", {}), {})
    history = _validated_chat_history(payload)

    client = SarvamAI(
        api_subscription_key=api_key,
        timeout=SARVAM_REQUEST_TIMEOUT_SECONDS,
    )
    extension = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp4": "mp4",
        "audio/wav": "wav",
    }[mime_type]
    transcription = _sarvam_request(
        request_id,
        "speech recognition",
        lambda: client.speech_to_text.transcribe(
            file=(f"farmer-audio.{extension}", BytesIO(audio_bytes), mime_type),
            model="saaras:v4",
            language_code="unknown",
        ),
    )
    transcript = getattr(transcription, "transcript", None)
    if not isinstance(transcript, str):
        raise APIError(502, "Sarvam returned an invalid speech transcript.")
    transcript = transcript.strip()
    detected_language = getattr(transcription, "language_code", None)
    if not isinstance(detected_language, str) or not re.fullmatch(
        r"[A-Za-z0-9-]{1,16}", detected_language
    ):
        detected_language = "unknown"
    if not transcript:
        LOGGER.warning(
            "request_id=%s stage=speech recognition status=empty_transcript "
            "detected_language=%s",
            request_id,
            detected_language,
        )
        if language == "kn":
            raise APIError(
                422,
                "ಮಾತು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. ಕೆಲವು ಸೆಕೆಂಡುಗಳ ಕಾಲ ಸ್ಪಷ್ಟವಾಗಿ ಮಾತನಾಡಿ, "
                "ಮೈಕ್ ಹತ್ತಿರ ಇರಿಸಿ, ಸರಿಯಾದ ಇನ್‌ಪುಟ್ ಮೈಕ್ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
            )
        raise APIError(
            422,
            "No speech was recognized. Speak clearly for a few seconds near the "
            "microphone, choose the correct input device, and try again.",
        )
    LOGGER.info(
        "request_id=%s stage=speech recognition transcript_chars=%d "
        "detected_language=%s",
        request_id,
        len(transcript),
        detected_language,
    )
    response_language = (
        "kn" if detected_language.lower().startswith("kn")
        else "en" if detected_language.lower().startswith("en")
        else language
    )

    # Keep voice-turn profile extraction local and deterministic.
    voice_profile = merge_profile(current_profile, _deterministic_extract(transcript))
    voice_evaluations = _eligibility_results(voice_profile)
    show_evaluations = _is_scheme_query(transcript)
    voice_missing = (
        _missing_chat_slots(voice_profile, transcript) if show_evaluations else []
    )
    LOGGER.info(
        "request_id=%s stage=profile_extraction status=completed transcript_chars=%d",
        request_id,
        len(transcript),
    )
    scheme_context = [
        {
            "scheme": result["scheme_name_en"],
            "status": result["status"],
            "benefit_summary": result["benefit_summary_en"],
            "missing_information": result.get("missing_information", []),
        }
        for result in voice_evaluations
    ] if show_evaluations else []
    system_prompt = (
        "You are Krishi Mitra, a warm, natural agricultural information voice assistant "
        "for farmers in Karnataka. "
        f"Reply only in {'Kannada' if response_language == 'kn' else 'Indian English'} using natural, spoken phrasing. "
        "Answer the farmer's actual question first, including general farming questions; "
        "use recent conversation for follow-ups. Do not start with a list of schemes or "
        "mention government programmes unless the farmer asks about support, a scheme, "
        "subsidy, insurance, or eligibility. Use only supplied programme context for "
        "scheme details. Never invent current rates, dates, funding, or availability, and "
        "never promise eligibility or approval. Keep the answer to at most three short "
        "sentences and, when useful, finish by asking one natural question about the farmer's "
        "crop, district, or farm. Do not ask for details already provided."
    )
    user_context = {
        "farmer_message": transcript,
        "farmer_profile": voice_profile,
        "preliminary_programme_screening": (
            scheme_context if show_evaluations else
            "Not requested. Do not introduce government schemes."
        ),
    }
    chat_messages = [{"role": "system", "content": system_prompt}]
    chat_messages.extend(history)
    chat_messages.append({
        "role": "user",
        "content": json.dumps(user_context, ensure_ascii=False),
    })
    try:
        chat_response = _groq_chat_completion(request_id, chat_messages)
        reply = _validated_model_reply(chat_response, "Groq")
        model_mode = f"Groq {GROQ_CHAT_MODEL}"
    except APIError as error:
        LOGGER.warning(
            "request_id=%s route=/api/voice-turn status=local_fallback http_status=%d",
            request_id,
            error.status,
        )
        reply = _local_chat_reply(response_language, voice_missing)
        model_mode = f"Local assistant (Groq unavailable: {error})"

    speaker = "chaitra_kn_conversation" if response_language == "kn" else "simran_en_conversation"
    speech = _sarvam_request(
        request_id,
        "speech synthesis",
        lambda: client.text_to_speech.convert(
            text=reply,
            model="bulbul:v4-flash",
            language_code="kn-IN" if response_language == "kn" else "en-IN",
            speaker=speaker,
            output_audio_codec="wav",
        ),
    )
    audio_segments = getattr(speech, "audios", None)
    if (
        not isinstance(audio_segments, list)
        or not audio_segments
        or not all(isinstance(segment, str) for segment in audio_segments)
    ):
        raise APIError(502, "Sarvam did not return generated speech audio.")

    return {
        "transcript": transcript,
        "detected_language": detected_language,
        "reply": reply,
        "language": response_language,
        "audio": "".join(audio_segments),
        "mime_type": "audio/wav",
        "profile": voice_profile,
        "evaluations": voice_evaluations,
        "show_evaluations": show_evaluations,
        "missing_slots": voice_missing,
        "model_mode": (
            f"Sarvam Saaras v4 + {model_mode} + Bulbul v4 Flash"
        ),
    }


class KrishiMitraHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, status: int, data: dict[str, Any]) -> None:
        encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        request_id = getattr(self, "request_id", None)
        if request_id:
            self.send_header("X-Request-ID", request_id)
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self._send_json(200, {
                "ok": True,
                "model_mode": (
                    f"Groq {GROQ_CHAT_MODEL}"
                    if os.environ.get("GROQ_API_KEY", "").strip()
                    else "Local assistant"
                ),
                "voice_mode": (
                    "Sarvam speech ready"
                    if os.environ.get("SARVAM_API_KEY", "").strip()
                    else "Set SARVAM_API_KEY in .env to enable voice chat"
                ),
            })
            return
        if path not in {
            "/", "/index.html", "/chat.html", "/web_app.js",
            "/assets/hero_video.mp4", "/assets/hero_video_2.mp4",
            "/assets/farm_hero.mp4",
        }:
            self._send_json(404, {"error": "Resource not found."})
            return
        super().do_GET()

    def do_POST(self) -> None:
        route = urlparse(self.path).path
        request_id = uuid.uuid4().hex[:12]
        self.request_id = request_id
        started_at = time.monotonic()
        LOGGER.info("request_id=%s route=%s status=started", request_id, route)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            max_request_bytes = (
                MAX_VOICE_REQUEST_BYTES if route == "/api/voice-turn" else MAX_REQUEST_BYTES
            )
            if length <= 0 or length > max_request_bytes:
                raise APIError(413, "Request body is empty or exceeds the supported size.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise APIError(400, "Request body must be a JSON object.")
            if route == "/api/chat":
                self._send_json(200, handle_chat(payload, request_id))
            elif route == "/api/evaluate":
                profile = merge_profile(payload.get("profile", {}), {})
                self._send_json(200, {
                    "profile": profile,
                    "evaluations": _eligibility_results(profile),
                })
            elif route == "/api/voice-turn":
                self._send_json(200, handle_voice_turn(payload, request_id))
            else:
                self._send_json(404, {"error": "API route not found."})
            LOGGER.info(
                "request_id=%s route=%s status=completed duration_ms=%d",
                request_id,
                route,
                round((time.monotonic() - started_at) * 1000),
            )
        except APIError as error:
            LOGGER.warning(
                "request_id=%s route=%s status=error http_status=%d message=%s duration_ms=%d",
                request_id,
                route,
                error.status,
                str(error),
                round((time.monotonic() - started_at) * 1000),
            )
            self._send_json(error.status, {"error": str(error)})
        except (UnicodeDecodeError, json.JSONDecodeError):
            LOGGER.warning("request_id=%s route=%s status=invalid_json", request_id, route)
            self._send_json(400, {"error": "Request body must be valid UTF-8 JSON."})
        except (BrokenPipeError, ConnectionResetError):
            raise

    def log_message(self, format: str, *args: Any) -> None:
        # Do not log request content; farmer messages may contain personal details.
        if self.path.startswith("/api/"):
            return
        super().log_message(format, *args)


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), KrishiMitraHandler)
    print(f"Krishi Mitra web app: http://127.0.0.1:{port}")
    print(
        "Chat assistant: "
        + (f"Groq {GROQ_CHAT_MODEL} ready"
           if os.environ.get("GROQ_API_KEY", "").strip()
           else "local fallback (GROQ_API_KEY not set)")
    )
    print(
        "Voice chat: "
        + ("Sarvam ready" if os.environ.get("SARVAM_API_KEY", "").strip()
           else "disabled (SARVAM_API_KEY not set)")
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Krishi Mitra server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
