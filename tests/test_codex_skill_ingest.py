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

    def test_invalid_metadata_is_not_modeled(self):
        self.assertEqual(parse_integer("1,000"), 1000)
        self.assertIsNone(parse_integer("Unknown"))
        self.assertIsNone(parse_stat_pair("unknown"))
        self.assertEqual(parse_skills_html("<h3>No Value</h3><div>Cooldown: 5s</div>",
                                          "https://example.com/test"), [])


if __name__ == "__main__":
    unittest.main()
