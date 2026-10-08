"""Create compact human-auditable gear candidates from the full Rogue catalog.

This is evidence indexing, not a "best item" ranking. Raw item stats are
retained; undocumented stat-key semantics are not guessed.
"""
from __future__ import annotations

from collections import Counter
import argparse
import json
from pathlib import Path


CATEGORIES = {
    "knuckleblades": ("knuckle", "fist"),
    "dhiothu_named": ("dhiothu",),
    "doch_gul": ("doch gul",),
    "blight": ("blight",),
    "ferocity": ("ferocity",),
    "concealment": ("concealment",),
    "valley_of_ancients": ("valley",),
    "proteus": ("proteus",),
    "hasted": ("hasted",),
    "vested": ("vested",),
}
SHORTLIST_LIMIT = 120


def summarize_items(items: list[dict]) -> tuple[dict, dict]:
    index = {
        "schema_version": 1,
        "method": "case_insensitive_name_search_not_BIS_ranking",
        "source": "data/catalog/rogue_endgame_items.json",
        "categories": {},
    }
    for category, needles in CATEGORIES.items():
        matches = [i for i in items if any(n in str(i.get("name", "")).casefold()
                                            for n in needles)]
        matches.sort(key=lambda i: (-(i.get("level") or 0),
                                    str(i.get("name", "")).casefold()))
        index["categories"][category] = {
            "count": len(matches),
            "truncated": len(matches) > SHORTLIST_LIMIT,
            "entries": [
                {k: i.get(k) for k in ("id", "name", "level", "class", "slot", "stats")}
                for i in matches[:SHORTLIST_LIMIT]
            ]
        }
    keycounts = Counter()
    shape_examples = {}
    class_counts = Counter()
    slot_counts = Counter()
    for item in items:
        stats = item.get("stats") or {}
        for key in stats:
            keycounts[key] += 1
            if key not in shape_examples:
                shape_examples[key] = {"item": item.get("name"), "example_value": stats[key]}
        class_counts[str(item.get("class"))] += 1
        slot_counts[str(item.get("slot"))] += 1
    schema = {
        "total_items": len(items),
        "numeric_and_categorical_field_counts": dict(keycounts.most_common()),
        "field_examples": shape_examples,
        "class_counts": dict(class_counts.most_common()),
        "slot_counts": dict(slot_counts.most_common()),
        "warning": "Raw upstream item/stat fields may contain undocumented encodings. "
                   "Counts refer only to filtered endgame/rogue data.",
    }
    return index, schema


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", type=Path,
                        default=Path("data/catalog/rogue_endgame_items.json"))
    opts = parser.parse_args()
    items = json.loads(opts.catalog.read_text(encoding="utf-8"))
    index, schema = summarize_items(items)
    out = opts.catalog.parent
    for filename, payload in (
        ("priority_gear_lookup.json", index),
        ("item_stat_schema.json", schema),
    ):
        (out / filename).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(json.dumps({k: v["count"] for k, v in index["categories"].items()}))


if __name__ == "__main__":
    main()
