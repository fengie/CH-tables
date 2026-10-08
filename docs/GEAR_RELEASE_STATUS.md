# Item release verification: avoid developer-only/unused gear in BIS

Updated October 8, 2026. Canonical implementation:
[ch_tables/release_status.py](../ch_tables/release_status.py).

## Why this is essential

A database hit is not an actual player-obtainable item. The maintainer of
the unofficial Celtic Heroes Database explicitly states that extracted records
include **developer testing gear** and **historically discontinued items**:
- https://celticheroesdb.com/search
- https://forum.celtic-heroes.com/forum/viewtopic.php?f=169&t=100965

The CH Encyclopedia's mob loot associations are **reconstructed** from public
data, not first-hand confirmations of drops. Its six manually curated questlines
are useful guides, but also do not verify every exact item ID in live inventories:
- https://github.com/celtichero2026/CH-Encyclopedia

## Two independent axes

1. **Release status** (positive/negative evidence):
   - `released_documented`: release evidence connects an exact item ID/name to
     an officially or otherwise verifiably released item; might not be farmable
     today.
   - `historically_released`: evidenced to have existed publicly and has
     additional evidence of retirement or seasonality. Do NOT call this
     "unreleased".
   - `confirmed_unreleased`: evidence directly confirms never released
     publicly; requires official/developer confirmation from an official domain.
   - `unverified`: only game data or insufficient external evidence; no
     conclusion about whether the item was ever released.
2. **Obtainability right now**: stored independently as `currently_obtainable`.
   Current values are `unknown` until separately verified. Even a documented
   released item might be impossible to acquire today but still exist in
   somebody's inventory.

Other source signals are **not evidence of release**:
- `reconstructed_loot_reference`
- `curated_questline_reference`
- `unattributed_database_record`

These distinctions prevent an unused development weapon from winning a
theoretical "BIS" search simply because it has extraordinary stat numbers.

## Audit coverage

As of October 8, 2026:

- 23,752 item IDs assigned evidence-backed states
- **8** released via official family-level documentation:
  - Creidhne's Knuckleblade of Ashes (#65537)
  - Creidhne's Knuckleblade of Winter (#65538)
  - Creidhne's Knuckleblade of Earth (#65539)
  - Doch Gul Fortitude pieces (#900001–900005)
- **23,744 unverified** (NOT described as unreleased)
- **0 confirmed unreleased** (no item-specific official proof collected yet)
- **0 historically released** (no item-specific retirement evidence collected yet)

Dhiothu weapon-tier public documentation:
https://www.celtic-heroes.com/news/6110-release-patch-notes-st-patricks-event

Doch Gul Fortitude public documentation:
https://www.celtic-heroes.com/news/version-522

Evidence scope is explicitly `official_named_set_and_exact_matching_quest_item`
or `explicit_weapon_family_plus_exact_item_name`. These are **family-level**
official release announcements matched to pinned database item names/IDs, not
a claim to have seen each exact item in an inventory screenshot.

The curated index remains usable for research: 8,686 with reconstructed
loot links, 215 with questline references, and 14,851 without either source
signal. All three groups contain potentially released gear; none is treated
as individually proven released from that signal alone.

## Usage and BIS safety

Every `items` search response now displays `release_status`,
`release_evidence`, `release_source_signals`,
`currently_obtainable`, and `excluded_from_default_bis`.

Examples:

    python -m ch_tables.game_query items "Knuckleblade" --limit 30
    python -m ch_tables.game_query items "Knuckleblade" --released-only
    python -m ch_tables.game_query items "Knuckleblade" --release-status unverified

The keyword shortlist at
[data/catalog/priority_gear_lookup.json](../data/catalog/priority_gear_lookup.json)
also annotates each entry. It is a research lookup, **not** an automatic BIS
ranking. Only `released_documented` passes the strict default BIS gate.
Users may explicitly investigate unverified items, but do not advertise
those as real-world obtainable gear.

## Adding reliable evidence

Evidence is maintained at [data/release/evidence.json](../data/release/evidence.json).
Each item requires:
- Exact numeric item ID AND exact pinned game-data name
- A defensible release state, evidence type and public HTTPS source
- Source publication/observation date (ISO), explanation and scope
- For official/developer claims: `celtic-heroes.com` or a subdomain
- For historically retired items: separate evidence of retirement/seasonality
- For confirmed never-released items: direct official/developer confirmation

**Never** add an item to the unreleased category purely because no forum
post, loot source, or screenshot was found. Absence of evidence is not proof.

Rebuild:

    python -m ch_tables.release_status --data data/game --evidence data/release/evidence.json
    python -m ch_tables.catalog_report
    python -m unittest tests.test_release_status tests.test_game_query tests.test_catalog_report -v

The automated [gear release status gate](../.github/workflows/gear-release-status.yml)
validates identities, flags unsupported claims, checks archive hashes and
publishes the classification to main. The full public game-data import also
rebuilds these states so an updated item table cannot silently keep stale
evidence classifications.

## Known limits

The current number of released confirmations is intentionally a **lower
bound of examined/corroborated item IDs**, not a claim that only eight items
were ever released. Old items, seasonal gear, event chest cosmetics, clan
quest equipment and most endgame jewelry still need independent individual
corroboration. These remain in the research database and cannot silently
enter authoritative recommendations.

An item can remain flagged documented released if it is later retired;
actual farming/trading availability must be assessed independently by date
and game server.
