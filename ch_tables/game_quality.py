"""Source consistency audit for the game-data reference; does not infer game mechanics.

python -m ch_tables.game_quality --data data/game
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path

from .full_game_ingest import canonical_json
from .game_query import load_records


def audit(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if "upstream_commit" not in manifest:
        raise ValueError("Missing source commit metadata")
    for filename, meta in manifest["generated_files"].items():
        p = root / filename
        if hashlib.sha256(p.read_bytes()).hexdigest() != meta["sha256"]:
            raise ValueError(f"Source file changed after verification: {filename}")
    items = list(load_records("items", root=root))
    mobs = list(load_records("mobs", root=root))
    combat = list(load_records("combat_mobs", root=root))
    spotlight = list(load_records("spotlight_mobs", root=root))
    drops = list(load_records("mob_drop_records", root=root))
    itemrefs = list(load_records("item_mob_references", root=root))
    item_ids = {str(r["id"]) for r in items}
    mob_ids = {str(r["id"]) for r in mobs}
    combat_by_id = {str(r["id"]): r for r in combat}
    linked_combat = mob_ids & set(combat_by_id)
    unresolved = Counter()
    linked = 0
    unidentifiable = 0
    for entry in drops:
        value = entry.get("record")
        if not isinstance(value, dict) or value.get("itemId") is None:
            unidentifiable += 1
        elif str(value["itemId"]) in item_ids:
            linked += 1
        else:
            unresolved[str(value["itemId"])] += 1
    item_ref_unmatched = sum(1 for e in itemrefs
                             if str(e.get("item_id")) not in item_ids)
    changed_keys = Counter()
    changed_examples = []
    for row in spotlight:
        newer = combat_by_id.get(str(row["id"]))
        if newer is None:
            changed_keys["absent_from_all_combat"] += 1
            continue
        differences = [
            key for key in set(row) | set(newer)
            if row.get(key) != newer.get(key)
        ]
        changed_keys.update(differences)
        if differences and len(changed_examples) < 12:
            changed_examples.append({
                "id": row["id"], "name": row.get("name"),
                "different_fields": sorted(differences),
            })
    return {
        "as_of": date.today().isoformat(),
        "provenance": {
            "source": manifest["upstream_repo"],
            "commit": manifest["upstream_commit"],
            "sha256_verified": True,
        },
        "counts": {
            "items": len(items), "loot_mobs": len(mobs),
            "combat_mobs": len(combat), "combat_linked_to_loot_mobs": len(linked_combat),
            "combat_unlinked_to_loot_mobs": len(combat) - len(linked_combat),
            "mob_drop_records": len(drops),
            "mob_drop_refs_resolve_to_item_index": linked,
            "mob_drop_refs_missing_item_id": unidentifiable,
            "mob_drop_refs_item_id_not_in_index": sum(unresolved.values()),
            "distinct_unmatched_drop_item_ids": len(unresolved),
            "item_mob_ref_records": len(itemrefs),
            "item_mob_refs_with_absent_item": item_ref_unmatched,
            "spotlight_mobs": len(spotlight),
        },
        "top_missing_drop_ids": unresolved.most_common(20),
        "spotlight_differences": {
            "affected_record_fields": dict(changed_keys.most_common()),
            "examples": changed_examples,
        },
        "not_covered": [
            "SkillTemplates full per-rank engine coefficients",
            "QuestTemplates full NPC/dialogue quest database",
            "PetAppearances and animation/graphics/assets",
            "Live-server loot probabilities and current combat scaling",
            "Unverified equipment speed, direct physical weapon damage and proc chances",
            "Whether legacy/development/test items are currently obtainable",
        ],
        "interpretation": "All numbers describe an extracted community snapshot, not live servers. "
                          "Absence of matching IDs or fields does not establish unobtainability.",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/game"))
    opts = parser.parse_args()
    report = audit(opts.data)
    target = opts.data / "quality_report.json"
    pending = target.with_name(target.name + ".tmp")
    pending.write_bytes(canonical_json(report))
    pending.replace(target)
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main()
