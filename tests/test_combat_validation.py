"""Synthetic source-identity and blinded-session regressions; not game proof."""
import unittest

from ch_tables.combat_simulator import encounter_from_dict
from ch_tables.combat_validation import (
    evaluate_holdout, load_observations, scenario_digest,
)


def bundle(scenario, *, kind="synthetic"):
    digest = scenario_digest(scenario)
    return {
        "schema_version": 1, "evidence_kind": kind, "patch_id": "toy-patch",
        "boss_id": "toy-boss", "build_id": "anonymous-toy-rogue",
        "scenario_sha256": digest, "frozen_model_sha256": digest,
        "sessions": [
            {"session_id": f"s{i}", "recording_sha256": format(i + 1, "064x"),
             "duration_s": 10, "elapsed_s": 10, "total_damage": 50,
             "end_reason": "time_limit", "hp_potions": 0,
             "energy_potions": 0, "split": "calibration" if i == 0 else "holdout"}
            for i in range(3)
        ],
    }


class CombatValidationTests(unittest.TestCase):
    def setUp(self):
        self.scenario = {"duration_s": 10, "max_hp": 100, "max_energy": 0,
                         "auto": {"interval_s": 2, "damage": 10}}
        self.encounter = encounter_from_dict(self.scenario)

    def test_deterministic_holdout_and_excludes_calibration_sessions(self):
        raw = bundle(self.scenario)
        raw["sessions"][0]["total_damage"] = 1000000  # not included
        result = evaluate_holdout(self.encounter, self.scenario,
                                  load_observations(raw), seeds=16)
        self.assertEqual(result["status"], "synthetic_regression_only")
        self.assertEqual(result["n_heldout_sessions"], 2)
        self.assertEqual(result["n_calibration_sessions_excluded"], 1)
        self.assertEqual(result["metrics"]["fixed_window_dps"]["model_mean"], 5)
        self.assertEqual(result["metrics"]["fixed_window_dps"]["holdout_mae_vs_simulated_mean"], 0)
        self.assertEqual(result, evaluate_holdout(self.encounter, self.scenario,
                                                 load_observations(raw), seeds=16))

    def test_digest_canonical_and_mismatch_fails(self):
        self.assertEqual(scenario_digest({"z": 1, "a": 2}),
                         scenario_digest({"a": 2, "z": 1}))
        raw = bundle(self.scenario)
        with self.assertRaisesRegex(ValueError, "Scenario changed"):
            evaluate_holdout(self.encounter, {**self.scenario, "max_hp": 101},
                             load_observations(raw), seeds=2)
        raw["frozen_model_sha256"] = "a" * 64
        with self.assertRaisesRegex(ValueError, "Frozen model"):
            evaluate_holdout(self.encounter, self.scenario,
                             load_observations(raw), seeds=2)

    def test_duplicate_sessions_and_recordings_fail(self):
        raw = bundle(self.scenario)
        raw["sessions"][2]["session_id"] = "s1"
        with self.assertRaisesRegex(ValueError, "session ID"):
            load_observations(raw)
        raw = bundle(self.scenario)
        raw["sessions"][2]["recording_sha256"] = raw["sessions"][1]["recording_sha256"]
        with self.assertRaisesRegex(ValueError, "Repeated recording"):
            load_observations(raw)

    def test_invalid_numeric_boolean_and_time_limits_fail(self):
        for field, bad in (("duration_s", 0), ("total_damage", -1),
                           ("elapsed_s", 11), ("hp_potions", True),
                           ("energy_potions", -1)):
            with self.subTest(field=field):
                raw = bundle(self.scenario)
                raw["sessions"][1][field] = bad
                with self.assertRaises(ValueError):
                    load_observations(raw)

    def test_end_reason_and_fixed_window_consistency(self):
        raw = bundle(self.scenario)
        raw["sessions"][1]["elapsed_s"] = 9
        with self.assertRaisesRegex(ValueError, "full elapsed"):
            load_observations(raw)
        raw = bundle(self.scenario)
        raw["sessions"][1]["end_reason"] = "unknown"
        with self.assertRaisesRegex(ValueError, "end reason"):
            load_observations(raw)

    def test_same_horizon_and_explicit_game_provenance_required(self):
        raw = bundle(self.scenario)
        raw["sessions"][1]["duration_s"] = 9
        raw["sessions"][1]["elapsed_s"] = 9
        with self.assertRaisesRegex(ValueError, "windows"):
            load_observations(raw)
        raw = bundle(self.scenario, kind="recorded_gameplay")
        with self.assertRaisesRegex(ValueError, "sourced observed"):
            evaluate_holdout(self.encounter, self.scenario,
                             load_observations(raw), seeds=2)

    def test_unknown_fields_and_empty_holdout_rejected(self):
        raw = bundle(self.scenario)
        raw["sessions"][1]["user_handle"] = "Do not collect this"
        with self.assertRaisesRegex(ValueError, "session field schema"):
            load_observations(raw)
        raw = bundle(self.scenario)
        for row in raw["sessions"]:
            row["split"] = "calibration"
        with self.assertRaisesRegex(ValueError, "held-out"):
            load_observations(raw)

    def test_explicit_split_and_strict_schema_version(self):
        raw = bundle(self.scenario)
        del raw["sessions"][1]["split"]
        with self.assertRaises(ValueError):
            load_observations(raw)
        raw = bundle(self.scenario)
        raw["schema_version"] = True
        with self.assertRaises(ValueError):
            load_observations(raw)

    def test_seed_count_and_scenario_types(self):
        raw = load_observations(bundle(self.scenario))
        for n in (True, 1, 513, 2.0):
            with self.subTest(n=n), self.assertRaises(ValueError):
                evaluate_holdout(self.encounter, self.scenario, raw, seeds=n)
        with self.assertRaises(ValueError):
            scenario_digest([])


if __name__ == "__main__":
    unittest.main()
