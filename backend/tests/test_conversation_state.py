"""
Unit tests for ConversationState and conflict-aware merge policies.
Verifies immutability, conflict quarantine, set union for crops, missing slots, and JSON serialization.
"""

import unittest
from backend.conversation.state import (
    ConversationState,
    merge_extraction,
    get_missing_slots,
    is_profile_complete,
    add_turn,
    REQUIRED_SLOTS,
)


class TestConversationState(unittest.TestCase):
    def setUp(self):
        self.state = ConversationState(session_id="test_session_123")

    def test_initial_state_empty(self):
        self.assertEqual(self.state.session_id, "test_session_123")
        self.assertEqual(len(self.state.confirmed_profile), 0)
        self.assertEqual(len(self.state.quarantined_conflicts), 0)
        self.assertEqual(self.state.turn_count, 0)
        self.assertEqual(len(self.state.turn_history), 0)

    def test_merge_new_scalars(self):
        updated = merge_extraction(self.state, {"land_acres": 3.0, "district": "Dharwad"})
        self.assertEqual(updated.confirmed_profile["land_acres"], 3.0)
        self.assertEqual(updated.confirmed_profile["district"], "Dharwad")
        self.assertEqual(len(updated.quarantined_conflicts), 0)

    def test_none_never_overwrites_confirmed_value(self):
        s1 = merge_extraction(self.state, {"land_acres": 4.5, "irrigation_type": "Borewell"})
        s2 = merge_extraction(s1, {"land_acres": None, "district": "Mandya"})
        self.assertEqual(s2.confirmed_profile["land_acres"], 4.5)
        self.assertEqual(s2.confirmed_profile["irrigation_type"], "Borewell")
        self.assertEqual(s2.confirmed_profile["district"], "Mandya")

    def test_crops_set_union(self):
        s1 = merge_extraction(self.state, {"crops": ["Ragi"]})
        s2 = merge_extraction(s1, {"crops": ["Paddy", "Ragi"]})
        self.assertEqual(s2.confirmed_profile["crops"], ["Ragi", "Paddy"])

    def test_crops_set_union_empty_initially(self):
        s = merge_extraction(self.state, {"crops": ["Jowar", "Cotton"]})
        self.assertEqual(s.confirmed_profile["crops"], ["Jowar", "Cotton"])

    def test_conflicting_scalar_is_quarantined(self):
        s1 = merge_extraction(self.state, {"land_acres": 3.0})
        s2 = merge_extraction(s1, {"land_acres": 5.0})
        # Original value preserved
        self.assertEqual(s2.confirmed_profile["land_acres"], 3.0)
        # Conflict logged
        self.assertEqual(len(s2.quarantined_conflicts), 1)
        conflict = s2.quarantined_conflicts[0]
        self.assertEqual(conflict["field"], "land_acres")
        self.assertEqual(conflict["old_value"], 3.0)
        self.assertEqual(conflict["new_value"], 5.0)

    def test_matching_scalar_causes_no_conflict(self):
        s1 = merge_extraction(self.state, {"irrigation_type": "Borewell"})
        s2 = merge_extraction(s1, {"irrigation_type": "Borewell"})
        self.assertEqual(s2.confirmed_profile["irrigation_type"], "Borewell")
        self.assertEqual(len(s2.quarantined_conflicts), 0)

    def test_get_missing_slots_all_missing(self):
        missing = get_missing_slots(self.state)
        self.assertEqual(set(missing), set(REQUIRED_SLOTS))
        self.assertFalse(is_profile_complete(self.state))

    def test_get_missing_slots_partial(self):
        s = merge_extraction(self.state, {"land_acres": 2.0, "crops": ["Ragi"]})
        missing = get_missing_slots(s)
        self.assertEqual(set(missing), {"irrigation_type", "district"})
        self.assertFalse(is_profile_complete(s))

    def test_is_profile_complete_true_when_all_populated(self):
        s = merge_extraction(
            self.state,
            {
                "land_acres": 2.5,
                "crops": ["Ragi"],
                "irrigation_type": "Rainfed",
                "district": "Tumkur",
            },
        )
        self.assertEqual(len(get_missing_slots(s)), 0)
        self.assertTrue(is_profile_complete(s))

    def test_empty_crops_list_considered_missing(self):
        s = merge_extraction(
            self.state,
            {
                "land_acres": 2.5,
                "crops": [],
                "irrigation_type": "Rainfed",
                "district": "Tumkur",
            },
        )
        self.assertIn("crops", get_missing_slots(s))
        self.assertFalse(is_profile_complete(s))

    def test_zero_acres_considered_missing(self):
        s = merge_extraction(
            self.state,
            {
                "land_acres": 0.0,
                "crops": ["Ragi"],
                "irrigation_type": "Rainfed",
                "district": "Tumkur",
            },
        )
        self.assertIn("land_acres", get_missing_slots(s))

    def test_turn_history_append_and_trim(self):
        s = self.state
        for i in range(10):
            s = add_turn(s, "user", f"Utterance {i}")
            s = add_turn(s, "assistant", f"Response {i}")

        self.assertEqual(s.turn_count, 20)
        self.assertEqual(len(s.turn_history), 6)
        self.assertEqual(s.turn_history[-1]["content"], "Response 9")
        self.assertEqual(s.turn_history[-2]["content"], "Utterance 9")

    def test_empty_merge_does_not_corrupt_state(self):
        s1 = merge_extraction(self.state, {"district": "Belagavi"})
        s2 = merge_extraction(s1, {})
        self.assertEqual(s2.confirmed_profile["district"], "Belagavi")
        self.assertEqual(len(s2.quarantined_conflicts), 0)

    def test_json_serialization_roundtrip(self):
        s = merge_extraction(
            self.state,
            {
                "land_acres": 3.0,
                "crops": ["Pigeon Pea (Togari)"],
                "district": "Kalaburagi",
            },
        )
        s = add_turn(s, "user", "ನಮ್ಮ ಹೊಲ 3 ಎಕರೆ")
        json_data = s.model_dump_json()
        loaded = ConversationState.model_validate_json(json_data)
        self.assertEqual(loaded.session_id, s.session_id)
        self.assertEqual(loaded.confirmed_profile, s.confirmed_profile)
        self.assertEqual(loaded.turn_history, s.turn_history)
        self.assertEqual(loaded.turn_count, s.turn_count)


if __name__ == "__main__":
    unittest.main()
