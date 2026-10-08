# Celtic Heroes full public factual-game-data archive

Generated and verified October 8, 2026. Repository: fengie/CH-tables.

**Scope:** All factual records extracted from the five pinned, publicly
accessible CH Encyclopedia JS datasets, plus the independently indexed
Codex skill panels and wiki-based skill/ability references.

This is **NOT** a complete dump of the current live game/server/client.
It excludes creative descriptions, dialogue, icons, models and artwork.
Some extracted game records represent unused or unreleased content.

## Source provenance

Source: https://github.com/celtichero2026/CH-Encyclopedia
Pinned source commit: fb6d99ba035dd28e5df08e6303f653da0de9a024
Assets: data/base.js, data/items-01.js, data/items-02.js,
data/mobstats-all.js and data/mobstats.js.

The full manifest at ../data/game/manifest.json records a SHA256 for each
input and output and archives all retained factual fields as reproducible
gzip-compressed JSON/JSON Lines. Upstream JavaScript is parsed only as a
JSON literal; it is never executed. Do not conflate these extracts with
verified in-game obtainable items or live server formulas.

## Complete source inventory

| Category | Records | Files |
| --- | ---: | --- |
| All item IDs and structural data | 23,752 | data/game/items.jsonl.gz |
| Item ID/name text index | 23,752 | data/game/item_names.tsv |
| Monster loot-source records | 5,484 | data/game/mobs.jsonl.gz |
| Detailed combat monsters | 8,406 | data/game/combat_mobs.jsonl.gz |
| Curated boss spotlight records | 71 | data/game/spotlight_mobs.jsonl.gz |
| Monster drop records | 322,763 | data/game/mob_drop_records.jsonl.gz |
| Reverse item-to-mob references | 322,763 | data/game/item_mob_references.jsonl.gz |
| Major questline groups | 6 | data/game/questlines.json.gz |
| Structured set metadata | 1 section | data/game/other_structured_base.json.gz |
| All flattened item bonuses | 28,290 | data/game/all_item_bonuses.jsonl.gz |
| Distinct stat names/occurrences | - | data/game/all_bonus_names.json |
| Source field schema + examples | - | data/game/field_inventory.json |
| Cross-dataset validation | - | data/game/quality_report.json |

Flattened item bonuses include 7,250 attribute, 3,006 ability,
5,153 skill, 10,155 resistance and 2,726 evasion entries.
Distinct names observed: 5 attributes, 29 abilities, 96 skill bonuses,
14 resistances and 6 evasions. Raw bonus tuples remain unchanged
including unknown trailing numbers.

Detailed mob combat data includes attack, defence, damage types,
resistances, evasions, health, energy, gold, experience, attack speed,
zones and source-dependent spawn coordinates. See field_inventory.json
rather than relying on a partial hardcoded list.

### Data quality audit

All 322,763 drop entries refer to known item IDs (0 unresolved).
All 5,484 loot mobs have matching records in the larger combat table.
There are 2,922 combat-only mob IDs.
The 71 spotlight mobs' only differing field categories against the
full combat dataset are fishingDamage, radius or spawns.
Both variants are retained instead of silently overwriting one.

**These are source consistency checks, not proof of current live
obtainability, probabilities, exact mitigation or attack speed effects.**

## Reproduce or search any game record

From the repository root (Python 3.12+):

    python -m ch_tables.game_query items "Creidhne's Knuckleblade"
    python -m ch_tables.game_query items "Ferocity" --class Rogue
    python -m ch_tables.game_query combat_mobs "Dhiothu"
    python -m ch_tables.game_query mobs "Bloodthorn"
    python -m ch_tables.game_query items "" --id 65539
    python -m ch_tables.game_query items "" --all-fields --class Rogue --limit 50
    python -m ch_tables.game_query questlines
    python -m ch_tables.game_query mob_drop_records "" --id 142027 --limit 50

Source-pinned collection:

    python -m ch_tables.full_game_ingest --output data/game
    python -m ch_tables.gear_bonus_index --data data/game
    python -m ch_tables.game_quality --data data/game
    python -m unittest discover -s tests -v

The automated one-shot ingestion and source integrity gates are in
.github/workflows/full-game-import.yml and deliberately do not perform
continuous automated external scraping.

## Other separately evidenced skill data

- ch_tables/skill_reference.py: 93 community skill entries,
  43 abilities and known stat types.
- data/reference/codex_skill_panel_observations.json:
  122 modelled skill observations across 12 publicly saved builds.
- ch_tables/calibration.py: segmented-STR candidate inference,
  robust regression and uncertainty methods; not a recovered engine law.
- docs/DEX_FIST_ROGUE_PROFILE.md: fixed user DEX-only Rogue personal
  build, named STR knuckles, owned equipment and fixed skill roster.

## Material information still unavailable from retrieved sources

1. Raw full-client SkillTemplates across all skill levels/ranks
   (including energy costs, cooldown modification and coefficients).
2. Raw QuestTemplates, dialogue/complete NPC quest logic.
3. Full PetAppearances and proprietary art/assets.
4. Official current server loot probabilities or spawn logic.
5. Verified 2026 item physical weapon damage, swing delays and
   hidden proc rates; these are NOT in the extracted item-stat fields.
6. Current game-client/patch data beyond the pinned public snapshot.
7. Account-specific equipped-stat screens and measured combat logs.

A May 2026 Reddit post claims that SkillTemplates, QuestTemplates,
PetAppearances and Abilities tables were extracted independently,
but supplies no verifiable public download for those extra tables:
https://www.reddit.com/r/Celticheroes/comments/1tg9wvv/

Public supplemental sources:
https://celticheroesdb.com/groups
https://celticheroesdb.com/calculator
https://the-codex.ch/builds
https://celtic-heroes.fandom.com/wiki/Skills

Do not substitute reconstructed coefficients for unknown source data,
mix patches, attempt unauthorized server access, or republish media
assets. Source provenance and confidence are mandatory.
