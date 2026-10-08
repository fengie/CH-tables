# Contributing game facts and optimization evidence

This is currently a personal-first Celtic Heroes planner, being designed to
support community maintenance later. **No account connection or private
player data is required.** The official game/data belongs to its respective
rights holders; this fan project is not endorsed by DECA Games.

## The four data categories and proof required

### 1. Released/retired/unreleased gear

Update `data/release/evidence.json` with:
- exact item ID and exact name from the pinned game dataset
- status, source type, date, public HTTPS URL and a concrete reason
- public release proof for `released_documented`
- evidence of *both* historical ownership and retirement for
  `historically_released`
- explicit publisher/developer confirmation of never releasing an item for
  `confirmed_unreleased`

Source text about a whole set should identify the exact set and variant
before being applied to exact item IDs. Database appearance, item rarity,
absence of drops, an unlabeled screenshot, and reconstructed loot links
are **not enough** to mark an item either released or unreleased.

### 2. Skill ranks and character stat formulas

Use identical character/equipment/target/patch except for the one varied
parameter. Record exact rank (allocated and effective), STR/DEX/FOC/VIT,
active weapon ability, skill ability, item bonuses, target, crit/miss
sampling, cooldown/cast/lockout, and source file or publishable URL.
Document sample size and uncertainty. Never mix rank-40 with rank-50
screenshots into one coefficient without accounting for rank effects.

Add reproducible tests in `tests/`. Do not "reverse engineer" from one
saved build alone, then present guessed coefficients as exact game values.

### 3. Prices by world

`data/community/prices.csv` only accepts date, actual world,
item ID, gold, quantity and source reference. Record separately:

- `completed_sale`: a completed trade/auction transaction
- `sale_listing`: an advertised asking price
- `buyer_offer`: advertised bid
- `npc_vendor`: shop price

No seller/player handles, private message screenshots, account names or
bank details should be published. Do not convert the prices of one
world into another without independent actual trade samples.

### 4. Item rarity and boss drops

`data/community/drops.csv` tracks counted trials, successes, target
boss, exact item, world, timestamp and independent encounter-session
source. Remember that a game-data item tier is **not** its loot rate.
Drop-rate estimates are probabilistic, game-patch and world dependent.
If only anecdotes exist, leave the rate unknown.

## Code quality and security

- Every claim carries source URL, exact scope, current version and
  evidence type; every derived value clearly shows formula and
  uncertainty.
- Use `python -m unittest discover -s tests -v` locally.
- Built-in ingestion parses upstream JS **as inert JSON**, never executes it.
- No automated login, private scraping, spoofing of game traffic, or
  unauthorized client/server access.
- Add regression tests for broken parsing, stale data, bad assumptions,
  rank thresholds, equipment conflicts and source mismatches.
- Make patches small and avoid force pushing parallel contributor work.
- Do not include game artwork, proprietary client files, or copyright
  dialogue in contributions.

## Current code layout

| Area | Primary code |
| --- | --- |
| Public game reference | ch_tables/full_game_ingest.py |
| Item provenance and release | ch_tables/release_status.py |
| Item rarity | ch_tables/item_rarity.py |
| Skills and numerical evidence | ch_tables/skill_reference.py; ch_tables/skill_priorities.py |
| Skill points and swap search | ch_tables/build_planner.py |
| Pet species and tier evidence | ch_tables/pet_catalog.py |
| Pet performance | ch_tables/companions.py |
| World market/RNG/effort | ch_tables/economy.py; ch_tables/market_import.py |
| Combined character planner | ch_tables/personal_planner.py |
| Product and algorithm roadmap | docs/BUILD_PLANNER.md |

## Licensing consideration before wider public launch

A permissive code license (e.g. MIT or Apache-2.0) can be evaluated
**separately** from third-party game-data rights. The game-data extracts,
logo, images and other copyrighted content are **not automatically**
relicensed by publishing application code. Check DECA Games' policies
and upstream contributor attribution/licensing before broad distribution.
No license should be selected on another contributor's behalf.
