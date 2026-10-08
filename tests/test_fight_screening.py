"""Toy-only falsification tests: defensive and resource gear can win."""
import unittest
from dataclasses import replace
from ch_tables.fight_screening import FightScreen, HastePlan, screen_fight


class FightScreenTests(unittest.TestCase):
    def baseline(self):
        return FightScreen(
            duration_s=100, auto_dps=100, skill_dps=100,
            max_hp=1000, max_energy=500, incoming_damage_per_s=20,
            hp_potion_amount=500, hp_potion_gold=20, hp_potion_limit=5,
            energy_spend_per_s=8, energy_potion_amount=400,
            energy_potion_gold=10, energy_potion_limit=4,
            potion_action_seconds=3,
        )

    def test_defensive_offhand_reduces_pot_spam_and_increases_screening_bound(self):
        damage_offhand = replace(self.baseline(), auto_dps=110)
        shield = replace(self.baseline(), incoming_reduction_per_s=12)
        a, b = screen_fight(damage_offhand), screen_fight(shield)
        self.assertTrue(a["necessary_resource_balance_satisfied"])
        self.assertTrue(b["necessary_resource_balance_satisfied"])
        self.assertEqual(a["minimum_hp_potions_lower_bound"], 2)
        self.assertEqual(b["minimum_hp_potions_lower_bound"], 0)
        self.assertGreater(b["optimistic_practical_dps_upper_bound"],
                           a["optimistic_practical_dps_upper_bound"])

    def test_mount_energy_and_hp_reduce_resource_needs_without_damage_bonus(self):
        base = screen_fight(self.baseline())
        augmented = screen_fight(replace(
            self.baseline(), mount_flat_hp=1000, mount_flat_energy=400,
            mount_effects_verified_in_combat=True,
        ))
        self.assertEqual(base["minimum_energy_potions_lower_bound"], 1)
        self.assertEqual(augmented["minimum_energy_potions_lower_bound"], 0)
        self.assertEqual(augmented["minimum_hp_potions_lower_bound"], 0)
        with self.assertRaisesRegex(ValueError, "verified"):
            replace(self.baseline(), mount_flat_hp=400)

    def test_unsustainable_damage_has_no_fabricated_real_dps(self):
        scenario = replace(self.baseline(), hp_potion_limit=0)
        outcome = screen_fight(scenario)
        self.assertFalse(outcome["necessary_resource_balance_satisfied"])
        self.assertIsNone(outcome["optimistic_practical_dps_upper_bound"])

    def test_heroic_lix_and_unknown_prices_handled_explicitly(self):
        profile = replace(
            self.baseline(), haste=HastePlan(1.2, 30, 800),
            hp_potion_gold=None,
        )
        o = screen_fight(profile)
        self.assertEqual(o["haste_elixirs_required"], 4)
        self.assertIsNone(o["consumable_gold_lower_bound"])
        self.assertEqual(o["ideal_uninterrupted_dps"], 220)

    def test_different_spell_resource_profiles_change_energy_pots(self):
        regular = screen_fight(self.baseline())
        low_energy = screen_fight(replace(
            self.baseline(), energy_regeneration_per_s=8,
        ))
        self.assertEqual(regular["minimum_energy_potions_lower_bound"], 1)
        self.assertEqual(low_energy["minimum_energy_potions_lower_bound"], 0)

    def test_bounds_and_inputs_are_not_live_celtic_heroes_constants(self):
        with self.assertRaises(ValueError):
            HastePlan(0.9, 60, 10)
        with self.assertRaises(ValueError):
            replace(self.baseline(), incoming_damage_per_s=-1)
        with self.assertRaises(ValueError):
            replace(self.baseline(), duration_s=0)
        d = screen_fight(self.baseline())
        self.assertIn("unmodeled", d)
        self.assertIn("optimistic", d["method"])


if __name__ == "__main__":
    unittest.main()
