from __future__ import annotations

import argparse
import csv
import re
from datetime import date
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

from .models import PublishedBuild
from .normalize import normalize_builds, summarize_classes, write_dict_rows
from .sources import CODEX_BUILDS


USER_AGENT = "CH-tables/0.1 (+https://github.com/fengie/CH-tables)"


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


def parse_saved_builds_page(html: str, page_url: str = CODEX_BUILDS) -> list[PublishedBuild]:
    """Parse The Codex Saved Builds table into typed records."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise RuntimeError("Could not find Saved Builds table")

    output: list[PublishedBuild] = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue

        build_cell, class_cell, level_cell, metric_cell, desc_cell, created_cell = cells[:6]

        try:
            level = int(level_cell.get_text(" ", strip=True))
        except ValueError:
            continue

        link = build_cell.find("a")
        build_url = ""
        if link and link.get("href"):
            build_url = clean_url(urljoin(page_url, link["href"]))

        build_type, benchmark_dps = _parse_benchmark(metric_cell.get_text(" ", strip=True))

        output.append(PublishedBuild(
            name=build_cell.get_text(" ", strip=True),
            character_class=class_cell.get_text(" ", strip=True),
            level=level,
            build_type=build_type,
            benchmark_dps=benchmark_dps,
            description=desc_cell.get_text(" ", strip=True),
            created=created_cell.get_text(" ", strip=True),
            build_url=build_url,
            source_url=clean_url(page_url),
        ))

    return output


def fetch_saved_builds(url: str = CODEX_BUILDS, timeout: int = 30) -> list[PublishedBuild]:
    """Fetch the currently rendered Saved Builds table."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return parse_saved_builds_page(response.text, page_url=url)


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


def refresh_dataset(
    raw_path: Path,
    normalized_path: Path,
    class_summary_path: Path,
    min_level: int = 220,
) -> tuple[int, int]:
    records = fetch_saved_builds()
    write_raw_csv(raw_path, records)
    normalized = normalize_builds(records, min_level=min_level)
    summary = summarize_classes(records, min_level=min_level)
    write_dict_rows(normalized_path, normalized)
    write_dict_rows(class_summary_path, summary)
    return len(records), len(normalized)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh sourced Celtic Heroes build datasets.")
    parser.add_argument("--min-level", type=int, default=220)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/codex_builds_latest.csv"))
    parser.add_argument("--normalized", type=Path, default=Path("data/normalized/builds_normalized.csv"))
    parser.add_argument("--summary", type=Path, default=Path("data/normalized/class_summary.csv"))
    args = parser.parse_args()

    raw_count, normalized_count = refresh_dataset(
        raw_path=args.raw,
        normalized_path=args.normalized,
        class_summary_path=args.summary,
        min_level=args.min_level,
    )

    print(f"Fetched {raw_count} visible Saved Builds rows.")
    print(f"Kept {normalized_count} comparable damage rows at level >= {args.min_level}.")
    print(f"Source: {CODEX_BUILDS}")
    print(f"Refresh date: {date.today().isoformat()}")


if __name__ == "__main__":
    main()
