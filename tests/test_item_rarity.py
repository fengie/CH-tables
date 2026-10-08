import unittest
from ch_tables.item_rarity import label_item, create_metadata


class ItemRarityTests(unittest.TestCase):
    def test_rarity_label_not_falsely_interpreted_as_probability(self):
        rare = label_item({"id": 1, "name": "Godly Ferocity Charm",
                           "rarity": "tier4"})
        self.assertEqual(rare["item_rarity_source_value"], "tier4")
        self.assertEqual(rare["name_prefix_tier"], "Godly")
        self.assertIsNone(rare["observed_drop_probability"])
        unknown = label_item({"id": 2, "name": "Unidentified Tool"})
        self.assertEqual(unknown["rarity_status"], "unknown")
        self.assertIsNone(unknown["name_prefix_tier"])
        pet = label_item({"id": 3, "name": "Spirit Dragon Pet"})
        self.assertEqual(pet["rarity_status"], "name_pattern_only")
        self.assertIsNone(pet["observed_drop_probability"])

    def test_full_catalog_coverage_and_no_imaginary_drop_chances(self):
        rows, summary = create_metadata([
            {"id": 1, "name": "Royal Ring"},
            {"id": 2, "name": "Some Weapon"},
        ])
        self.assertEqual(summary["source_items"], 2)
        self.assertEqual(summary["drop_chances_populated"], 0)
        self.assertEqual(summary["name_prefix_tier_counts"]["Royal"], 1)
        self.assertTrue(all(x["observed_drop_probability"] is None for x in rows))


if __name__ == "__main__":
    unittest.main()
