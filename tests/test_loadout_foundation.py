"""Prove conservative dominance retains utility/sustain/mount surprises."""
import unittest
from ch_tables.loadout_foundation import (
    EquipmentCandidate as Gear, BuildContext, can_safely_dominate,
    safe_prefilter, loadout_legal, permitted,
)


def item(id, slot, role, values=(0, 0, 0, 0, 0, 0), **kw):
    return Gear(str(id), slot, role, values, unknown_effects=False,
                released_documented=True, cost_gold=100, **kw)


class LoadoutTests(unittest.TestCase):
    def setUp(self):
        self.ctx = BuildContext("Rogue", 220)

    def test_shield_and_cg_offhand_cannot_be_pruned_by_dps_offhand(self):
        damage = item("dps", "offhand", "offhand", (100, 0, 0, 0, 0, 0))
        shield = item("shield", "offhand", "shield", (5, 400, 300, 0, 0, 30))
        cg = item("cg", "offhand", "offhand", (20, 0, 0, 0, 0, 0),
                  skill_bonus_levels=(("Shadowstrike", 4),))
        out, audit = safe_prefilter([damage, shield, cg], self.ctx)
        self.assertEqual(len(out), 3)
        self.assertFalse(loadout_legal([damage, shield], self.ctx))
        self.assertFalse(loadout_legal([damage, cg], self.ctx))
        self.assertTrue(loadout_legal([shield], self.ctx))

    def test_verified_mount_with_hp_energy_is_not_thrown_away(self):
        vit = item("vitmount", "mount", "mount", (0, 600, 800, 0, 15, 0),
                   in_combat_effect_verified=True)
        attack = item("attackmount", "mount", "mount", (50, 0, 0, 0, 0, 0),
                      in_combat_effect_verified=True)
        unknown = item("unknownmount", "mount", "mount", (999, 0, 0, 0, 0, 0))
        remaining, _ = safe_prefilter([vit, attack, unknown], self.ctx)
        self.assertEqual({x.item_id for x in remaining}, {"vitmount", "attackmount"})
        self.assertTrue(permitted(unknown, BuildContext("Rogue", 220,
                                                       allow_unknown_mount_in_combat=True)))
        self.assertFalse(can_safely_dominate(attack, vit))

    def test_provable_same_interaction_boundary_dominance(self):
        old = item("old", "head", "armor", (10, 50, 20, 0, 0, 0))
        good = item("good", "head", "armor", (15, 70, 40, 0, 0, 0))
        chosen, audit = safe_prefilter([old, good], self.ctx)
        self.assertEqual([x.item_id for x in chosen], ["good"])
        self.assertEqual(audit["proven_conditional_dominance"],
                         [{"item_id": "old", "dominated_by": "good"}])

    def test_unknown_effects_set_threshold_and_unverified_price_block_pruning(self):
        known = item("known", "torso", "armor", (100, 100, 100, 0, 0, 0))
        extra = item("set", "torso", "armor", (1, 1, 1, 0, 0, 0),
                     set_family="dochgul")
        hidden = Gear("hidden", "torso", "armor", (0, 0, 0, 0, 0, 0),
                      released_documented=True, cost_gold=100,
                      unknown_effects=True)
        self.assertFalse(can_safely_dominate(known, extra))
        self.assertFalse(can_safely_dominate(known, hidden))
        self.assertEqual(len(safe_prefilter([known, extra, hidden], self.ctx)[0]), 3)

    def test_rarity_unreleased_level_class_eligibility(self):
        blocked = Gear("test", "head", "armor", (100, 0, 0, 0, 0, 0))
        self.assertFalse(permitted(blocked, self.ctx))
        self.assertTrue(permitted(Gear("owned", "head", "armor",
                                      (0, 0, 0, 0, 0, 0), owned=True), self.ctx))
        high = item("lvl", "head", "armor", min_level=240)
        self.assertFalse(permitted(high, self.ctx))
        classlocked = item("mage", "head", "armor", classes=frozenset({"Mage"}))
        self.assertFalse(permitted(classlocked, self.ctx))


if __name__ == "__main__":
    unittest.main()
