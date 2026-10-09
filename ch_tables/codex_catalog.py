"""Complete, versioned Codex PUBLIC listing import (facts, not game-truth DPS).

The pinned listing is collected through four read-only browser UI pages, not
from an undisclosed internal API. Detailed skill panels are a separate source.
Never silently publish an incomplete page-1-only dataset as a full catalog.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile

from .models import PublishedBuild
from .normalize import normalize_builds, summarize_classes, write_dict_rows
from .scrape import _publish_generation, write_raw_csv

CATALOG = "https://the-codex.ch/builds"
DETAIL = re.compile(r"^https://the-codex[.]ch/(damagebuilder|tankbuilder)/[a-z0-9_-]+$")
CLASSES = frozenset(("Warrior", "Druid", "Mage", "Ranger", "Rogue"))
RAW_FIELDS = frozenset(("source_url", "name", "character_class", "level",
                        "metric", "description", "created", "build_type",
                        "benchmark_dps"))


def _read_json(path: Path) -> dict:
    if path.stat().st_size > 8_000_000:
        raise ValueError("Source JSON too large")
    return json.loads(path.read_text(encoding="utf-8"),
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + x)))


def validate_catalog(doc: dict) -> list[PublishedBuild]:
    """Fail closed on incomplete pagination, duplicate IDs and spoofed URLs."""
    if type(doc) is not dict or doc.get("schema_version") != 1 or \
            doc.get("source_url") != CATALOG or \
            doc.get("source_type") != "public_saved_build_listing_snapshot":
        raise ValueError("Wrong Codex catalog schema/source")
    rows = doc.get("records")
    total = doc.get("declared_total")
    if type(rows) is not list or not rows or len(rows) > 20_000 or \
            type(total) is not int or type(doc.get("extracted_total")) is not int or \
            len(rows) != total or total != doc["extracted_total"]:
        raise ValueError("Incomplete Codex catalog; refuse partial pagination")
    pages = doc.get("pages")
    if type(pages) is not list or not pages or type(doc.get("page_size")) is not int:
        raise ValueError("Missing page provenance")
    start = 1
    for index, page in enumerate(pages, 1):
        if type(page) is not dict or type(page.get("page")) is not int or \
                type(page.get("count")) is not int or \
                page.get("range") != [start, start + page["count"] - 1, total] or \
                page["page"] != index or not 1 <= page["count"] <= doc["page_size"]:
            raise ValueError("Missing/overlapping/invalid listing page")
        if index < len(pages) and page["count"] != doc["page_size"]:
            raise ValueError("Nonfinal page incomplete")
        start += page["count"]
    if start != total + 1:
        raise ValueError("Pagination misses a build")
    builds = []
    seen = set()
    for n, row in enumerate(rows):
        if type(row) is not dict or set(row) != RAW_FIELDS:
            raise ValueError(f"Malformed Codex listing row {n}")
        url = row["source_url"]
        if type(url) is not str or not DETAIL.fullmatch(url) or url in seen:
            raise ValueError("Duplicate or untrusted build URL")
        seen.add(url)
        cls, typ, lvl = row["character_class"], row["build_type"], row["level"]
        if cls not in CLASSES or typ not in ("Damage", "Tank") or \
                type(lvl) is not int or not 1 <= lvl <= 1000:
            raise ValueError("Invalid class, build type or level")
        if typ == "Tank" and not url.startswith("https://the-codex.ch/tankbuilder/"):
            raise ValueError("Tank record URL/type mismatch")
        if typ == "Damage" and not url.startswith("https://the-codex.ch/damagebuilder/"):
            raise ValueError("Damage record URL/type mismatch")
        if any(type(row[x]) is not str or len(row[x]) > cap for x, cap in
               (("name", 160), ("description", 280), ("created", 80),
                ("metric", 80))) or not row["name"].strip():
            raise ValueError("Malformed build title/description/date/metric")
        dps = row["benchmark_dps"]
        if typ == "Tank":
            if dps is not None or row["metric"] != "Tank":
                raise ValueError("Tank cannot carry a damage benchmark")
        else:
            if type(dps) not in (int, float) or not math.isfinite(dps) or dps < 0:
                raise ValueError("Invalid reported damage benchmark")
            match = re.fullmatch(r"([0-9,]+(?:[.][0-9]+)?) DPS", row["metric"])
            if match is None or abs(float(match[1].replace(",", "")) - dps) > .011:
                raise ValueError("Display benchmark and numeric DPS disagree")
        builds.append(PublishedBuild(name=row["name"], character_class=cls,
                  level=lvl, build_type=typ, benchmark_dps=dps,
                  description=row["description"], created=row["created"],
                  build_url=url, source_url=CATALOG))
    return builds


def _write_sqlite(path: Path, builds: list[PublishedBuild],
                  skill_doc: dict | None, catalog_sha: str) -> tuple[int, int]:
    """Materialize both listing and existing panel observations in SQLite."""
    db = sqlite3.connect(path)
    try:
        db.executescript("""
        CREATE TABLE codex_builds (
          build_url TEXT PRIMARY KEY, name TEXT NOT NULL, character_class TEXT NOT NULL,
          level INTEGER NOT NULL, build_type TEXT NOT NULL,
          benchmark_dps REAL, description TEXT NOT NULL, created TEXT NOT NULL,
          listing_url TEXT NOT NULL
        );
        CREATE INDEX build_filters ON codex_builds(character_class, build_type, level);
        CREATE TABLE codex_skill_panels (
          build_url TEXT NOT NULL, skill_name TEXT NOT NULL,
          numeric_metrics_json TEXT NOT NULL, timing_json TEXT NOT NULL,
          ability_json TEXT, scaling_json TEXT, model_provenance TEXT NOT NULL,
          listed_in_catalog INTEGER NOT NULL,
          PRIMARY KEY(build_url, skill_name)
        );
        CREATE TABLE import_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        db.executemany("INSERT INTO codex_builds VALUES (?,?,?,?,?,?,?,?,?)", [
            (b.build_url, b.name, b.character_class, b.level, b.build_type,
             b.benchmark_dps, b.description, b.created, b.source_url)
            for b in builds])
        known = {b.build_url for b in builds}
        count = 0
        if skill_doc is not None:
            from .codex_surrogate import read_panels
            # Validate the same source inventory/provenance contract as the
            # empirical estimator before adding linked observations.
            read_panels(skill_doc)
            for row in skill_doc["observations"]:
                u, skill = row["source_url"], row["skill_name"]
                db.execute("INSERT INTO codex_skill_panels VALUES (?,?,?,?,?,?,?,?)",
                    (u, skill,
                     json.dumps(row["numeric_metrics"], sort_keys=True, allow_nan=False),
                     json.dumps(row["timing_s"], sort_keys=True, allow_nan=False),
                     json.dumps(row.get("skill_ability"), sort_keys=True, allow_nan=False),
                     json.dumps(row.get("scaling_attribute"), sort_keys=True, allow_nan=False),
                     row["model_provenance"], int(u in known)))
                count += 1
        db.executemany("INSERT INTO import_meta VALUES (?,?)", [
            ("source", CATALOG), ("catalog_sha256", catalog_sha),
            ("evidence_label", "CODEX_MODELED_VALUES_NOT_GAME_DPS"),
            ("listing_total", str(len(builds))),
            ("skill_panels", str(count))])
        db.commit()
        return len(builds), count
    finally:
        db.close()


def publish_catalog(snapshot: Path, raw: Path, normalized: Path,
                    summary: Path, manifest: Path, *, skill_snapshot: Path | None = None,
                    sqlite_path: Path | None = None, min_level: int = 220) -> dict:
    """Validate fully, stage outputs, then publish with rollback and manifest last."""
    snapshot = Path(snapshot)
    payload = snapshot.read_bytes()
    doc = _read_json(snapshot)
    builds = validate_catalog(doc)
    if type(min_level) is not int or not 1 <= min_level <= 1000:
        raise ValueError("Invalid level filter")
    normal = normalize_builds(builds, min_level=min_level)
    classes = summarize_classes(builds, min_level=min_level)
    if not normal:
        raise ValueError("No comparable damage builds")
    skill_doc = _read_json(Path(skill_snapshot)) if skill_snapshot is not None else None
    outputs = [Path(p).resolve() for p in (raw, normalized, summary, manifest)]
    if sqlite_path is not None:
        outputs.insert(3, Path(sqlite_path).resolve())
    if len(set(outputs)) != len(outputs):
        raise ValueError("Outputs must be distinct")
    with tempfile.TemporaryDirectory(prefix=".codex-catalog-",
            dir=Path(manifest).resolve().parent) as temp:
        root = Path(temp)
        stages = [root / "raw.csv", root / "normalized.csv", root / "summary.csv"]
        write_raw_csv(stages[0], builds)
        write_dict_rows(stages[1], normal)
        write_dict_rows(stages[2], classes)
        counts = {"listed_builds": len(builds), "damage_builds": sum(b.is_damage_build for b in builds),
                  "tank_builds": sum(b.build_type == "Tank" for b in builds),
                  "filtered_damage_builds": len(normal),
                  "skill_panels": 0}
        if sqlite_path is not None:
            dbstage = root / "catalog.sqlite"
            _, counts["skill_panels"] = _write_sqlite(
                dbstage, builds, skill_doc, hashlib.sha256(payload).hexdigest())
            stages.append(dbstage)
        manifest_stage = root / "manifest.json"
        details = {
            "schema_version": 1,
            "source": CATALOG,
            "source_sha256": hashlib.sha256(payload).hexdigest(),
            "snapshot_date": doc.get("snapshot_date"),
            "evidence_kind": "Codex-modeled-public-build-metadata",
            "min_level": min_level, "counts": counts,
            "outputs_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in stages},
            "limitations": "These are public saved-build calculator results, not measured combat. Detailed coverage is independently partial."
        }
        manifest_stage.write_text(json.dumps(details, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        stages.append(manifest_stage)
        _publish_generation(list(zip(stages, outputs)))
    return details


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--snapshot", type=Path, default=Path("data/reference/codex_published_build_catalog.json"))
    p.add_argument("--raw", type=Path, default=Path("data/raw/codex_builds_latest.csv"))
    p.add_argument("--normalized", type=Path, default=Path("data/normalized/builds_normalized.csv"))
    p.add_argument("--summary", type=Path, default=Path("data/normalized/class_summary.csv"))
    p.add_argument("--manifest", type=Path, default=Path("data/normalized/dataset_manifest.json"))
    p.add_argument("--sqlite", type=Path, default=Path("data/normalized/codex_catalog.sqlite"))
    p.add_argument("--skill-snapshot", type=Path, default=Path("data/reference/codex_skill_panel_observations.json"))
    p.add_argument("--min-level", type=int, default=220)
    a = p.parse_args()
    print(json.dumps(publish_catalog(a.snapshot, a.raw, a.normalized, a.summary,
        a.manifest, skill_snapshot=a.skill_snapshot, sqlite_path=a.sqlite,
        min_level=a.min_level), indent=2))


if __name__ == "__main__":
    main()
