from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .calculations import (
    effective_dps,
    effective_dps_auto_only,
    effective_dps_with_deaths,
    required_uptime_to_match,
    vitality_opportunity_cost,
)
from .data import BOSS_AUTOS, RANGER, REPRESENTATIVE_BUILDS, ROGUE
from .normalize import read_published_builds, summarize_classes
from .sources import SOURCES


console = Console()


def number(value: float | int, digits: int = 1) -> str:
    return f"{value:,}" if isinstance(value, int) else f"{value:,.{digits}f}"


def pct(value: float, digits: int = 2) -> str:
    return f"{value * 100:.{digits}f}%"


def table(title: str, columns: list[str]) -> Table:
    result = Table(title=title, box=box.ROUNDED, header_style="bold cyan")
    for column in columns:
        result.add_column(column)
    return result


def render_representative_builds() -> None:
    t = table(
        "Representative sourced builds",
        ["Class", "HP", "Energy", "Attack", "Defence", "Base Vit", "Total Vit", "Practical DPS", "Auto share"],
    )
    for build in REPRESENTATIVE_BUILDS:
        t.add_row(
            build.character_class,
            number(build.hp),
            number(build.energy),
            number(build.attack),
            number(build.defence),
            number(build.base_vitality),
            number(build.total_vitality),
            number(build.practical_dps) if build.practical_dps is not None else "N/A",
            pct(build.auto_share) if build.auto_share is not None else "N/A",
        )
    console.print(t)
    console.print("[dim]Defence is not Armour. No Armour values are fabricated here.[/dim]")
    for build in REPRESENTATIVE_BUILDS:
        console.print(f"[dim]{build.character_class}: {build.source_url}[/dim]")
    console.print()


def render_vitality_tax() -> None:
    t = table(
        "Base-stat allocation / Vitality tax",
        ["Class", "Base STR", "Base DEX", "Base FOC", "Base VIT", "Base pool", "% pool in VIT"],
    )
    for build in REPRESENTATIVE_BUILDS:
        t.add_row(
            build.character_class,
            number(build.base_strength),
            number(build.base_dexterity),
            number(build.base_focus),
            number(build.base_vitality),
            number(build.base_stat_pool),
            pct(build.vitality_share),
        )
    console.print(t)

    cost = vitality_opportunity_cost(ROGUE)
    console.print(Panel.fit(
        f"Rogue has [bold]{cost['extra_vit']:.0f}[/bold] extra base Vit versus a 10-Vit comparison build.\n"
        f"Moving those points only to STR would change base STR to "
        f"[bold]{cost['hypothetical_base_strength']:.0f}[/bold] "
        f"({pct(cost['base_strength_increase_pct'])} higher), and total STR to "
        f"[bold]{cost['hypothetical_total_strength']:.0f}[/bold] "
        f"({pct(cost['total_strength_increase_pct'])} higher).\n"
        "[dim]Opportunity cost only. The code does not assume DPS scales linearly with STR.[/dim]",
        title="Rogue stat-budget example",
    ))


def render_generic_class_summary(snapshot: Path) -> None:
    if not snapshot.exists():
        console.print(f"[yellow]Missing sample snapshot: {snapshot}[/yellow]")
        return

    summary = summarize_classes(read_published_builds(snapshot), min_level=220)
    t = table(
        "Generic class sample: published damage builds, level >= 220",
        ["Class", "n", "Mean level", "Mean DPS", "Median DPS", "Min DPS", "Max DPS", "Median index"],
    )
    for row in summary:
        t.add_row(
            row["class"],
            str(row["count"]),
            number(row["mean_level"], 1),
            number(row["mean_dps"], 1),
            number(row["median_dps"], 1),
            number(row["min_dps"], 1),
            number(row["max_dps"], 1),
            f"{row['median_index_vs_sample']:.1f}",
        )
    console.print(t)
    console.print(
        "[dim]Median index 100 = median DPS of the filtered sample. "
        "This is a sample description, not a population estimate.[/dim]"
    )
    console.print(f"[dim]Source: {SOURCES['codex_builds']}[/dim]\n")


def render_uptime() -> None:
    t = table("Rogue effective DPS by total attack uptime", ["Uptime", "Effective DPS", "DPS lost", "Loss"])
    for uptime in [1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70]:
        result = effective_dps(ROGUE, uptime)
        lost = ROGUE.practical_dps - result
        t.add_row(pct(uptime, 0), number(result), number(lost), pct(lost / ROGUE.practical_dps))
    console.print(t)

    t = table("Conservative Rogue auto-only downtime", ["Auto downtime", "Effective DPS", "DPS lost", "Total loss"])
    for downtime in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30]:
        result = effective_dps_auto_only(ROGUE, downtime)
        lost = ROGUE.practical_dps - result
        t.add_row(pct(downtime, 0), number(result), number(lost), pct(lost / ROGUE.practical_dps))
    console.print(t)
    console.print("[dim]Auto-only model assumes every non-auto source keeps working perfectly.[/dim]\n")


def render_rogue_vs_ranger() -> None:
    t = table(
        "Ranger uptime vs Rogue uptime required to match",
        ["Ranger uptime", "Ranger effective DPS", "Rogue uptime needed", "Possible <= 100%?"],
    )
    for ranger_uptime in [1.00, 0.98, 0.95, 0.90, 0.85, 0.80]:
        ranger_effective = effective_dps(RANGER, ranger_uptime)
        needed = required_uptime_to_match(ROGUE, RANGER, ranger_uptime)
        t.add_row(
            pct(ranger_uptime, 0),
            number(ranger_effective),
            pct(needed),
            "Yes" if needed <= 1 else "No",
        )
    console.print(t)
    console.print(f"[dim]Rogue source: {ROGUE.source_url}[/dim]")
    console.print(f"[dim]Ranger source: {RANGER.source_url}[/dim]\n")


def render_deaths() -> None:
    t = table(
        "10-minute Rogue fight: 15 seconds complete downtime per death",
        ["Deaths", "Seconds lost", "Uptime", "Effective DPS", "DPS lost"],
    )
    for deaths in range(7):
        result, uptime = effective_dps_with_deaths(
            ROGUE,
            fight_seconds=600,
            deaths=deaths,
            seconds_lost_per_death=15,
        )
        t.add_row(
            str(deaths),
            str(deaths * 15),
            pct(uptime),
            number(result),
            number(ROGUE.practical_dps - result),
        )
    console.print(t)
    console.print("[dim]15 seconds is a scenario input. Change it in code to match observed raid recovery time.[/dim]\n")


def render_bosses() -> None:
    for boss in BOSS_AUTOS:
        t = table(f"{boss.name}: normal raw auto composition", ["Damage type", "Raw damage", "Share"])
        for damage_type, raw in boss.components.items():
            t.add_row(damage_type, number(raw), pct(raw / boss.total_raw))
        t.add_row("TOTAL", number(boss.total_raw), "100.00%")
        console.print(t)
        console.print(f"[dim]Source: {boss.source_url}[/dim]\n")


def render_sources() -> None:
    console.print(Panel("\n".join(f"{name}: {url}" for name, url in SOURCES.items()), title="Original source URLs"))


def run_report() -> None:
    console.print(Panel.fit(
        "Celtic Heroes sourced class / boss analysis\n"
        "[dim]Community build sample + transparent scenario math[/dim]",
        title="CH-tables",
    ))
    render_representative_builds()
    render_vitality_tax()
    render_generic_class_summary(Path("data/raw/codex_builds_sample_2026-09-30.csv"))
    render_uptime()
    render_rogue_vs_ranger()
    render_deaths()
    render_bosses()
    render_sources()
