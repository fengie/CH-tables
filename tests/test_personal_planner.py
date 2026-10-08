import unittest
from ch_tables.build_planner import Swap
from ch_tables.economy import EffortBudget
from ch_tables.personal_planner import (
    price_map, drop_map, apply_acquisition_filters,
)


class PersonalPlannerTests(unittest.TestCase):
    def test_same_world_pricing_and_observed_boss_rate_only(self):
        market = {
            "price_by_item_world": [
                {"item_id": 5, "world": "Epona", "sold_median_gold": 1000,
                 "evidence_status": "observed_sales"},
                {"item_id": 5, "world": "Sulis", "sold_median_gold": 5,
                 "evidence_status": "observed_sales"},
                {"item_id": 6, "world": "Epona", "sold_median_gold": None,
                 "evidence_status": "only_asks_or_bids"},
            ],
            "drop_rate_by_item_world_boss": [
                {"item_id": 5, "world": "Epona", "boss_id": 1,
                 "drop_rate": .002, "status": "estimated_from_observed_trials"},
                {"item_id": 5, "world": "Sulis", "boss_id": 1,
                 "drop_rate": .9, "status": "estimated_from_observed_trials"},
            ],
        }
        self.assertEqual(price_map(market, "Epona"), {5: 1000})
        self.assertEqual(drop_map(market, "Epona"), {5: .002})

    def test_evidence_is_loaded_from_repo_not_untrusted_scenario(self):
        swaps = {"A": [
            Swap("5", "Ring1", bonus_levels=2,
                 release_status="released_documented"),
            Swap("6", "Ring2", bonus_levels=8, owned=True),
        ]}
        items = {
            "5": {"id": 5, "name": "Dev-only", "stats": {"slot": "Ring"}},
            "6": {"id": 6, "name": "My Confirmed Item", "stats": {"slot": "Ring"}},
        }
        # A scenario claiming released_documented cannot override trusted index.
        status = {"5": {"release_status": "unverified"}}
        prefs = EffortBudget(world="Epona", gold=500,
                             acquisition_mode="any")
        selected, rejected = apply_acquisition_filters(
            swaps, item_catalog=items, status_index=status,
            market={}, budget=prefs,
        )
        self.assertEqual([x.item_id for x in selected["A"]], ["6"])
        self.assertEqual(rejected[0]["rejection"]["reason"],
                         "release_not_documented")
        self.assertEqual(selected["A"][0].release_status, "unverified")
        self.assertEqual(selected["A"][0].acquisition_gold_cost, 0)

    def test_missing_item_and_wrong_equipment_slot_refused(self):
        with self.assertRaisesRegex(ValueError, "not in game"):
            apply_acquisition_filters(
                {"A": [Swap("10", "ring")]}, item_catalog={}, status_index={},
                market={}, budget=EffortBudget(world="Sulis"),
            )
        with self.assertRaisesRegex(ValueError, "slot mismatch"):
            apply_acquisition_filters(
                {"A": [Swap("10", "ring")]},
                item_catalog={"10": {"name": "Weapon",
                                     "stats": {"slot": "Weapon"}}},
                status_index={}, market={},
                budget=EffortBudget(world="Sulis"),
            )


if __name__ == "__main__":
    unittest.main()
