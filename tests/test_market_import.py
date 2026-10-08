import tempfile
from pathlib import Path
import unittest

from ch_tables.market_import import (
    read_validated_csv, load_market_rows, summarize_prices,
    PRICE_HEADERS, DROP_HEADERS,
)


class MarketImportTests(unittest.TestCase):
    def test_empty_submissions_publish_unknown(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            (root / "prices.csv").write_text(",".join(PRICE_HEADERS) + "\n")
            (root / "drops.csv").write_text(",".join(DROP_HEADERS) + "\n")
            ps, ds = load_market_rows(root, {1: "Sword"}, {10})
            self.assertEqual(ps, [])
            self.assertEqual(ds, [])
            summary = summarize_prices(ps, ds)
            self.assertEqual(summary["prices_submitted"], 0)
            self.assertEqual(summary["price_by_item_world"], [])

    def test_real_price_kind_and_no_fake_completed_sale(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            (root / "prices.csv").write_text(
                ",".join(PRICE_HEADERS) + "\n" +
                "1,Epona,1000000,2026-10-08,sale_listing,https://example.com/a,Sword,1,sample-1\n"
            )
            (root / "drops.csv").write_text(",".join(DROP_HEADERS) + "\n")
            ps, ds = load_market_rows(root, {1: "Sword"}, {10})
            summary = summarize_prices(ps, ds)
            self.assertEqual(summary["price_by_item_world"][0]["completed_sales"], 0)
            self.assertIsNone(summary["price_by_item_world"][0]["sold_median_gold"])
            self.assertEqual(summary["price_by_item_world"][0]["asking_median_gold"],
                             1_000_000)
            with self.assertRaisesRegex(ValueError, "unknown item ID"):
                load_market_rows(root, {2: "Other"}, {10})

    def test_invalid_csv_schema_fails(self):
        with tempfile.TemporaryDirectory() as path:
            root = Path(path)
            (root / "prices.csv").write_text("some,bad,headers\n")
            with self.assertRaisesRegex(ValueError, "header mismatch"):
                read_validated_csv(root / "prices.csv", PRICE_HEADERS)


if __name__ == "__main__":
    unittest.main()
