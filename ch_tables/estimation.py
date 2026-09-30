"""Applied-math fallbacks for metrics not directly exposed by a target build.

Rules:
- Prefer directly sourced values whenever available.
- Estimates are labeled ESTIMATE in reports.
- Calibration inputs keep their original source URLs.
- Small calibration samples use robust medians and empirical min/max ranges
  instead of pretending to have a precise population confidence interval.
"""

from __future__ import annotations

from dataclasses import dataclass
import statistics

from .sources import (
    CODEX_BUILDS,
    WARRIOR_CAL_DRAGA,
    WARRIOR_CAL_GWYN,
    WARRIOR_CAL_YUHHH,
)


@dataclass(frozen=True)
class WarriorCalibrationPoint:
    name: str
    overall_dps: float
    practical_dps: float
    practical_auto_share: float
    source_url: str

    @property
    def practical_ratio(self) -> float:
        """Practical DPS divided by Overall Rotation DPS."""
        return self.practical_dps / self.overall_dps


@dataclass(frozen=True)
class WarriorEstimate:
    benchmark_dps: float
    practical_dps: float
    practical_dps_low: float
    practical_dps_high: float
    auto_share: float
    auto_share_low: float
    auto_share_high: float
    auto_dps: float
    practical_ratio: float
    calibration_n: int
    benchmark_source_url: str
    calibration_source_urls: tuple[str, ...]


# Each source exposes both Overall Rotation Results and Practical Rotation Guide.
# Data read from the source pages:
#
# Draga:
#   Overall DPS       = 2,132.0
#   Practical DPS     = 2,051.5
#   Practical auto    = 50.7%
#
# yuhhh:
#   Overall DPS       = 5,029.5
#   Practical DPS     = 4,851.2
#   Practical auto    = 48.9%
#
# Gwyn Shields DPS:
#   Overall DPS       = 1,338.8
#   Practical DPS     = 1,285.3
#   Practical auto    = 40.6%
#
# Source URLs are original URLs with no tracking parameters.
WARRIOR_CALIBRATION = (
    WarriorCalibrationPoint(
        name="Draga",
        overall_dps=2132.0,
        practical_dps=2051.5,
        practical_auto_share=0.507,
        source_url=WARRIOR_CAL_DRAGA,
    ),
    WarriorCalibrationPoint(
        name="yuhhh",
        overall_dps=5029.5,
        practical_dps=4851.2,
        practical_auto_share=0.489,
        source_url=WARRIOR_CAL_YUHHH,
    ),
    WarriorCalibrationPoint(
        name="Gwyn Shields DPS",
        overall_dps=1338.8,
        practical_dps=1285.3,
        practical_auto_share=0.406,
        source_url=WARRIOR_CAL_GWYN,
    ),
)


def estimate_warrior_practical_metrics(
    benchmark_dps: float,
    benchmark_source_url: str = CODEX_BUILDS,
) -> WarriorEstimate:
    """Estimate missing Warrior practical metrics from same-class calibration.

    Applied mathematics:
      practical_ratio_i = practical_dps_i / overall_dps_i

      estimated practical DPS
        = target benchmark DPS * median(practical_ratio_i)

      estimated auto share
        = median(calibration practical auto shares)

    Because n=3 is intentionally small, uncertainty is shown as the empirical
    min/max calibration range rather than a misleading parametric 95% CI.
    """
    if benchmark_dps <= 0:
        raise ValueError("benchmark_dps must be positive")

    ratios = [point.practical_ratio for point in WARRIOR_CALIBRATION]
    auto_shares = [point.practical_auto_share for point in WARRIOR_CALIBRATION]

    ratio = statistics.median(ratios)
    ratio_low = min(ratios)
    ratio_high = max(ratios)

    auto_share = statistics.median(auto_shares)
    auto_share_low = min(auto_shares)
    auto_share_high = max(auto_shares)

    practical_dps = benchmark_dps * ratio

    return WarriorEstimate(
        benchmark_dps=benchmark_dps,
        practical_dps=practical_dps,
        practical_dps_low=benchmark_dps * ratio_low,
        practical_dps_high=benchmark_dps * ratio_high,
        auto_share=auto_share,
        auto_share_low=auto_share_low,
        auto_share_high=auto_share_high,
        auto_dps=practical_dps * auto_share,
        practical_ratio=ratio,
        calibration_n=len(WARRIOR_CALIBRATION),
        benchmark_source_url=benchmark_source_url,
        calibration_source_urls=tuple(point.source_url for point in WARRIOR_CALIBRATION),
    )


# The Saved Builds index reports Surya8 at 11,982.1 benchmark DPS.
SURYA8_BENCHMARK_DPS = 11982.1
SURYA8_ESTIMATE = estimate_warrior_practical_metrics(SURYA8_BENCHMARK_DPS)
