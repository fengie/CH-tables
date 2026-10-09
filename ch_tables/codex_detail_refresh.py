"""Bounded, incremental Codex skill-panel ingestion from public detail pages.

Existing pinned observations are append-only by source URL for each batch.
No crawling beyond the verified public catalog; no login, internal API,
unbounded requests or published raw copyrighted HTML. URLs are source IDs.
"""
from __future__ import annotations

import argparse
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import tempfile
from time import sleep

import requests

from .codex_catalog import _read_json, validate_catalog
from .codex_skill_ingest import parse_skills_html
from .codex_surrogate import read_panels

UA = "CH-tables source-index/1.0 (public, bounded, read-only)"
CLASSES = ("Rogue", "Mage", "Warrior", "Ranger", "Druid")


def pending_damage_urls(catalog: dict, existing: dict) -> list[str]:
    """Class-balanced round robin, skip already harvested build sources."""
    builds = validate_catalog(catalog)
    seen = {s["url"] for s in existing["snapshots"]}
    buckets = {c: [] for c in CLASSES}
    for row in builds:
        if row.build_type == "Damage" and row.build_url not in seen:
            buckets[row.character_class].append(row.build_url)
    selected = []
    while any(buckets.values()):
        for cls in CLASSES:
            if buckets[cls]:
                selected.append(buckets[cls].pop(0))
    return selected


def refresh_details(catalog_file: Path, observations_file: Path, *,
                    limit: int = 12, delay_s: float = 1.5,
                    transport=None, sleeper=sleep) -> dict:
    if type(limit) is not int or not 1 <= limit <= 25:
        raise ValueError("Incremental fetch limit must be 1..25")
    if type(delay_s) not in (float, int) or not 1 <= delay_s <= 300:
        raise ValueError("Rate limit must be at least one second")
    catalog = _read_json(Path(catalog_file))
    existing = _read_json(Path(observations_file))
    read_panels(existing)  # Must preserve a valid, independent source archive.
    if existing.get("source_method") != "read_only_public_saved_build_HTML":
        raise ValueError("Unrecognized observations source method")
    urls = pending_damage_urls(catalog, existing)
    target = urls[:limit]
    if not target:
        return {"status": "already_covered", "new_builds": 0,
                "unprocessed_damage_builds": 0}
    if transport is None:
        transport = requests.Session()
    snapshots = list(existing["snapshots"])
    observations = list(existing["observations"])
    errors = list(existing.get("errors", []))
    successes = 0
    for i, url in enumerate(target):
        if i:
            sleeper(delay_s)
        try:
            res = transport.get(url, timeout=25, headers={"User-Agent": UA})
            if res.status_code == 429:
                # A host-imposed rate limit stops this batch completely.
                raise RuntimeError("Codex returned 429: do not retry automatically")
            res.raise_for_status()
            if res.url.rstrip("/") != url:
                raise ValueError("Unexpected source redirect")
            content = res.content
            if not 0 < len(content) <= 4_000_000:
                raise ValueError("Source HTML exceeds per-page cap")
            skills = parse_skills_html(res.text, url)
            if not skills:
                raise ValueError("No renderable skill-panel metrics")
            observations.extend(skills)
            snapshots.append({"url": url, "html_sha256": hashlib.sha256(content).hexdigest(),
                              "skills": len(skills)})
            successes += 1
            errors = [e for e in errors if e.get("url") != url]
        except (requests.RequestException, ValueError) as ex:
            errors.append({"url": url, "error": str(ex)[:160]})
    if successes == 0:
        # Retain all old data, including its original harvest date.
        return {"status": "no_new_valid_panels", "new_builds": 0,
                "unprocessed_damage_builds": len(urls), "errors": errors[-25:]}
    result = dict(existing)
    result.update({"collected_on": date.today().isoformat(),
                   "snapshots": snapshots, "observations": observations,
                   "errors": errors[-100:],
                   "warning": "Codex panel outputs are modeled, not measured gameplay. "
                              "Individual source builds are correlated; unseen configurations "
                              "and real boss DPS remain unvalidated."})
    read_panels(result)  # Full merged data must stay valid before replacement.
    path = Path(observations_file)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".codex-detail-",
                                     mode="w", encoding="utf-8", delete=False) as fp:
        staged = Path(fp.name)
        try:
            json.dump(result, fp, indent=2, ensure_ascii=False, allow_nan=False)
            fp.write("\n")
            fp.flush()
            os.fsync(fp.fileno())
        except BaseException:
            staged.unlink(missing_ok=True)
            raise
    try:
        os.replace(staged, path)
    except BaseException:
        staged.unlink(missing_ok=True)
        raise
    return {"status": "published_incremental_source_index",
            "new_builds": successes,
            "total_indexed_source_builds": len(snapshots),
            "total_indexed_skill_panels": len(observations),
            "unprocessed_damage_builds": len(urls) - successes,
            "attempted": len(target), "errors": errors[-25:]}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--catalog", type=Path,
        default=Path("data/reference/codex_published_build_catalog.json"))
    p.add_argument("--observations", type=Path,
        default=Path("data/reference/codex_skill_panel_observations.json"))
    p.add_argument("--limit", type=int, default=12)
    p.add_argument("--delay", type=float, default=1.5)
    a = p.parse_args()
    print(json.dumps(refresh_details(a.catalog, a.observations,
                   limit=a.limit, delay_s=a.delay), indent=2))


if __name__ == "__main__":
    main()
