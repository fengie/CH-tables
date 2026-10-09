"""GitHub monorepo smoke: ensure AION 2 source and its six tests remain runnable."""
from pathlib import Path
import subprocess
import sys
import unittest

APP = Path(__file__).resolve().parents[1] / 'apps' / 'aion2-value-atlas'

class AionAtlasIntegrationTests(unittest.TestCase):
    def test_embedded_atlas_project(self):
        self.assertTrue((APP / 'data' / 'catalog.json').is_file())
        self.assertTrue((APP / 'src' / 'app.template.html').is_file())
        p = subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=APP,capture_output=True,text=True,timeout=90)
        self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
