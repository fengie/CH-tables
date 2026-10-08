import unittest
from ch_tables.skill_priorities import snapshot_comparison


class SkillPrioritiesTests(unittest.TestCase):
    def test_isolated_per_build_and_observation_rank(self):
        items = [
            {"source_url": "https://test.example/build-a", "skill_name": "Fast",
             "timing_s": {"effective_cooldown_s": 5, "cooldown_s": 10},
             "numeric_metrics": {"Avg Damage": 1000, "Dmg Lost": 200}},
            {"source_url": "https://test.example/build-a", "skill_name": "Slow",
             "timing_s": {"cooldown_s": 10},
             "numeric_metrics": {"Avg Damage": 1200}},
            {"source_url": "https://test.example/build-b", "skill_name": "Huge",
             "timing_s": {"cooldown_s": 5},
             "numeric_metrics": {"Avg Damage": 90000}},
        ]
        output = snapshot_comparison(items)
        self.assertEqual(len(output), 2)
        x = output["https://test.example/build-a"]["by_gross_damage_cooldown"]
        self.assertEqual(x[0]["skill"], "Fast")
        self.assertEqual(x[0]["gross_damage_per_cooldown_s"], 200)
        self.assertEqual(x[0]["codex_net_after_reported_lost_auto"], 160)
        self.assertIsNone(x[1]["codex_net_after_reported_lost_auto"])
        self.assertFalse(x[0]["strictly_comparable_to_other_characters"])

    def test_does_not_make_false_dps_from_invalid_cooldown(self):
        result = snapshot_comparison([{"source_url": "x", "skill_name": "A",
                                       "timing_s": {"cooldown_s": 0},
                                       "numeric_metrics": {"Avg Damage": 500}}])
        self.assertEqual(result, {})


if __name__ == "__main__":
    unittest.main()
