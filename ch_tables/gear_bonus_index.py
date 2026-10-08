"""Expand every accessible item bonus into analyzable factual rows.

No undocumented percentages or extrapolated game effects are invented.
The source item stats fields are copied exactly, preserving variable-length tuples.

python -m ch_tables.gear_bonus_index --data data/game
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from .full_game_ingest import canonical_json, gzip_deterministic, jsonl_bytes
from .game_query import load_records

CATEGORIES = ("attributes", "abilities", "skillBonuses", "resists", "evasions")


def index_items(items):
    entries = []
    cardinalities = Counter()
    source_values = defaultdict(Counter)
    examples = {}
    stats_keys = Counter()
    for item in items:
        stats = item.get("stats")
        if not isinstance(stats, dict):
            continue
        stats_keys.update(stats)
        for category in CATEGORIES:
            values = stats.get(category, [])
            if values is None:
                continue
            if not isinstance(values, list):
                raise ValueError(f"Unexpected bonus collection {category}")
            for val in values:
                if not isinstance(val, (list, tuple)) or len(val) < 2:
                    raise ValueError(f"Malformed bonus {category} item {item['id']}")
                name = str(val[0])
                row = {"item_id": item["id"], "item_name": item["name"],
                       "category": category, "stat": name, "source_values": val[1:]}
                entries.append(row)
                cardinalities[category] += 1
                source_values[category][name] += 1
                examples.setdefault(category + ":" + name, row)
    entries.sort(key=lambda r: (r["category"], r["stat"].casefold(),
                                str(r["item_id"]), str(r["source_values"])))
    return entries, {
        "total_entries": len(entries),
        "category_entry_counts": dict(cardinalities),
        "distinct_stats": {k: len(v) for k, v in source_values.items()},
        "stat_name_counts": {k: dict(v.most_common()) for k, v in source_values.items()},
        "raw_item_stat_fields": dict(stats_keys.most_common()),
        "examples": examples,
        "interpretation_warning": "Source tuples preserve game-specific auxiliary "
                                  "numbers; do not assume unknown trailing fields "
                                  "are damage, duration or proc probability.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/game"))
    opts = parser.parse_args()
    input_path = opts.data / "items.jsonl.gz"
    original = input_path.read_bytes()
    entries, summary = index_items(load_records("items", root=opts.data))
    source_sha = hashlib.sha256(original).hexdigest()
    manifest_path = opts.data / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest["generated_files"]["items.jsonl.gz"]["sha256"] != source_sha:
        raise ValueError("Item archive differs from verified source manifest")
    target_data = gzip_deterministic(jsonl_bytes(entries))
    summary["source_item_archive_sha256"] = source_sha
    summary["source_repo"] = manifest["upstream_repo"]
    summary["source_commit"] = manifest["upstream_commit"]
    summary["index_sha256"] = hashlib.sha256(target_data).hexdigest()
    payloads = {
        "all_item_bonuses.jsonl.gz": target_data,
        "all_bonus_names.json": canonical_json(summary),
    }
    for name, payload in payloads.items():
        pending = opts.data / (name + ".tmp")
        pending.write_bytes(payload)
        pending.replace(opts.data / name)
    print(json.dumps({
        "bonus_rows": len(entries),
        "categories": summary["category_entry_counts"],
        "distinct_stats": summary["distinct_stats"],
    }))


if __name__ == "__main__":
    main()
