"""Complete Codex listing and SQLite import regression tests."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from ch_tables.codex_catalog import validate_catalog, publish_catalog
from ch_tables.scrape import SourceSchemaError, refresh_dataset

CAT = "https://the-codex.ch/builds"


def make_doc():
    rows = [
        {"source_url": "https://the-codex.ch/damagebuilder/a",
         "name": "A", "character_class": "Rogue", "level": 230,
         "metric": "1000.0 DPS", "description": "model only", "created": "Oct 8, 2026",
         "build_type": "Damage", "benchmark_dps": 1000.0},
        {"source_url": "https://the-codex.ch/tankbuilder/b",
         "name": "B", "character_class": "Warrior", "level": 225,
         "metric": "Tank", "description": "", "created": "Oct 8, 2026",
         "build_type": "Tank", "benchmark_dps": None},
    ]
    return {"schema_version": 1, "source_url": CAT,
            "source_type": "public_saved_build_listing_snapshot",
            "snapshot_date": "2026-10-08",
            "declared_total": 2, "extracted_total": 2, "page_size": 2,
            "pages": [{"page": 1, "count": 2, "range": [1, 2, 2]}],
            "records": rows}


class CatalogTests(unittest.TestCase):
    def test_load_full_frozen_repository_snapshot(self):
        path = Path("data/reference/codex_published_build_catalog.json")
        doc = json.loads(path.read_text(encoding="utf-8"))
        rows = validate_catalog(doc)
        self.assertEqual(len(rows), 327)
        self.assertEqual(sum(r.build_type == "Tank" for r in rows), 21)
        self.assertEqual(sum(r.is_damage_build for r in rows), 306)
        self.assertEqual(len(set(r.build_url for r in rows)), len(rows))

    def test_partial_page_or_duplicate_cannot_publish(self):
        d = make_doc()
        d["declared_total"] = 3
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            validate_catalog(d)
        d = make_doc()
        d["records"][1]["source_url"] = d["records"][0]["source_url"]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate_catalog(d)
        d = make_doc()
        d["pages"][0]["range"] = [2, 3, 2]
        with self.assertRaisesRegex(ValueError, "page"):
            validate_catalog(d)

    def test_source_and_typed_numeric_gates(self):
        d = make_doc()
        d["records"][0]["source_url"] = "https://evil.example/damagebuilder/a"
        with self.assertRaisesRegex(ValueError, "untrusted"):
            validate_catalog(d)
        d = make_doc()
        d["records"][0]["benchmark_dps"] = True
        with self.assertRaisesRegex(ValueError, "damage benchmark"):
            validate_catalog(d)
        d = make_doc()
        d["records"][1]["benchmark_dps"] = 5
        with self.assertRaisesRegex(ValueError, "Tank"):
            validate_catalog(d)
        d = make_doc()
        d["records"][0]["benchmark_dps"] = 5.0
        with self.assertRaisesRegex(ValueError, "disagree"):
            validate_catalog(d)

    def test_publish_csv_manifest_sqlite_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            src = p / "source.json"
            src.write_text(json.dumps(make_doc()), encoding="utf-8")
            args = [p / "raw.csv", p / "norm.csv", p / "summary.csv", p / "manifest.json"]
            sqlite = p / "db.sqlite"
            output = publish_catalog(src, *args, sqlite_path=sqlite)
            self.assertEqual(output["counts"]["listed_builds"], 2)
            self.assertEqual(output["counts"]["tank_builds"], 1)
            self.assertEqual(output["counts"]["filtered_damage_builds"], 1)
            with sqlite3.connect(sqlite) as conn:
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM codex_builds").fetchone()[0], 2)
                self.assertEqual(conn.execute("SELECT benchmark_dps FROM codex_builds WHERE name='B'").fetchone()[0], None)
            before = [f.read_bytes() for f in [*args, sqlite]]
            d = make_doc()
            d["records"][1]["source_url"] = "https://another.site/b"
            src.write_text(json.dumps(d), encoding="utf-8")
            with self.assertRaises(ValueError):
                publish_catalog(src, *args, sqlite_path=sqlite)
            self.assertEqual(before, [f.read_bytes() for f in [*args, sqlite]])

    def test_existing_skill_panels_join_without_fake_catalog_membership(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            snap = Path("data/reference/codex_published_build_catalog.json")
            skill = Path("data/reference/codex_skill_panel_observations.json")
            r = publish_catalog(snap, p / "raw.csv", p / "norm.csv",
                 p / "summary.csv", p / "manifest.json",
                 sqlite_path=p / "builds.sqlite", skill_snapshot=skill)
            self.assertEqual(r["counts"]["listed_builds"], 327)
            self.assertEqual(r["counts"]["skill_panels"], 122)
            with sqlite3.connect(p / "builds.sqlite") as c:
                self.assertEqual(c.execute("SELECT COUNT(*) FROM codex_builds").fetchone()[0], 327)
                self.assertEqual(c.execute("SELECT COUNT(*) FROM codex_skill_panels").fetchone()[0], 122)

if __name__ == "__main__":
    unittest.main()
