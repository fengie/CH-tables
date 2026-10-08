"""Evidence-backed release state for item-database entries.

Source-derived loot, zone, and quest links are *signals*, never proof
that an item was released to players. Unknown != confirmed unreleased.

python -m ch_tables.release_status --data data/game --evidence data/release/evidence.json
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

from .full_game_ingest import canonical_json, gzip_deterministic, jsonl_bytes
from .game_query import load_records

STATUSES = frozenset({
    "released_documented", "historically_released",
    "confirmed_unreleased", "unverified",
})
EVIDENCE_TYPES = frozenset({
    "official_patch", "official_confirmation",
    "verified_in_game_screenshot", "documented_player_ownership",
    "historical_community_documentation", "developer_confirmation",
})
CONFIRMED_NEGATIVE_EVIDENCE = frozenset({
    "official_confirmation", "developer_confirmation",
})
RELEASED_EVIDENCE = EVIDENCE_TYPES - frozenset({"developer_confirmation"})
SOURCE_SIGNAL_NAMES = frozenset({
    "reconstructed_loot_reference",
    "curated_questline_reference",
    "unattributed_database_record",
})


def check_evidence(entries: list[dict], by_id: dict[str, dict]) -> dict[str, dict]:
    if not isinstance(entries, list):
        raise ValueError("Evidence must be a JSON list")
    result = {}
    for row in entries:
        if not isinstance(row, dict):
            raise ValueError("Evidence row must be an object")
        item_id = str(row.get("item_id"))
        matched = by_id.get(item_id)
        if not matched:
            raise ValueError(f"Item ID not found in source: {item_id}")
        if item_id in result:
            raise ValueError(f"Conflicting or duplicated evidence: {item_id}")
        name = str(row.get("exact_name", ""))
        if not name or name != matched["name"]:
            raise ValueError(f"Item identity/name changed: {item_id}, {name!r}")
        status = row.get("release_status")
        evidence_type = row.get("evidence_type")
        if status not in STATUSES - {"unverified"}:
            raise ValueError(f"Invalid explicit release status for {item_id}")
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"Invalid source evidence type for {item_id}")
        if status == "confirmed_unreleased" and evidence_type not in CONFIRMED_NEGATIVE_EVIDENCE:
            raise ValueError("Unreleased requires explicit developer or official confirmation")
        if status in ("released_documented", "historically_released") and \
           evidence_type not in RELEASED_EVIDENCE:
            raise ValueError("Positive release requires positive evidence")
        if status == "historically_released" and \
           not row.get("retirement_or_seasonality_evidence"):
            raise ValueError("Historical status needs retirement/seasonality evidence")
        source_url = row.get("url")
        parsed = urlparse(str(source_url))
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError(f"Bad public evidence URL: {item_id}")
        if evidence_type in ("official_patch", "official_confirmation",
                             "developer_confirmation"):
            host = (parsed.hostname or "").casefold()
            if host != "celtic-heroes.com" and not host.endswith(".celtic-heroes.com"):
                raise ValueError(
                    f"Official/developer evidence must use an official Celtic Heroes domain: {item_id}"
                )
        when = row.get("evidence_date")
        try:
            when_date = date.fromisoformat(when)
        except (TypeError, ValueError) as e:
            raise ValueError(f"Evidence date invalid for {item_id}") from e
        if when_date > date.today():
            raise ValueError(f"Future evidence date for {item_id}")
        if not isinstance(row.get("reason"), str) or len(row["reason"].strip()) < 20:
            raise ValueError("Require a concrete written release reason")
        result[item_id] = dict(row)
    return result


def derive_signal(item: dict) -> dict:
    """Never equate file linkage to a released item."""
    source_type = item.get("sourceType")
    listed_mobs = item.get("mobs")
    in_loot = isinstance(listed_mobs, list) and bool(listed_mobs)
    questline = item.get("questline")
    curated = bool(questline) or str(source_type).casefold() == "questline"
    signals = []
    if in_loot:
        signals.append("reconstructed_loot_reference")
    if curated:
        signals.append("curated_questline_reference")
    if not signals:
        signals.append("unattributed_database_record")
    return {
        "source_type": source_type,
        "loot_mob_reference_count": len(listed_mobs) if in_loot else 0,
        "questline": questline,
        "signals": signals,
    }


def classify(items: list[dict], evidence: list[dict]) -> tuple[list[dict], dict]:
    by_id = {str(i["id"]): i for i in items}
    if len(by_id) != len(items):
        raise ValueError("Source has duplicate item IDs")
    overrides = check_evidence(evidence, by_id)
    records = []
    source_counts = Counter()
    status_counts = Counter()
    # Deliberately do not infer "confirmed_unreleased" from missing drops,
    # missing release notes, unused slot types or suspicious item names.
    for item in sorted(items, key=lambda i: (str(i["name"]).casefold(), str(i["id"]))):
        item_id = str(item["id"])
        signals = derive_signal(item)
        override = overrides.get(item_id)
        status = override["release_status"] if override else "unverified"
        result = {
            "item_id": item["id"],
            "name": item["name"],
            "release_status": status,
            "currently_obtainable": "unknown",
            "evidence": [override] if override else [],
            "source_signals": signals,
            "excluded_from_default_bis": status != "released_documented",
            "annotation": (
                "Documented public release; current obtainability not established."
                if status == "released_documented"
                else "Historical release; current obtainability not established."
                if status == "historically_released"
                else "Explicit evidence of never being publicly released."
                if status == "confirmed_unreleased"
                else "Database presence is not public release evidence."
            ),
        }
        records.append(result)
        status_counts[status] += 1
        source_counts.update(signals["signals"])
    summary = {
        "schema_version": 1,
        "source_items": len(items),
        "status_counts": dict(status_counts),
        "source_signal_counts": dict(source_counts),
        "evidence_count": len(overrides),
        "rules": {
            "database_only_does_not_imply_unreleased": True,
            "reconstructed_loot_does_not_imply_released": True,
            "curated_questline_is_not_individual_item_release_proof": True,
            "released_documented_required_for_default_bis": True,
            "currently_obtainable_requires_separate_current_evidence": True,
        },
    }
    return records, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data/game"))
    parser.add_argument("--evidence", type=Path,
                        default=Path("data/release/evidence.json"))
    args = parser.parse_args()
    manifest = json.loads((args.data / "manifest.json").read_text(encoding="utf-8"))
    src = args.data / "items.jsonl.gz"
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    if digest != manifest["generated_files"]["items.jsonl.gz"]["sha256"]:
        raise ValueError("Source item data does not match pinned manifest")
    evidence_content = args.evidence.read_bytes()
    document = json.loads(evidence_content)
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError("Unsupported evidence schema version")
    evidence = document.get("records")
    entries, summary = classify(list(load_records("items", root=args.data)), evidence)
    summary["upstream_source_commit"] = manifest["upstream_commit"]
    summary["source_item_archive_sha256"] = digest
    summary["evidence_sha256"] = hashlib.sha256(evidence_content).hexdigest()
    output = gzip_deterministic(jsonl_bytes(entries))
    summary["index_sha256"] = hashlib.sha256(output).hexdigest()
    for name, data in (
        ("item_release_status.jsonl.gz", output),
        ("release_status_summary.json", canonical_json(summary)),
    ):
        tmp = args.data / (name + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(args.data / name)
    print(json.dumps({
        "total": summary["source_items"],
        "release_states": summary["status_counts"],
        "evidence_count": summary["evidence_count"],
        "signals": summary["source_signal_counts"],
    }))


if __name__ == "__main__":
    main()
