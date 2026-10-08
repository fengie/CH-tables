"""Regression coverage for the sourced CH skill/ability reference module."""

import math
import unittest

from ch_tables.skill_reference import (
    ABILITIES, ROGUE_ROTATION_BASELINE, SKILL_ROWS, attack,
    compare_flat_damage, defence, displayed_damage, energy,
    health, lookup_skill, skills_for, validate_reference,
)


class SkillReferenceTests(unittest.TestCase):
    def test_catalog_invariants(self):
        validate_reference()
        self.assertEqual(sum(map(len, SKILL_ROWS.values())), 93)
        self.assertEqual(sum(map(len, ABILITIES.values())), 43)
        for group in ("Warrior", "Ranger", "Mage", "Druid", "Rogue"):
            self.assertGreater(len(skills_for(group)), 10)

    def test_rogue_scaling_is_stat_specific(self):
        expected = {
            "ss": ("Dexterity", "Cunning"),
            "qs": ("Strength", "Cunning"),
            "ls": ("Dexterity", "Cunning"),
            "Rend": ("Strength", "Cunning"),
            "Smoke Bomb": ("Dexterity", "Cunning"),
            "Expose": ("Dexterity", "Cunning"),
            "Double Attack": (None, None),
        }
        for name, (stat, ability) in expected.items():
            with self.subTest(name=name):
                skill = lookup_skill(name)
                self.assertEqual((skill.scaling_stat, skill.skill_ability),
                                 (stat, ability))

    def test_no_dagger_ability_assumed_for_knuckles(self):
        self.assertEqual(attack(1000, 3000, 600), 4600)
        # Only ACTIVE mainhand weapon ability is passed; dagger ability
        # from a different weapon is neither added nor substituted.
        self.assertNotEqual(attack(1000, 3000), attack(1000, 8000))

    def test_community_stats_formulas(self):
        self.assertEqual(defence(1000, 100), 2100)
        self.assertAlmostEqual(health(100, 100), 725.05)
        self.assertAlmostEqual(energy(100, 10, 50), 649.95)
        self.assertAlmostEqual(
            displayed_damage(100, 100, 100, 390),
            (0.159132 * 10 + 0.05972 * 10 + 0.96523) * 100 + 390,
        )

    def test_increments_and_fail_closed_high_str(self):
        old = displayed_damage(500, 1000, 100, 0)
        self.assertGreater(
            compare_flat_damage(500, 1000, 100, 0,
                                500, 1000, 100, 390), 389.99
        )
        self.assertGreater(displayed_damage(500, 1000, 101, 0), old)
        with self.assertRaisesRegex(ValueError, "revalidation"):
            displayed_damage(3001, 1000, 100, 0)
        with self.assertRaises(ValueError):
            displayed_damage(-1, 1000, 100, 0)

    def test_snapshot_has_provenance_of_numeric_timings(self):
        for name in ("Shadowstrike", "Quick Strike", "Life Steal",
                     "Rend", "Double Attack"):
            with self.subTest(name=name):
                d = ROGUE_ROTATION_BASELINE[name]
                self.assertGreater(d["cooldown"], 0)
                self.assertGreaterEqual(d["cast"], 0)
                self.assertGreaterEqual(d["lockout"], 0)
        for name in ("Smoke Bomb", "Expose Weakness"):
            self.assertIsNone(ROGUE_ROTATION_BASELINE[name]["cooldown"])

    def test_lookup_rejects_unverified_skills(self):
        with self.assertRaises(KeyError):
            lookup_skill("Imaginary Skill")
        with self.assertRaises(ValueError):
            skills_for("Paladin")


if __name__ == "__main__":
    unittest.main()
