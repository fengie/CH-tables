import unittest

from ch_tables.codex_skill_ingest import (
    parse_skills_html, parse_integer, parse_stat_pair
)


class CodexSkillIngestTests(unittest.TestCase):
    def test_parse_math_and_skill_scaling_without_inventing_ranks(self):
        html = """<html><body>
            <h3>Quick Strike</h3>
            <div>Enemy Pierce Physical</div>
            <div>Cooldown: 10s (6s) | Cast: 0s | Lockout: 0.01s</div>
            <div>Cunning</div><div>2,400 (4,950)</div>
            <div>Strength</div><div>710 (4,062)</div>
            <div>Max Damage</div><div>11,766</div>
            <div>Base Skill</div><div>6,457</div>
            <div>Direct Dmg</div><div>5,309</div>
            <div>Avg Damage</div><div>9,998</div>
            <h3>Shadowstrike</h3>
            <div>Cooldown: 12s | Cast: 0s</div>
            <div>Cunning</div><div>2,400 (5,650)</div>
            <div>Dexterity</div><div>5 (1,537)</div>
            <div>Max Damage</div><div>7,022</div>
            </body></html>"""
        x = parse_skills_html(html, "https://example.com/test")
        self.assertEqual(len(x), 2)
        self.assertEqual(x[0]["skill_name"], "Quick Strike")
        self.assertEqual(x[0]["numeric_metrics"]["Max Damage"], 11766)
        self.assertEqual(x[0]["skill_ability"]["value"]["effective"], 4950)
        self.assertEqual(x[0]["scaling_attribute"]["stat"], "Strength")
        self.assertEqual(x[0]["scaling_attribute"]["value"]["effective"], 4062)
        self.assertEqual(x[1]["scaling_attribute"]["stat"], "Dexterity")

    def test_split_dom_tokens_capture_effective_and_duration(self):
        html = """<html><body><h3>Quick Strike</h3>
          <span>Cooldown:</span><span>10s</span><span>(6s)</span>
          <span>Cast:</span><span>0s</span><span>Lockout:</span><span>0.01s</span>
          <span>Cunning</span><span>2,400</span><span>(4,950)</span>
          <span>Strength</span><span>710</span><span>(4,062)</span>
          <div>Max Damage</div><div>11,766</div>
          <div>Dmg Lost</div><div>140</div>
          <div>Dmg Lost</div><div>200,000</div></body></html>"""
        data = parse_skills_html(html, "https://example.com/rogue")
        self.assertEqual(len(data), 1)
        got = data[0]
        self.assertEqual(got["skill_ability"]["value"]["effective"], 4950)
        self.assertEqual(got["scaling_attribute"]["value"]["effective"], 4062)
        self.assertEqual(got["timing_s"]["cooldown_s"], 10)
        self.assertEqual(got["timing_s"]["effective_cooldown_s"], 6)
        self.assertEqual(got["timing_s"]["cast_s"], 0)
        self.assertAlmostEqual(got["timing_s"]["lockout_s"], 0.01)
        self.assertEqual(got["numeric_metrics"]["Dmg Lost"], 140)
        self.assertEqual(got["additional_metric_occurrences"]["Dmg Lost"], [200000])

    def test_invalid_metadata_is_not_modeled(self):
        self.assertEqual(parse_integer("1,000"), 1000)
        self.assertIsNone(parse_integer("Unknown"))
        self.assertIsNone(parse_stat_pair("unknown"))
        self.assertEqual(parse_skills_html("<h3>No Value</h3><div>Cooldown: 5s</div>",
                                          "https://example.com/test"), [])


if __name__ == "__main__":
    unittest.main()
