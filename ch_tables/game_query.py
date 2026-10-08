"""Fast, dependency-free queries over the complete public factual CH archive.

Examples:
  python -m ch_tables.game_query items "Creidhne's Knuckleblade" --limit 15
  python -m ch_tables.game_query items "Ferocity" --class Rogue
  python -m ch_tables.game_query items "Knuckleblade" --released-only
  python -m ch_tables.game_query items "Knuckleblade" --release-status unverified
  python -m ch_tables.game_query combat_mobs "Dhiothu"
  python -m ch_tables.game_query mobs "Bloodthorn"
  python -m ch_tables.game_query questlines
  python -m ch_tables.game_query item_mob_references "" --id 65539

The result contains exact source records; no unsolicited BIS ranking or
fabricated stat formulas. The source archive is not necessarily up-to-date.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Iterator

KINDS = frozenset({
    "items", "mobs", "combat_mobs", "spotlight_mobs",
    "mob_drop_records", "item_mob_references",
    "questlines", "other_structured_base",
})


def load_records(kind: str, *, root: Path = Path("data/game")) -> Iterator[dict]:
    if kind not in KINDS:
        raise ValueError(f"Unknown archive type {kind!r}")
    ext = ".json.gz" if kind in ("questlines", "other_structured_base") else ".jsonl.gz"
    path = root / f"{kind}{ext}"
    if not path.exists():
        raise FileNotFoundError(f"Run full_game_ingest first: {path}")
    with gzip.open(path, "rt", encoding="utf-8") as fp:
        if ext == ".json.gz":
            value = json.load(fp)
            if not isinstance(value, dict):
                raise ValueError(f"{path} should contain a JSON object")
            for key, entry in value.items():
                yield {"key": key, "value": entry}
        else:
            for lineno, line in enumerate(fp, 1):
                if line.strip():
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{path}:{lineno}: corrupt JSON") from exc
                    yield record


def release_index(root: Path) -> dict[str, dict]:
    """Load only source-hash-matched release evidence; stale indexes fail closed."""
    summary_path = root / "release_status_summary.json"
    data_path = root / "item_release_status.jsonl.gz"
    source = root / "items.jsonl.gz"
    if not summary_path.exists() or not data_path.exists() or not source.exists():
        return {}
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    status_digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    if summary.get("source_item_archive_sha256") != source_digest or \
       summary.get("index_sha256") != status_digest:
        raise ValueError("Stale or altered release-status index; regenerate release status")
    out = {}
    with gzip.open(data_path, "rt", encoding="utf-8") as fp:
        for line in fp:
            if line.strip():
                row = json.loads(line)
                key = str(row["item_id"])
                if key in out:
                    raise ValueError("Duplicate release-status item ID")
                out[key] = row
    return out


def property_filters(record: dict, klass: str | None,
                     slot: str | None, level_min: int | None) -> bool:
    stats = record.get("stats") if isinstance(record.get("stats"), dict) else {}
    if klass:
        actual = str(stats.get("classReq", record.get("class", ""))).casefold()
        if actual and klass.casefold() not in actual and actual not in ("all", "none"):
            return False
    if slot:
        actual_slot = str(stats.get("slot", record.get("slot", ""))).casefold()
        if slot.casefold() not in actual_slot:
            return False
    if level_min is not None:
        n = stats.get("levelReq", record.get("level", -1))
        if not isinstance(n, (int, float)) or n < level_min:
            return False
    return True


def search(kind: str, text: str = "", *, root: Path = Path("data/game"),
           limit: int = 20, record_id: str | None = None,
           klass: str | None = None, slot: str | None = None,
           level_min: int | None = None,
           full_text: bool = False, released_only: bool = False,
           release_state: str | None = None) -> list[dict]:
    if limit < 1 or limit > 500:
        raise ValueError("Search limit must be 1..500")
    if kind != "items" and (released_only or release_state):
        raise ValueError("Release-status filters only apply to items")
    if release_state and release_state not in {
        "released_documented", "historically_released",
        "confirmed_unreleased", "unverified"
    }:
        raise ValueError("Unknown release status")
    annotations = release_index(root) if kind == "items" else {}
    query = text.casefold().strip()
    matches: list[dict] = []
    for record in load_records(kind, root=root):
        if record_id is not None:
            fields = ("id", "item_id", "mob_id")
            if all(str(record.get(k)) != str(record_id) for k in fields):
                continue
        if not property_filters(record, klass, slot, level_min):
            continue
        if query:
            haystack = (json.dumps(record, ensure_ascii=False).casefold()
                        if full_text else
                        str(record.get("name", record.get("key", ""))).casefold())
            if query not in haystack:
                continue
        if kind == "items":
            info = annotations.get(str(record["id"]))
            label = info["release_status"] if info else "unverified"
            if released_only and label != "released_documented":
                continue
            if release_state and label != release_state:
                continue
            record = dict(record)
            record["release_status"] = label
            record["currently_obtainable"] = (
                info["currently_obtainable"] if info else "unknown"
            )
            record["excluded_from_default_bis"] = label != "released_documented"
            record["release_evidence"] = info["evidence"] if info else []
            record["release_source_signals"] = (
                info["source_signals"] if info else None
            )
        matches.append(record)
        if len(matches) >= limit:
            break
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=sorted(KINDS))
    parser.add_argument("text", nargs="?", default="")
    parser.add_argument("--data", type=Path, default=Path("data/game"))
    parser.add_argument("--id", dest="record_id")
    parser.add_argument("--class", dest="klass")
    parser.add_argument("--slot")
    parser.add_argument("--min-level", type=int)
    parser.add_argument("--all-fields", action="store_true",
                        help="Search nested numeric/stat field names too")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--released-only", action="store_true",
                        help="Exclude all unverified, discontinued and unreleased gear")
    parser.add_argument("--release-status", dest="release_state",
                        choices=["released_documented", "historically_released",
                                 "confirmed_unreleased", "unverified"])
    args = parser.parse_args()
    print(json.dumps(search(
        args.kind, args.text, root=args.data, limit=args.limit,
        record_id=args.record_id, klass=args.klass, slot=args.slot,
        level_min=args.min_level, full_text=args.all_fields,
        released_only=args.released_only, release_state=args.release_state,
    ), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
