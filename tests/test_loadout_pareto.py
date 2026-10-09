"""Independent tiny exhaustive Pareto oracle, adversarial interactions, and limits."""
import math
import unittest
from dataclasses import replace
from itertools import product
from random import Random

from ch_tables.loadout_foundation import BuildContext, EquipmentCandidate, METRICS
from ch_tables.loadout_search import Interaction, SearchSpec, optimize_loadouts
from ch_tables.loadout_pareto import (
    ParetoResult, dominates, pareto_loadouts, exhaustive_pareto_oracle,
)


def item(name, slot, *, metrics=(0, 0, 0, 0, 0, 0), cost=0,
         family=None, role="armor", **kw):
    return EquipmentCandidate(
        item_id=name, slot=slot, role=role, metrics=tuple(metrics),
        cost_gold=cost, set_family=family, class_scope="all",
        metric_basis="toy-boss-v1", unknown_effects=False,
        released_documented=True, **kw)


def spec(candidates, slots, **kwargs):
    return SearchSpec(
        tuple(candidates), BuildContext("rogue", 220), tuple(slots),
        "toy-boss-v1", (1, 0, 0, 0, 0, 0), **kwargs)


def independent_oracle(problem):
    """Unpruned, independently assembled possible sets; no optimization helpers."""
    def allowed(it):
        return (it.slot in problem.slots and it.class_scope in ("all", "restricted") and
                (it.class_scope != "restricted" or "rogue" in it.classes) and
                it.min_level <= problem.context.level and
                (it.released_documented or (it.owned and problem.context.include_owned_unverified)) and
                it.metric_basis == problem.metric_basis and
                (not it.unknown_effects or problem.allow_uncertain_effects) and
                (it.owned or it.cost_gold is not None) and
                (it.role != "mount" or it.in_combat_effect_verified or problem.context.allow_unknown_mount_in_combat))
    groups = [[it for it in problem.candidates if it.slot == slot and allowed(it)]
              for slot in problem.slots]
    points = []
    for chosen in product(*groups):
        ids = tuple(x.item_id for x in chosen)
        idset = set(ids)
        if len(idset) != len(ids):
            continue
        if any(a in idset and b in idset for a, b in problem.incompatible_pairs):
            continue
        if not problem.mount_combinations_verified and any(x.role == "mount" for x in chosen) and any(
                x.slot in {"mainhand", "offhand", "pet"} for x in chosen):
            continue
        cost = sum(0 if x.owned else x.cost_gold for x in chosen)
        if problem.budget_gold is not None and cost > problem.budget_gold:
            continue
        metrics = [sum(x.metrics[j] for x in chosen) for j in range(len(METRICS))]
        triggered = []
        for rule in problem.interactions:
            counts = {family:sum(it.set_family == family for it in chosen)
                      for family, _ in rule.required_families}
            if rule.required_item_ids <= idset and all(
                    counts[family] >= need for family, need in rule.required_families):
                triggered.append(rule.name)
                for m in range(len(METRICS)):
                    metrics[m] += rule.metric_delta[m]
        points.append((ids, tuple(metrics), cost, tuple(triggered)))
    def dominance(a, b):
        return a[2] <= b[2] and all(x>=y for x,y in zip(a[1],b[1])) and (
            a[2] < b[2] or any(x>y for x,y in zip(a[1],b[1])))
    answer = []
    for p in points:
        if any(q is not p and (dominance(q,p) or
                (q[1:3] == p[1:3] and q[0] < p[0])) for q in points):
            continue
        answer.append(p)
    return sorted(answer)


class ParetoTests(unittest.TestCase):
    def verify(self, scenario):
        run = pareto_loadouts(scenario)
        self.assertTrue(run.certified_exact, run.as_dict())
        expected = independent_oracle(scenario)
        actual = [(r.item_ids, r.metrics, r.gold_cost, r.triggered_interactions)
                  for r in run.frontier]
        self.assertEqual(sorted(actual), expected)
        self.assertEqual(run.frontier, exhaustive_pareto_oracle(scenario))
        for i,a in enumerate(run.frontier):
            for j,b in enumerate(run.frontier):
                if i!=j: self.assertFalse(dominates(a,b))
        return run

    def test_defense_low_gold_and_damage_can_all_be_nondominated(self):
        scenario=spec([
            item("shield", "offhand", metrics=(0,250,0,0,0,15),cost=0,role="shield"),
            item("offhand", "offhand", metrics=(150,0,0,0,0,0),cost=80,role="offhand"),
            item("free", "offhand", metrics=(20,0,0,0,0,0),cost=0,role="offhand"),
        ], ["offhand"])
        front=self.verify(scenario)
        self.assertEqual(set(r.item_ids[0] for r in front.frontier),{"shield","offhand","free"})

    def test_energy_mount_vs_raw_damage_preserved(self):
        scenario=spec([
            item("energy-mount", "mount", metrics=(0,200,500,0,7,0),cost=10,
                 role="mount",in_combat_effect_verified=True),
            item("damage-mount", "mount", metrics=(90,0,0,0,0,0),cost=10,
                 role="mount",in_combat_effect_verified=True),
        ], ["mount"])
        self.assertEqual({r.item_ids[0] for r in self.verify(scenario).frontier},
                         {"energy-mount","damage-mount"})

    def test_known_two_piece_buff_preserves_low_individual_components(self):
        scenario=spec([
            item("hood", "head", metrics=(3,0,0,0,0,0),cost=5,family="set"),
            item("hat", "head", metrics=(10,0,0,0,0,0),cost=5),
            item("gloves", "hands", metrics=(3,0,0,0,0,0),cost=5,family="set"),
            item("mitts", "hands", metrics=(10,0,0,0,0,0),cost=5),
        ],["head","hands"],interactions=(Interaction(
            "set-bonus",(20,0,0,0,0,0),"toy-boss-v1",required_families=(("set",2),)),))
        front=self.verify(scenario)
        self.assertEqual(front.frontier[0].item_ids, ("hood","gloves"))

    def test_negative_interaction_does_not_falsely_prune_alternative(self):
        scenario=spec([
            item("h1", "head", metrics=(100,0,0,0,0,0)),
            item("h2", "head", metrics=(90,10,0,0,0,0)),
            item("g1", "hands", metrics=(100,0,0,0,0,0)),
            item("g2", "hands", metrics=(90,10,0,0,0,0)),
        ],["head","hands"],interactions=(Interaction(
            "penalty",(-1000,0,0,0,0,0),"toy-boss-v1",required_item_ids=frozenset(("h1","g1"))),))
        self.verify(scenario)

    def test_identical_scores_choose_canonical_lexicographic_item(self):
        scenario=spec([item("z","head",cost=5),item("a","head",cost=5)], ["head"])
        front=self.verify(scenario)
        self.assertEqual([p.item_ids for p in front.frontier],[('a',)])

    def test_unreleased_unknown_price_and_different_basis_rejected(self):
        candidates=[item("valid","head",metrics=(2,0,0,0,0,0)),
                    replace(item("unknown","head",metrics=(999,0,0,0,0,0)),unknown_effects=True),
                    item("unknown-price","head",metrics=(1000,0,0,0,0,0),cost=None),
                    replace(item("wrong-basis","head",metrics=(1000,0,0,0,0,0)),metric_basis="other"),
                    replace(item("unreleased","head",metrics=(1000,0,0,0,0,0)),released_documented=False)]
        front=self.verify(spec(candidates,["head"]))
        self.assertEqual([p.item_ids for p in front.frontier], [('valid',)])

    def test_mount_weapon_incompatible_without_explicit_proof(self):
        candidates=[item("mount","mount",metrics=(50,0,0,0,0,0),role="mount",in_combat_effect_verified=True),
                    item("sword","mainhand",metrics=(50,0,0,0,0,0),role="weapon")]
        base=spec(candidates,["mount","mainhand"])
        self.assertFalse(self.verify(base).frontier)
        self.assertEqual(len(self.verify(replace(base,mount_combinations_verified=True)).frontier),1)

    def test_gold_budget_and_owned_items(self):
        scenario=spec([item("owned","head",metrics=(20,0,0,0,0,0),cost=None,owned=True),
                       item("purchased","head",metrics=(30,0,0,0,0,0),cost=60)],
                      ["head"],budget_gold=10)
        self.assertEqual(self.verify(scenario).frontier[0].item_ids,("owned",))

    def test_frontier_limit_and_node_cap_are_not_certificates(self):
        candidates=[item(f"{slot}-{i}",slot,metrics=(i,5-i,0,0,0,0),cost=i)
                    for slot in ("head","hands","legs") for i in range(6)]
        base=spec(candidates,["head","hands","legs"])
        low=pareto_loadouts(replace(base,max_nodes=3))
        self.assertFalse(low.certified_exact)
        self.assertEqual(low.stop_reason,"node_limit")
        self.assertLessEqual(low.visited_nodes,3)
        front=pareto_loadouts(base,max_frontier=1)
        self.assertFalse(front.certified_exact)
        self.assertEqual(front.stop_reason,"frontier_limit")
        self.assertLessEqual(len(front.frontier),1)
        self.assertIn("Incomplete",front.warning)

    def test_input_validation(self):
        base=spec([item("a","head")],["head"])
        for n in (0,True,-1,100001,1.1):
            with self.subTest(n=n),self.assertRaises(ValueError):
                pareto_loadouts(base,max_frontier=n)

    def test_randomized_against_independent_oracle(self):
        rng=Random(1907)
        for case in range(170):
            slots=("head","hands","offhand")
            candidates=[]
            for slot in slots:
                for i in range(3):
                    metrics=tuple(rng.randrange(-4,15) if m==0 else rng.randrange(0,12) for m in range(6))
                    candidates.append(item(f"{case}-{slot}-{i}",slot,metrics=metrics,
                                           cost=rng.randrange(0,28), family=("set" if rng.random()<.4 else None),
                                           role=("shield" if slot=="offhand" and i==0 else "armor")))
            interactions=(Interaction("set-bonus",tuple(rng.randrange(-10,12) for _ in range(6)),
                                      "toy-boss-v1",required_families=(("set",2),)),
                          Interaction("pair",tuple(rng.randrange(-20,20) for _ in range(6)),
                                      "toy-boss-v1",required_item_ids=frozenset(
                                          (candidates[0].item_id,candidates[-1].item_id))))
            scenario=spec(candidates,slots,interactions=interactions,
                          budget_gold=rng.randrange(14,73),
                          incompatible_pairs=((candidates[1].item_id,candidates[8].item_id),))
            with self.subTest(case=case): self.verify(scenario)

    def test_weighted_objective_cannot_delete_nondominated_vector(self):
        candidates=[item("damage","head",metrics=(50,0,0,0,0,0),cost=10),
                    item("hp","head",metrics=(0,1000,0,0,0,0),cost=10)]
        p=spec(candidates,["head"])
        a=self.verify(p)
        b=self.verify(replace(p,weights=(0,1,0,0,0,0)))
        self.assertEqual({x.item_ids for x in a.frontier},{x.item_ids for x in b.frontier})
        self.assertEqual(len(optimize_loadouts(p).winners),1)

    def test_schema_output_labels_are_transparent(self):
        p=spec([item("a","head",metrics=(1,2,3,4,5,6),cost=7)],["head"])
        data=pareto_loadouts(p).as_dict()
        self.assertTrue(data["certified_exact"])
        self.assertEqual(len(data["objectives"]),7)
        self.assertEqual(data["objectives"][-1],{"name":"acquisition_gold","direction":"minimize"})
        self.assertIn("UNCALIBRATED",data["warning"])


if __name__=="__main__": unittest.main()
