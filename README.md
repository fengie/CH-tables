# CH-tables

> ⏱️ Last README update: **October 8, 2026 · 9:00:43 PM EDT** _(repo-enforced)_

Celtic Heroes class/boss data utilities, normalized class samples, and reproducible effective-DPS analysis.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Refresh the **full public Codex Saved Builds catalog (327 linked builds)** from the pinned, verified four-page snapshot:

```powershell
python -m ch_tables.codex_catalog
```

This rebuilds all public listing rows, derived CSV tables, provenance manifest and a local indexed SQLite database joining the existing skill-panel observations. [Coverage and limitations](docs/CODEX_CATALOG.md). The older one-page network refresher is guarded against silently truncating a complete dataset.

Refresh the community build sample:

```powershell
python -m ch_tables.scrape
python main.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Personalized gear, skill and pet optimization (personal beta)

This repo is moving toward a Prydwen-style guide and character builder, with
per-level skill points, **0–3 gear swaps per skill**, item-release safety,
pet tiers, game-server trade observations, RNG limits and QoL alternatives.
The current implementation is a local Python **research optimizer**, not
a finished website or validated live-game DPS simulator.

- [Combat holdout validation harness](docs/COMBAT_VALIDATION.md): source-locked
  recorded-session comparisons against seeded simulations; synthetic fixtures
  are regression evidence only, **not** real-game calibration.

- [Design, algorithms, exact limits and roadmap](docs/BUILD_PLANNER.md)
- [User's DEX-only knuckleblade Rogue template](data/planner/personal_dex_fist_rogue_template.json)
- [Runnable explicitly synthetic example](data/planner/example_scenario.json)
  and [example comparison report](data/planner/demo_report.json)
- [Source-specific skill-DPS indices](data/planner/skill_snapshot_rankings.json)
- [Public pet species/tier/index](data/pets/pets_and_tiers.json)
- [Full rarity metadata](data/game/item_rarity_summary.json):
  rarity labels are not drop probabilities
- [Per-world market and drop input schema](data/community/README.md):
  completed sales are never confused with asking prices
- [Community contribution/evidence policy](CONTRIBUTING.md)

Run:

```powershell
# One command runs all optimizer, data-ingestion and safety tests
python -m unittest discover -s tests -v

# Synthetic proof that point allocation and multiple playstyles run
python -m ch_tables.build_planner --scenario data/planner/example_scenario.json

# Real personal runner, once exact per-skill rank curves are provided
python -m ch_tables.personal_planner --scenario data/planner/personal_dex_fist_rogue_template.json

# Inspect item rarity and availability labels, source skills and pets
python -m ch_tables.game_query items "Creidhne's Knuckleblade" --released-only
python -m ch_tables.pet_catalog
python -m ch_tables.skill_priorities

# Recalculate from sourced marketplace or documented loot observations
python -m ch_tables.market_import
```

**No fabricated stat curves/prices:** Skill-rank damage in the personal
template is intentionally blank, world and exact level must be confirmed,
and the market submission files initially contain no observations. The
personal runner fails rather than inventing a BIS rotation. The automated
snapshot-specific skill ranking is NOT a universal skill priority list.

## Reproducible refresh pipeline

The Saved Builds refresh is validate-before-publish rather than a direct scrape-to-`latest` write:

1. fetch the canonical source HTML and bounded response metadata;
2. content-address the source snapshot under `data/source_snapshots/codex-builds/`;
3. bind the parser to the Saved Builds semantic headers and fail closed on schema drift;
4. parse, normalize, summarize, and validate everything in per-run staging;
5. publish the CSVs only after all staged artifacts pass validation;
6. publish `data/normalized/dataset_manifest.json` last as the generation marker.

The manifest records the source/content hash, parser schema, filter parameters, row counts, output SHA-256 values, and calibration-source identities. Source snapshots are deduplicated by SHA-256 and retain only the newest 10 by default; override with `--snapshot-retention`.

Network, schema, parse, normalization, staging, or mid-publication failures do not replace the previously published CSV/manifest set; partial publication is rolled back from same-directory recovery siblings. This keeps a failed upstream refresh from silently turning into a new analysis baseline.

## Missing-data policy

The report no longer prints a blank/N/A merely because a target build page is missing a derived metric.

1. Direct values are preferred and labeled **SOURCE**.
2. If a useful derived metric is missing, it may be reconstructed only from sourced comparable data.
3. Reconstructed values are labeled **ESTIMATE** in the tables.
4. The model, calibration sample, formulas, sample size, empirical range, and original source URLs are printed.
5. Estimates are never silently presented as observed facts.

### Warrior example

The Surya8 Saved Builds entry exposes a benchmark DPS of **11,982.1**, while its current detail page does not expose a populated Practical Rotation Guide value.

The fallback uses three Warrior builds that expose both Overall Rotation DPS and Practical DPS:

- Draga — https://the-codex.ch/damagebuilder/draga
- yuhhh — https://the-codex.ch/damagebuilder/yuhhh
- Gwyn Shields DPS — https://the-codex.ch/damagebuilder/gwyn-shields-dps

For each calibration build:

```text
practical_ratio = practical_dps / overall_dps
```

The target estimate is:

```text
Surya8 practical DPS
    = Surya8 benchmark DPS
    * median(calibration practical_ratio)
```

The practical auto share is estimated with the median practical auto share of the same Warrior calibration sample.

With the current calibration data this gives approximately:

```text
Surya8 estimated practical DPS: 11,529.7
Empirical practical-DPS range:  11,503.3 - 11,557.3
Estimated practical auto share: 48.9%
Observed auto-share range:       40.6% - 50.7%
Estimated auto DPS:              5,638.0
Calibration n:                   3
```

Because the calibration sample is small, the code reports its observed min/max range instead of claiming a misleading high-confidence population interval.

## Full extracted public game-data archive

The [complete source-pinned game-data inventory](docs/FULL_GAME_DATA.md)
is now available for all classes, not just endgame Rogue. It records
23,752 items, 8,406 detailed combat mobs, 5,484 loot-source mobs,
322,763 item-drop references, six major questline groups and
28,290 original item bonus tuples, with cross-dataset hash and ID
validation. The data does not include unpublished server or client
coefficients; live availability remains unverified.

Search locally with:
```powershell
python -m ch_tables.game_query items "Creidhne's Knuckleblade"
python -m ch_tables.game_query combat_mobs "Dhiothu"
python -m ch_tables.game_query questlines
```

## Released gear vs unreleased database-only entries

The full item archive is intentionally broader than equipment that
players can actually obtain. The [evidence-backed release-status system](docs/GEAR_RELEASE_STATUS.md)
separates documented released, historically released, confirmed unreleased,
and **unverified** items. Reconstructed loot entries and questline links
do **not** independently prove public release.

At the latest evidence audit: 8 exact items have official family-level
release documentation; 23,744 are unverified, **not** "unreleased".
Current farmability/tradability is checked separately.

All item queries and the [priority gear lookup](data/catalog/priority_gear_lookup.json)
show release flags; only sourced released gear is admitted by default to
strict BIS comparison:

```powershell
python -m ch_tables.game_query items "Creidhne's Knuckleblade" --released-only
python -m ch_tables.game_query items "Knuckleblade" --release-status unverified
```

Research can still inspect every unverified item without treating development
records as real-world upgrades. New evidence is validated against exact
item IDs/names and official source links before the catalog is reclassified.

## Reusable CH mechanics and gear research

This repository now includes a source-pinned, reproducible Celtic Heroes
reference system. All numerical observations are labeled; published
calculator approximations are not claimed as official server equations.

- [Skill / ability registry](ch_tables/skill_reference.py): 93 community-indexed
  skills and 43 named abilities, with character-stat scaling and evasion types
  where documented.
- [Cross-class skill panel observations](data/reference/codex_skill_panel_observations.json):
  **122 modeled skill observations from 12 public Codex builds**, spanning all
  five classes. Includes base/effective attributes, skill abilities,
  cooldown/cast/lockout, and per-skill damage when present. These are
  *saved-build snapshots*, not fitted engine coefficients.
- [Endgame/rogue item catalog](data/catalog/rogue_endgame_items.json):
  **3,203 candidate records** selected from **23,752** unique upstream items
  using the pinned [catalog manifest](data/catalog/catalog_manifest.json).
- [Priority gear lookup](data/catalog/priority_gear_lookup.json) and
  [item-stat schema](data/catalog/item_stat_schema.json): inspect raw item
  field names, exact item bonuses and plausible alternative gear without
  pretending to have proven BIS ranks.
- [Boss resistances/evasions](data/reference/raid_boss_resistances_2026_10_08.json):
  eight historical upstream raid-boss records.
- [Robust stat inverse-modeling](ch_tables/calibration.py): identifiability
  checks, segmented-sqrt STR candidates, Huber IRLS, leave-session-out
  validation, session bootstrap, and information-guided next experiments.
- [Research and validation protocol](docs/SCALING_RESEARCH.md) explains
  exactly what measurements are needed to recover currently unknown
  rank-specific skill formulas.
- [Personal DEX fist Rogue profile](docs/DEX_FIST_ROGUE_PROFILE.md)
  documents fixed skills, held gear, and knuckleblade-only constraints.

Source refreshes are explicit and bounded, not scheduled to scrape on
every push. Local commands:

```powershell
python -m ch_tables.catalog_ingest --output data/catalog
python -m ch_tables.catalog_report
python -m ch_tables.codex_skill_ingest
python -m unittest discover -s tests -v
```

**Known gaps:** Some user-owned Valley of Ancients and Proteus items are absent
from the imported item names; current-client weapon speed/procs and complete
skill rank coefficients remain unverified. Never fill unknown values by guess.

## Data sources

Original source URLs live in `ch_tables/sources.py`.

The Codex is an unofficial community resource, not an official DECA Games stat sheet:

- https://the-codex.ch/
- https://the-codex.ch/builds

The generic class summary describes the sampled published builds after filtering to comparable damage builds at level 220+, not the entire player population.

## Current plans & progress

Canonical ledger: [`_AGENT_CONTEXT/PROJECT_PLAN.md`](_AGENT_CONTEXT/PROJECT_PLAN.md)

Issue #2 is complete on canonical `main` at `2b1fd85a4468ce813bd101b5bfa34e6a2a680d8b`; exact PR head `b78033f49d254ece4fac7fc82f4a172f93fea260` passed Tests run `37128924361` before integration.
