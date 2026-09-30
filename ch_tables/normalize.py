from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from .models import PublishedBuild


def comparable_damage_builds(
    records: Iterable[PublishedBuild],
    min_level: int = 220,
) -> list[PublishedBuild]:
    """Keep high-level damage builds with an actual benchmark DPS value."""
    return [
        row for row in records
        if row.is_damage_build and row.level >= min_level and row.benchmark_dps is not None
    ]


def normalize_builds(
    records: Iterable[PublishedBuild],
    min_level: int = 220,
) -> list[dict]:
    """Add transparent sample-relative and within-class DPS indices.

    sample_dps_index:
        100 == median DPS of the entire filtered sample.

    class_dps_index:
        100 == median DPS of the filtered build's own class.

    We intentionally do NOT divide DPS by level or assume linear level scaling.
    """
    filtered = comparable_damage_builds(records, min_level=min_level)
    if not filtered:
        return []

    all_dps = [float(row.benchmark_dps) for row in filtered]
    sample_median = statistics.median(all_dps)

    by_class: dict[str, list[float]] = defaultdict(list)
    for row in filtered:
        by_class[row.character_class].append(float(row.benchmark_dps))

    class_medians = {
        cls: statistics.median(values)
        for cls, values in by_class.items()
    }

    output: list[dict] = []
    for row in filtered:
        dps = float(row.benchmark_dps)
        item = asdict(row)
        item["sample_dps_index"] = dps / sample_median * 100
        item["class_dps_index"] = dps / class_medians[row.character_class] * 100
        item["normalization_min_level"] = min_level
        item["sample_median_dps"] = sample_median
        output.append(item)

    return output


def summarize_classes(
    records: Iterable[PublishedBuild],
    min_level: int = 220,
) -> list[dict]:
    """Describe the filtered sample by class.

    These are sample summaries, not estimates of the full player population.
    """
    filtered = comparable_damage_builds(records, min_level=min_level)
    if not filtered:
        return []

    all_dps = [float(row.benchmark_dps) for row in filtered]
    sample_median = statistics.median(all_dps)
    sample_mean = statistics.mean(all_dps)

    grouped: dict[str, list[PublishedBuild]] = defaultdict(list)
    for row in filtered:
        grouped[row.character_class].append(row)

    output = []
    for cls in sorted(grouped):
        rows = grouped[cls]
        levels = [row.level for row in rows]
        dps = [float(row.benchmark_dps) for row in rows]
        class_median = statistics.median(dps)
        class_mean = statistics.mean(dps)
        output.append({
            "class": cls,
            "count": len(rows),
            "mean_level": statistics.mean(levels),
            "mean_dps": class_mean,
            "median_dps": class_median,
            "min_dps": min(dps),
            "max_dps": max(dps),
            "median_index_vs_sample": class_median / sample_median * 100,
            "mean_index_vs_sample": class_mean / sample_mean * 100,
            "sample_median_dps": sample_median,
            "sample_mean_dps": sample_mean,
            "min_level_filter": min_level,
        })

    return output


def write_dict_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def read_published_builds(path: Path) -> list[PublishedBuild]:
    rows: list[PublishedBuild] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            benchmark = raw.get("benchmark_dps", "").strip()
            rows.append(PublishedBuild(
                name=raw["name"],
                character_class=raw["character_class"],
                level=int(raw["level"]),
                build_type=raw["build_type"],
                benchmark_dps=float(benchmark) if benchmark else None,
                description=raw.get("description", ""),
                created=raw.get("created", ""),
                build_url=raw.get("build_url", ""),
                source_url=raw.get("source_url", ""),
            ))
    return rows
