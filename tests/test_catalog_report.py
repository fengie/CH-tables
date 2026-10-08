import unittest

from ch_tables.catalog_report import summarize_items


class CatalogReportTests(unittest.TestCase):
    def test_priority_lookup_retains_raw_numeric_stats(self):
        data = [
            {"id": 101, "name": "Named Knuckleblade", "level": 220,
             "class": "Rogue", "slot": "Weapon",
             "stats": {"pierce": 200, "strength": 150}},
            {"id": 102, "name": "Godly Ferocity Amulet", "level": 220,
             "class": "Rogue", "slot": "Amulet",
             "stats": {"attack": 1500}},
            {"id": 103, "name": "Doch Gul Gauntlets", "level": 215,
             "class": "Rogue", "slot": "Gloves",
             "stats": {"dexterity": 100}},
        ]
        index, schema = summarize_items(data)
        self.assertEqual(index["categories"]["knuckleblades"]["count"], 1)
        self.assertEqual(index["categories"]["ferocity"]["count"], 1)
        self.assertEqual(index["categories"]["doch_gul"]["count"], 1)
        self.assertEqual(index["categories"]["valley_of_ancients"]["count"], 0)
        self.assertEqual(index["categories"]["knuckleblades"]["entries"][0]
                         ["stats"]["pierce"], 200)
        self.assertEqual(schema["numeric_and_categorical_field_counts"]["attack"], 1)
        self.assertEqual(schema["total_items"], 3)


if __name__ == "__main__":
    unittest.main()
