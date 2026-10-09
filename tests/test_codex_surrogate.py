"""Leakage, provenance and numerical checks for Codex panel surrogate."""
import unittest
import json
from pathlib import Path
from dataclasses import replace
from ch_tables.codex_surrogate import (Panel, RatioPrior, read_panels,
                                        validate_by_build, calibrate)

URL = "https://the-codex.ch/damagebuilder/"

def toy():
    snapshots = [{"url": URL + str(i)} for i in range(3)]
    samples = []
    for i, ratio in enumerate((.8, .9, .7)):
        for name, maximum in (("Quick Strike", 100.0), ("Rend", 200.0)):
            samples.append({"source_url": snapshots[i]["url"],
                            "skill_name": name,
                            "model_provenance": "single_saved_build_not_engine_coefficients",
                            "numeric_metrics": {"Max Damage": maximum,
                                                "Avg Damage": maximum * ratio}})
    return {"schema": 1, "collected_on": "2026-10-08", "snapshots": snapshots,
            "observations": samples}

class SurrogateTests(unittest.TestCase):
    def test_explicit_ratios_and_skill_fallback(self):
        rows = (Panel(URL+"a", "Quick", 100, 80),
                Panel(URL+"b", "Quick", 200, 180),
                Panel(URL+"c", "Different", 20, 14))
        m = RatioPrior.fit(rows)
        self.assertAlmostEqual(m.predict("Quick", 50)["predicted_codex_avg_damage"], 42.5)
        self.assertEqual(m.predict("Unknown", 100)["estimator"], "all_skill_global_median")
        self.assertEqual(m.predict("Unknown", 100)["other_build_skill_examples"], 0)

    def test_group_held_out_not_row_held_out(self):
        d = toy()
        p = read_panels(d)
        result = validate_by_build(p)
        self.assertEqual(result["independent_build_groups"], 3)
        self.assertEqual(result["usable_panel_rows"], 6)
        # 100% accuracy would mean the held-out build's own ratio was leaked.
        self.assertGreater(result["skill_aware"]["mape_pct"], 0)
        self.assertEqual(sum(x["n"] for x in result["by_heldout_build"]), 6)

    def test_missing_panel_value_skipped_not_fake_zero(self):
        d = toy()
        del d["observations"][0]["numeric_metrics"]["Avg Damage"]
        self.assertEqual(len(read_panels(d)), 5)

    def test_bad_source_and_duplicate_build_skill_fail_closed(self):
        d = toy()
        d["observations"][0]["source_url"] = "https://evil.example/path"
        with self.assertRaisesRegex(ValueError, "Unrecognized build"):
            read_panels(d)
        d = toy()
        d["observations"].append(dict(d["observations"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate skill"):
            read_panels(d)

    def test_nonfinite_bool_negative_and_provenance_rejected(self):
        for bad in (True, 0, float('nan'), float('inf'), -1):
            d=toy()
            d["observations"][0]["numeric_metrics"]["Max Damage"] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                read_panels(d)
        d = toy()
        d["observations"][0]["model_provenance"] = "observed_game_hit"
        with self.assertRaisesRegex(ValueError, "provenance"):
            read_panels(d)

    def test_calibrate_provenance_digest_and_reproducibility(self):
        a, b = calibrate(toy()), calibrate(toy())
        self.assertEqual(a, b)
        self.assertEqual(a["scope"], "CODEX_PANEL_ONLY_NOT_LIVE_DPS")
        self.assertEqual(len(a["input_sha256"]), 64)
        self.assertGreater(a["validation"]["skill_aware"]["mape_pct"], 0)

    def test_prediction_requires_known_positive_max_damage(self):
        m = RatioPrior.fit(read_panels(toy()))
        for bad in (0, -2, float("nan"), None, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                m.predict("Quick Strike", bad)

    def test_pinned_codex_12_build_snapshot_grouped_cv(self):
        dataset = (Path(__file__).resolve().parents[1] / 'data' / 'reference' /
                   'codex_skill_panel_observations.json')
        if not dataset.exists():
            self.skipTest('Pinned snapshot supplied by owning repository')
        report = calibrate(json.loads(dataset.read_text(encoding='utf8')))
        cv = report['validation']
        self.assertEqual(cv['independent_build_groups'], 12)
        self.assertEqual(cv['usable_panel_rows'], 117)
        # These are Codex Max -> Codex Avg errors, NOT actual game DPS.
        self.assertAlmostEqual(cv['skill_aware']['mape_pct'], 4.030072, places=3)
        self.assertAlmostEqual(cv['global_median_baseline']['mape_pct'], 5.122837, places=3)
        self.assertGreater(cv['unseen_build_max_damage_transfer_diagnostic']['mape_pct'], 40)
        self.assertLess(cv['skill_aware']['within_5pct_pct'], 70)

    def test_short_group_inventory_rejected(self):
        rows = tuple(r for r in read_panels(toy()) if r.build != URL+"2")
        with self.assertRaisesRegex(ValueError, "3 independent"):
            validate_by_build(rows)

if __name__ == "__main__":
    unittest.main()
