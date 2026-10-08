import unittest
from ch_tables.gear_bonus_index import index_items


class GearBonusIndexTests(unittest.TestCase):
    def test_preserves_all_raw_item_stat_tuple_parts(self):
        data = [
            {"id": 1, "name": "Knuckles", "stats": {
                "abilities": [["Hand to Hand", 1200]],
                "skillBonuses": [["Quick Strike", 1000, 0]],
                "attributes": [["Strength", 320]],
                "resists": [["Heat", 650]],
                "evasions": [["Weakening", 100]],
            }},
            {"id": 2, "name": "Second", "stats": {"slot": "Ring"}},
        ]
        rows, summary = index_items(data)
        self.assertEqual(len(rows), 5)
        self.assertEqual(summary["distinct_stats"]["abilities"], 1)
        self.assertEqual(summary["raw_item_stat_fields"]["slot"], 1)
        skill = next(x for x in rows if x["category"] == "skillBonuses")
        self.assertEqual(skill["source_values"], [1000, 0])
        self.assertEqual(skill["item_id"], 1)

    def test_fails_closed_when_bonus_is_malformed(self):
        with self.assertRaisesRegex(ValueError, "Malformed bonus"):
            index_items([{"id": 1, "name": "Bad", "stats": {
                "skillBonuses": [["Quick Strike"]]
            }}])


if __name__ == "__main__":
    unittest.main()
