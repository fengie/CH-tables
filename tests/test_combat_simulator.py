"""Deterministic and adversarial tests for the uncalibrated event engine."""
import unittest
from dataclasses import replace
from pathlib import Path
import json
from types import SimpleNamespace

from ch_tables.combat_simulator import (
    Attack, DamageOverTime, Encounter, MountBonus, Potion, SimSkill,
    SwapDelay, TimedEffect, compare_candidates, encounter_from_dict,
    from_build_choices, simulate,
)


class CombatSimulatorTests(unittest.TestCase):
    def case(self, **kw):
        return Encounter(duration_s=10, max_hp=100, max_energy=20, **kw)

    def test_exact_auto_baseline_and_window_denominator(self):
        r = simulate(self.case(auto=Attack(2, 10)))
        self.assertEqual(r["total_damage"], 50)
        self.assertEqual(r["fixed_window_dps"], 5)
        self.assertEqual(r["elapsed_s"], 10)
        self.assertEqual(r["end_reason"], "time_limit")

    def test_cast_interruption_delays_not_instant_autos(self):
        s = SimSkill("once", 40, 100, 3)
        r = simulate(self.case(auto=Attack(2, 10), skills=(s,)))
        self.assertEqual(r["skill_casts"]["once"], 1)
        self.assertEqual(r["damage_breakdown"]["skills"], 40)
        self.assertEqual(r["damage_breakdown"]["auto"], 30)
        self.assertEqual(r["total_damage"], 70)

    def test_energy_never_overdrawn_without_consumables(self):
        s = SimSkill("blast", 10, 2, 0, energy_cost=2)
        r = simulate(Encounter(duration_s=10, max_hp=100, max_energy=2, skills=(s,)))
        self.assertEqual(r["skill_casts"]["blast"], 1)
        self.assertEqual(r["remaining_energy"], 0)
        self.assertEqual(r["total_damage"], 10)

    def test_regeneration_reopens_affordable_skill(self):
        s = SimSkill("blast", 10, 2, 0, energy_cost=2)
        r = simulate(Encounter(duration_s=8, max_hp=100, max_energy=2,
                               energy_regen_s=1, skills=(s,)))
        self.assertEqual(r["skill_casts"]["blast"], 5)
        self.assertEqual(r["total_damage"], 50)

    def test_potion_charges_and_gold_not_free(self):
        s = SimSkill("blast", 10, 2, 0, energy_cost=2)
        r = simulate(Encounter(duration_s=4, max_hp=100, max_energy=2,
                               skills=(s,), energy_potion=Potion(2, 1, .5, 1, 5, 7)))
        self.assertEqual(r["potions_used"], {"hp": 0, "energy": 1})
        self.assertEqual(r["consumable_gold"], 7)
        self.assertEqual(r["skill_casts"]["blast"], 2)
        self.assertEqual(r["total_damage"], 20)

    def test_death_stops_damage_and_potion_can_save_window(self):
        naked = Encounter(duration_s=10, max_hp=25, max_energy=0,
                          auto=Attack(2, 10), enemy=Attack(2, 10))
        dead = simulate(naked)
        self.assertEqual(dead["end_reason"], "player_died")
        self.assertEqual(dead["elapsed_s"], 6)
        self.assertLess(dead["fixed_window_dps"], 5)
        restored = simulate(replace(naked, duration_s=8, hp_potion=Potion(30, 1, .5, .5, 10, 17)))
        self.assertTrue(restored["survived_full_window"])
        self.assertEqual(restored["potions_used"]["hp"], 1)
        self.assertEqual(restored["consumable_gold"], 17)

    def test_effect_expires_before_same_time_auto(self):
        buff = SimSkill("buff", 0, 100, 0, effect=TimedEffect("boost", 2, 2))
        r = simulate(Encounter(duration_s=4, max_hp=100, max_energy=0,
                               auto=Attack(1, 10), skills=(buff,)))
        self.assertEqual(r["damage_breakdown"]["auto"], 50)

    def test_dot_refresh_prevents_infinite_stacks(self):
        s = SimSkill("dot", 0, 1, 0, dot=DamageOverTime(10, 2, 3))
        r = simulate(self.case(skills=(s,)))
        self.assertEqual(r["damage_breakdown"]["dots"], 0)
        self.assertEqual(r["skill_casts"]["dot"], 11)

    def test_swaps_cost_action_time_and_counted(self):
        no_swap = SimSkill("cast", 10, 100, 0)
        with_swap = replace(no_swap, swaps=(SwapDelay("ring", "ring1", 3, 0),))
        a = simulate(self.case(auto=Attack(2, 10), skills=(no_swap,)))
        b = simulate(self.case(auto=Attack(2, 10), skills=(with_swap,)))
        self.assertGreater(a["total_damage"], b["total_damage"])
        self.assertEqual(b["swap_operations"], 2)

    def test_seeded_rng_reproducible_and_separate_enemy_stream(self):
        case = self.case(enemy=Attack(1, 1, .5), auto=Attack(1, 10, .5))
        self.assertEqual(simulate(case, seed=99), simulate(case, seed=99))
        no_auto = replace(case, auto=None)
        x = simulate(case, seed=42, trace_limit=25)
        y = simulate(no_auto, seed=42, trace_limit=25)
        hits = lambda r: [x["damage"] for x in r["trace"] if x["event"] == "enemy_hit"]
        self.assertEqual(hits(x), hits(y))

    def test_mount_hard_evidence_gate(self):
        with self.assertRaisesRegex(ValueError, "Unverified mount"):
            MountBonus(max_hp=500)
        boosted = self.case(mount=MountBonus(max_hp=10, verified_in_combat=True))
        self.assertEqual(simulate(boosted)["remaining_hp"], 110)

    def test_boss_kill_damage_capped_and_dps_not_kill_time_ratio(self):
        r = simulate(self.case(auto=Attack(1, 100), boss_hp=30))
        self.assertEqual(r["end_reason"], "boss_killed")
        self.assertEqual(r["total_damage"], 30)
        self.assertEqual(r["fixed_window_dps"], 3)
        self.assertEqual(r["active_time_dps"], 30)

    def test_fails_closed_on_malformed_probabilities_and_swaps(self):
        with self.assertRaises(ValueError):
            Attack(1, 10, hit_probability=1.1)
        with self.assertRaises(ValueError):
            Attack(float("nan"), 10)
        with self.assertRaises(ValueError):
            SimSkill("a", 5, 2, 1, swaps=(SwapDelay("a", "ring", 0, 0),
                                          SwapDelay("b", "ring", 0, 0)))
        with self.assertRaisesRegex(ValueError, "provenance"):
            self.case(evidence="observed")
        with self.assertRaises(ValueError):
            Encounter(10, 100, 10, skills=(SimSkill("dup", 5, 1, 0),
                                           SimSkill("dup", 5, 1, 0)))

    def test_adapter_preserves_rank_and_swap_data(self):
        rank = SimpleNamespace(expected_damage=100, cooldown_s=5,
                               occupied_s=1, energy_cost=10, healing=4,
                               hit_probability=.75)
        swap = SimpleNamespace(item_id="CG_offhand", slot="offhand",
                               direct_damage=20, equip_seconds=.25,
                               unequip_seconds=.15)
        c = SimpleNamespace(skill="Strike", rank=rank, swaps=(swap,))
        skill, = from_build_choices((c,), priority={"Strike": 8})
        self.assertEqual(skill.damage, 120)
        self.assertEqual(skill.occupied_s, 1.4)
        self.assertEqual(skill.priority, 8)
        self.assertEqual(skill.energy_cost, 10)

    def test_idle_time_regen_is_accounted_to_horizon(self):
        case = Encounter(duration_s=10, max_hp=10, max_energy=10,
                         energy_regen_s=1, skills=(SimSkill("drain", 0, 30, 0, energy_cost=8),))
        r = simulate(case)
        self.assertEqual(r["remaining_energy"], 10)
        self.assertEqual(r["skill_casts"]["drain"], 1)

    def test_synthetic_json_and_paired_seed_comparison(self):
        source = Path(__file__).resolve().parents[1] / "data/planner/synthetic_combat_scenario.json"
        case = encounter_from_dict(json.loads(source.read_text()))
        r = simulate(case, seed=9)
        self.assertEqual(r["input_evidence"], "synthetic")
        self.assertGreater(r["events_processed"], 0)
        paired = compare_candidates({"same1": case, "same2": case}, (1, 2, 3))
        self.assertEqual(paired["candidates"]["same1"], paired["candidates"]["same2"])


if __name__ == "__main__":
    unittest.main()
