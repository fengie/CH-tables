"""Conservative steady-rate fight screening, NOT game-validated combat simulation.

Measures sustained resource viability, optimistic consumable lower bounds and
upper-bound uninterrupted DPS after mandatory manual actions. This is a cheap
prefilter before a calibrated discrete-event/Monte Carlo encounter simulator.
All rates (including armour mitigation and haste) must be supplied from
observed player/game data; no inferred armour or stat scaling formula.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class HastePlan:
    """Buff duration/price and *measured* auto-rate multiplier, no game default."""
    auto_dps_multiplier: float
    duration_s: float
    gold_per_elixir: int

    def __post_init__(self):
        if self.auto_dps_multiplier < 1 or not math.isfinite(self.auto_dps_multiplier):
            raise ValueError("Haste multiplier must be finite and >=1")
        if self.duration_s <= 0 or self.gold_per_elixir < 0:
            raise ValueError("Positive duration and nonnegative cost required")


@dataclass(frozen=True)
class FightScreen:
    duration_s: float
    auto_dps: float
    skill_dps: float
    max_hp: float
    max_energy: float
    incoming_damage_per_s: float
    incoming_reduction_per_s: float = 0.0  # measured after armour/defence
    hp_regeneration_per_s: float = 0.0
    energy_regeneration_per_s: float = 0.0
    passive_healing_per_s: float = 0.0
    energy_spend_per_s: float = 0.0
    hp_potion_amount: float = 0.0
    energy_potion_amount: float = 0.0
    hp_potion_gold: int | None = None
    energy_potion_gold: int | None = None
    potion_action_seconds: float = 0.0
    required_swap_seconds: float = 0.0
    hp_potion_limit: int = 0
    energy_potion_limit: int = 0
    haste: HastePlan | None = None
    mount_flat_hp: float = 0.0
    mount_flat_energy: float = 0.0
    mount_effects_verified_in_combat: bool = False

    def __post_init__(self):
        numeric = (
            self.duration_s, self.auto_dps, self.skill_dps, self.max_hp,
            self.max_energy, self.incoming_damage_per_s,
            self.incoming_reduction_per_s, self.hp_regeneration_per_s,
            self.energy_regeneration_per_s, self.passive_healing_per_s,
            self.energy_spend_per_s, self.hp_potion_amount,
            self.energy_potion_amount, self.potion_action_seconds,
            self.required_swap_seconds, self.mount_flat_hp,
            self.mount_flat_energy,
        )
        if any(not isinstance(x, (int, float)) or not math.isfinite(x) or x < 0
               for x in numeric) or self.duration_s <= 0:
            raise ValueError("Finite nonnegative measured rates and duration >0 required")
        if min(self.hp_potion_limit, self.energy_potion_limit) < 0:
            raise ValueError("Negative potion count limit")
        if ((self.mount_flat_hp or self.mount_flat_energy) and
                not self.mount_effects_verified_in_combat):
            raise ValueError("Mount in-combat HP/energy require verified applicability")
        for price in (self.hp_potion_gold, self.energy_potion_gold):
            if price is not None and price < 0:
                raise ValueError("Negative consumable price")


def _lower_bound(deficit: float, amount: float) -> int | None:
    if deficit <= 1e-9:
        return 0
    if amount <= 0:
        return None
    return math.ceil((deficit - 1e-9) / amount)


def screen_fight(profile: FightScreen) -> dict:
    """Cheap optimistic *necessary* resource conditions, not sufficient proof.

    HP/E deficits calculated over full target window; no over-heal/over-cap,
    burst deaths, timing conflicts, healing casts or attack variance modeled.
    Actual consumables may be higher, and outcomes may be worse.
    """
    p = profile
    hp = p.max_hp + p.mount_flat_hp
    energy = p.max_energy + p.mount_flat_energy
    net_damage_s = max(
        0.0,
        p.incoming_damage_per_s - p.incoming_reduction_per_s -
        p.hp_regeneration_per_s - p.passive_healing_per_s,
    )
    net_energy_s = max(0.0, p.energy_spend_per_s - p.energy_regeneration_per_s)
    hpb = _lower_bound(max(0.0, net_damage_s * p.duration_s - hp),
                       p.hp_potion_amount)
    enb = _lower_bound(max(0.0, net_energy_s * p.duration_s - energy),
                       p.energy_potion_amount)
    sustainable_by_balance = (
        hpb is not None and enb is not None and
        hpb <= p.hp_potion_limit and enb <= p.energy_potion_limit
    )
    num_haste = (math.ceil(p.duration_s / p.haste.duration_s - 1e-10)
                 if p.haste else 0)
    haste_multiplier = p.haste.auto_dps_multiplier if p.haste else 1.0
    ideal_dps = p.auto_dps * haste_multiplier + p.skill_dps
    if sustainable_by_balance:
        action_seconds = (p.required_swap_seconds +
                          (hpb + enb) * p.potion_action_seconds)
        availability = max(0.0, (p.duration_s - action_seconds) / p.duration_s)
        practical_screening_bound = ideal_dps * availability
    else:
        action_seconds = None
        availability = None
        practical_screening_bound = None
    costs = []
    for count, value in (
        (hpb, p.hp_potion_gold),
        (enb, p.energy_potion_gold),
    ):
        if count is None:
            continue
        if count and value is None:
            costs.append(None)
        else:
            costs.append(count * (value or 0))
    if p.haste:
        costs.append(num_haste * p.haste.gold_per_elixir)
    gold = sum(costs) if all(x is not None for x in costs) else None
    return {
        "method": "optimistic_steady_rate_feasibility_screen_v1",
        "fight_duration_s": p.duration_s,
        "ideal_uninterrupted_dps": ideal_dps,
        "necessary_resource_balance_satisfied": sustainable_by_balance,
        "minimum_hp_potions_lower_bound": hpb,
        "minimum_energy_potions_lower_bound": enb,
        "haste_elixirs_required": num_haste,
        "consumable_gold_lower_bound": gold,
        "minimum_mandatory_action_seconds": action_seconds,
        "maximum_activity_fraction_under_assumed_minimum_actions": availability,
        "optimistic_practical_dps_upper_bound": practical_screening_bound,
        "unmodeled": [
            "Damage burst/death, armour conversion, pet skill procs, movement",
            "Potion cooldown, over-heal, pot timing, skill cooldown/auto contention",
            "Buff expiration, focus/vitality-to-resource conversion, regen suppression",
            "Haste effect on skill timing or proc behavior and server patch changes",
        ],
        "warning": "This is not a validated expected DPS estimate. It is an "
                   "optimistic steady-rate upper bound; passing does not "
                   "prove fight survival, and missing data must stay unknown.",
    }
