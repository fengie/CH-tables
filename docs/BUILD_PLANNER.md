# Personalized Celtic Heroes build planner — current implementation and public roadmap

**Research and implementation baseline: 8 October 2026.** This project
starts as an exact, source-annotated local Python tool. It is **not yet a
fully featured website**, nor a validated current-patch combat simulator.

The long-term design is a Prydwen-like guide and equipment builder,
plus user-specific simulation, transparent math, swap policies,
farming/trading investment planning and community-maintained game data.

## Design principles

1. **No false precision.** Unknown skill rank curves, pet damage,
   loot probabilities, weapon delays or live world prices remain unknown.
2. **Release-vs-database protection.** Never recommend unused developer gear.
   See [GEAR_RELEASE_STATUS.md](GEAR_RELEASE_STATUS.md).
3. **User equipment first.** Prefer already-owned gear over theoretical
   unobtainable gear. Make each item's source and uncertainty visible.
4. **Respect individual objectives.** An attack/Expose-support rogue and an
   auto-DPS rogue can share a character but need different objective functions.
5. **Effective damage over screenshots.** Subtract cast/gear-swap opportunity
   costs, account for survival, support and uptime.
6. **All knobs optional and explicit.** A quiet casual playstyle isn't
   "wrong"; it is a valid objective.

## Features implemented in Python

| Area | Current executable component | Status |
| --- | --- | --- |
| Historic max skill level by level | `build_planner.level_skill_cap` | In use; current-patch override |
| Skill points available at level X | `build_planner.skill_point_budget` | 1 per level gained, base level-1 plus explicit starting/quest/other points |
| Skill choices | `Skill`, `SkillRank` | Needs sourced rank-specific measurements |
| Extra effective skill levels from swaps | `SkillSwap` equivalents under `Swap` | Supports per-skill max 0,1,2,3 |
| Surface versus swap gear | `Swap` has explicit slot, item ID, timing | Source release-status validation in `personal_planner` |
| Exact skill-point allocation | Multiple-choice knapsack DP | Uses rank-based marginal DPS, heal, actions and occupation |
| Shared swap inventory | DP reuses item IDs; one gold charge | Supports distinct item limit and global gold cap |
| Swap time and autocancel cost | `SkillRank` and `Choice` | Explicit interruption and manual-action cost; not full real-time scheduling |
| QoL alternatives | `compare_playstyles` | No-swaps, casual 1, balanced 2, competitive 3 |
| Observed damage rankings | `skill_priorities` | 12 source builds, not transferable rankings |
| Pets and pet levels | `pet_catalog` | 11 species/groups, historical tier stats, candidate items |
| Pet comparison | `companions.pet_shortlist` | Only pets with explicit measured marginal DPS are rankable |
| Item rarity descriptors | `item_rarity` | Explicit fields and prefix tiers, **never** fake drop rates |
| Per-world economy | `economy`, `market_import` | Completed sales, listing asks, bids and NPC prices distinguished |
| Uncertainty-aware drops | `drop_rate_estimate` | Jeffreys Beta interval from actual counted attempts |
| RNG/gold effort | `EffortBudget`, `feasible_acquisition` | Gold cap, kills cap, desired chance and trade/grind mode |
| Full data archive | `full_game_ingest` and `game_query` | 23,752 items, 8,406 combat NPCs, loot and quest metadata |
| Source release annotations | `release_status` | 23,752 classified; unknown does not mean unreleased |

Current optimizer evaluates additively approximated cast damage over
cooldown minus opportunity cost and filters high-occupation setups.
It is **not** an event simulator; auto and DoT contention, casts delayed
by other spells, accuracy debuffs and team DPS must be included before
an absolute DPS output can be called fully verified.

## Level X — historic skill cap reference

Source: https://forum.celtic-heroes.com/forum/viewtopic.php?p=93058
and https://forum.celtic-heroes.com/forum/viewtopic.php?f=48&t=11316

| Character level | Historical unboosted rank cap |
| --- | --- |
| 1–14 | 5 |
| 15–29 | 10 |
| 30–59 | 15 |
| 60–89 | 20 |
| 90–119 | 25 |
| 120–149 | 30 |
| 150–179 | 35 |
| 180–209 | 40 |
| 210–239 | 45 |
| 240+ | 50 |

At level 220, conservative level-up-only budget = 219 points
(if zero spendable points exist at initial level 1). Any actual starting,
bonus, quest or special point counts must be user-confirmed. A +10 skill
ring at 45 allocated points is capped by the 50 maximum effective
rank unless the current game says otherwise. Both constraints are
configurable.

## Why swapping can improve rank-50 skill selection

With ordinary surface gear and point budget B, choose allocated
points p_i per skill, subject to sum p_i <= B and base skill rank cap.
When casting skill i, equip 0..k_i source-verified swap items in
distinct slots, increasing that skill's *temporary* effective rank
or damage, and then restore the surface set.

The actual benefit is approximately:

    net_i = hit_probability_i * expected_damage_i / effective_cooldown_i
            - interrupted_auto_DPS * occupied_cast_and_swap_time_i / cooldown_i

Cost is charged for the same item only once even if reused across
skills. The exact rank-effect values must be measured at every rank
being considered; the system deliberately refuses to invent points
for levels not in supplied rank curves. Debuffs like Expose Weakness
are not ranked as direct damage spells; their contribution to party
damage must be modeled separately.

This is mathematically a multiple-choice knapsack with cardinality and
gear-sharing constraints. A Pareto frontier handles alternative
time-occupation costs. Compare solutions across 0–3 allowed swaps and
explicit QoL penalties. Future versions should extend this to multiple
target-boss scenarios and release/price uncertainty.

Source on practical swapping:
https://forum.celtic-heroes.com/forum/viewtopic.php?p=750708

## Personal gear preferences already preserved

The sample personal template lives at
[data/planner/personal_dex_fist_rogue_template.json](../data/planner/personal_dex_fist_rogue_template.json).

- All freely allocated primary stats stay DEX; no automatic STR rebirth.
- Personal weapon target: named STR Dhiothu/Creidhne Hand-to-Hand knuckles.
- Existing raid Expose gear remains separate from persistent/solo gear.
- Exactly these personal skills: Shadowstrike, Quick Strike, Life Steal,
  Double Attack, Rend, Smoke Bomb and Expose Weakness.
- No maintenance optimization relying on Poison Weapon/Fast Reflexes.
- Existing Godly/Imperial Ferocity, Concealment, Valley ring, Proteus
  HP/Energy brace and planned Doch Gul set retained as priorities.
- HP/Energy sustain, personal solo damage, lower maintenance and fashion
  acquisition are valid secondary objectives.
- Level, world, exact gold, game version and measured skill rank values
  are **not yet confirmed** and must not be inferred from this template.

## Pet evidence, rarity and investment

[Eagle](https://celticheroes.blogspot.com/2020/07/eagle-pet-guide.html),
[Wolf](https://celticheroes.blogspot.com/2020/07/wolf-pet-guide.html),
[Chicken](https://celticheroes.blogspot.com/2020/07/chicken-pet-guide.html)
and [Phoenix](https://celticheroes.blogspot.com/2020/07/phoenix-pet-guide.html)
guides document tier-dependent stats. Some basic pet guide breeding
examples require 32 tokens for a Giant lowest-tier pet, versus 128 for
the top color tier; this does not establish the cost of all premium pets.

The full extracted item names are parsed for possible pet items.
Name-only candidates remain unverified, and pet DPS isn't inferred
from species names. Enter measured active-skill damage, cooldown,
passive stat gains and hit data to compare real companions.

Item prefixes like Godly/Imperial/Royal and any literal source
`rarity` field are kept distinct from a measured drop rate. Without
actual kills/drops, RNG probability and expected number of raids are
*unknown*. Estimates from community submissions carry the number of
trials and uncertainty intervals.

World-specific prices require
[data/community/prices.csv](../data/community/prices.csv) and
[drops.csv](../data/community/drops.csv), with verifiable links.
Asking price is NOT a completed transaction. A 2013 world price
cannot automatically represent a 2026 market.
There is no verified cross-world trading-price feed currently imported.

## How to run now

```powershell
python -m unittest discover -s tests -v

# Works with clearly marked toy data to verify the optimizer itself:
python -m ch_tables.build_planner --scenario data/planner/example_scenario.json

# Source-grounded item/pet and modeled-skill inventory:
python -m ch_tables.game_query items "Creidhne's Knuckleblade" --released-only
python -m ch_tables.pet_catalog
python -m ch_tables.skill_priorities

# Personal runner requires real measured rank curves in its profile:
python -m ch_tables.personal_planner --scenario data/planner/personal_dex_fist_rogue_template.json
```

The last command will intentionally fail with a missing rank-measurement
error until real evidence is supplied. This prevents fabricated BIS advice.

## Prioritized roadmap for a future community website

**Phase A — local accurate optimizer:**
1. Collect real per-skill-rank curves and player stat screenshots by
   controlled item swaps, with reproducible source evidence.
2. Implement discrete-event multi-skill auto/cast/DoT simulation, rank
   thresholds and buff/debuff effects, validate against actual combat logs.
3. Add full equipment-slot/set synergies, switching back to surface gear,
   and active pet/mount skill timers in the same simulator.
4. Jointly optimize HP/defence/DPS/sustain, no-upkeep QoL, unique swap
   inventory, gold and expected farming effort; return a Pareto front.
5. Add saved personal profiles, import/export JSON, versioned snapshots.

**Phase B — local front end / personal guide:**
6. Clean tabbed build-builder: level/classes, gear inventory, skills,
   pet/mount, enemy, swaps-per-skill controls, world, and investment.
7. Side-by-side results: max DPS, budget, easy rotation, survival and
   support raid alternatives, with estimated intervals and evidence links.
8. Gear acquisition planner: owned → affordable/tradable → farmable →
   rare/unverified separately, with boss/drop/questline provenance.
9. Printable build guides with simple explanations and advanced math
   expandable rather than displayed to every user.

**Phase C — opt-in community extension:**
10. Community PR contributions for item descriptions, skill rank
    observations, prices, encounter logs and released-gear proof.
11. Moderated source audit, dedupe, version/patch review and reversible
    corrections to prevent false source claims or manipulated prices.
12. World-specific price coverage, freshness controls and sample sizes;
    **never** present auction asking prices as completed trades.
13. Versioned public dataset API, cacheable client JSON/SQLite, full-text
    search and documented source citations/licenses.
14. Build sharing with opt-in public profile fields. Keep all private
    inventory, account names and screenshots local by default.

For inspiration:
- Prydwen design: https://www.prydwen.gg/
- Fribbels optimizer documented filters and permutations:
  https://github.com/fribbels/hsr-optimizer/blob/main/docs/guides/en/optimizer.md
- Celtic Heroes Codex current combat builder:
  https://the-codex.ch/damagebuilder
- Celtic Heroes DB formula limitations:
  https://celticheroesdb.com/calculator

**Caution:** This is a community fan project; avoid unauthorized
game-server scraping and third-party site copying. Public game-data
facts should carry provenance and permission/licensing considerations.
