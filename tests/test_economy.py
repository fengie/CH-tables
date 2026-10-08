import unittest
from datetime import date, timedelta

from ch_tables.economy import (
    PriceObservation, DropObservation, EffortBudget,
    summarize_world_price, drop_rate_estimate,
    acquisition_chance, feasible_acquisition, median_expected_trials,
)


TODAY = date.today().isoformat()
URL = "https://forum.celtic-heroes.com/forum/viewtopic.php?p=750708"


class EconomyTests(unittest.TestCase):
    def test_worlds_are_never_blended_asks_not_claimed_as_sales(self):
        records = [
            PriceObservation(7, "Epona", 9_000_000, TODAY, "sale_listing", URL,
                             sample_id="ask1"),
            PriceObservation(7, "Epona", 5_000_000, TODAY, "completed_sale", URL,
                             sample_id="sold1"),
            PriceObservation(7, "Epona", 7_000_000, TODAY, "completed_sale", URL,
                             sample_id="sold2"),
            PriceObservation(7, "Sulis", 1_000_000, TODAY, "completed_sale", URL),
            PriceObservation(7, "Epona", 5_000_000, TODAY, "completed_sale", URL,
                             sample_id="sold1"),
        ]
        summary = summarize_world_price(records, item_id=7, world="Epona")
        self.assertEqual(summary["sold_median_gold"], 6_000_000)
        self.assertEqual(summary["asking_median_gold"], 9_000_000)
        self.assertEqual(summary["completed_sales"], 2)
        no = summarize_world_price(records, item_id=7, world="Morrigan")
        self.assertIsNone(no["sold_median_gold"])
        self.assertEqual(no["evidence_status"], "no_current_price_evidence")

    def test_explicit_rng_trials_confidence(self):
        samples = [
            DropObservation(7, "Epona", 10, "Boss", 200, 2, URL, TODAY, "one"),
            DropObservation(7, "Epona", 10, "Boss", 300, 1, URL, TODAY, "two"),
        ]
        result = drop_rate_estimate(samples, item_id=7, world="Epona", boss_id=10,
                                    draws=1000)
        self.assertEqual(result["attempts"], 500)
        self.assertEqual(result["successes"], 3)
        self.assertLess(result["interval_95"][0], result["drop_rate"])
        self.assertGreater(result["interval_95"][1], result["drop_rate"])
        no = drop_rate_estimate([], item_id=7, world="Epona", boss_id=10)
        self.assertIsNone(no["drop_rate"])
        with self.assertRaises(ValueError):
            drop_rate_estimate(samples + samples[:1], item_id=7,
                               world="Epona", boss_id=10)

    def test_chance_and_purchase_budget(self):
        self.assertAlmostEqual(acquisition_chance(.1, 10), 1 - .9 ** 10)
        self.assertEqual(acquisition_chance(1.0, 0), 0)
        self.assertEqual(acquisition_chance(1.0, 1), 1)
        self.assertIsNone(acquisition_chance(None, 40))
        self.assertEqual(median_expected_trials(.5), 1)
        cfg = EffortBudget(world="Epona", gold=1_000_000,
                           maximum_boss_kills=20, minimum_success_chance=.7)
        denied = feasible_acquisition(owned=False, released=True,
                                      market_price_gold=2_000_000,
                                      drop_probability=.01, budget=cfg)
        self.assertFalse(denied["feasible"])
        approved = feasible_acquisition(owned=False, released=True,
                                        market_price_gold=500_000,
                                        drop_probability=None, budget=cfg)
        self.assertTrue(approved["feasible"])
        owned = feasible_acquisition(owned=True, released=False,
                                     market_price_gold=None, drop_probability=None,
                                     budget=cfg)
        self.assertTrue(owned["feasible"])

    def test_source_quality_guards(self):
        with self.assertRaises(ValueError):
            PriceObservation(1, "World", 10, TODAY, "rumor", URL)
        with self.assertRaises(ValueError):
            DropObservation(7, "World", 1, "Boss", 2, 3, URL, TODAY, "a")
        with self.assertRaises(ValueError):
            EffortBudget(world="", gold=100)


if __name__ == "__main__":
    unittest.main()
