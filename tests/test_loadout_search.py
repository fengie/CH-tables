"""Tiny exact oracle and adversarial loadout search regression tests."""
import unittest
from dataclasses import replace
from itertools import product
from random import Random

from ch_tables.loadout_foundation import BuildContext, EquipmentCandidate
from ch_tables.loadout_search import (
    Interaction, SearchSpec, exhaustive_oracle, optimize_loadouts,
)


def item(name, slot, value, *, cost=0, family=None, role='armor', **kw):
    return EquipmentCandidate(
        name,slot,role,(value,0,0,0,0,0),cost_gold=cost,
        class_scope='all',metric_basis='toy-v1',unknown_effects=False,
        released_documented=True,set_family=family,**kw)


def spec(items, slots, **kw):
    return SearchSpec(tuple(items), BuildContext('rogue',220),tuple(slots),
                      'toy-v1',(1,0,0,0,0,0),**kw)


class ExactSearchTests(unittest.TestCase):
    def assertOracle(self, problem, k=3):
        actual=optimize_loadouts(problem,top_k=k)
        expected=exhaustive_oracle(problem,top_k=k)
        self.assertTrue(actual.certified_exact)
        self.assertEqual(actual.winners,expected)
        return actual

    def test_additive_optimum(self):
        s=spec([item('a','head',10,cost=10),item('b','head',12,cost=30),
                item('c','offhand',7,cost=10),item('d','offhand',10,cost=90)],
               ['head','offhand'],budget_gold=40)
        r=self.assertOracle(s)
        self.assertEqual(r.winners[0].item_ids,('b','c'))
        self.assertEqual(r.winners[0].score,19)

    def test_expensive_high_dps_not_free(self):
        s=spec([item('cheap','head',1,cost=0),item('premium','head',100,cost=100)],
               ['head'],budget_gold=10)
        self.assertEqual(self.assertOracle(s).winners[0].item_ids,('cheap',))

    def test_unknown_price_and_basis_are_rejected(self):
        p=spec([item('unknown','head',100,cost=None),item('free','head',2,cost=0),
                replace(item('old','head',1000),metric_basis='different')],['head'])
        self.assertEqual(self.assertOracle(p).winners[0].item_ids,('free',))

    def test_defensive_shield_can_win_under_survival_weights(self):
        shield=replace(item('shield','offhand',0,role='shield'),
                       metrics=(0,200,0,0,0,12))
        offhand=item('dps-offhand','offhand',100,role='offhand')
        p=replace(spec([shield,offhand],['offhand']),
                  weights=(1,1,0,0,0,0))
        r=self.assertOracle(p)
        self.assertEqual(r.winners[0].item_ids,('shield',))
        self.assertEqual(r.winners[0].metrics[1],200)

    def test_energy_sustain_vs_raw_damage_profile(self):
        regen=replace(item('regen','bracelet1',0),metrics=(0,0,100,0,6,0))
        raw=item('raw','bracelet1',120)
        s=spec([regen,raw],['bracelet1'])
        self.assertEqual(self.assertOracle(s).winners[0].item_ids,('raw',))
        self.assertEqual(self.assertOracle(replace(s,weights=(.5,0,1,0,20,0))).winners[0].item_ids,('regen',))

    def test_unknown_effects_fail_closed(self):
        risky=replace(item('magic','head',100),unknown_effects=True)
        base=spec([risky,item('plain','head',1)],['head'])
        self.assertEqual(self.assertOracle(base).winners[0].item_ids,('plain',))
        research=self.assertOracle(replace(base,allow_uncertain_effects=True))
        self.assertTrue(research.winners[0].unknown_effects)

    def test_conditional_negative_effect_survives_branch_bound(self):
        items=[item('strong','head',10),item('mild','head',9),
               item('ally','offhand',10),item('solo','offhand',9)]
        effect=Interaction('incompatible-proc',(-100,0,0,0,0,0),'toy-v1',
                           required_item_ids=frozenset(('strong','ally')))
        s=spec(items,['head','offhand'],interactions=(effect,))
        self.assertOracle(s)
        self.assertNotEqual(optimize_loadouts(s).winners[0].item_ids,('strong','ally'))

    def test_set_family_interaction_and_skill_bonus(self):
        items=[item('hood','head',4,family='set',skill_bonus_levels=(('Quick Strike',2),)),
               item('hat','head',6),item('gloves','hands',4,family='set'),
               item('other','hands',6)]
        bonus=Interaction('set-2',(8,0,0,0,0,0),'toy-v1',required_families=(('set',2),))
        s=spec(items,['head','hands'],interactions=(bonus,))
        r=self.assertOracle(s)
        self.assertEqual(r.winners[0].item_ids,('hood','gloves'))
        self.assertEqual(dict(r.winners[0].skill_bonuses)['Quick Strike'],2)
        self.assertEqual(r.winners[0].triggered_interactions,('set-2',))

    def test_mount_weapon_needs_compatibility_proof(self):
        mount=item('horse','mount',100,role='mount',in_combat_effect_verified=True)
        sword=item('sword','mainhand',10,role='weapon')
        p=spec([mount,sword],['mount','mainhand'])
        self.assertFalse(self.assertOracle(p).winners)
        self.assertEqual(len(self.assertOracle(replace(p,mount_combinations_verified=True)).winners),1)

    def test_shield_and_dps_offhand_are_same_slot(self):
        items=[item('shield','offhand',1,role='shield'),item('dagger','offhand',10,role='offhand')]
        p=spec(items,['offhand'])
        self.assertEqual(self.assertOracle(p).winners[0].item_ids,('dagger',))

    def test_incompatible_specific_pair(self):
        items=[item('a','head',10),item('b','head',5),item('c','offhand',10),item('d','offhand',5)]
        p=spec(items,['head','offhand'],incompatible_pairs=(('a','c'),))
        self.assertOracle(p)
        self.assertNotEqual(optimize_loadouts(p).winners[0].item_ids,('a','c'))

    def test_cap_is_not_false_optimality_proof(self):
        items=[item(f'{s}-{i}',s,float(i)) for s in ('head','hands','legs','feet') for i in range(6)]
        p=spec(items,['head','hands','legs','feet'],max_nodes=3)
        r=optimize_loadouts(p)
        self.assertFalse(r.certified_exact)
        self.assertLessEqual(r.visited_nodes,3)

    def test_randomized_oracle_agreement(self):
        rng=Random(129)
        for case in range(80):
            slots=['head','hands','offhand']
            items=[item(f'{case}-{s}-{i}',s,rng.randrange(-9,15),cost=rng.randrange(0,20))
                   for s in slots for i in range(3)]
            p=spec(items,slots,budget_gold=rng.randrange(10,50))
            self.assertOracle(p,k=4)

    def test_negative_or_invalid_weights_rejected(self):
        p=spec([item('a','head',2)],['head'])
        with self.assertRaises(ValueError):
            replace(p,weights=(-1,0,0,0,0,0))
        with self.assertRaises(ValueError):
            replace(p,weights=(float('nan'),0,0,0,0,0))
        with self.assertRaises(ValueError):
            replace(p,slots=('head','head'))

    def test_conditional_rule_id_cannot_disappear(self):
        p=spec([item('a','head',1)],['head'])
        with self.assertRaises(ValueError):
            replace(p,interactions=(Interaction('x',(3,0,0,0,0,0),'toy-v1',
                                              required_item_ids=frozenset(('missing',))),))

    def test_mixed_class_item_cannot_enter_eligible(self):
        bad=replace(item('mage','head',99),class_scope='restricted',classes=frozenset({'mage'}))
        p=spec([bad,item('rogue','head',3)],['head'])
        self.assertEqual(self.assertOracle(p).winners[0].item_ids,('rogue',))

if __name__=='__main__':
    unittest.main()
