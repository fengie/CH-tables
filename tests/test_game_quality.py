import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from ch_tables import full_game_ingest as f
from ch_tables.game_quality import audit
from tests.test_full_game_ingest import fixture


class GameQualityTests(unittest.TestCase):
    def test_source_integrity_and_referential_counts(self):
        with mock.patch.object(f, "MIN_ITEMS", 1), \
             mock.patch.object(f, "MIN_MOBS", 1), \
             mock.patch.object(f, "MIN_COMBAT", 1):
            sections, manifest = f.prepare(fixture())
        with TemporaryDirectory() as td:
            root = Path(td)
            f.write_outputs(root, f.build_outputs(sections, manifest))
            result = audit(root)
            self.assertTrue(result["provenance"]["sha256_verified"])
            self.assertEqual(result["counts"]["items"], 2)
            self.assertEqual(result["counts"]["mob_drop_refs_resolve_to_item_index"], 1)
            self.assertEqual(result["counts"]["mob_drop_refs_item_id_not_in_index"], 0)
            self.assertEqual(result["counts"]["item_mob_refs_with_absent_item"], 0)
            with (root / "item_names.tsv").open("a") as out:
                out.write("corrupt\n")
            with self.assertRaisesRegex(ValueError, "Source file changed"):
                audit(root)


if __name__ == "__main__":
    unittest.main()
