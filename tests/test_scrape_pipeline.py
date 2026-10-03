from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import ch_tables.scrape as scrape_module
from ch_tables.scrape import SourceSchemaError, parse_saved_builds_page, refresh_dataset


GOOD_HTML = """
<html><body>
<table><tr><th>Unrelated</th></tr><tr><td>ignore me</td></tr></table>
<table>
  <thead><tr>
    <th>Build</th><th>Class</th><th>Level</th>
    <th>Build Type info Damage builds show benchmark DPS.</th>
    <th>Description</th><th>Created</th><th>Actions</th>
  </tr></thead>
  <tbody>
    <tr>
      <td><a href="/damagebuilder/test-warrior">Test Warrior</a> Damage</td>
      <td>Warrior</td><td>233</td><td>12000.0 DPS</td>
      <td>fixture</td><td>Oct 3, 2026</td><td>Open</td>
    </tr>
    <tr>
      <td><a href="/damagebuilder/test-ranger">Test Ranger</a> Damage</td>
      <td>Ranger</td><td>230</td><td>9000.0 DPS</td>
      <td>fixture 2</td><td>Oct 3, 2026</td><td>Open</td>
    </tr>
  </tbody>
</table>
</body></html>
"""

DRIFT_HTML = """
<table>
  <tr>
    <th>Build</th><th>Class</th><th>Level</th>
    <th>Power</th><th>Description</th><th>Created</th>
  </tr>
  <tr>
    <td>Broken</td><td>Warrior</td><td>233</td>
    <td>12000 DPS</td><td>fixture</td><td>Oct 3, 2026</td>
  </tr>
</table>
"""


class ScrapePipelineTests(unittest.TestCase):
    def test_semantic_table_selection_ignores_unrelated_first_table(self) -> None:
        rows = parse_saved_builds_page(GOOD_HTML, "https://the-codex.ch/builds?utm_source=test")
        self.assertEqual([row.name for row in rows], ["Test Warrior", "Test Ranger"])
        self.assertEqual(rows[0].build_url, "https://the-codex.ch/damagebuilder/test-warrior")
        self.assertEqual(rows[0].source_url, "https://the-codex.ch/builds")

    def test_schema_drift_fails_closed(self) -> None:
        with self.assertRaises(SourceSchemaError):
            parse_saved_builds_page(DRIFT_HTML)

    def test_failed_refresh_preserves_published_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            root = Path(root_text)
            raw = root / "raw.csv"
            normalized = root / "normalized.csv"
            summary = root / "summary.csv"
            manifest = root / "manifest.json"
            snapshots = root / "snapshots"
            for path, content in (
                (raw, "old raw\n"),
                (normalized, "old normalized\n"),
                (summary, "old summary\n"),
                (manifest, '{"old": true}\n'),
            ):
                path.write_text(content, encoding="utf-8")
            before = {path: path.read_bytes() for path in (raw, normalized, summary, manifest)}

            with patch(
                "ch_tables.scrape.fetch_saved_builds_source",
                return_value=(
                    DRIFT_HTML,
                    {"source_url": "https://the-codex.ch/builds", "etag": "", "last_modified": ""},
                ),
            ):
                with self.assertRaises(SourceSchemaError):
                    refresh_dataset(
                        raw, normalized, summary,
                        manifest_path=manifest,
                        snapshot_dir=snapshots,
                    )

            self.assertEqual(
                before,
                {path: path.read_bytes() for path in (raw, normalized, summary, manifest)},
            )

    def test_mid_publication_failure_rolls_back_previous_generation(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            root = Path(root_text)
            raw = root / "raw.csv"
            normalized = root / "normalized.csv"
            summary = root / "summary.csv"
            manifest = root / "manifest.json"
            snapshots = root / "snapshots"
            for path, content in (
                (raw, "old raw\n"),
                (normalized, "old normalized\n"),
                (summary, "old summary\n"),
                (manifest, '{"old": true}\n'),
            ):
                path.write_text(content, encoding="utf-8")
            before = {
                path: path.read_bytes()
                for path in (raw, normalized, summary, manifest)
            }

            real_publish = scrape_module._publish_file
            calls = 0

            def fail_second_publish(staged: Path, destination: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected publication failure")
                real_publish(staged, destination)

            with patch(
                "ch_tables.scrape.fetch_saved_builds_source",
                return_value=(
                    GOOD_HTML,
                    {
                        "source_url": "https://the-codex.ch/builds",
                        "etag": "",
                        "last_modified": "",
                    },
                ),
            ), patch(
                "ch_tables.scrape._publish_file",
                side_effect=fail_second_publish,
            ):
                with self.assertRaises(OSError):
                    refresh_dataset(
                        raw,
                        normalized,
                        summary,
                        manifest_path=manifest,
                        snapshot_dir=snapshots,
                    )

            self.assertEqual(
                before,
                {
                    path: path.read_bytes()
                    for path in (raw, normalized, summary, manifest)
                },
            )

    def test_successful_refresh_publishes_manifest_and_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as root_text:
            root = Path(root_text)
            raw = root / "raw.csv"
            normalized = root / "normalized.csv"
            summary = root / "summary.csv"
            manifest = root / "manifest.json"
            snapshots = root / "snapshots"

            with patch(
                "ch_tables.scrape.fetch_saved_builds_source",
                return_value=(
                    GOOD_HTML,
                    {
                        "source_url": "https://the-codex.ch/builds",
                        "etag": '"fixture"',
                        "last_modified": "Sat, 03 Oct 2026 00:00:00 GMT",
                    },
                ),
            ):
                raw_count, normalized_count = refresh_dataset(
                    raw, normalized, summary,
                    manifest_path=manifest,
                    snapshot_dir=snapshots,
                    snapshot_retention=2,
                )

            self.assertEqual(raw_count, 2)
            self.assertEqual(normalized_count, 2)
            self.assertTrue(raw.exists())
            self.assertTrue(normalized.exists())
            self.assertTrue(summary.exists())
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["parser_schema_version"], 2)
            self.assertEqual(payload["rows"]["raw"], 2)
            self.assertEqual(payload["rows"]["normalized"], 2)
            self.assertEqual(payload["source"]["etag"], '"fixture"')
            self.assertEqual(len(list(snapshots.glob("*.html"))), 1)
            for output in ("raw", "normalized", "class_summary"):
                self.assertRegex(payload["outputs"][output]["sha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
