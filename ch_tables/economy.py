"""Source-aware Celtic Heroes item rarity, per-server prices and RNG effort.

Rarity label ("Godly") does not imply drop probability. Prices are WORLD
and date dependent; no cross-world conversion and no fabricated estimates.

Accepted submissions are anonymized, separately sourced and validated.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
import math
from random import Random
from statistics import median
from typing import Iterable


@dataclass(frozen=True)
class PriceObservation:
    item_id: int
    world: str
    price_gold: int
    observed_on: str
    kind: str  # completed_sale, sale_listing, buyer_offer, npc_vendor
    source_url: str
    item_name: str = ""
    quantity: int = 1
    sample_id: str = ""

    def __post_init__(self):
        if self.item_id < 0 or self.price_gold < 0 or self.quantity < 1:
            raise ValueError("Invalid price")
        if not self.world.strip() or "://" not in self.source_url:
            raise ValueError("World and verifiable source URL required")
        if self.kind not in ("completed_sale", "sale_listing", "buyer_offer", "npc_vendor"):
            raise ValueError("Unsupported observation kind")
        when = date.fromisoformat(self.observed_on)
        if when > date.today():
            raise ValueError("Future price observation")
        if self.sample_id and len(self.sample_id) > 120:
            raise ValueError("Invalid evidence identifier")


def _quantile(data: list[float], p: float) -> float:
    values = sorted(data)
    pos = (len(values) - 1) * p
    i = int(pos)
    return values[i] + (values[min(i + 1, len(values) - 1)] - values[i]) * (pos - i)


def summarize_world_price(records: Iterable[PriceObservation], *,
                          item_id: int, world: str,
                          max_age_days: int = 90,
                          as_of: date | None = None) -> dict:
    """Only observed *completed* sales estimate realized market price.

    Listing asks and buyer bids remain separate; no pseudo-price when n=0.
    All units normalized to gold per item.
    """
    as_of = as_of or date.today()
    filtered = []
    seen = set()
    for row in records:
        if row.item_id != item_id or row.world.casefold() != world.casefold():
            continue
        key = row.sample_id or (
            row.item_id, row.world.casefold(), row.observed_on,
            row.kind, row.price_gold, row.source_url
        )
        if key in seen:
            continue
        seen.add(key)
        if (as_of - date.fromisoformat(row.observed_on)).days > max_age_days:
            continue
        filtered.append(row)
    categories = defaultdict(list)
    for row in filtered:
        categories[row.kind].append(row.price_gold / row.quantity)
    sold = categories["completed_sale"]
    return {
        "item_id": item_id, "world": world,
        "currency": "in_game_gold_per_item",
        "window_days": max_age_days, "as_of": as_of.isoformat(),
        "completed_sales": len(sold),
        "sold_median_gold": median(sold) if sold else None,
        "sold_iqr_gold": [_quantile(sold, .25), _quantile(sold, .75)]
        if len(sold) >= 4 else None,
        "listing_count": len(categories["sale_listing"]),
        "asking_median_gold": median(categories["sale_listing"])
        if categories["sale_listing"] else None,
        "buyer_offer_count": len(categories["buyer_offer"]),
        "buyer_offer_median_gold": median(categories["buyer_offer"])
        if categories["buyer_offer"] else None,
        "vendor_count": len(categories["npc_vendor"]),
        "vendor_price_gold": median(categories["npc_vendor"])
        if categories["npc_vendor"] else None,
        "evidence_status": "observed_sales" if sold else
                           "only_asks_or_bids" if filtered else
                           "no_current_price_evidence",
        "warning": "Do not infer realizable trade prices from asking listings, "
                   "unverified forum anecdotes, NPC vendor price, or another world.",
    }


@dataclass(frozen=True)
class DropObservation:
    item_id: int
    world: str
    boss_id: int
    boss_name: str
    attempts: int
    successes: int
    source_url: str
    observed_on: str
    independent_session: str

    def __post_init__(self):
        if self.item_id < 0 or self.boss_id < 0:
            raise ValueError("Invalid item or boss id")
        if self.attempts <= 0 or not 0 <= self.successes <= self.attempts:
            raise ValueError("Require counted attempts and successes")
        if not self.world or not self.independent_session or "://" not in self.source_url:
            raise ValueError("World, encounter session and URL required")
        if date.fromisoformat(self.observed_on) > date.today():
            raise ValueError("Future drop evidence")


def drop_rate_estimate(observations: Iterable[DropObservation], *,
                       item_id: int, world: str, boss_id: int,
                       draws: int = 3500, seed: int = 79) -> dict:
    """Jeffreys prior Beta(0.5,0.5), conditional on comparable encounter trials.

    Estimates uncertainty only under stationary independent Bernoulli drops.
    Does not presume that every loot slot is an independent roll.
    """
    rows = [x for x in observations if
            x.item_id == item_id and x.world.casefold() == world.casefold()
            and x.boss_id == boss_id]
    if not rows:
        return {
            "item_id": item_id, "world": world, "boss_id": boss_id,
            "drop_rate": None, "interval_95": None, "observations": 0,
            "status": "unknown_no_attempt_counts",
        }
    sessions = {x.independent_session for x in rows}
    if len(sessions) != len(rows):
        raise ValueError("Duplicate session; aggregate and deduplicate source first")
    a = sum(r.successes for r in rows) + .5
    b = sum(r.attempts - r.successes for r in rows) + .5
    rng = Random(seed)
    posterior = sorted(rng.betavariate(a, b) for _ in range(draws))
    return {
        "item_id": item_id, "world": world, "boss_id": boss_id,
        "attempts": sum(r.attempts for r in rows),
        "successes": sum(r.successes for r in rows),
        "independent_sessions": len(rows),
        "drop_rate": a / (a + b),
        "interval_95": [_quantile(posterior, .025), _quantile(posterior, .975)],
        "status": "estimated_from_observed_trials",
        "warning": "Beta-Bernoulli approximates independent same-version attempts; "
                   "drop table or patch drift invalidates pooled estimates.",
    }


def acquisition_chance(probability: float | None, attempts: int) -> float | None:
    if attempts < 0:
        raise ValueError("Negative number of attempts")
    if probability is None:
        return None
    if not 0 <= probability <= 1 or not math.isfinite(probability):
        raise ValueError("Drop rate must be 0..1")
    return -math.expm1(attempts * math.log1p(-probability)) if probability < 1 else (
        0.0 if attempts == 0 else 1.0
    )


def median_expected_trials(probability: float | None) -> int | None:
    if probability is None:
        return None
    if probability == 0:
        return None
    if not 0 <= probability <= 1:
        raise ValueError("Invalid drop chance")
    return math.ceil(math.log(.5) / math.log1p(-probability)) if probability < 1 else 1


@dataclass(frozen=True)
class EffortBudget:
    world: str
    gold: int | None = None
    maximum_boss_kills: int | None = None
    minimum_success_chance: float | None = None
    acquisition_mode: str = "any"  # trade, grind, any
    include_unknown_rng: bool = False
    include_unknown_market: bool = False

    def __post_init__(self):
        if not self.world.strip():
            raise ValueError("World is required to price gear")
        if self.gold is not None and self.gold < 0:
            raise ValueError("Negative budget")
        if self.maximum_boss_kills is not None and self.maximum_boss_kills < 0:
            raise ValueError("Negative boss budget")
        if self.minimum_success_chance is not None and not (
            0 <= self.minimum_success_chance <= 1
        ):
            raise ValueError("Invalid success threshold")
        if self.acquisition_mode not in ("trade", "grind", "any"):
            raise ValueError("Invalid acquisition mode")


def feasible_acquisition(*, owned: bool, released: bool,
                         market_price_gold: float | None,
                         drop_probability: float | None,
                         budget: EffortBudget) -> dict:
    """No silent fantasy gold/RNG estimates; owning an item bypasses acquisition."""
    if owned:
        return {"feasible": True, "method": "already_owned"}
    if not released:
        return {"feasible": False, "reason": "release_not_documented"}
    trade = budget.acquisition_mode in ("any", "trade")
    grind = budget.acquisition_mode in ("any", "grind")
    outcomes = []
    if trade:
        if market_price_gold is None and not budget.include_unknown_market:
            outcomes.append((False, "no_server_trade_price"))
        elif budget.gold is not None and market_price_gold is not None \
                and market_price_gold > budget.gold:
            outcomes.append((False, "over_gold_budget"))
        else:
            outcomes.append((True, "trade"))
    if grind:
        if drop_probability is None:
            outcomes.append((budget.include_unknown_rng, "unknown_rng"))
        elif budget.maximum_boss_kills is None:
            outcomes.append((True, "grind_unbounded"))
        else:
            p = acquisition_chance(drop_probability, budget.maximum_boss_kills)
            need = budget.minimum_success_chance
            outcomes.append((need is None or (p is not None and p >= need),
                             "grind_within_budget"))
    accepted = next((reason for yes, reason in outcomes if yes), None)
    return {
        "feasible": accepted is not None,
        "method": accepted,
        "blocking_reasons": [why for yes, why in outcomes if not yes],
    }
