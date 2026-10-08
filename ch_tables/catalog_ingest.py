"""Pinned, non-executing CH Encyclopedia item catalog ingestion.

Fetches public JSON-bearing .js assets as DATA ONLY: no eval/Node/VM.
Fails closed on schema drift or unexpected upstream volume; records provenance.
Use:
    python -m ch_tables.catalog_ingest --output data/catalog
"""
from __future__ import annotations

import argparse
import hashlib
import json
from json import JSONDecodeError
from pathlib import Path
import re
from urllib.request import Request, urlopen

UPSTREAM_REPO = "celtichero2026/CH-Encyclopedia"
UPSTREAM_COMMIT = "fb6d99ba035dd28e5df08e6303f653da0de9a024"
ASSETS = ("data/base.js", "data/items-01.js", "data/items-02.js")
USER_TERMS = (
    "knuckle", "dhiothu", "blight", "ferocity", "bloodthorn", "concealment",
    "proteus", "doch gul", "valley of", "vested", "hasted", "necro",
    "mordris", "gelebron", "charm", "bracelet", "ring", "amulet",
    "weapon", "offhand", "aura", "rogue", "hand to hand",
)
TARGET_OWNED = (
    "knuckle", "blight", "ferocity", "doch gul", "valley", "proteus",
    "concealment",
)
SOURCE_MAX_BYTES = 35_000_000
ASSIGNMENT = re.compile(
    r"(?:window\.)?[A-Za-z_$][\w.$]*\s*=\s*|"
    r"\.(?:push|concat)\s*\(\s*(?:\.\.\.)?",
)


def source_url(asset: str) -> str:
    if asset not in ASSETS:
        raise ValueError("Asset not in allowlist")
    return f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{UPSTREAM_COMMIT}/{asset}"


def download(asset: str, timeout_s: int = 50) -> tuple[str, str]:
    req = Request(source_url(asset), headers={"User-Agent": "CH-tables-research/1.0"})
    with urlopen(req, timeout=timeout_s) as response:
        body = response.read(SOURCE_MAX_BYTES + 1)
    if len(body) > SOURCE_MAX_BYTES:
        raise ValueError("Upstream asset exceeds data cap")
    text = body.decode("utf-8-sig")
    return text, hashlib.sha256(body).hexdigest()


def extract_json_literal(script: str):
    """Extract the one major JSON literal; reject non-JSON script transformations.

    Supports assignments, .push(...[items]), .concat([items]) and simple
    literal-prefixed JS bundles. This parser NEVER executes upstream JS.
    """
    decoder = json.JSONDecoder()
    candidate_positions: list[int] = []
    prefix = script[:4096]
    for match in ASSIGNMENT.finditer(prefix):
        for idx in range(match.end(), min(match.end() + 160, len(script))):
            if script[idx] in "[{":
                candidate_positions.append(idx)
                break
    for i, ch in enumerate(prefix):
        if ch in "[{":
            candidate_positions.append(i)
    successful = []
    for idx in dict.fromkeys(candidate_positions):
        try:
            value, last = decoder.raw_decode(script, idx)
            if isinstance(value, (dict, list)):
                successful.append((last - idx, value))
        except (JSONDecodeError, RecursionError):
            continue
    if not successful:
        raise ValueError("No valid JSON literal: upstream schema changed")
    size, value = max(successful, key=lambda pair: pair[0])
    if size < 100:
        raise ValueError("Suspiciously short upstream data literal")
    return value


def iter_items(node):
    """Traverse expected 'items' data containers without treating mobs as items."""
    if isinstance(node, dict):
        if isinstance(node.get("items"), list):
            for item in node["items"]:
                if isinstance(item, dict) and item.get("name") and item.get("id") is not None:
                    yield item
        for key, child in node.items():
            if key != "items" and isinstance(child, dict):
                yield from iter_items(child)
    elif isinstance(node, list):
        if any(isinstance(x, dict) and x.get("id") is not None and x.get("name")
               for x in node[:min(15, len(node))]):
            for x in node:
                if isinstance(x, dict) and x.get("name") and x.get("id") is not None:
                    yield x
        else:
            for x in node:
                if isinstance(x, dict):
                    yield from iter_items(x)


def get_int(*values) -> int | None:
    for x in values:
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return int(x)
        if isinstance(x, str) and x.strip().isdecimal():
            return int(x.strip())
    return None


def normalize_item(item: dict, source_asset: str) -> dict:
    stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
    fields = dict(stats)
    for key in ("slot", "class", "classReq", "classes", "level", "levelReq", "minLevel", "levelRequirement"):
        if key in item and key not in fields:
            fields[key] = item[key]
    normalized = {
        "id": item["id"],
        "name": str(item["name"]),
        "slot": fields.get("slot"),
        "class": fields.get("class", fields.get("classReq", fields.get("classes"))),
        "level": get_int(fields.get("level"), fields.get("levelReq"),
                         fields.get("minLevel"), fields.get("levelRequirement")),
        "stats": stats,
        "description": item.get("description"),
        "source_asset": source_asset,
    }
    for k in ("source", "sources", "effects", "requirements", "set", "rarity", "type"):
        if item.get(k) is not None:
            normalized[k] = item[k]
    return normalized


def relevant_item(item: dict) -> bool:
    """Broad endgame rogue + generic jewellery, no reliance on exact item names."""
    name = item["name"].casefold()
    slot = str(item.get("slot") or "").casefold()
    klass = str(item.get("class") or "").casefold()
    stats_blob = json.dumps(item.get("stats") or {}, ensure_ascii=False).casefold()
    high = item.get("level") is not None and item["level"] >= 170
    equipment = any(k in slot for k in (
        "ring", "brace", "neck", "amulet", "misc", "helm", "chest",
        "glove", "boot", "leg", "weapon", "offhand", "charm",
    ))
    chosen_keyword = any(k in name for k in USER_TERMS)
    is_rogue_or_universal = not klass or "rogue" in klass or "all" in klass
    # Include known special sets even if source metadata is sparse.
    owned_match = any(k in name for k in TARGET_OWNED)
    return (owned_match or
            (is_rogue_or_universal and high and (equipment or chosen_keyword)) or
            (is_rogue_or_universal and chosen_keyword and
             (equipment or "attack" in stats_blob or "damage" in stats_blob)))


def assemble(assets: dict[str, str]) -> tuple[list[dict], dict]:
    records: dict[str, dict] = {}
    manifest = {
        "schema_version": 1, "source_repository": UPSTREAM_REPO,
        "source_commit": UPSTREAM_COMMIT,
        "sources": [], "policy": "public-data-only_no_upstream_JS_execution",
    }
    for asset in ASSETS:
        script = assets[asset]
        parsed = extract_json_literal(script)
        found = list(iter_items(parsed))
        if not found and asset != ASSETS[0]:
            raise ValueError(f"No item records from {asset}: schema drift")
        if found:
            samples = [i for i in found if any(t in str(i.get("name", "")).casefold() for t in ("knuckle", "ferocity", "doch gul", "blight"))]
            print(f"asset {asset} records={len(found)} examples={[(i.get(chr(110)+chr(97)+chr(109)+chr(101)), i.get(chr(115)+chr(116)+chr(97)+chr(116)+chr(115))) for i in samples[:4]]}", flush=True)
        sha = hashlib.sha256(script.encode("utf-8")).hexdigest()
        manifest["sources"].append({
            "path": asset, "url": source_url(asset), "sha256_text": sha,
            "items_parsed": len(found),
        })
        for record in found:
            norm = normalize_item(record, asset)
            records[str(norm["id"])] = norm
    if len(records) < 500:
        raise ValueError("Far too few item records; upstream layout likely changed")
    selected = sorted((i for i in records.values() if relevant_item(i)),
                      key=lambda i: (i["name"].casefold(), str(i["id"])))
    if not selected:
        raise ValueError("No endgame rogue items found")
    manifest["total_unique_items"] = len(records)
    manifest["selected_relevant_items"] = len(selected)
    manifest["known_terms_found"] = {
        t: sum(t in it["name"].casefold() for it in selected)
        for t in TARGET_OWNED
    }
    manifest["missing_terms"] = [
        t for t, count in manifest["known_terms_found"].items() if count == 0
    ]
    return selected, manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/catalog"))
    opts = parser.parse_args()
    assets = {name: download(name)[0] for name in ASSETS}
    for name, script in assets.items():
        print(f"input {name}: {len(script)} chars, prefix={script[:160]!r}", flush=True)
    records, manifest = assemble(assets)
    opts.output.mkdir(parents=True, exist_ok=True)
    # Atomic publication for the data file; the manifest is published last.
    target = opts.output / "rogue_endgame_items.json"
    staged = target.with_suffix(".json.tmp")
    staged.write_text(json.dumps(records, ensure_ascii=False,
                                 separators=(",", ":")) + "\n", encoding="utf-8")
    staged.replace(target)
    manifest["catalog_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    last = opts.output / "catalog_manifest.json"
    last_tmp = last.with_suffix(".json.tmp")
    last_tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    last_tmp.replace(last)
    print(json.dumps({"total_unique_items": manifest["total_unique_items"],
                      "relevant": len(records),
                      "missing_terms": manifest["missing_terms"],
                      "sha256": manifest["catalog_sha256"]}))


if __name__ == "__main__":
    main()
