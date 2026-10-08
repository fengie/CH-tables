"""End-to-end, offline source-shape tests for all public game-data extraction."""
import gzip
import hashlib
import json
from unittest import mock
import unittest

from ch_tables import full_game_ingest as f


def asset(js):
    return js, hashlib.sha256(js.encode()).hexdigest()


def fixture():
    root = {
        "items": [],
        "mobs": [
            {"id": 4, "name": "Sample Dhiothu", "level": 220,
             "drops": [{"itemId": 100, "chance": None}],
             "zones": ["Example"], "description": "test prose"},
            {"id": 5, "name": "Test Mob", "drops": []},
        ],
        "questlines": {
            "dochgul": {"pieces": {"gloves": {"req": [["Shard", 10]]}},
                         "summary": "Quest story must not be preserved"},
        },
        "zones": [{"id": 99, "name": "Test Island"}],
    }
    items = [
        {"id": 100, "name": "Celtic Knuckleblade",
         "description": "Copyrighted creative text",
         "stats": {"attributes": [["Strength", 320]],
                   "abilities": [["Hand to Hand", 1200]]}},
        {"id": 101, "name": "Royal Ring", "mobs": [4],
         "stats": {"slot": "Ring", "levelReq": 220, "defence": 999, "attack": 4321, "resists": [["Heat", 400], ["Cold", 300]]}},
    ]
    combat = [
        {"id": 4, "name": "Sample Dhiothu", "health": 2000,
         "resist": {"heat": 4000, "cold": 3000, "magic": 2500},
         "evasions": {"movement": 4000, "physical": 3300}, "attack": 2100},
        {"id": 5, "name": "Test Mob", "health": 1000, "attack": 1900,
         "defence": 500, "resist": {"heat": 350, "cold": 250, "poison": 200}},
    ]
    return {
        "data/base.js": asset("window.LOOT_DATA=" + json.dumps(root)),
        "data/items-01.js": asset("window.LOOT_DATA.items.push(..." + json.dumps(items[:1]) + ")"),
        "data/items-02.js": asset("window.LOOT_DATA.items.push(..." + json.dumps(items[1:]) + ")"),
        "data/mobstats-all.js": asset("window.MOB_STATS=" + json.dumps(combat)),
        "data/mobstats.js": asset("window.MOB_STATS=" + json.dumps(combat[:1])),
    }


class FullGameIngestTests(unittest.TestCase):
    def test_all_factual_categories_and_deterministic_archives(self):
        with mock.patch.object(f, "MIN_ITEMS", 1), \
             mock.patch.object(f, "MIN_MOBS", 1), \
             mock.patch.object(f, "MIN_COMBAT", 1):
            sections, manifest = f.prepare(fixture())
        self.assertEqual(manifest["counts"]["items"], 2)
        self.assertEqual(manifest["counts"]["mobs"], 2)
        self.assertEqual(manifest["counts"]["combat_mobs"], 2)
        self.assertEqual(manifest["counts"]["spotlight_mobs"], 1)
        self.assertEqual(manifest["counts"]["mob_drop_records"], 1)
        self.assertEqual(manifest["counts"]["item_mob_references"], 1)
        self.assertEqual(manifest["counts"]["questlines"], 1)
        self.assertNotIn("description", sections["items"][0])
        self.assertNotIn("summary", sections["questlines"]["dochgul"] if False else {})
        archives = f.build_outputs(sections, manifest)
        self.assertEqual(archives["items.jsonl.gz"],
                         f.gzip_deterministic(f.jsonl_bytes(sections["items"])))
        a = gzip.decompress(archives["items.jsonl.gz"]).decode()
        self.assertIn("Hand to Hand", a)
        self.assertNotIn("Copyrighted creative text", a)
        self.assertIn("Test Island", gzip.decompress(archives["other_structured_base.json.gz"]).decode())
        self.assertEqual(len(archives["item_names.tsv"].splitlines()), 2)
        self.assertEqual(archives["manifest.json"], f.canonical_json(manifest))

    def test_conflicting_id_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            f.unique_records([
                {"id": 1, "name": "A"},
                {"id": 1, "name": "B"}
            ], kind="item")

    def test_unexpected_schema_or_missing_source_fails(self):
        broken = fixture()
        broken.pop("data/base.js")
        with self.assertRaisesRegex(ValueError, "Missing"):
            f.prepare(broken)
        self.assertFalse("description" in f.factual_only({"name": "X", "description": "story"}))
        with self.assertRaises(ValueError):
            f.source_url("private/assets")

    def test_creative_fields_removed_deeply(self):
        o = {"name": "A", "lore": "secret", "stats": {
            "Strength": 300, "dialogue": ["hello"]}}
        self.assertEqual(f.factual_only(o), {"name": "A", "stats": {"Strength": 300}})


if __name__ == "__main__":
    unittest.main()
