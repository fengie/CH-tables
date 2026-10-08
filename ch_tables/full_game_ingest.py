"""Deterministic, fail-closed ingestion of ALL accessible public CH Encyclopedia facts.

No executable JavaScript, game binaries, images, dialogue or descriptions are
copied. Numeric/structural game-data fields and item/mob names are retained.
Each upstream source is pinned to an exact Git commit for reproducibility.

python -m ch_tables.full_game_ingest --output data/game
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from datetime import date
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
from urllib.request import Request, urlopen

from .catalog_ingest import (
    UPSTREAM_COMMIT, UPSTREAM_REPO, extract_json_literal,
)

ASSETS = (
    "data/base.js",
    "data/items-01.js",
    "data/items-02.js",
    "data/mobstats-all.js",
    "data/mobstats.js",
)
MAX_BYTES = 36_000_000
BANNED_KEYS = frozenset({
    "description", "longDescription", "dialogue", "dialog", "lore",
    "flavorText", "flavourText", "story", "image", "imageUrl",
    "icon", "iconUrl", "texture", "sprite", "artwork",
})
MIN_ITEMS = 10000
MIN_MOBS = 100
MIN_COMBAT = 100
MAX_ITEMS = 1000000
MAX_MOBS = 1000000
MAX_COMBAT = 1000000


def source_url(path: str) -> str:
    if path not in ASSETS:
        raise ValueError(f"Unapproved upstream asset: {path}")
    return (
        f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/"
        f"{UPSTREAM_COMMIT}/{path}"
    )


def fetch_assets(*, timeout: int = 65) -> dict[str, tuple[str, str]]:
    out = {}
    for asset in ASSETS:
        req = Request(source_url(asset), headers={
            "User-Agent": "CH-tables-research/1.0 public factual data"
        })
        with urlopen(req, timeout=timeout) as response:
            body = response.read(MAX_BYTES + 1)
        if not body or len(body) > MAX_BYTES:
            raise ValueError(f"Missing or oversized input: {asset}")
        out[asset] = (body.decode("utf-8-sig"), hashlib.sha256(body).hexdigest())
    return out


def factual_only(value):
    """Remove creative/non-stat text fields and presentation assets recursively."""
    if isinstance(value, dict):
        return {k: factual_only(v) for k, v in value.items()
                if k not in BANNED_KEYS and not k.lower().endswith("html")}
    if isinstance(value, list):
        return [factual_only(v) for v in value]
    return value


def unique_records(records, *, kind: str):
    seen: dict[str, dict] = {}
    conflict = []
    for rec in records:
        if not isinstance(rec, dict):
            raise ValueError(f"Non-object {kind} record")
        if rec.get("id") is None or not rec.get("name"):
            raise ValueError(f"{kind} record lacks id/name")
        key = str(rec["id"])
        normalized = factual_only(rec)
        if key in seen and seen[key] != normalized:
            conflict.append(key)
        seen[key] = normalized
    if conflict:
        raise ValueError(f"Conflicting duplicated {kind} ids: {conflict[:8]}")
    return [seen[k] for k in sorted(seen, key=lambda x: (int(x) if x.isdigit() else 10**15, x))]


def extract_relations(items: list[dict], mobs: list[dict]):
    """Retain exact item drop evidence, but don't invent missing probabilities."""
    drop_records = []
    references = []
    for mob in mobs:
        mid = mob["id"]
        for drop in mob.get("drops", []) or []:
            if isinstance(drop, dict):
                # Keep raw drop information: list may represent potential drops,
                # nested tables, or item-group references.
                drop_records.append({"mob_id": mid, "record": factual_only(drop)})
            elif isinstance(drop, (int, str)):
                drop_records.append({"mob_id": mid, "record": {"raw": drop}})
    for item in items:
        for mob in item.get("mobs", []) or []:
            references.append({"item_id": item["id"], "mob_reference": factual_only(mob)})
    return drop_records, references


def enumerate_structural_fields(data: list[dict], max_depth: int = 5) -> dict:
    """Count observed paths rather than assuming names imply game semantics."""
    counter = Counter()
    examples = {}
    def walk(o, path="", depth=0):
        if depth > max_depth:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                here = f"{path}.{k}" if path else k
                counter[here] += 1
                if here not in examples:
                    examples[here] = {"type": type(v).__name__,
                                      "example": str(v)[:90] if not isinstance(v, (dict, list)) else None}
                if isinstance(v, (dict, list)):
                    walk(v, here, depth + 1)
        elif isinstance(o, list):
            for v in o[:12]:
                if isinstance(v, (dict, list)):
                    walk(v, f"{path}[]", depth + 1)
    for x in data:
        walk(x)
    return {
        "total": len(data),
        "field_counts": dict(counter.most_common()),
        "field_examples": examples,
    }


def prepare(assets: dict[str, tuple[str, str]]):
    if set(assets) != set(ASSETS):
        raise ValueError("Missing or extra source assets")
    parsed = {key: extract_json_literal(script)
              for key, (script, _) in assets.items()}
    base = parsed["data/base.js"]
    if not isinstance(base, dict) or not isinstance(base.get("mobs"), list):
        raise ValueError("Base data schema drift: expected object.mobs array")
    mobs = unique_records(base["mobs"], kind="mob")
    chunks = []
    for path in ("data/items-01.js", "data/items-02.js"):
        block = parsed[path]
        if not isinstance(block, list):
            raise ValueError(f"{path}: expected chunk list")
        chunks.extend(block)
    items = unique_records(chunks, kind="item")
    # Full combat records may share ids with 71-record spotlight; dedup by id,
    # but refuse conflicting numeric record and prefer the much larger source.
    combat = parsed["data/mobstats-all.js"]
    spotlight = parsed["data/mobstats.js"]
    if not isinstance(combat, list) or not isinstance(spotlight, list):
        raise ValueError("Expected MOB_STATS arrays")
    if not (MIN_ITEMS <= len(items) <= MAX_ITEMS):
        raise ValueError(f"Unexpected item cardinality {len(items)}")
    if not (MIN_MOBS <= len(mobs) <= MAX_MOBS):
        raise ValueError(f"Unexpected mob cardinality {len(mobs)}")
    if not (MIN_COMBAT <= len(combat) <= MAX_COMBAT):
        raise ValueError(f"Unexpected combat cardinality {len(combat)}")
    combat = unique_records(combat, kind="combat")
    # Spotlight is a subset index and may be older/different; retain evidence
    # separately and disclose discrepancies rather than merging deceptively.
    spotlight = unique_records(spotlight, kind="spotlight")
    main_combat = {str(x["id"]): x for x in combat}
    mismatch = [x["id"] for x in spotlight
                if str(x["id"]) in main_combat and x != main_combat[str(x["id"])]]
    quests = factual_only(base.get("questlines", {}))
    if not isinstance(quests, dict) or not quests:
        raise ValueError("No structured questline data found")
    drops, references = extract_relations(items, mobs)
    base_other = {
        key: factual_only(value) for key, value in base.items()
        if key not in ("mobs", "items", "questlines")
        and isinstance(value, (dict, list))
    }
    sections = {
        "items": items,
        "mobs": mobs,
        "combat_mobs": combat,
        "spotlight_mobs": spotlight,
        "mob_drop_records": drops,
        "item_mob_references": references,
        "questlines": quests,
        "other_structured_base": base_other,
    }
    manifest = {
        "schema_version": 1,
        "snapshot_date": date.today().isoformat(),
        "upstream_repo": UPSTREAM_REPO,
        "upstream_commit": UPSTREAM_COMMIT,
        "extractor": "nonexecuting_json_literal_parser",
        "content_policy": "factual_structured_data_no_description_dialogue_media",
        "source_assets": {
            path: {"url": source_url(path), "sha256": digest, "bytes": len(script.encode("utf-8"))}
            for path, (script, digest) in assets.items()
        },
        "counts": {key: len(data) if hasattr(data, "__len__") else None
                   for key, data in sections.items()},
        "base_root_keys": list(base.keys()),
        "spotlight_combat_conflicting_ids": mismatch[:100],
        "spotlight_conflict_count": len(mismatch),
        "notes": [
            "Source may include unreleased/test items; not live server truth",
            "Drops are observed source references, not probabilistic drop rates",
            "Monster combat stats may refer to another game version",
            "Questlines are curated progression references, not complete quests",
            "The 122 Codex skill panel samples are a separate community dataset",
        ],
    }
    return sections, manifest


def canonical_json(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def jsonl_bytes(records) -> bytes:
    return b"".join(canonical_json(x) for x in records)


def gzip_deterministic(body: bytes) -> bytes:
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode="wb", mtime=0,
                       compresslevel=9, filename="") as fh:
        fh.write(body)
    return stream.getvalue()


def build_outputs(sections: dict, manifest: dict) -> dict[str, bytes]:
    blobs = {}
    for key, value in sections.items():
        if isinstance(value, list):
            raw = jsonl_bytes(value)
            fmt = "jsonl"
        else:
            raw = canonical_json(value)
            fmt = "json"
        path = f"{key}.{fmt}.gz"
        zipped = gzip_deterministic(raw)
        blobs[path] = zipped
        manifest.setdefault("generated_files", {})[path] = {
            "rows": len(value), "uncompressed_bytes": len(raw),
            "compressed_bytes": len(zipped),
            "sha256": hashlib.sha256(zipped).hexdigest(),
            "format": fmt, "encoding": "gzip",
        }
    # GitHub-diffable name-only index; this is not a claim of unobtainability.
    index = "\n".join(
        f'{r["id"]}\t{str(r["name"]).replace(chr(9), " ").replace(chr(10), " ")}'
        for r in sections["items"]
    ) + "\n"
    blobs["item_names.tsv"] = index.encode("utf-8")
    manifest["generated_files"]["item_names.tsv"] = {
        "rows": len(sections["items"]),
        "sha256": hashlib.sha256(blobs["item_names.tsv"]).hexdigest(),
        "format": "tsv",
    }
    summaries = {}
    for key in ("items", "mobs", "combat_mobs"):
        summaries[key] = enumerate_structural_fields(sections[key], max_depth=2)
    blobs["field_inventory.json"] = canonical_json(summaries)
    manifest["generated_files"]["field_inventory.json"] = {
        "sha256": hashlib.sha256(blobs["field_inventory.json"]).hexdigest(),
        "format": "json",
    }
    blobs["manifest.json"] = canonical_json(manifest)
    return blobs


def write_outputs(directory: Path, outputs: dict[str, bytes]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    # Stage all outputs; write manifest LAST as a generation marker.
    for filename in sorted(outputs, key=lambda k: k == "manifest.json"):
        destination = directory / filename
        pending = destination.with_name(destination.name + ".tmp")
        pending.write_bytes(outputs[filename])
        pending.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/game"))
    opts = parser.parse_args()
    assets = fetch_assets()
    sections, manifest = prepare(assets)
    output = build_outputs(sections, manifest)
    write_outputs(opts.output, output)
    print(json.dumps({
        "counts": manifest["counts"], "files": manifest["generated_files"],
        "spotlight_conflicts": manifest["spotlight_conflict_count"],
        "root_keys": manifest["base_root_keys"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
