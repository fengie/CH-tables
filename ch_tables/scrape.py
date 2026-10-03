from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from .models import PublishedBuild
from .normalize import normalize_builds, summarize_classes, write_dict_rows
from .sources import CODEX_BUILDS, SOURCES


USER_AGENT = "CH-tables/0.2 (+https://github.com/fengie/CH-tables)"
PARSER_SCHEMA_VERSION = 2
DEFAULT_SNAPSHOT_RETENTION = 10

_REQUIRED_COLUMNS = {"build", "class", "level", "metric", "description", "created"}


class SourceSchemaError(RuntimeError):
    """The upstream page no longer matches the validated Saved Builds schema."""


def clean_url(url: str) -> str:
    """Store clean provenance URLs without tracking query parameters."""
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def _parse_benchmark(text: str) -> tuple[str, float | None]:
    value = text.strip()
    if value.lower() == "tank":
        return "Tank", None

    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*DPS", value, flags=re.I)
    if match:
        return "Damage", float(match.group(1))

    return "Unknown", None


def _normalize_header(text: str) -> str | None:
    value = " ".join(text.split()).strip().lower()
    if value == "build":
        return "build"
    if value == "class":
        return "class"
    if value == "level":
        return "level"
    if value.startswith("build type"):
        return "metric"
    if value == "description":
        return "description"
    if value == "created":
        return "created"
    return None


def _saved_builds_table(soup: BeautifulSoup):
    """Return the Saved Builds table and semantic column mapping.

    The page contains responsive/auxiliary markup and may gain unrelated tables.
    We therefore bind parsing to the required semantic headers rather than table
    position or a hard-coded cell order.
    """
    candidates: list[tuple[object, dict[str, int]]] = []
    for table in soup.find_all("table"):
        headers = table.find_all("th")
        if not headers:
            continue
        mapping: dict[str, int] = {}
        for index, header in enumerate(headers):
            key = _normalize_header(header.get_text(" ", strip=True))
            if key is not None:
                if key in mapping:
                    raise SourceSchemaError(f"Duplicate Saved Builds column: {key}")
                mapping[key] = index
        if _REQUIRED_COLUMNS.issubset(mapping):
            candidates.append((table, mapping))

    if len(candidates) != 1:
        raise SourceSchemaError(
            "Expected exactly one Saved Builds table with required semantic columns; "
            f"found {len(candidates)}"
        )
    return candidates[0]


def parse_saved_builds_page(html: str, page_url: str = CODEX_BUILDS) -> list[PublishedBuild]:
    """Parse a validated Saved Builds table into typed records."""
    soup = BeautifulSoup(html, "html.parser")
    table, columns = _saved_builds_table(soup)
    max_index = max(columns.values())

    output: list[PublishedBuild] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if not cells:
            continue
        if len(cells) <= max_index:
            raise SourceSchemaError(
                f"Saved Builds row has {len(cells)} cells; expected at least {max_index + 1}"
            )

        build_cell = cells[columns["build"]]
        class_cell = cells[columns["class"]]
        level_cell = cells[columns["level"]]
        metric_cell = cells[columns["metric"]]
        desc_cell = cells[columns["description"]]
        created_cell = cells[columns["created"]]

        try:
            level = int(level_cell.get_text(" ", strip=True))
        except ValueError as exc:
            raise SourceSchemaError(
                f"Invalid level value: {level_cell.get_text(' ', strip=True)!r}"
            ) from exc
        if level <= 0:
            raise SourceSchemaError(f"Invalid non-positive level: {level}")

        link = build_cell.find("a")
        build_url = ""
        name = build_cell.get_text(" ", strip=True)
        if link:
            name = link.get_text(" ", strip=True) or name
            if link.get("href"):
                build_url = clean_url(urljoin(page_url, link["href"]))

        build_type, benchmark_dps = _parse_benchmark(metric_cell.get_text(" ", strip=True))
        character_class = class_cell.get_text(" ", strip=True)
        if not name or not character_class:
            raise SourceSchemaError("Saved Builds row is missing build name or class")

        output.append(PublishedBuild(
            name=name,
            character_class=character_class,
            level=level,
            build_type=build_type,
            benchmark_dps=benchmark_dps,
            description=desc_cell.get_text(" ", strip=True),
            created=created_cell.get_text(" ", strip=True),
            build_url=build_url,
            source_url=clean_url(page_url),
        ))

    if not output:
        raise SourceSchemaError("Saved Builds table contained no data rows")
    return output


def fetch_saved_builds_source(
    url: str = CODEX_BUILDS,
    timeout: int = 30,
) -> tuple[str, dict[str, str]]:
    """Fetch source HTML plus bounded provenance metadata."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return response.text, {
        "source_url": clean_url(response.url or url),
        "etag": response.headers.get("ETag", ""),
        "last_modified": response.headers.get("Last-Modified", ""),
    }


def fetch_saved_builds(url: str = CODEX_BUILDS, timeout: int = 30) -> list[PublishedBuild]:
    """Compatibility helper returning parsed currently rendered Saved Builds."""
    html, meta = fetch_saved_builds_source(url=url, timeout=timeout)
    return parse_saved_builds_page(html, page_url=meta["source_url"])


def write_raw_csv(path: Path, records: list[PublishedBuild]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name", "character_class", "level", "build_type", "benchmark_dps",
        "description", "created", "build_url", "source_url",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({
                "name": row.name,
                "character_class": row.character_class,
                "level": row.level,
                "build_type": row.build_type,
                "benchmark_dps": "" if row.benchmark_dps is None else row.benchmark_dps,
                "description": row.description,
                "created": row.created,
                "build_url": row.build_url,
                "source_url": row.source_url,
            })


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_snapshot(
    snapshot_dir: Path,
    html: str,
    *,
    retention: int,
) -> tuple[Path, str]:
    payload = html.encode("utf-8")
    digest = _sha256_bytes(payload)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot = snapshot_dir / f"{digest}.html"
    if not snapshot.exists():
        temporary = snapshot.with_suffix(".html.partial")
        temporary.write_bytes(payload)
        os.replace(temporary, snapshot)

    if retention > 0:
        snapshots = sorted(
            snapshot_dir.glob("*.html"),
            key=lambda item: item.stat().st_mtime,
            reverse=True,
        )
        for stale in snapshots[retention:]:
            if stale != snapshot:
                stale.unlink(missing_ok=True)
    return snapshot, digest


def _validate_records(records: list[PublishedBuild], normalized: list[dict]) -> None:
    if not records:
        raise SourceSchemaError("No Saved Builds records were parsed")
    if not any(row.is_damage_build for row in records):
        raise SourceSchemaError("Parsed dataset contains no benchmark damage builds")
    if not normalized:
        raise SourceSchemaError("Filtered normalized dataset is empty")


def _calibration_sources() -> list[str]:
    return sorted(
        clean_url(url)
        for key, url in SOURCES.items()
        if key.startswith("warrior_cal_")
    )


def _publish_file(staged: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(staged, destination)


def refresh_dataset(
    raw_path: Path,
    normalized_path: Path,
    class_summary_path: Path,
    min_level: int = 220,
    *,
    manifest_path: Path = Path("data/normalized/dataset_manifest.json"),
    snapshot_dir: Path = Path("data/source_snapshots/codex-builds"),
    snapshot_retention: int = DEFAULT_SNAPSHOT_RETENTION,
) -> tuple[int, int]:
    """Refresh the dataset through a validate-before-publish staging pipeline.

    Existing published CSV/manifest files are not touched until fetch, schema
    validation, parsing, normalization, and staging writes all succeed.
    """
    html, source_meta = fetch_saved_builds_source()
    snapshot_path, source_sha256 = _write_snapshot(
        snapshot_dir,
        html,
        retention=snapshot_retention,
    )
    records = parse_saved_builds_page(html, page_url=source_meta["source_url"])
    normalized = normalize_builds(records, min_level=min_level)
    summary = summarize_classes(records, min_level=min_level)
    _validate_records(records, normalized)

    published_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with tempfile.TemporaryDirectory(prefix="ch-tables-refresh-") as stage_root_text:
        stage_root = Path(stage_root_text)
        staged_raw = stage_root / "raw.csv"
        staged_normalized = stage_root / "normalized.csv"
        staged_summary = stage_root / "summary.csv"
        staged_manifest = stage_root / "manifest.json"

        write_raw_csv(staged_raw, records)
        write_dict_rows(staged_normalized, normalized)
        write_dict_rows(staged_summary, summary)

        manifest = {
            "schema_version": 1,
            "parser_schema_version": PARSER_SCHEMA_VERSION,
            "published_at_utc": published_at,
            "source": {
                **source_meta,
                "content_sha256": source_sha256,
                "snapshot": str(snapshot_path),
            },
            "parameters": {
                "min_level": min_level,
            },
            "rows": {
                "raw": len(records),
                "normalized": len(normalized),
                "class_summary": len(summary),
            },
            "outputs": {
                "raw": {"path": str(raw_path), "sha256": _sha256_file(staged_raw)},
                "normalized": {
                    "path": str(normalized_path),
                    "sha256": _sha256_file(staged_normalized),
                },
                "class_summary": {
                    "path": str(class_summary_path),
                    "sha256": _sha256_file(staged_summary),
                },
            },
            "calibration_sources": _calibration_sources(),
        }
        staged_manifest.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        # Publication starts only after every staged artifact and invariant above
        # succeeded. The manifest is committed last and acts as the generation
        # marker for the self-consistent set.
        _publish_file(staged_raw, raw_path)
        _publish_file(staged_normalized, normalized_path)
        _publish_file(staged_summary, class_summary_path)
        _publish_file(staged_manifest, manifest_path)

    return len(records), len(normalized)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh sourced Celtic Heroes build datasets.")
    parser.add_argument("--min-level", type=int, default=220)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/codex_builds_latest.csv"))
    parser.add_argument("--normalized", type=Path, default=Path("data/normalized/builds_normalized.csv"))
    parser.add_argument("--summary", type=Path, default=Path("data/normalized/class_summary.csv"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("data/normalized/dataset_manifest.json"),
    )
    parser.add_argument(
        "--snapshots",
        type=Path,
        default=Path("data/source_snapshots/codex-builds"),
    )
    parser.add_argument("--snapshot-retention", type=int, default=DEFAULT_SNAPSHOT_RETENTION)
    args = parser.parse_args()

    raw_count, normalized_count = refresh_dataset(
        raw_path=args.raw,
        normalized_path=args.normalized,
        class_summary_path=args.summary,
        min_level=args.min_level,
        manifest_path=args.manifest,
        snapshot_dir=args.snapshots,
        snapshot_retention=args.snapshot_retention,
    )

    print(f"Fetched {raw_count} visible Saved Builds rows.")
    print(f"Kept {normalized_count} comparable damage rows at level >= {args.min_level}.")
    print(f"Source: {CODEX_BUILDS}")
    print(f"Manifest: {args.manifest}")
    print(f"Refresh date: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
