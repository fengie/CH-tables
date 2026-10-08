import gzip
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ch_tables.game_query import search, load_records, property_filters


class GameQueryTests(unittest.TestCase):
    def test_searches_nested_item_values_by_exact_id_and_filter(self):
        with TemporaryDirectory() as work:
            root = Path(work)
            records = [
                {"id": 65539, "name": "Creidhne's Knuckleblade of Earth",
                 "stats": {"slot": "Weapon", "levelReq": 220,
                           "attributes": [["Strength", 320]],
                           "abilities": [["Hand to Hand", 1200]]}},
                {"id": 100, "name": "Rogue Ring",
                 "stats": {"slot": "Ring", "levelReq": 215, "classReq": "Rogue"}},
                {"id": 101, "name": "Mage Ring",
                 "stats": {"slot": "Ring", "levelReq": 100, "classReq": "Mage"}},
            ]
            with gzip.open(root / "items.jsonl.gz", "wt", encoding="utf-8") as fp:
                for row in records:
                    fp.write(json.dumps(row) + "\n")
            self.assertEqual(search("items", "Knuckleblade", root=root)[0]["id"], 65539)
            self.assertEqual(search("items", "", root=root, klass="Rogue",
                                    slot="Ring", level_min=200)[0]["id"], 100)
            self.assertEqual(len(search("items", "", root=root,
                                        record_id="65539")), 1)
            self.assertEqual(len(search("items", "Hand to Hand", root=root,
                                        full_text=True)), 1)
            with self.assertRaises(ValueError):
                search("items", root=root, limit=0)
            with self.assertRaises(ValueError):
                list(load_records("unknown", root=root))

    def test_every_item_is_labeled_and_bis_is_released_only(self):
        import hashlib
        from ch_tables.full_game_ingest import gzip_deterministic, jsonl_bytes
        with TemporaryDirectory() as folder:
            root = Path(folder)
            items = [
                {"id": 1, "name": "Released Knuckleblade", "stats": {"slot": "Weapon"}},
                {"id": 2, "name": "Database-only Knuckleblade", "stats": {"slot": "Weapon"}},
            ]
            source = gzip_deterministic(jsonl_bytes(items))
            (root / "items.jsonl.gz").write_bytes(source)
            statuses = [
                {"item_id": 1, "release_status": "released_documented",
                 "currently_obtainable": "unknown", "evidence": [
                     {"url": "https://example.org/release"}
                 ], "source_signals": {"signals": ["official"]}},
                {"item_id": 2, "release_status": "unverified",
                 "currently_obtainable": "unknown", "evidence": [],
                 "source_signals": {"signals": ["reconstructed_loot_reference"]}},
            ]
            encoded = gzip_deterministic(jsonl_bytes(statuses))
            (root / "item_release_status.jsonl.gz").write_bytes(encoded)
            summary = {
                "source_item_archive_sha256": hashlib.sha256(source).hexdigest(),
                "index_sha256": hashlib.sha256(encoded).hexdigest(),
            }
            (root / "release_status_summary.json").write_text(json.dumps(summary))
            both = search("items", "Knuckleblade", root=root)
            self.assertEqual([x["release_status"] for x in both],
                             ["released_documented", "unverified"])
            usable = search("items", "Knuckleblade", root=root, released_only=True)
            self.assertEqual([x["id"] for x in usable], [1])
            self.assertEqual(search("items", "", root=root,
                                    release_state="unverified")[0]["id"], 2)
            (root / "release_status_summary.json").write_text(json.dumps({
                **summary, "index_sha256": "bad",
            }))
            with self.assertRaisesRegex(ValueError, "Stale"):
                search("items", "Knuckleblade", root=root)

    def test_quest_dict_is_iterable(self):
        with TemporaryDirectory() as work:
            root = Path(work)
            with gzip.open(root / "questlines.json.gz", "wt", encoding="utf-8") as fp:
                json.dump({"dochgul": {"pieces": {"hands": 1}}}, fp)
            data = search("questlines", "doch", root=root)
            self.assertEqual(data[0]["key"], "dochgul")


if __name__ == "__main__":
    unittest.main()
