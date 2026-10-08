"""Offline fixtures for the public game-item extractor (no outbound requests)."""
import json
import unittest

from ch_tables.catalog_ingest import (
    ASSETS, assemble, extract_json_literal, iter_items,
    normalize_item, relevant_item, source_url,
)


class CatalogIngestTests(unittest.TestCase):
    def test_assignment_and_spread_chunks_are_data_only(self):
        records = [
            {"id": 1, "name": "Named Dhiothu Knuckleblades",
             "stats": {"slot": "Mainhand", "level": 220, "class": "Rogue",
                       "Strength": 320}},
            {"id": 2, "name": "Royal Bloodthorn Ring",
             "stats": {"slot": "Ring", "level": 215, "class": "Rogue"}},
        ]
        blob = json.dumps(records, separators=(",", ":"))
        a = extract_json_literal("window.LOOT_DATA.items.push(..." + blob + ");")
        b = extract_json_literal("window.LOOT_DATA.items = " + blob + ";")
        self.assertEqual(a, b)
        self.assertEqual(len(list(iter_items(a))), 2)

    def test_not_an_executable_js_evaluator(self):
        with self.assertRaises(ValueError):
            extract_json_literal("window.LOOT_DATA.items = dangerousFunction();")
        with self.assertRaises(ValueError):
            source_url("../../../secrets")
        # Only JSON literals are interpreted, not expressions.
        with self.assertRaises(ValueError):
            extract_json_literal("window.LOOT_DATA.items.push([{id:1, name:'bad JS'}]);")

    def test_relevant_filter(self):
        owned = normalize_item({"id": 5, "name": "Imperial Ferocity Misc",
                                "stats": {}}, ASSETS[0])
        rogue = normalize_item({"id": 6, "name": "Unusual Ring",
                                "stats": {"slot": "Ring", "level": 220,
                                          "class": "Rogue", "attack": 900}},
                               ASSETS[0])
        excluded = normalize_item({"id": 7, "name": "Level 15 Novice Sword",
                                   "stats": {"slot": "Weapon", "level": 15,
                                             "class": "Warrior"}}, ASSETS[0])
        self.assertTrue(relevant_item(owned))
        self.assertTrue(relevant_item(rogue))
        self.assertFalse(relevant_item(excluded))

    def test_collection_and_source_provenance(self):
        data = []
        for idx in range(505):
            data.append({"id": idx + 1,
                         "name": "Rare Rogue Ring" if idx % 2 else "Novice Cloth",
                         "stats": {"slot": "Ring" if idx % 2 else "Chest",
                                   "level": 220 if idx % 2 else 12,
                                   "class": "Rogue" if idx % 2 else "Mage"}})
        parts = [data[:200], data[200:350], data[350:]]
        source = {
            ASSETS[0]: "window.LOOT_DATA=" + json.dumps({"items": parts[0]}),
            ASSETS[1]: "window.LOOT_DATA.items.push(..." + json.dumps(parts[1]) + ")",
            ASSETS[2]: "window.LOOT_DATA.items=window.LOOT_DATA.items.concat(" +
                       json.dumps(parts[2]) + ")",
        }
        selected, manifest = assemble(source)
        self.assertEqual(manifest["total_unique_items"], 505)
        self.assertEqual(len(selected), 252)
        self.assertEqual(len(manifest["sources"]), 3)
        self.assertIn("knuckle", manifest["missing_terms"])

    def test_no_valid_catalog_is_accepted_silently(self):
        source = {name: "window.LOOT_DATA.items=[]" for name in ASSETS}
        with self.assertRaises(ValueError):
            assemble(source)


if __name__ == "__main__":
    unittest.main()
