"""Offline intake regressions; fixtures are synthetic, never gameplay claims."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ch_tables.combat_evidence import ingest, _transcript
from ch_tables.combat_validation import load_observations, evaluate_holdout
from ch_tables.combat_simulator import encounter_from_dict


class CombatEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.scenario = {"duration_s": 10, "max_hp": 100, "max_energy": 0,
                         "auto": {"interval_s": 2, "damage": 10},
                         "evidence": "synthetic"}
        self.scenario_file = self.write("scenario.json", self.scenario)
        self.manifest = {
            "schema_version": 1, "evidence_kind": "synthetic",
            "patch_id": "synthetic", "boss_id": "toy-boss", "build_id": "toy-build",
            "sessions": [
                {"session_id": "cal-1", "split": "calibration",
                 "recording_file": "capture-a.txt", "transcript_file": "events-a.json"},
                {"session_id": "hold-1", "split": "holdout",
                 "recording_file": "capture-b.txt", "transcript_file": "events-b.json"},
            ]}
        for n in ("a", "b"):
            (self.root / f"capture-{n}.txt").write_bytes(("synthetic recording " + n).encode())
        self.write("events-a.json", self.trace(8))
        self.write("events-b.json", self.trace(13))
        self.manifest_file = self.write("manifest.json", self.manifest)

    def write(self, name, data):
        p = self.root / name
        p.write_text(json.dumps(data), encoding="utf-8")
        return p

    @staticmethod
    def trace(dmg):
        return {"schema_version": 1, "duration_s": 10, "events": [
            {"t_s": 1, "type": "auto_damage", "amount": dmg},
            {"t_s": 3, "type": "hp_potion"},
            {"t_s": 10, "type": "window_end"}]}

    def get(self):
        return ingest(self.manifest_file, self.scenario_file)

    def test_intake_preserves_real_source_hashes_and_excludes_incoming_damage(self):
        b, r = self.get()
        load_observations(b)
        self.assertEqual([x["total_damage"] for x in b["sessions"]], [8, 13])
        self.assertEqual([x["hp_potions"] for x in b["sessions"]], [1, 1])
        self.assertEqual(b["sessions"][0]["recording_sha256"], hashlib.sha256(b"synthetic recording a").hexdigest())
        self.assertEqual(r["session_receipts"][0]["recording_sha256"], b["sessions"][0]["recording_sha256"])
        self.assertNotIn("capture-a.txt", json.dumps((b,r)))  # No source file path leaks
        self.assertEqual(b["evidence_kind"], "synthetic")
        self.assertEqual(b["scenario_sha256"], b["frozen_model_sha256"])
        self.assertEqual(r["session_receipts"][1]["events"], 3)

    def test_generated_bundle_runs_through_existing_holdout_evaluator(self):
        bundle, _ = self.get()
        result = evaluate_holdout(encounter_from_dict(self.scenario), self.scenario,
                                  load_observations(bundle), seeds=4)
        self.assertEqual(result["status"], "synthetic_regression_only")
        self.assertEqual(result["n_heldout_sessions"], 1)
        self.assertEqual(result["n_calibration_sessions_excluded"], 1)

    def test_death_terminates_window_and_tracks_damage_breakdown(self):
        raw = {"schema_version": 1, "duration_s": 10, "events": [
            {"t_s": 1, "type": "enemy_damage", "amount": 50},
            {"t_s": 2, "type": "pet_damage", "amount": 7},
            {"t_s": 2, "type": "skill_damage", "amount": 20},
            {"t_s": 3, "type": "energy_potion"},
            {"t_s": 4, "type": "player_died"}]}
        self.write("events-b.json", raw)
        b, r = self.get()
        self.assertEqual(b["sessions"][1]["end_reason"], "player_died")
        self.assertEqual(b["sessions"][1]["elapsed_s"], 4)
        self.assertEqual(b["sessions"][1]["total_damage"], 27)
        self.assertEqual(b["sessions"][1]["energy_potions"], 1)
        self.assertEqual(r["session_receipts"][1]["enemy_damage"], 50)

    def test_rejects_unsourced_real_claim(self):
        self.manifest["evidence_kind"] = "recorded_gameplay"
        self.write("manifest.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "sourced, observed"):
            self.get()

    def test_recorded_mode_requires_observed_sourced_scenario(self):
        self.scenario["evidence"] = "observed"
        self.scenario["source_url"] = "https://example.com/source"
        self.write("scenario.json", self.scenario)
        self.manifest["evidence_kind"] = "recorded_gameplay"
        self.write("manifest.json", self.manifest)
        self.assertEqual(self.get()[0]["evidence_kind"], "recorded_gameplay")

    def test_window_missing_or_early(self):
        for ending in ({"t_s": 9, "type": "window_end"}, None):
            with self.subTest(ending=ending):
                t = self.trace(8)
                t["events"][-1:] = [ending] if ending else []
                with self.assertRaises(ValueError):
                    _transcript(t, 10)

    def test_after_terminal_event_rejected(self):
        t = self.trace(8)
        t["events"].append({"t_s": 10, "type": "hp_potion"})
        with self.assertRaisesRegex(ValueError, "after terminal"):
            _transcript(t, 10)

    def test_event_timestamps_ordered_and_inside_window(self):
        for at in (-1, float("nan"), 11, 0.5, True):
            with self.subTest(at=at):
                t = self.trace(8)
                t["events"][1]["t_s"] = at
                with self.assertRaises(ValueError):
                    _transcript(t, 10)

    def test_strict_event_schema_no_implicit_damage(self):
        for mutation in (
            lambda e: e.update(amount=99),
            lambda e: e.update(player_name="secret"),
            lambda e: e.pop("t_s"),
            lambda e: e.update(type="unknown"),
        ):
            with self.subTest(mutation=mutation):
                t = self.trace(8)
                mutation(t["events"][1])
                with self.assertRaises(ValueError):
                    _transcript(t, 10)

    def test_rejects_invalid_damage_and_boolean(self):
        for dmg in (float("inf"), -1, True):
            with self.subTest(dmg=dmg):
                with self.assertRaises(ValueError):
                    _transcript(self.trace(dmg), 10)

    def test_rejects_unknown_or_duplicate_recordings(self):
        self.manifest["sessions"][1]["recording_file"] = "capture-a.txt"
        self.write("manifest.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "Repeated recording"):
            self.get()

    def test_rejects_duplicate_transcription_even_different_recordings(self):
        self.write("events-b.json", self.trace(8))
        with self.assertRaisesRegex(ValueError, "Duplicate transcript"):
            self.get()

    def test_rejects_parent_path_and_symlink_escape(self):
        for bad in ("../recording.txt", "/tmp/source.txt"):
            with self.subTest(bad=bad):
                self.manifest["sessions"][0]["recording_file"] = bad
                self.write("manifest.json", self.manifest)
                with self.assertRaisesRegex(ValueError, "relative"):
                    self.get()
        self.manifest["sessions"][0]["recording_file"] = "escape"
        (self.root / "escape").symlink_to(self.scenario_file.resolve().parent.parent / "nowhere")
        self.write("manifest.json", self.manifest)
        with self.assertRaises((ValueError, FileNotFoundError)):
            self.get()

    def test_rejects_hidden_fields_and_missing_holdout(self):
        self.manifest["owner_email"] = "not permitted"
        self.write("manifest.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "manifest schema"):
            self.get()
        del self.manifest["owner_email"]
        self.manifest["sessions"][1]["split"] = "calibration"
        self.write("manifest.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "held-out"):
            self.get()

    def test_rejects_inconsistent_window_and_extra_session_field(self):
        t = self.trace(8)
        t["duration_s"] = 11
        self.write("events-a.json", t)
        with self.assertRaisesRegex(ValueError, "window differs"):
            self.get()
        self.write("events-a.json", self.trace(8))
        self.manifest["sessions"][0]["gear_name"] = "private"
        self.write("manifest.json", self.manifest)
        with self.assertRaisesRegex(ValueError, "Session must"):
            self.get()

    def test_nonfinite_json_and_empty_files_rejected(self):
        self.write("events-a.json", self.trace(8))
        (self.root / "events-a.json").write_text('{"duration_s":NaN}')
        with self.assertRaises(ValueError):
            self.get()
        (self.root / "capture-a.txt").write_bytes(b"")
        self.write("events-a.json", self.trace(8))
        with self.assertRaisesRegex(ValueError, "empty or"):
            self.get()

    def test_model_does_not_allow_recorded_source_for_synthetic_manifest(self):
        self.scenario.update(evidence="observed", source_url="https://example.com")
        self.write("scenario.json", self.scenario)
        with self.assertRaisesRegex(ValueError, "synthetic scenario"):
            self.get()

    def test_source_hash_changes_with_source_bytes(self):
        b1, _ = self.get()
        (self.root / "capture-a.txt").write_bytes(b"different synthetic bytes")
        b2, _ = self.get()
        self.assertNotEqual(b1["sessions"][0]["recording_sha256"], b2["sessions"][0]["recording_sha256"])


if __name__ == "__main__":
    unittest.main()