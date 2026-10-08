import unittest

from ch_tables.pet_catalog import (
    SPECIES, source_pet_tiers, candidate_pet_items,
)


class PetCatalogTests(unittest.TestCase):
    def test_published_noninvented_pet_tier_samples(self):
        tiers = source_pet_tiers()
        self.assertEqual(len(tiers), 24)
        wolf = next(p for p in tiers
                    if p.species == "Wolf" and p.size == "Giant")
        self.assertEqual(wolf.level_requirement, 200)
        self.assertEqual(wolf.attributes["Strength"], 120)
        self.assertEqual(wolf.attributes["Attack"], 200)
        self.assertEqual(wolf.token_cost, 32)
        phoenix = next(p for p in tiers
                       if p.species == "Phoenix" and p.size == "Giant")
        self.assertEqual(phoenix.attributes, {"Focus": 240, "Vitality": 240})
        self.assertIsNone(phoenix.rarity_probability)
        self.assertIn("Seedling", SPECIES)

    def test_no_false_positives_boss_and_items_not_pets(self):
        source = [
            {"id": 1, "name": "Tiny Brown Wolf", "stats": {}},
            {"id": 2, "name": "Dragon Pet Token", "stats": {}},
            {"id": 3, "name": "Wolf Fang Ring", "stats": {"slot": "Ring"}},
            {"id": 4, "name": "Giant Wolf Boss Sword", "stats": {"slot": "Weapon"}},
            {"id": 5, "name": "Flying Pet", "stats": {"slot": "Pet"}},
        ]
        got, counter = candidate_pet_items(source)
        found = {x["item_id"] for x in got}
        self.assertIn(1, found)
        self.assertIn(2, found)  # low confidence, not necessarily equippable
        self.assertIn(5, found)
        self.assertNotIn(3, found)
        self.assertIn("name_only_possible_pet", counter)
        self.assertTrue(all(x["released_to_players"] == "unverified"
                            for x in got))


if __name__ == "__main__":
    unittest.main()
