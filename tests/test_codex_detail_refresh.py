import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock

from ch_tables.codex_detail_refresh import pending_damage_urls, refresh_details
from ch_tables.codex_catalog import validate_catalog


class MockResponse:
    def __init__(self, url, html, status=200):
        self.url = url
        self.text = html
        self.content = html.encode("utf-8")
        self.status_code = status
    def raise_for_status(self):
        if self.status_code >= 400:
            raise ValueError("HTTP error")


class IncrementalDetailTests(unittest.TestCase):
    def setUp(self):
        self.c = Path("data/reference/codex_published_build_catalog.json")
        self.old = Path("data/reference/codex_skill_panel_observations.json")
        self.catalog = json.loads(self.c.read_text(encoding="utf-8"))
        self.base = json.loads(self.old.read_text(encoding="utf-8"))
        self.html = """<h3>Quick Strike</h3><div>Cooldown: 10s | Cast: 0s</div>
                    <div>Max Damage</div><div>100</div>
                    <div>Avg Damage</div><div>80</div>"""

    def test_class_balanced_pending_public_detail_urls(self):
        urls = pending_damage_urls(self.catalog, self.base)
        self.assertTrue(urls)
        self.assertTrue(all(u.startswith("https://the-codex.ch/damagebuilder/") for u in urls))
        self.assertTrue(set(urls).isdisjoint({x["url"] for x in self.base["snapshots"]}))
        self.assertEqual(len(urls), 306 - sum(
            s["url"] in {r.build_url for r in validate_catalog(self.catalog)
                        if r.build_type == "Damage"}
            for s in self.base["snapshots"]))

    def test_incremental_merge_keeps_original_observations_and_hash(self):
        pending = pending_damage_urls(self.catalog, self.base)
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "observations.json"
            dst.write_text(json.dumps(self.base), encoding="utf-8")
            transport = MagicMock()
            transport.get.return_value = MockResponse(pending[0], self.html)
            out = refresh_details(self.c, dst, limit=1, delay_s=1.0,
                                  transport=transport, sleeper=lambda n: None)
            self.assertEqual(out["status"], "published_incremental_source_index")
            self.assertEqual(out["new_builds"], 1)
            data = json.loads(dst.read_text(encoding="utf-8"))
            self.assertEqual(len(data["snapshots"]), len(self.base["snapshots"]) + 1)
            self.assertEqual(len(data["observations"]), len(self.base["observations"]) + 1)
            self.assertEqual(data["observations"][0], self.base["observations"][0])
            self.assertEqual(data["snapshots"][0], self.base["snapshots"][0])
            self.assertEqual(data["observations"][-1]["source_url"], pending[0])

    def test_invalid_html_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "obs.json"
            dst.write_text(json.dumps(self.base), encoding="utf-8")
            old = dst.read_bytes()
            transport = MagicMock()
            transport.get.side_effect = lambda u, **kw: MockResponse(u, "<h3>Nothing</h3>")
            out = refresh_details(self.c, dst, limit=1, transport=transport)
            self.assertEqual(out["status"], "no_new_valid_panels")
            self.assertEqual(dst.read_bytes(), old)

    def test_source_429_and_unbounded_crawl_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            dst = Path(d) / "obs.json"
            dst.write_text(json.dumps(self.base), encoding="utf-8")
            old = dst.read_bytes()
            transport = MagicMock()
            transport.get.side_effect = lambda u, **kw: MockResponse(u, "", status=429)
            with self.assertRaisesRegex(RuntimeError, "429"):
                refresh_details(self.c, dst, limit=1, transport=transport)
            self.assertEqual(dst.read_bytes(), old)
            with self.assertRaises(ValueError):
                refresh_details(self.c, dst, limit=200)
            with self.assertRaises(ValueError):
                refresh_details(self.c, dst, delay_s=0)

if __name__ == "__main__":
    unittest.main()
