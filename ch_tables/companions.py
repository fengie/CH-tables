"""Optional one-pet shortlist with explicit DPS observations and investment gates.

Pets interact with class stats, buffs and boss mitigation. Ranking based only
on species name or pet 'rarity' is prohibited: every numeric DPS comparison
requires an in-game measurement/model clearly marked with provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable

from .economy import EffortBudget, feasible_acquisition


@dataclass(frozen=True)
class PetCandidate:
    key: str
    species: str
    color: str
    level_requirement: int
    item_id: int | None = None
    owned: bool = False
    release_status: str = "unverified"
    token_cost: int | None = None
    measured_marginal_dps: float | None = None
    measured_marginal_hps: float | None = None
    actions_per_min: float = 0.0
    evidence_url: str = ""
    evidence_kind: str = "unmeasured"

    def __post_init__(self):
        if self.level_requirement < 0 or not self.key or not self.species:
            raise ValueError("Invalid pet")
        if self.token_cost is not None and self.token_cost < 0:
            raise ValueError("Invalid pet token cost")
        if self.measured_marginal_dps is not None and self.measured_marginal_dps < 0:
            raise ValueError("Negative marginal pet DPS")
        if self.measured_marginal_hps is not None and self.measured_marginal_hps < 0:
            raise ValueError("Negative marginal pet healing")
        if self.actions_per_min < 0:
            raise ValueError("Negative pet actions")
        if self.evidence_kind not in (
            "unmeasured", "user_estimate", "observed", "community_model"
        ):
            raise ValueError("Unknown pet evidence kind")
        if self.measured_marginal_dps is not None and self.evidence_kind == "unmeasured":
            raise ValueError("Numeric pet DPS cannot be labeled unmeasured")
        if self.evidence_kind in ("observed", "community_model") and not self.evidence_url.startswith("https://"):
            raise ValueError("Observed pet benefit requires verifiable HTTPS provenance")


def pet_shortlist(pets: Iterable[PetCandidate], *,
                  character_level: int,
                  effort: EffortBudget,
                  owned_pet_tokens: int | None = None,
                  world_sale_prices: dict[int, float] | None = None,
                  item_drop_rates: dict[int, float] | None = None,
                  qol_cost_per_action: float = 0.0,
                  healing_value_per_hp: float = 0.0) -> dict:
    if character_level < 1:
        raise ValueError("Invalid character level")
    if owned_pet_tokens is not None and owned_pet_tokens < 0:
        raise ValueError("Negative pet token budget")
    prices = world_sale_prices or {}
    rates = item_drop_rates or {}
    ranked = []
    unresolved = []
    excluded = []
    for pet in pets:
        if character_level < pet.level_requirement:
            excluded.append({"pet": pet.key, "reason": "level_too_low"})
            continue
        if pet.token_cost is not None and owned_pet_tokens is not None \
                and pet.token_cost > owned_pet_tokens and not pet.owned:
            excluded.append({"pet": pet.key, "reason": "insufficient_upgrade_tokens"})
            continue
        # Documented "pet species" is not necessarily a published exact item.
        # If there is no exact item ID, non-owned availability stays unverified.
        if pet.item_id is not None:
            access = feasible_acquisition(
                owned=pet.owned,
                released=pet.release_status == "released_documented",
                market_price_gold=prices.get(pet.item_id),
                drop_probability=rates.get(pet.item_id),
                budget=effort,
            )
        else:
            access = {"feasible": pet.owned,
                      "reason": None if pet.owned else "no_verified_item_identity"}
        if not access["feasible"]:
            excluded.append({"pet": pet.key, "reason": access})
            continue
        if pet.measured_marginal_dps is None:
            unresolved.append({
                "pet": pet.key,
                "reason": "no_measured_pet_marginal_dps",
                "source_url": pet.evidence_url,
                "token_cost": pet.token_cost,
            })
            continue
        score = (
            pet.measured_marginal_dps +
            (pet.measured_marginal_hps or 0) * healing_value_per_hp -
            pet.actions_per_min * qol_cost_per_action
        )
        ranked.append({
            "pet": pet.key, "species": pet.species,
            "measured_marginal_dps": pet.measured_marginal_dps,
            "measured_marginal_hps": pet.measured_marginal_hps,
            "actions_per_min": pet.actions_per_min,
            "utility": score, "source_kind": pet.evidence_kind,
            "source_url": pet.evidence_url,
            "token_cost": pet.token_cost,
            "acquisition": access,
            "warning": "Marginal performance is specific to the measured player "
                       "build, target and encounter; not a universal pet ranking.",
        })
    ranked.sort(key=lambda x: (-x["utility"], x["pet"]))
    return {
        "ranked_measured_pets": ranked,
        "feasible_but_unmeasured_pets": unresolved,
        "ineligible_pets": excluded,
        "default_pet_ranking": ranked[0] if ranked else None,
        "warning": "Only independently measured/explicit user-estimated pets "
                   "can have numerical DPS ranks. Numeric ranks do not include "
                   "unmeasured pet effects, boss debuffs or team synergy.",
    }
