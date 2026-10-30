"""
Krishi Mitra — NLU Wire Schemas
Pydantic v2 models representing narrow extraction shapes from rural Kannada transcripts.
No derived fields (e.g. normalized_acres) are computed here; those are computed deterministically in Python.
"""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict


class LandSize(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float = Field(gt=0, le=1000, description="Number exactly as spoken")
    unit: Literal["acre", "gunta", "hectare"] = Field(description="Unit exactly as spoken")


class ExtractOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dialect_region: Optional[Literal["North_Karnataka", "Old_Mysore", "Coastal", "General"]] = None
    district: Optional[str] = None
    land_size: Optional[LandSize] = None
    ownership_type: Literal["Owner", "Tenant", "Joint Family", "Unknown"] = "Unknown"
    crops_local: List[str] = Field(default_factory=list, max_length=10)
    irrigation_source: Optional[Literal["Rainfed", "Borewell", "Canal", "Open Well", "None"]] = None
    assistance_intent: Optional[
        Literal[
            "scheme_discovery",
            "crop_loss_compensation",
            "solar_pump",
            "loan_waiver",
            "fertilizer_seed_subsidy",
            "general_inquiry",
        ]
    ] = None

    @field_validator("district")
    @classmethod
    def no_placeholder_district(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if cleaned.lower() in {"", "unknown", "n/a", "none", "null"}:
                return None
            return cleaned
        return None
