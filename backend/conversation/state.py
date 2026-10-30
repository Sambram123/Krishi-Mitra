"""
Krishi Mitra — Conversation State & Conflict-Aware Merge
Pydantic v2 session state management with conflict quarantine, slot completeness tracking,
and immutable merge policies.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

REQUIRED_SLOTS: List[str] = ["land_acres", "crops", "irrigation_type", "district"]


class ConversationState(BaseModel):
    session_id: str
    confirmed_profile: Dict[str, Any] = Field(default_factory=dict)
    inferred_slots: Dict[str, Any] = Field(default_factory=dict)
    quarantined_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    turn_history: List[Dict[str, str]] = Field(default_factory=list)
    turn_count: int = 0
    schema_version: str = "1.0"


def merge_extraction(state: ConversationState, new_fields: Dict[str, Any]) -> ConversationState:
    """
    Merges newly extracted fields into ConversationState.
    Merge rules:
      1. None or empty values NEVER overwrite an existing confirmed value.
      2. 'crops' performs a set union preserving order.
      3. Conflicting scalars are quarantined without overwriting confirmed values.
      4. New or matching scalars are updated into confirmed_profile.
    """
    updated_confirmed = dict(state.confirmed_profile)
    updated_conflicts = list(state.quarantined_conflicts)

    for field, new_val in new_fields.items():
        if new_val is None:
            continue

        if field == "crops":
            existing_crops = updated_confirmed.get("crops", [])
            merged_crops = list(existing_crops)
            seen = set(existing_crops)
            for c in new_val:
                if c not in seen:
                    merged_crops.append(c)
                    seen.add(c)
            updated_confirmed["crops"] = merged_crops

        else:
            if field in updated_confirmed:
                old_val = updated_confirmed[field]
                # Compare scalars
                if old_val != new_val:
                    # Conflict detected - quarantine without overwriting
                    updated_conflicts.append({
                        "field": field,
                        "old_value": old_val,
                        "new_value": new_val,
                        "turn": state.turn_count,
                    })
                # If old_val == new_val, no conflict, keep value
            else:
                updated_confirmed[field] = new_val

    return state.model_copy(
        update={
            "confirmed_profile": updated_confirmed,
            "quarantined_conflicts": updated_conflicts,
        }
    )


def get_missing_slots(state: ConversationState) -> List[str]:
    """Identifies which mandatory slots are still missing from the confirmed profile."""
    missing: List[str] = []
    profile = state.confirmed_profile

    for slot in REQUIRED_SLOTS:
        val = profile.get(slot)
        if val is None:
            missing.append(slot)
        elif slot == "crops" and (not isinstance(val, list) or len(val) == 0):
            missing.append(slot)
        elif slot == "land_acres" and (not isinstance(val, (int, float)) or val <= 0):
            missing.append(slot)
        elif isinstance(val, str) and not val.strip():
            missing.append(slot)

    return missing


def is_profile_complete(state: ConversationState) -> bool:
    """Returns True if all mandatory profile slots are populated."""
    return len(get_missing_slots(state)) == 0


def add_turn(state: ConversationState, role: str, content: str) -> ConversationState:
    """Appends an interaction turn to history and trims to the last 6 turns."""
    new_history = list(state.turn_history)
    new_history.append({"role": role, "content": content})
    if len(new_history) > 6:
        new_history = new_history[-6:]

    return state.model_copy(
        update={
            "turn_history": new_history,
            "turn_count": state.turn_count + 1,
        }
    )
