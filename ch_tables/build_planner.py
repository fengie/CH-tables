"""Personalized Celtic Heroes skill-point, gear-swap and practical DPS planner.

The engine does NOT invent unobserved per-rank skill scaling. Supply explicit
rank curves measured in-game, sourced externally, or labeled as estimates.
It finds maximum utility subject to an exact skill-point budget and controlled
swap limits, and compares multiple quality-of-life policies.

Use:
    python -m ch_tables.build_planner --scenario data/planner/example_scenario.json
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from itertools import combinations
import json
import math
from pathlib import Path


# Historical tables are sourced, current-patch override is ALWAYS supported.
HISTORICAL_CAP_THRESHOLDS = (
    (1, 5), (15, 10), (30, 15), (60, 20), (90, 25),
    (120, 30), (150, 35), (180, 40), (210, 45), (240, 50),
)
SOURCE_SKILL_CAP = "https://forum.celtic-heroes.com/forum/viewtopic.php?p=93058"
SOURCE_POINTS = "https://celtic-heroes.fandom.com/wiki/Character"
SOURCE_SWAPS = "https://forum.celtic-heroes.com/forum/viewtopic.php?p=750708"


def level_skill_cap(level: int, *, override: int | None = None) -> int:
    if level < 1:
        raise ValueError("Character level >=1 required")
    if override is not None:
        if not 1 <= override <= 100:
            raise ValueError("Override must be between 1 and 100")
        return override
    return max(cap for threshold, cap in HISTORICAL_CAP_THRESHOLDS if level >= threshold)


def skill_point_budget(level: int, *, starting_points: int = 0,
                       bonus_points: int = 0,
                       override: int | None = None) -> int:
    """One point on each level-up; starting/free points must be user verified.

    level-1 is a conservative number for levels gained since creation;
    it is NOT a claim about available points on a level-1 character.
    """
    if level < 1 or min(starting_points, bonus_points) < 0:
        raise ValueError("Invalid point-budget inputs")
    if override is not None:
        if override < 0:
            raise ValueError("Negative point budget")
        return override
    return (level - 1) + starting_points + bonus_points


@dataclass(frozen=True)
class SkillRank:
    level: int
    expected_damage: float
    cooldown_s: float
    occupied_s: float
    hit_probability: float = 1.0
    healing: float = 0.0
    energy_cost: float = 0.0
    source_url: str = ""
    evidence_kind: str = "user_estimate"

    def __post_init__(self):
        if self.level < 1 or self.cooldown_s <= 0 or self.occupied_s < 0:
            raise ValueError("Invalid skill rank, cooldown or occupation")
        if self.expected_damage < 0 or self.healing < 0 or self.energy_cost < 0:
            raise ValueError("Negative damage, healing or energy cost")
        if not 0 <= self.hit_probability <= 1:
            raise ValueError("Hit probability must be 0..1")
        if self.evidence_kind not in ("observed", "community_model", "user_estimate"):
            raise ValueError("Evidence kind mandatory")
        if self.evidence_kind in ("observed", "community_model") and not self.source_url.startswith("https://"):
            raise ValueError("Sourced skill ranks need public HTTPS provenance")
        if not all(math.isfinite(x) for x in (
            self.expected_damage, self.cooldown_s, self.occupied_s,
            self.hit_probability, self.healing, self.energy_cost
        )):
            raise ValueError("Nonfinite rank stat")


@dataclass(frozen=True)
class Skill:
    name: str
    ranks: dict[int, SkillRank]
    permanent_bonus_levels: int = 0
    mandatory: bool = False
    auto_interruption_fraction: float = 1.0
    upkeep_actions_per_min: float = 0.0
    role: str = "damage"
    required_points: int = 0

    def __post_init__(self):
        if not self.name or self.permanent_bonus_levels < 0 or self.required_points < 0:
            raise ValueError("Invalid skill profile")
        if not 0 <= self.auto_interruption_fraction <= 1:
            raise ValueError("Auto interruption fraction must be 0..1")
        if self.upkeep_actions_per_min < 0:
            raise ValueError("Negative upkeep")
        if self.role not in ("damage", "heal", "support", "buff"):
            raise ValueError("Unknown skill role")
        if any(k != v.level for k, v in self.ranks.items()):
            raise ValueError("Rank keys and rank records disagree")


@dataclass(frozen=True)
class Swap:
    item_id: str
    slot: str
    bonus_levels: int = 0
    direct_damage: float = 0.0
    equip_seconds: float = 0.15
    unequip_seconds: float = 0.15
    release_status: str = "unverified"
    owned: bool = False
    acquisition_gold_cost: int | None = None
    requires_manual_action: bool = True

    def __post_init__(self):
        if not self.item_id or not self.slot or self.bonus_levels < 0:
            raise ValueError("Swap must have item ID, unique slot and level bonus")
        if min(self.direct_damage, self.equip_seconds, self.unequip_seconds) < 0:
            raise ValueError("Negative swap bonus or time")
        if self.acquisition_gold_cost is not None and self.acquisition_gold_cost < 0:
            raise ValueError("Negative acquisition cost")


@dataclass(frozen=True)
class Choice:
    skill: str
    points: int
    effective_rank: int
    rank: SkillRank | None
    swaps: tuple[Swap, ...] = ()
    dps_gain: float = 0
    healing_per_second: float = 0
    actions_per_min: float = 0
    occupation_share: float = 0
    confidence: str = "none"

    @property
    def swap_count(self) -> int:
        return len(self.swaps)

    @property
    def swap_item_ids(self) -> frozenset[str]:
        return frozenset(x.item_id for x in self.swaps)


@dataclass(frozen=True)
class Preferences:
    level: int
    max_swaps_per_skill: int = 0
    per_skill_swap_limit: dict[str, int] = field(default_factory=dict)
    unique_swap_item_limit: int = 0
    total_gold_budget: int | None = None
    skill_points_available: int | None = None
    starting_skill_points: int = 0
    bonus_skill_points: int = 0
    skill_rank_cap_override: int | None = None
    max_effective_skill_rank: int = 50
    baseline_auto_dps: float = 0.0
    auto_loss_fraction: float = 1.0
    manual_action_penalty_dps: float = 0.0
    healing_value_per_hp: float = 0.0
    allow_unverified_owned_swaps: bool = False
    max_occupation_fraction: float = 0.80

    def __post_init__(self):
        if not 0 <= self.max_swaps_per_skill <= 3:
            raise ValueError("Swap limit must be 0..3")
        if not 0 <= self.unique_swap_item_limit <= 30:
            raise ValueError("Unique swap limit must be 0..30")
        if self.max_effective_skill_rank < 1:
            raise ValueError("Invalid effective skill cap")
        if self.total_gold_budget is not None and self.total_gold_budget < 0:
            raise ValueError("Negative gold budget")
        if min(self.baseline_auto_dps, self.manual_action_penalty_dps,
               self.healing_value_per_hp) < 0:
            raise ValueError("Negative preferences")
        if not 0 <= self.max_occupation_fraction <= 1:
            raise ValueError("Occupation limit must be in 0..1")
        if not 0 <= self.auto_loss_fraction <= 1:
            raise ValueError("Auto loss must be 0..1")
        for limit in self.per_skill_swap_limit.values():
            if not 0 <= limit <= 3:
                raise ValueError("Per-skill swap limits must be 0..3")


@dataclass(frozen=True)
class BuildResult:
    choices: tuple[Choice, ...]
    allocated_skill_points: int
    total_points: int
    estimated_dps: float
    estimated_healing_per_second: float
    manual_actions_per_min: float
    occupied_share: float
    utility: float
    used_swap_ids: frozenset[str]
    gold_cost: int | None
    warning: str

    def as_dict(self) -> dict:
        return {
            "allocated_skill_points": self.allocated_skill_points,
            "available_skill_points": self.total_points,
            "estimated_dps": round(self.estimated_dps, 3),
            "estimated_healing_per_second": round(self.estimated_healing_per_second, 3),
            "manual_actions_per_min": round(self.manual_actions_per_min, 3),
            "estimated_skill_time_occupancy": round(self.occupied_share, 5),
            "utility": round(self.utility, 3),
            "unique_swap_item_ids": sorted(self.used_swap_ids),
            "total_acquisition_gold": self.gold_cost,
            "warning": self.warning,
            "skills": [
                {
                    "skill": c.skill,
                    "points": c.points,
                    "effective_rank": c.effective_rank,
                    "dps_gain_vs_auto": round(c.dps_gain, 3),
                    "hps": round(c.healing_per_second, 3),
                    "swaps": [s.item_id for s in c.swaps],
                    "actions_per_min": round(c.actions_per_min, 3),
                    "evidence_kind": c.confidence,
                } for c in self.choices
            ],
        }


def _released(swap: Swap, preferences: Preferences) -> bool:
    return (swap.release_status == "released_documented" or
            (swap.owned and preferences.allow_unverified_owned_swaps))


def options_for_skill(skill: Skill, swaps: list[Swap],
                      prefs: Preferences, point_budget: int) -> list[Choice]:
    cap = level_skill_cap(prefs.level, override=prefs.skill_rank_cap_override)
    max_alloc = min(cap, point_budget)
    effective_cap = min(prefs.max_effective_skill_rank, 100)
    max_items = min(prefs.max_swaps_per_skill,
                    prefs.per_skill_swap_limit.get(skill.name, prefs.max_swaps_per_skill))
    permitted = [s for s in swaps if _released(s, prefs)]
    if len({s.item_id for s in permitted}) != len(permitted):
        raise ValueError(f"Duplicate swap item identifiers for {skill.name}")
    groupings = [()]
    for count in range(1, max_items + 1):
        for choice in combinations(permitted, count):
            if len({x.slot for x in choice}) == count:
                groupings.append(choice)
    candidates = []
    if not skill.mandatory and skill.required_points == 0:
        candidates.append(Choice(skill.name, 0, 0, None))
    for points in range(max(1, skill.required_points), max_alloc + 1):
        for group in groupings:
            rank_num = min(effective_cap, points + skill.permanent_bonus_levels +
                           sum(s.bonus_levels for s in group))
            rank = skill.ranks.get(rank_num)
            if rank is None:  # fail closed: no imaginary interpolated rank formula
                continue
            operations = sum(2 for s in group if s.requires_manual_action)
            overhead = sum(s.equip_seconds + s.unequip_seconds for s in group)
            total_occupied = rank.occupied_s + overhead
            if total_occupied > rank.cooldown_s:
                continue
            casts_per_s = 1 / rank.cooldown_s
            damage = (rank.expected_damage + sum(s.direct_damage for s in group))
            gained = damage * rank.hit_probability * casts_per_s
            auto_lost = (prefs.baseline_auto_dps * total_occupied *
                         skill.auto_interruption_fraction * prefs.auto_loss_fraction *
                         casts_per_s)
            hp_s = rank.healing * rank.hit_probability * casts_per_s
            actions = (operations + 1) * 60 * casts_per_s + skill.upkeep_actions_per_min
            utility = (gained - auto_lost +
                       hp_s * prefs.healing_value_per_hp -
                       actions * prefs.manual_action_penalty_dps)
            candidates.append(Choice(
                skill.name, points, rank_num, rank, tuple(group),
                gained - auto_lost, hp_s, actions,
                total_occupied * casts_per_s, rank.evidence_kind,
            ))
    if skill.mandatory and not candidates:
        raise ValueError(f"Mandatory {skill.name} has no source-backed rank values")
    return candidates


def optimize(skills: list[Skill], swaps_by_skill: dict[str, list[Swap]],
             prefs: Preferences) -> BuildResult:
    if len({s.name for s in skills}) != len(skills):
        raise ValueError("Duplicate skill names")
    budget = skill_point_budget(
        prefs.level, starting_points=prefs.starting_skill_points,
        bonus_points=prefs.bonus_skill_points,
        override=prefs.skill_points_available,
    )
    # Gold cost is charged ONCE per unique non-owned item, regardless of
    # how many skills reuse that item in the rotation.
    cost_by_id = {}
    for group in swaps_by_skill.values():
        for item in group:
            price = 0 if item.owned else item.acquisition_gold_cost
            if item.item_id in cost_by_id and cost_by_id[item.item_id] != price:
                raise ValueError("Inconsistent price/ownership for swap item ID")
            cost_by_id[item.item_id] = price
    # Exact multiple-choice knapsack over the validated per-skill options.
    # State also tracks distinct swap items so "max swap inventory" is exact.
    # Keep up to four non-dominated occupation variants per key to avoid
    # discarding a low-occupation plan which allows later skills to fit.
    dp: dict[tuple[int, frozenset[str]], list[tuple[float, float, tuple[Choice, ...]]]] = {
        (0, frozenset()): [(0.0, 0.0, ())]
    }
    for skill in skills:
        options = options_for_skill(skill, swaps_by_skill.get(skill.name, []),
                                    prefs, budget)
        next_dp: dict[tuple[int, frozenset[str]], list] = {}
        for (spent, ids), variants in dp.items():
            for option in options:
                total = spent + option.points
                if total > budget:
                    continue
                newids = ids | option.swap_item_ids
                if prefs.unique_swap_item_limit and len(newids) > prefs.unique_swap_item_limit:
                    continue
                if prefs.total_gold_budget is not None:
                    costs = [cost_by_id.get(i) for i in newids]
                    if any(c is None for c in costs) or sum(costs) > prefs.total_gold_budget:
                        continue
                key = (total, newids)
                for oldvalue, occupied, prev in variants:
                    newocc = occupied + option.occupation_share
                    if newocc > prefs.max_occupation_fraction + 1e-9:
                        continue
                    utility = (
                        oldvalue + option.dps_gain +
                        prefs.healing_value_per_hp * option.healing_per_second -
                        prefs.manual_action_penalty_dps * option.actions_per_min
                    )
                    list_for_key = next_dp.setdefault(key, [])
                    # Stable Pareto frontier in (occupation, utility).
                    if any(other_occ <= newocc + 1e-10 and
                           other_util >= utility - 1e-10
                           for other_util, other_occ, _ in list_for_key):
                        continue
                    list_for_key[:] = [
                        row for row in list_for_key
                        if not (newocc <= row[1] + 1e-10 and
                                utility >= row[0] - 1e-10)
                    ]
                    list_for_key.append((utility, newocc, prev + (option,)))
        dp = next_dp
        if not dp:
            raise ValueError(f"No feasible allocation including {skill.name}")
    winner = max(
        ((score, occupancy, plan, spent, ids)
         for (spent, ids), variants in dp.items()
         for score, occupancy, plan in variants),
        key=lambda row: (row[0], -row[1], -len(row[4]), -row[3]),
    )
    utility, occ, choices, spent, ids = winner
    final_prices = [cost_by_id.get(i) for i in ids]
    gold_total = (sum(final_prices) if all(p is not None for p in final_prices)
                  else None)
    return BuildResult(
        choices, spent, budget,
        prefs.baseline_auto_dps + sum(x.dps_gain for x in choices),
        sum(x.healing_per_second for x in choices),
        sum(x.actions_per_min for x in choices),
        occ, utility + prefs.baseline_auto_dps, ids, gold_total,
        "Rank-specific inputs are observations/estimates, not validated game "
        "coefficients. Additive cooldown DPS is a screening model, not a "
        "simulation of GCD, simultaneous cooldown contention, DoT overlap, "
        "resistances, player movement or buff uptime.",
    )


def compare_playstyles(skills: list[Skill], swaps_by_skill: dict[str, list[Swap]],
                       prefs: Preferences) -> dict:
    from dataclasses import replace
    modes = {
        "no_swaps": (0, 0.0),
        "casual_one_swap": (1, 0.02),
        "balanced_two_swaps": (2, 0.08),
        "competitive_three_swaps": (3, 0.0),
    }
    results = {}
    for label, (swap_limit, action_penalty) in modes.items():
        selected = replace(
            prefs, max_swaps_per_skill=min(swap_limit, prefs.max_swaps_per_skill),
            manual_action_penalty_dps=max(action_penalty,
                                          prefs.manual_action_penalty_dps),
        )
        try:
            results[label] = optimize(skills, swaps_by_skill, selected).as_dict()
        except ValueError as error:
            results[label] = {"feasible": False, "reason": str(error)}
    return {
        "character_level": prefs.level,
        "base_skill_cap": level_skill_cap(
            prefs.level, override=prefs.skill_rank_cap_override
        ),
        "point_budget": skill_point_budget(
            prefs.level, starting_points=prefs.starting_skill_points,
            bonus_points=prefs.bonus_skill_points,
            override=prefs.skill_points_available,
        ),
        "historical_cap_source": SOURCE_SKILL_CAP,
        "points_source": SOURCE_POINTS,
        "results": results,
    }


def load_scenario(data: dict):
    ps = Preferences(**data["preferences"])
    skills = []
    for raw in data["skills"]:
        obj = dict(raw)
        obj["ranks"] = {int(k): SkillRank(level=int(k), **v)
                        for k, v in obj["ranks"].items()}
        skills.append(Skill(**obj))
    swaps = {key: [Swap(**entry) for entry in group]
             for key, group in data.get("swaps_by_skill", {}).items()}
    return skills, swaps, ps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", type=Path, required=True)
    args = parser.parse_args()
    skills, swaps, preferences = load_scenario(
        json.loads(args.scenario.read_text(encoding="utf-8"))
    )
    print(json.dumps(compare_playstyles(skills, swaps, preferences),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
