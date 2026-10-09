#!/usr/bin/env python3
"""Build self-contained offline app; fail closed on invalid catalog or broken citations."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
catalog = json.loads((root / 'data/catalog.json').read_text(encoding='utf-8'))
assert catalog['schema_version'] == 1
ids = {source['id'] for source in catalog['sources']}
assert len(ids) == len(catalog['sources'])
for group in ('packs', 'products', 'patches'):
    for record in catalog[group]:
        assert set(record['source_ids']) <= ids, (group, record)
for item in catalog['packs']:
    assert item['quna'] > 0 and item['usd_cents'] > 0 and item['mileage'] >= 0
for item in catalog['mileage_items']:
    assert item['mileage'] > 0
raw = json.dumps(catalog, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')
template = (root / 'src/app.template.html').read_text(encoding='utf-8')
assert template.count('/* DATA_INSERT */') == 1
out = template.replace('/* DATA_INSERT */', raw)
(root / 'index.html').write_text(out, encoding='utf-8')
print('Built index.html from structured, source-linked data.')
