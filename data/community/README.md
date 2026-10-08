# Community economy observations (personal-first)

These CSV files start deliberately empty. There is **no verified public
cross-server completed-sales database** included with this project.

Place only **actual sourced observations** in the CSVs: item ID from
`data/game/items.jsonl.gz`, exact world name, actual quantity, source URL,
and calendar date. Use full numerical gold, not ambiguous 1m/3k suffixes.

## prices.csv
`item_id,world,price_gold,observed_on,kind,source_url,item_name,quantity,sample_id`

Kinds:
- `completed_sale` — sale actually happened; preferred for market medians
- `sale_listing` — asking price, **never** represented as paid price
- `buyer_offer` — advertised bid, **never** represented as paid price
- `npc_vendor` — NPC posted price (may differ from trade market)

Use `sample_id` to prevent duplicate listings and screenshots.
Avoid including real player identities, handles, chat logs or account details.
A screenshot or public archived listing URL is not proof a listed item sold.

## drops.csv
`item_id,world,boss_id,boss_name,attempts,successes,observed_on,source_url,independent_session`

Track the exact boss, item, world and comparable game patch per cohort.
One row = one independently logged encounter session with the NUMBER OF
TRIALS AND SUCCESSES. Do not turn a "1/5000" forum guess into 5,000
measured attempts. Avoid deducing live loot rates from an item's "Godly"
rarity prefix.

## How results are modeled

Per world, only completed sales estimate a realized market median.
Listing asks, offers and NPC prices are displayed separately. Prices older
than 90 days are excluded by default. No prices are inferred across servers.

For submitted killed-boss attempts, use a Jeffreys-prior
Beta(successes + 0.5, failures + 0.5) estimate with credible intervals.
Unobserved drop probabilities remain **unknown**, never zero.

The `EffortBudget` model accepts gold, tolerated number of boss kills,
target acquisition success probability, and trade-vs-grind preference.
It explicitly distinguishes confirmed ownership from missing market/RNG data.

To regenerate:
```powershell
python -m ch_tables.market_import --game data/game --input data/community --output data/community
python -m unittest tests.test_economy tests.test_market_import -v
```

Keep community contributions as reviewable individual evidence records.
World economies are time-varying. Do not scrape private game data or
publish anyone's trade messages without their permission.
