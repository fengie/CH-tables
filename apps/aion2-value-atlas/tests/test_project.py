import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from economics import normalized, optimize

class AtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/catalog.json').read_text(encoding='utf-8'))
        cls.packs = cls.data['packs']

    def test_normalized_four_thousand(self):
        result = normalized(self.packs, 4000)
        self.assertEqual([(r['count'],r['usd_cents'],r['mileage']) for r in result], [(10,5990,8650),(4,5996,8600),(2,5998,8700),(1,5999,8650)])

    def test_mileage_and_quna_winner_not_conflated(self):
        self.assertEqual(max(self.packs,key=lambda x:x['mileage']/x['usd_cents'])['id'],'q2000')
        self.assertEqual(max(self.packs,key=lambda x:x['quna']/x['usd_cents'])['id'],'q400')

    def test_optimizer_budgets_and_accounting(self):
        for budget in [0,599,1499,3000,6000,10000,30000,50000]:
            for weight in [0,0.004,0.03]:
                result = optimize(self.packs,budget,weight)
                self.assertLessEqual(result['spent_cents'],budget)
                self.assertEqual(result['spent_cents'],sum(p['usd_cents']*result['counts'][p['id']] for p in self.packs))
                self.assertEqual(result['quna'],sum(p['quna']*result['counts'][p['id']] for p in self.packs))
                self.assertEqual(result['mileage'],sum(p['mileage']*result['counts'][p['id']] for p in self.packs))

    def test_every_record_has_known_source(self):
        known={source['id'] for source in self.data['sources']}
        for group in ('packs','products','patches'):
            for item in self.data[group]:
                self.assertTrue(item['source_ids'])
                self.assertTrue(set(item['source_ids'])<=known)
        self.assertEqual(len(self.data['mileage_items']),10)

    def test_no_unverified_mileage_double_credit(self):
        for item in self.data['products']:
            if item.get('quna') and item['quna'] > 0:
                self.assertIsNone(item['mileage'],f"Assumed mileage from spending Quna: {item['name']}")

    def test_offline_build_deterministic_and_embedded_js_parses(self):
        before=(ROOT/'index.html').read_bytes()
        subprocess.run([sys.executable,str(ROOT/'scripts/build.py')],check=True,capture_output=True)
        after=(ROOT/'index.html').read_bytes()
        self.assertEqual(before,after)
        script=re.search(r'<script>\s*(.*?)\s*</script>',after.decode(),re.S).group(1)
        path=ROOT/'tests/.script-check.js'
        try:
            path.write_text(script,encoding='utf-8')
            subprocess.run(['node','--check',str(path)],check=True,capture_output=True)
        finally:
            path.unlink(missing_ok=True)

if __name__=='__main__':
    unittest.main()
