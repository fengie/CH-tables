"""Exact point allocation and per-skill swaps, tested against tiny brute force."""
import unittest
from itertools import product

from ch_tables.build_planner import (
    Skill, SkillRank, Swap, Preferences, optimize, compare_playstyles,
    skill_point_budget, level_skill_cap, options_for_skill,
)


def rank(n, damage, cooldown=10, occupied=0):
    return SkillRank(
        n, damage, cooldown, occupied,
        evidence_kind="user_estimate",
    )


class BuildPlannerTests(unittest.TestCase):
    def test_level_caps_historical_and_explicit_user_overrides(self):
        cases = {
            1: 5, 14: 5, 15: 10, 29: 10, 30: 15,
            59: 15, 60: 20, 90: 25, 120: 30,
            150: 35, 180: 40, 210: 45, 240: 50,
        }
        for level, expected in cases.items():
            self.assertEqual(level_skill_cap(level), expected)
        self.assertEqual(level_skill_cap(220, override=50), 50)
        self.assertEqual(skill_point_budget(220), 219)
        self.assertEqual(skill_point_budget(220, bonus_points=3), 222)
        self.assertEqual(skill_point_budget(220, override=250), 250)
        with self.assertRaises(ValueError):
            level_skill_cap(0)

    def test_player_custom_max_swaps_per_skill_and_rank_cap(self):
        main = Skill("Quick Strike", {5: rank(5, 500), 10: rank(10, 1100)})
        swaps = [
            Swap("ring", "ring1", bonus_levels=5, release_status="released_documented"),
            Swap("charm", "charm", bonus_levels=5, release_status="released_documented"),
            Swap("unknown", "bracelet", bonus_levels=5, release_status="unverified"),
        ]
        cfg = Preferences(level=220, max_swaps_per_skill=1,
                          skill_points_available=10)
        options = options_for_skill(main, swaps, cfg, 10)
        self.assertFalse(any(x.swap_count > 1 for x in options))
        self.assertFalse(any("unknown" in x.swap_item_ids for x in options))
        self.assertTrue(any(x.points == 5 and x.effective_rank == 10
                            for x in options))
        cfg = Preferences(level=220, max_swaps_per_skill=3,
                          per_skill_swap_limit={"Quick Strike": 1},
                          skill_points_available=10)
        self.assertFalse(any(x.swap_count > 1 for x in
                             options_for_skill(main, swaps, cfg, 10)))

    def test_does_not_duplicate_same_equipment_slot(self):
        ability = Skill("Rend", {10: rank(10, 2000)})
        swaps = [
            Swap("ring_a", "ring", bonus_levels=5, release_status="released_documented"),
            Swap("ring_b", "ring", bonus_levels=5, release_status="released_documented"),
        ]
        prefs = Preferences(level=220, max_swaps_per_skill=2,
                            skill_points_available=10)
        opts = options_for_skill(ability, swaps, prefs, 10)
        self.assertTrue(opts)
        self.assertFalse(any(x.swap_count == 2 for x in opts))

    def test_exact_knapsack_vs_brute_force(self):
        skills = [
            Skill("A", {1: rank(1, 100), 2: rank(2, 270), 3: rank(3, 320)}),
            Skill("B", {1: rank(1, 300), 2: rank(2, 350), 3: rank(3, 500)}),
            Skill("C", {1: rank(1, 60), 2: rank(2, 100), 3: rank(3, 360)}),
        ]
        prefs = Preferences(level=30, skill_points_available=5)
        result = optimize(skills, {}, prefs)
        brute = max((sum((0 if n == 0 else s.ranks[n].expected_damage / 10)
                         for s, n in zip(skills, ns))
                     for ns in product(range(4), repeat=3) if sum(ns) <= 5),
                    default=0)
        self.assertAlmostEqual(result.estimated_dps, brute)
        self.assertLessEqual(result.allocated_skill_points, 5)

    def test_avoids_swaps_when_auto_loss_and_action_cost_dominates(self):
        skill = Skill("Quick Strike", {
            1: rank(1, 1100, occupied=0.01),
            2: rank(2, 1250, occupied=0.01)
        })
        item = Swap("ring", "ring", bonus_levels=1, equip_seconds=2,
                    unequip_seconds=2, release_status="released_documented")
        cfg = Preferences(level=220, max_swaps_per_skill=1,
                          skill_points_available=1,
                          baseline_auto_dps=800,
                          manual_action_penalty_dps=0.1)
        result = optimize([skill], {"Quick Strike": [item]}, cfg)
        self.assertNotIn("ring", result.used_swap_ids)

    def test_owned_unverified_only_if_opted_in(self):
        s = Skill("Shadowstrike", {2: rank(2, 2000)})
        swap = Swap("old_limited", "ring", bonus_levels=1,
                    owned=True, release_status="unverified")
        no = Preferences(level=220, max_swaps_per_skill=1,
                         skill_points_available=1)
        with self.assertRaises(ValueError):
            optimize([Skill(s.name, s.ranks, mandatory=True)], {s.name: [swap]}, no)
        yes = Preferences(level=220, max_swaps_per_skill=1,
                          skill_points_available=1,
                          allow_unverified_owned_swaps=True)
        build = optimize([Skill(s.name, s.ranks, mandatory=True)],
                         {s.name: [swap]}, yes)
        self.assertIn("old_limited", build.used_swap_ids)

    def test_max_unique_swaps_and_occupation(self):
        s1 = Skill("A", {1: rank(1, 500, occupied=2)})
        s2 = Skill("B", {1: rank(1, 600, occupied=2)})
        cfg = Preferences(level=220, skill_points_available=2,
                          max_occupation_fraction=0.21)
        result = optimize([s1, s2], {}, cfg)
        self.assertLessEqual(result.occupied_share, 0.21)
        self.assertEqual(result.allocated_skill_points, 1)

    def test_unique_swap_gold_charged_once_across_skills(self):
        a = Skill("A", {2: rank(2, 1000)})
        b = Skill("B", {2: rank(2, 1500)})
        item = Swap("ring", "ring1", bonus_levels=1,
                    acquisition_gold_cost=400,
                    release_status="released_documented")
        prefs = Preferences(level=220, skill_points_available=2,
                            max_swaps_per_skill=1, total_gold_budget=400)
        result = optimize([a, b], {"A": [item], "B": [item]}, prefs)
        self.assertEqual(result.estimated_dps, 250)
        self.assertEqual(result.gold_cost, 400)
        self.assertEqual(len(result.used_swap_ids), 1)
        tight = Preferences(level=220, skill_points_available=2,
                            max_swaps_per_skill=1, total_gold_budget=399)
        other = optimize([a, b], {"A": [item], "B": [item]}, tight)
        self.assertEqual(other.gold_cost, 0)
        self.assertLess(other.estimated_dps, result.estimated_dps)

    def test_unknown_price_does_not_become_zero_cost(self):
        skill = Skill("A", {2: rank(2, 1000)})
        unknown = Swap("rare", "ring", bonus_levels=1,
                       release_status="released_documented")
        with self.assertRaises(ValueError):
            optimize([Skill("A", skill.ranks, mandatory=True)],
                     {"A": [unknown]},
                     Preferences(level=220, skill_points_available=1,
                                 max_swaps_per_skill=1, total_gold_budget=1000))

    def test_rejects_malformed_rank_and_imaginary_scaling(self):
        with self.assertRaises(ValueError):
            rank(5, -200)
        s = Skill("Rend", {50: rank(50, 5000)}, mandatory=True)
        with self.assertRaisesRegex(ValueError, "source-backed"):
            optimize([s], {}, Preferences(level=30, skill_points_available=1))

    def test_playstyle_output_contains_four_variations(self):
        a = Skill("A", {1: rank(1, 800)})
        result = compare_playstyles([a], {}, Preferences(
            level=220, skill_points_available=1, max_swaps_per_skill=3))
        self.assertEqual(len(result["results"]), 4)
        self.assertIn("balanced_two_swaps", result["results"])


if __name__ == "__main__":
    unittest.main()
