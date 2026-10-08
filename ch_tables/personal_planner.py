"""Personal character planner with release, world-price and RNG gates.

The core point optimizer scores ONLY measured/per-rank skill damage inputs.
This adapter validates all swap IDs against the pinned game archive and
filters acquisition paths using world-specific evidence. No item is
assumed obtainable merely because it exists in an extracted database.

python -m ch_tables.personal_planner --scenario data/planner/example_scenario.json
"""
from __future__ import annotations

from dataclasses import replace
import argparse
import json
from pathlib import Path

from .build_planner import load_scenario, compare_playstyles
from .companions import PetCandidate, pet_shortlist
from .economy import EffortBudget, feasible_acquisition
from .game_query import load_records, release_index


def price_map(summary: dict, world: str) -> dict[int, float]:
    out = {}
    for row in summary.get("price_by_item_world", []):
        if row.get("world", "").casefold() == world.casefold() and \
           row.get("sold_median_gold") is not None and \
           row.get("evidence_status") == "observed_sales":
            out[int(row["item_id"])] = float(row["sold_median_gold"])
    return out


def drop_map(summary: dict, world: str) -> dict[int, float]:
    """For a specified world choose the best recorded boss route per item.

    This is not a claim every boss is currently farmable.
    """
    out = {}
    for row in summary.get("drop_rate_by_item_world_boss", []):
        if row.get("world", "").casefold() == world.casefold() and \
           row.get("status") == "estimated_from_observed_trials":
            item = int(row["item_id"])
            rate = float(row["drop_rate"])
            out[item] = max(rate, out.get(item, 0))
    return out


def apply_acquisition_filters(swaps_by_skill, *,
                              item_catalog: dict[str, dict],
                              status_index: dict[str, dict],
                              market: dict,
                              budget: EffortBudget):
    prices = price_map(market, budget.world)
    drops = drop_map(market, budget.world)
    accepted = {}
    rejected = []
    for skill, entries in swaps_by_skill.items():
        accepted[skill] = []
        for proposed in entries:
            record = item_catalog.get(proposed.item_id)
            if record is None:
                raise ValueError(f"{skill}: swap item ID {proposed.item_id} not in game database")
            if not proposed.slot:
                raise ValueError(f"{skill}: missing swap slot")
            actual_slot = str((record.get("stats") or {}).get("slot", "")).casefold()
            normalized_proposed_slot = proposed.slot.casefold().rstrip("0123456789")
            if actual_slot and normalized_proposed_slot != actual_slot:
                raise ValueError(f"{skill}: slot mismatch for {proposed.item_id}: "
                                 f"{proposed.slot} vs source {actual_slot}")
            release = status_index.get(proposed.item_id, {}).get(
                "release_status", "unverified"
            )
            released = release == "released_documented"
            item = int(proposed.item_id)
            evaluation = feasible_acquisition(
                owned=proposed.owned, released=released,
                market_price_gold=prices.get(item),
                drop_probability=drops.get(item),
                budget=budget,
            )
            if not evaluation["feasible"]:
                rejected.append({
                    "skill": skill, "item_id": item,
                    "item_name": record["name"], "release_status": release,
                    "source_gear_stats": record.get("stats"),
                    "rejection": evaluation,
                })
                continue
            # Never trust release-state assertions in contributed scenarios:
            # source-of-truth is the separately audited item ID index.
            acquisition_cost = (
                0 if proposed.owned
                else int(round(prices[item])) if evaluation["method"] == "trade" and
                         item in prices else
                0 if evaluation["method"] in ("grind_unbounded", "grind_within_budget")
                else None
            )
            accepted[skill].append(replace(
                proposed, release_status=release,
                acquisition_gold_cost=acquisition_cost,
            ))
    return accepted, rejected


def run_scenario(document: dict, *, data_dir: Path = Path("data/game"),
                 economy_file: Path = Path("data/community/market_summary.json")) -> dict:
    if document.get("scenario_status") not in ("synthetic_demo", "user_supplied"):
        raise ValueError("Scenario must identify synthetic demo or user-supplied measurements")
    skills, swaps_by_skill, pref = load_scenario(document)
    effort = EffortBudget(**document["effort_budget"])
    if pref.total_gold_budget is None and effort.gold is not None:
        pref = replace(pref, total_gold_budget=effort.gold)
    elif pref.total_gold_budget is not None and effort.gold is not None:
        pref = replace(pref, total_gold_budget=min(pref.total_gold_budget, effort.gold))
    items = {str(row["id"]): row
             for row in load_records("items", root=data_dir)}
    market = json.loads(economy_file.read_text()) if economy_file.exists() else {}
    status = release_index(data_dir)
    filtered, rejected = apply_acquisition_filters(
        swaps_by_skill, item_catalog=items,
        status_index=status, market=market, budget=effort,
    )
    result = compare_playstyles(skills, filtered, pref)
    pet_report = None
    if document.get("pet_candidates") is not None:
        candidates = []
        for source in document["pet_candidates"]:
            proposed = PetCandidate(**source)
            if proposed.item_id is not None:
                item_id = str(proposed.item_id)
                if item_id not in items:
                    raise ValueError("Companion item ID missing from pinned game archive")
                proposed = replace(
                    proposed, release_status=status.get(item_id, {}).get(
                        "release_status", "unverified"),
                )
            candidates.append(proposed)
        pet_report = pet_shortlist(
            candidates, character_level=pref.level, effort=effort,
            owned_pet_tokens=document.get("owned_pet_tokens"),
            world_sale_prices=price_map(market, effort.world),
            item_drop_rates=drop_map(market, effort.world),
            qol_cost_per_action=pref.manual_action_penalty_dps,
            healing_value_per_hp=pref.healing_value_per_hp,
        )
    return {
        "scenario_name": document.get("name", "Untitled"),
        "scenario_status": document["scenario_status"],
        "world": effort.world,
        "effort_budget": document["effort_budget"],
        "builds": result,
        "pet_comparison": pet_report,
        "swap_candidates_rejected": rejected,
        "warnings": [
            "No inferred skill rank-damage curves: each rank must carry evidence.",
            "Do not treat the DP screening model as validated real-time rotation DPS.",
            "Unverified gear can be used ONLY if user owns it and explicitly opts in.",
            "No fresh completed world sales or drop trials means cost/RNG are unknown.",
            "Pets must be compared with measured pet skill damage and stat effects.",
            "Pet and skill-swap budgets are screened separately; a joint gear/pet optimizer is not yet verified.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--game", type=Path, default=Path("data/game"))
    parser.add_argument("--economy", type=Path,
                        default=Path("data/community/market_summary.json"))
    args = parser.parse_args()
    doc = json.loads(args.scenario.read_text(encoding="utf-8"))
    print(json.dumps(run_scenario(doc, data_dir=args.game,
                                  economy_file=args.economy),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
