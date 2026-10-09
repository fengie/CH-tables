"""Codex saved-build *panel* surrogate with build-held-out validation.

This predicts Codex's Avg Damage from the same panel's Max Damage. It is not
independent gameplay DPS, nor a model of how gear/skill ranks change Max Damage.
A saved build is one correlated group; never split its skill rows across train
and test sets. No network requests and no learned parameters baked into code.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from statistics import mean, median

PREFIX = "https://the-codex.ch/damagebuilder/"
PROVENANCE = "single_saved_build_not_engine_coefficients"


def _number(value: object) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


@dataclass(frozen=True)
class Panel:
    build: str
    skill: str
    maximum: float
    average: float

    @property
    def ratio(self) -> float:
        return self.average / self.maximum


def read_panels(document: dict) -> tuple[Panel, ...]:
    """Parse the pinned, unmodified Codex skill snapshot with source gates."""
    if type(document) is not dict or type(document.get("schema")) is not int or document.get("schema") != 1:
        raise ValueError("Expected pinned Codex skill snapshot schema 1")
    snapshots = document.get("snapshots")
    observations = document.get("observations")
    if type(snapshots) is not list or type(observations) is not list or len(observations) > 20_000:
        raise ValueError("Missing/oversize Codex source inventory")
    allowed = set()
    for snap in snapshots:
        if type(snap) is not dict or type(snap.get("url")) is not str or \
                not snap["url"].startswith(PREFIX) or not snap["url"][len(PREFIX):] or \
                snap["url"] in allowed:
            raise ValueError("Invalid or duplicate source build URL")
        allowed.add(snap["url"])
    rows = []
    seen = set()
    for obs in observations:
        if type(obs) is not dict:
            raise ValueError("Non-object skill observation")
        build, skill = obs.get("source_url"), obs.get("skill_name")
        if type(build) is not str or build not in allowed or type(skill) is not str or not skill.strip():
            raise ValueError("Unrecognized build or skill identity")
        if obs.get("model_provenance") != PROVENANCE:
            raise ValueError("Unrecognized Codex observation provenance")
        key = (build, skill)
        if key in seen:
            raise ValueError("Duplicate skill measurement within build")
        seen.add(key)
        metrics = obs.get("numeric_metrics")
        if type(metrics) is not dict:
            raise ValueError("Malformed numeric metrics")
        maximum, average = metrics.get("Max Damage"), metrics.get("Avg Damage")
        if maximum is None or average is None:
            continue  # Explicitly unavailable, never substitute zero.
        if not _number(maximum) or not _number(average) or maximum <= 0 or average <= 0:
            raise ValueError("Max/Avg Damage must be positive finite Codex values")
        if average / maximum > 10:
            raise ValueError("Implausible panel ratio; check parser/schema drift")
        rows.append(Panel(build, skill, float(maximum), float(average)))
    if not rows:
        raise ValueError("No usable paired Codex damage observations")
    return tuple(rows)


@dataclass(frozen=True)
class RatioPrior:
    """Robust per-skill median with a global fallback for unseen skills.

    The estimator is intentionally fixed before cross-validation. At n=1,
    the specific skill estimate is high-uncertainty; it cannot imply a 5% bound.
    """
    global_ratio: float
    skills: dict[str, tuple[float, ...]]
    training_builds: frozenset[str]

    @classmethod
    def fit(cls, panels: tuple[Panel, ...]) -> "RatioPrior":
        if not panels:
            raise ValueError("No calibration panels")
        buckets: dict[str, list[float]] = defaultdict(list)
        for row in panels:
            buckets[row.skill].append(row.ratio)
        return cls(median(row.ratio for row in panels),
                   {key: tuple(val) for key, val in buckets.items()},
                   frozenset(p.build for p in panels))

    def predict(self, skill: str, maximum: float) -> dict:
        if type(skill) is not str or not skill.strip() or not _number(maximum) or maximum <= 0:
            raise ValueError("Nonempty skill and finite positive Max Damage required")
        peers = self.skills.get(skill, ())
        ratio = median(peers) if peers else self.global_ratio
        return {"skill": skill, "supplied_codex_max_damage": maximum,
                "predicted_codex_avg_damage": maximum * ratio,
                "ratio": ratio, "other_build_skill_examples": len(peers),
                "estimator": "other_build_skill_median" if peers else "all_skill_global_median",
                "evidence_label": "CODEX_MODEL_SURROGATE_NOT_GAME_DAMAGE",
                "warning": "Requires a known Max Damage from the same Codex-type panel; "
                           "does not infer stat/gear scaling or practical combat DPS."}


def _scores(errors: list[float]) -> dict:
    if not errors:
        raise ValueError("No grouped validation errors")
    return {"n": len(errors), "mape_pct": round(mean(errors), 6),
            "median_ape_pct": round(median(errors), 6),
            "within_5pct_pct": round(100 * sum(e <= 5 for e in errors) / len(errors), 6),
            "worst_ape_pct": round(max(errors), 6)}


def validate_by_build(panels: tuple[Panel, ...]) -> dict:
    """Hold out entire Codex saved builds, not correlated skills/rows.

    All hyperparameters are fixed (pure median). This is a retrospective
    exploratory 12-build estimate, not a prospective independent evaluation.
    """
    builds = sorted({p.build for p in panels})
    if len(builds) < 3:
        raise ValueError("At least 3 independent saved builds required")
    ours, global_baseline, max_transfer = [], [], []
    per_build = []
    for build in builds:
        train = tuple(p for p in panels if p.build != build)
        test = [p for p in panels if p.build == build]
        prior = RatioPrior.fit(train)
        errors = []
        for row in test:
            ours_err = 100 * abs(prior.predict(row.skill, row.maximum)[
                "predicted_codex_avg_damage"] - row.average) / row.average
            baseline_err = 100 * abs(row.maximum * prior.global_ratio - row.average) / row.average
            ours.append(ours_err)
            errors.append(ours_err)
            global_baseline.append(baseline_err)
            # Deliberately expose the *hard* unknown: new Max Damage cannot
            # be recovered by taking another build's number as your own.
            same_skill = [p.maximum for p in train if p.skill == row.skill]
            if same_skill:
                max_transfer.append(100 * abs(median(same_skill) - row.maximum) / row.maximum)
        per_build.append({"source_url": build, **_scores(errors)})
    return {
        "method": "leave_one_saved_build_out_fixed_skill_median_v1",
        "target": "Codex Avg Damage conditional on supplied Codex Max Damage",
        "independent_build_groups": len(builds),
        "usable_panel_rows": len(panels),
        "skill_aware": _scores(ours),
        "global_median_baseline": _scores(global_baseline),
        "unseen_build_max_damage_transfer_diagnostic": _scores(max_transfer),
        "by_heldout_build": per_build,
        "interpretation": [
            "Holdouts have no skills from their saved build in training; groups are build URLs.",
            "5% average percentage error is NOT 5% accuracy for every skill or unseen stat/gear configuration.",
            "Max Damage is a supplied Codex output, not an inferred gear/ability/rank damage law.",
            "No observed gameplay DPS or independent game mechanics were used.",
            "The same 12 builds informed exploration; confirm with newly collected builds before deployment claims.",
        ],
    }


def calibrate(document: dict) -> dict:
    panels = read_panels(document)
    prior = RatioPrior.fit(panels)
    canonical = json.dumps(document, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":"), allow_nan=False).encode("utf8")
    return {"model": "codex_skill_panel_ratio_median_v1",
            "input_sha256": hashlib.sha256(canonical).hexdigest(),
            "input_snapshot_date": document.get("collected_on"),
            "scope": "CODEX_PANEL_ONLY_NOT_LIVE_DPS",
            "validation": validate_by_build(panels),
            "fitted": {"global_ratio": prior.global_ratio,
                       "builds": len(prior.training_builds),
                       "skill_ratios": {name: median(values) for name, values in
                                        sorted(prior.skills.items())}},
            "warning": "Do not substitute these ratios for skill stat/rank curves, "
                       "boss mitigation, hit/crit models or validated fight DPS."}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(
        "data/reference/codex_skill_panel_observations.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.input.stat().st_size > 6_000_000:
        parser.error("Oversize Codex snapshot")
    doc = json.loads(args.input.read_text(encoding="utf-8"))
    report = calibrate(doc)
    output = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()
