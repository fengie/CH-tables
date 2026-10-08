"""Validate community-supplied world-specific prices and observed loot trials.

Does not scrape private markets, assume world-wide gold parity, or publish
unsourced forum anecdotes as completed sales. The starter data is intentionally
empty until evidence is supplied.

python -m ch_tables.market_import --input data/community --output data/community
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import json
from pathlib import Path

from .economy import (
    PriceObservation, DropObservation, summarize_world_price, drop_rate_estimate,
)
from .full_game_ingest import canonical_json
from .game_query import load_records

PRICE_HEADERS = (
    "item_id", "world", "price_gold", "observed_on", "kind", "source_url",
    "item_name", "quantity", "sample_id",
)
DROP_HEADERS = (
    "item_id", "world", "boss_id", "boss_name",
    "attempts", "successes", "observed_on", "source_url",
    "independent_session",
)


def read_validated_csv(path: Path, expected: tuple[str, ...]) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Expected contributions file: {path}")
    with path.open(encoding="utf-8-sig", newline="") as fp:
        rows = csv.DictReader(fp)
        if tuple(rows.fieldnames or ()) != expected:
            raise ValueError(f"{path}: CSV header mismatch. Required: {expected}")
        return list(rows)


def load_market_rows(source: Path, items: dict[int, str],
                     boss_ids: set[int]):
    raw_prices = read_validated_csv(source / "prices.csv", PRICE_HEADERS)
    raw_drops = read_validated_csv(source / "drops.csv", DROP_HEADERS)
    prices = []
    price_dedup = set()
    for i, row in enumerate(raw_prices, 2):
        try:
            data = PriceObservation(
                item_id=int(row["item_id"]), world=row["world"].strip(),
                price_gold=int(row["price_gold"]), observed_on=row["observed_on"],
                kind=row["kind"], source_url=row["source_url"],
                item_name=row["item_name"],
                quantity=int(row["quantity"] or 1),
                sample_id=row["sample_id"],
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"prices.csv line {i}: {e}") from e
        if data.item_id not in items:
            raise ValueError(f"prices.csv line {i}: unknown item ID")
        if data.item_name and data.item_name != items[data.item_id]:
            raise ValueError(f"prices.csv line {i}: item ID/name mismatch")
        ident = data.sample_id or (
            data.item_id, data.world.casefold(), data.observed_on,
            data.kind, data.price_gold, data.source_url,
        )
        if ident in price_dedup:
            raise ValueError(f"prices.csv line {i}: duplicate marketplace evidence")
        price_dedup.add(ident)
        prices.append(data)
    drops = []
    sessions = set()
    for i, row in enumerate(raw_drops, 2):
        try:
            data = DropObservation(
                item_id=int(row["item_id"]), world=row["world"],
                boss_id=int(row["boss_id"]), boss_name=row["boss_name"],
                attempts=int(row["attempts"]), successes=int(row["successes"]),
                source_url=row["source_url"],
                observed_on=row["observed_on"],
                independent_session=row["independent_session"],
            )
        except (ValueError, TypeError) as e:
            raise ValueError(f"drops.csv line {i}: {e}") from e
        if data.item_id not in items or data.boss_id not in boss_ids:
            raise ValueError(f"drops.csv line {i}: unknown item or boss ID")
        identity = (
            data.item_id, data.world.casefold(), data.boss_id,
            data.independent_session,
        )
        if identity in sessions:
            raise ValueError(f"drops.csv line {i}: duplicated item/world/boss session")
        sessions.add(identity)
        drops.append(data)
    return prices, drops


def summarize_prices(prices: list[PriceObservation],
                     drops: list[DropObservation]) -> dict:
    price_keys = sorted({(r.item_id, r.world) for r in prices})
    drop_keys = sorted({(r.item_id, r.world, r.boss_id) for r in drops})
    return {
        "schema_version": 1,
        "data_policy": "read_only_user_or_community_submissions_no_fake_market_prices",
        "prices_submitted": len(prices),
        "drop_observation_sessions": len(drops),
        "price_by_item_world": [
            summarize_world_price(prices, item_id=item_id, world=world)
            for item_id, world in price_keys
        ],
        "drop_rate_by_item_world_boss": [
            drop_rate_estimate(drops, item_id=item_id, world=world,
                               boss_id=boss)
            for item_id, world, boss in drop_keys
        ],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("data/community"))
    parser.add_argument("--output", type=Path, default=Path("data/community"))
    parser.add_argument("--game", type=Path, default=Path("data/game"))
    opts = parser.parse_args()
    items = {int(row["id"]): row["name"]
             for row in load_records("items", root=opts.game)}
    mobs = {int(row["id"]) for row in
            load_records("combat_mobs", root=opts.game)}
    prices, drops = load_market_rows(opts.input, items, mobs)
    summary = summarize_prices(prices, drops)
    opts.output.mkdir(parents=True, exist_ok=True)
    dest = opts.output / "market_summary.json"
    pending = dest.with_name(dest.name + ".tmp")
    pending.write_bytes(canonical_json(summary))
    pending.replace(dest)
    print(json.dumps({
        "prices_submitted": len(prices),
        "drop_sessions": len(drops),
        "worlds": sorted(set(x.world for x in prices + drops)),
    }))


if __name__ == "__main__":
    main()
