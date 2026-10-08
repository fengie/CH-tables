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

    def test_quest_dict_is_iterable(self):
        with TemporaryDirectory() as work:
            root = Path(work)
            with gzip.open(root / "questlines.json.gz", "wt", encoding="utf-8") as fp:
                json.dump({"dochgul": {"pieces": {"hands": 1}}}, fp)
            data = search("questlines", "doch", root=root)
            self.assertEqual(data[0]["key"], "dochgul")


if __name__ == "__main__":
    unittest.main()
