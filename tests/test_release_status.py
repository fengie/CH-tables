"""Release-status safety: database presence is never release confirmation."""
import unittest

from ch_tables.release_status import (
    check_evidence, classify, derive_signal, STATUSES,
)

URL = "https://www.celtic-heroes.com/news/6110-release-patch-notes-st-patricks-event"


def example():
    return [
        {"id": 65539, "name": "Creidhne's Knuckleblade of Earth",
         "mobs": [142027], "sourceType": "mob"},
        {"id": 99, "name": "Prototype Blade",
         "mobs": [142027], "sourceType": "mob"},
        {"id": 33, "name": "Quest Gloves",
         "mobs": [], "sourceType": "questline", "questline": "dochgul"},
        {"id": 40, "name": "Unreferenced Item",
         "mobs": [], "sourceType": "nonmob"},
        {"id": 44, "name": "Documented Retired Item",
         "mobs": [], "sourceType": "nonmob"},
    ]


def official():
    return {
        "item_id": 65539, "exact_name": "Creidhne's Knuckleblade of Earth",
        "release_status": "released_documented", "evidence_type": "official_patch",
        "url": URL, "evidence_date": "2026-03-11",
        "reason": "Explicit released weapon family and tier in an official 2026 update.",
    }


class ReleaseStatusTests(unittest.TestCase):
    def test_linked_drops_and_curated_quest_do_not_auto_promote(self):
        rows, totals = classify(example(), [official()])
        by_id = {str(r["item_id"]): r for r in rows}
        self.assertEqual(len(rows), 5)
        self.assertEqual(by_id["65539"]["release_status"], "released_documented")
        self.assertEqual(by_id["65539"]["currently_obtainable"], "unknown")
        self.assertFalse(by_id["65539"]["excluded_from_default_bis"])
        self.assertEqual(by_id["99"]["release_status"], "unverified")
        self.assertTrue(by_id["99"]["excluded_from_default_bis"])
        self.assertIn("reconstructed_loot_reference", by_id["99"]["source_signals"]["signals"])
        self.assertEqual(by_id["33"]["release_status"], "unverified")
        self.assertIn("curated_questline_reference", by_id["33"]["source_signals"]["signals"])
        self.assertEqual(by_id["40"]["release_status"], "unverified")
        self.assertIn("unattributed_database_record", by_id["40"]["source_signals"]["signals"])
        self.assertEqual(totals["status_counts"]["released_documented"], 1)
        self.assertEqual(totals["status_counts"]["unverified"], 4)

    def test_rejects_unsupported_negative_evidence(self):
        bad = {**official(), "item_id": 99, "exact_name": "Prototype Blade",
               "release_status": "confirmed_unreleased"}
        with self.assertRaisesRegex(ValueError, "explicit developer"):
            classify(example(), [bad])

    def test_confirmed_unreleased_requires_official_and_is_bis_excluded(self):
        supported = {**official(), "item_id": 99, "exact_name": "Prototype Blade",
                     "release_status": "confirmed_unreleased",
                     "evidence_type": "developer_confirmation",
                     "reason": "Publisher confirms this item is for unreleased test content."}
        out, _ = classify(example(), [supported])
        selected = next(x for x in out if x["item_id"] == 99)
        self.assertEqual(selected["release_status"], "confirmed_unreleased")
        self.assertTrue(selected["excluded_from_default_bis"])

    def test_historical_requires_discontinued_evidence(self):
        prior = {**official(), "item_id": 44, "exact_name": "Documented Retired Item",
                 "release_status": "historically_released"}
        with self.assertRaisesRegex(ValueError, "retirement"):
            classify(example(), [prior])
        prior["retirement_or_seasonality_evidence"] = "Publisher ended event distribution."
        out, _ = classify(example(), [prior])
        self.assertEqual(next(x for x in out if x["item_id"] == 44)["release_status"],
                         "historically_released")

    def test_duplicate_id_and_name_drift_and_missing_id_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "duplicated evidence"):
            classify(example(), [official(), official()])
        with self.assertRaisesRegex(ValueError, "identity"):
            classify(example(), [{**official(), "exact_name": "wrong name"}])
        with self.assertRaisesRegex(ValueError, "not found"):
            classify(example(), [{**official(), "item_id": 9876543}])

    def test_date_and_link_required(self):
        with self.assertRaisesRegex(ValueError, "URL"):
            classify(example(), [{**official(), "url": "http://example.org"}])
        with self.assertRaisesRegex(ValueError, "date"):
            classify(example(), [{**official(), "evidence_date": "invalid"}])


if __name__ == "__main__":
    unittest.main()
