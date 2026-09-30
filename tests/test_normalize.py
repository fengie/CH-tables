import unittest

from ch_tables.models import PublishedBuild
from ch_tables.normalize import normalize_builds, summarize_classes


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            PublishedBuild("r1", "Rogue", 230, "Damage", 10000),
            PublishedBuild("r2", "Rogue", 240, "Damage", 12000),
            PublishedBuild("w1", "Warrior", 230, "Damage", 11000),
            PublishedBuild("tank", "Warrior", 250, "Tank", None),
            PublishedBuild("low", "Mage", 100, "Damage", 99999),
        ]

    def test_filters_non_comparable_rows(self):
        self.assertEqual(len(normalize_builds(self.rows, min_level=220)), 3)

    def test_class_summary(self):
        by_class = {row["class"]: row for row in summarize_classes(self.rows, min_level=220)}
        self.assertEqual(by_class["Rogue"]["count"], 2)
        self.assertEqual(by_class["Warrior"]["count"], 1)
        self.assertNotIn("Mage", by_class)


if __name__ == "__main__":
    unittest.main()
