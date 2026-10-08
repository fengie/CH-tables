"""Separate item-name rarity/tier labels from empirically observed drop rates.

Source 'rarity' and affix tiers are item metadata, NOT drop probabilities.
When rarity is absent retain unknown (do not infer "common" from no label).
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from .full_game_ingest import canonical_json, gzip_deterministic, jsonl_bytes
from .game_query import load_records

PREFIXES = (
    "Common", "Uncommon", "Rare", "Mighty", "Majestic", "Royal",
    "Imperial", "Godly", "Void", "Shadow", "Spirit",
    "Exalted", "Blessed", "Legendary", "Mythic",
)
PATTERN = re.compile(r"^(?:" + "|".join(PREFIXES) + r")\b", re.I)


def label_item(item: dict) -> dict:
    raw = item.get("rarity")
    name = str(item["name"])
    title_match = PATTERN.match(name)
    title_tier = title_match.group(0).title() if title_match else None
    return {
        "item_id": item["id"],
        "name": name,
        "item_rarity_source_value": raw,
        "name_prefix_tier": title_tier,
        "rarity_status": "explicit_source_field" if raw is not None
                         else "name_pattern_only" if title_tier else "unknown",
        "observed_drop_probability": None,
        "observed_drop_probability_confidence": "not_measured",
        "warning": "Item rarity label, prefix, color, or tier is NOT a drop rate. "
                   "Name prefix is an ambiguous descriptor, not official rarity.",
    }


def create_metadata(items: list[dict]) -> tuple[list[dict], dict]:
    entries = [label_item(i) for i in items]
    by_prefix = Counter(x["name_prefix_tier"] for x in entries if x["name_prefix_tier"])
    by_status = Counter(x["rarity_status"] for x in entries)
    return entries, {
        "source_items": len(items),
        "rarity_field_coverage": dict(by_status),
        "name_prefix_tier_counts": dict(by_prefix.most_common()),
        "drop_chances_populated": 0,
        "rule": "Never substitute rarity labels for Bernoulli drop rates.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/game"))
    args = parser.parse_args()
    src = args.data / "items.jsonl.gz"
    manifest = json.loads((args.data / "manifest.json").read_text())
    if hashlib.sha256(src.read_bytes()).hexdigest() != \
       manifest["generated_files"]["items.jsonl.gz"]["sha256"]:
        raise ValueError("Item source integrity mismatch")
    records, summary = create_metadata(list(load_records("items", root=args.data)))
    summary["source_commit"] = manifest["upstream_commit"]
    summary["source_item_archive_sha256"] = manifest["generated_files"]["items.jsonl.gz"]["sha256"]
    body = gzip_deterministic(jsonl_bytes(records))
    summary["index_sha256"] = hashlib.sha256(body).hexdigest()
    output = {
        "item_rarity_metadata.jsonl.gz": body,
        "item_rarity_summary.json": canonical_json(summary),
    }
    for filename, content in output.items():
        p = args.data / filename
        pending = p.with_name(p.name + ".tmp")
        pending.write_bytes(content)
        pending.replace(p)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
