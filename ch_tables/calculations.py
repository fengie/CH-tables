from __future__ import annotations

from .models import Build


def effective_dps(build: Build, total_uptime: float) -> float:
    """Practical DPS multiplied by the fraction of time damage can be dealt."""
    if build.practical_dps is None:
        raise ValueError(f"{build.character_class} has no comparable practical DPS value")
    if not 0 <= total_uptime <= 1:
        raise ValueError("total_uptime must be between 0 and 1")
    return build.practical_dps * total_uptime


def effective_dps_auto_only(build: Build, auto_downtime: float) -> float:
    """Conservative model: autos stop while all other damage continues perfectly."""
    if build.practical_dps is None or build.auto_dps is None:
        raise ValueError(f"{build.character_class} lacks practical/auto DPS data")
    if not 0 <= auto_downtime <= 1:
        raise ValueError("auto_downtime must be between 0 and 1")
    return build.practical_dps - build.auto_dps * auto_downtime


def effective_dps_with_deaths(
    build: Build,
    fight_seconds: float,
    deaths: int,
    seconds_lost_per_death: float,
    extra_mechanic_downtime: float = 0,
) -> tuple[float, float]:
    """Return (effective DPS, total attack uptime) after complete downtime."""
    if build.practical_dps is None:
        raise ValueError(f"{build.character_class} has no practical DPS value")
    if fight_seconds <= 0:
        raise ValueError("fight_seconds must be positive")
    if deaths < 0 or seconds_lost_per_death < 0 or extra_mechanic_downtime < 0:
        raise ValueError("downtime inputs cannot be negative")

    lost = deaths * seconds_lost_per_death + extra_mechanic_downtime
    active = max(0.0, fight_seconds - lost)
    uptime = active / fight_seconds
    return build.practical_dps * uptime, uptime


def required_uptime_to_match(attacker: Build, opponent: Build, opponent_uptime: float) -> float:
    """Uptime attacker needs to equal opponent effective DPS."""
    if attacker.practical_dps is None or opponent.practical_dps is None:
        raise ValueError("both builds require practical DPS values")
    return (opponent.practical_dps * opponent_uptime) / attacker.practical_dps


def vitality_opportunity_cost(build: Build, comparison_base_vit: int = 10) -> dict[str, float]:
    """Measure stat points tied up in Vitality without assuming linear DPS scaling."""
    extra_vit = max(0, build.base_vitality - comparison_base_vit)
    hypothetical_base_strength = build.base_strength + extra_vit
    hypothetical_total_strength = build.total_strength + extra_vit
    return {
        "extra_vit": extra_vit,
        "hypothetical_base_strength": hypothetical_base_strength,
        "base_strength_increase_pct": hypothetical_base_strength / build.base_strength - 1,
        "hypothetical_total_strength": hypothetical_total_strength,
        "total_strength_increase_pct": hypothetical_total_strength / build.total_strength - 1,
    }
