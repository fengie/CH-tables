# ADR: interaction-aware search and realistic combat, Celtic Heroes v0

**Status:** accepted architectural boundary; numeric predictions UNCALIBRATED.
**Date:** October 8, 2026
**Scope:** CH-tables product only, not a new Heaven Toolbox policy.
**Toolbox source:** fengie/heaven-toolbox@deddf6000a7018f25eca1f6623b6e60626707a3e.
**Product baseline:** fengie/CH-tables@b906c68409fae13ca7cd9b094494f88a38ea9ea6.
**Related:** [BUILD_PLANNER.md](BUILD_PLANNER.md), [SCALING_RESEARCH.md](SCALING_RESEARCH.md), [GEAR_RELEASE_STATUS.md](GEAR_RELEASE_STATUS.md).

## Product thesis and why the old model is insufficient

The user wants a personal-first tool that eventually supports community-fed
data and Prydwen-style understandable guides. The winning build changes with
actual usable inventory, boss, level, stat allocation, weapon style, mount,
pet, skill-point bonuses, offhand swaps, health/energy needs, elixir/potion
burden and allowed micromanagement.

Existing build_planner.py optimizes a *screening proxy*; it is **not** an
encounter simulator. Do not advertise proxy DPS as empirical in-game DPS.
Existing per-rank Codex samples are build-specific, not transferable formulas.

## Full action/build representation

Treat each candidate as (character, encounter, equipped gear, active pet,
mount state, weapon/offhand/shield set, skill allocation, skill-specific
swap graph, rotation policy, consumable policy, acquisition strategy).

- **Fixed character:** class, allocated STR/DEX/FOC/VIT, level, skill budget,
  equipment slots, owned inventory, abilities, points from quest/gear and
  explicitly verified game patch.
- **Surface sets:** mainhand, offhand/shield, five armour slots, charm,
  jewellery, cape, pet and mount, with set-bonus thresholds and exclusion
  relationships. Add source-specific slots, not fabricated generic slots.
- **Gear snapshots:** base surface; during each skill cast; short
  mitigation/survival swap; raid-support loadout. Count swap operations,
  action lockout, lost autos and opportunity cost. For CG offhand or rings,
  effective rank is evaluated *at cast time*; then restore base offhand.
- **Mount:** catalog actual bonuses (including VIT, FOC, raw HP/Energy,
  regeneration, mobility), duration, combat applicability, equipment conflicts
  and activation/deactivation. **Unknown in-combat persistence is a hard
  evidence gap**, not implicit permanent combat HP. Do not assume a mount can
  be used concurrently with a weapon, offhand or pet until verified.
- **Survivability:** max HP, armour, each boss damage type, defence/avoidance,
  healing/regen, shields, energy sustain, heal action cost, probability of
  death, recovery/rebuff downtime, travel/positioning and party role.
- **Consumables:** type (HP pot, energy pot, heroic/attack-speed lix,
  regen lix), per-server gold price, measured effect/stacking, duration,
  cooldown, available inventory, interaction with attack speed/weapon caps,
  potion actions/minute and tolerable spending per fight/hour.
- **Acquisition:** released/legacy/unverified; account owned; world-specific
  observed *completed* sales; realistic rarity/drop probability with
  confidence, budget and farming time. No invented market values.
- **Objectives:** encounter damage, net practical DPS, damage taken/deaths,
  HP/E safety margin, healing/energy pots, lix uses, gold/hour, click/swaps
  per minute, acquisition probability, budget and scenario robustness.
  Return a Pareto set, NOT a misleading universally optimal single winner.
- **Profiles:** solo-no-pots, raid support, non-lix auto, low-input/mobile,
  budget, peak theoretical, high-sustain caster, high-survival glass cannon
  rescue, skill-heavy and weapon-family variants. User chooses tradeoffs.

No gear that was only present in a development client should silently
enter a recommended publicly obtainable build.

## Algorithm selection: decomposition beats brute-force combinations

Stage 0 — **evidence gates:** item release status, owned inventory, player
class/level, allowed role, slot; unknown weapon speed/ability and unknown
stat conversion are not silently zeroed.

Stage 1 — **interaction-preserving prefilter:** only drop item B if A is
strictly better on every modeled beneficial stat with no higher cost/level
requirement *and* identical slot, weapon family, source/version/gear ownership,
set threshold tags, skill breakpoints, trigger/proc signatures and known
effects. Preserve shields, mounts, CG skill offhands and conditional pieces.
See loadout_foundation.py and adversarial tests. Avoid pruning across
missing-effect intervals or set membership.

Stage 2 — **exact constraints:** CP-SAT/ILP for legal equipment, offhand
exclusion, stat/level gates, skill-point budget, temporary cast-time bonuses,
set thresholds, owned/affordable/risk choices, inventory reuse, maximum
swaps per skill. Use integer-scaled quantities and audit rounding; prefer
a small exact oracle for correctness. OR-Tools CP-SAT is an optional solver,
not a required runtime dependency until benchmarked.

Stage 3 — **cheap performance bounds:** source-backed sheet damage, attack
cap, resource-balance screen, simple survival upper bounds and action
opportunity costs. See fight_screening.py. It labels output optimistic.
Never call this "actual DPS".

Stage 4 — **calibrated discrete-event simulation:** priority queue of attack
ticks, ability casts, skill cooldown, damage ticks, energy use/regen,
buff/debuff expiration, swap-equipment events, mount/dismount states, pet
abilities, enemy attacks, heals/potions, interrupts, movement, death and
respawn. Include deterministic seeds; use paired common random numbers for
fair candidate comparisons. Unknown mechanics remain parameters with
uncertainty. An implementation must be calibrated to in-game measurements.

Stage 5 — **multiobjective optimization:** epsilon-constraint searches and
maintained nondominated populations; compare NSGA-II/R-NSGA-II, CP-SAT-based
epsilon Pareto enumerations and a seeded beam/local-neighborhood search.
Active surrogate or adaptive budget allocation prioritizes uncertain near-
frontier candidates and intentionally different outliers. Diversity on
weapon family, swap pattern, mount, role and set to discover combinations.

Stage 6 — **proof and explanations:** re-evaluate the surviving frontier on
the same fixed encounter scenario seeds with more samples; show variance
and confidence intervals, limitations and acquisition confidence. Export
"a shield beats a damage offhand here because X pots and Y deaths avoided"
or "CG swap saves Z skill points" as factor-level comparisons, not anecdotes.

### Correct research metrics

For time-limited fights: E[damage delivered by time T]/T.
For kills: record damage, completion probability, and a conditional time
statistic; separately present total time including deaths/recovery and
consumables. Avoid E[damage]/E[time] == E[damage/time] claims.
Benchmark expected damage and uncertainty under a fixed boss/patch,
not absolute DPS derived from uncalibrated formulas.

### Feasible algorithms and why not one "best"

- [OR-Tools CP-SAT](https://developers.google.com/optimization/cp/cp_solver):
  good for Boolean/integer assignment constraints. Requires integer
  scaling; return FEASIBLE vs OPTIMAL honestly.
- [pymoo NSGA-II](https://www.pymoo.org/algorithms/moo/nsga2.html):
  rank/crowding multiobjective heuristics, **no optimality certificate**.
- [SimPy event model](https://simpy.readthedocs.io/en/latest/api_reference/simpy.events.html):
  useful event semantics, not game timing formulas.
- [Optimal computing budget allocation](https://arxiv.org/abs/2209.11809):
  supports adaptive simulation effort instead of equal trials for all
  designs. Empirical superiority here **must** be measured.
- [Celtic Heroes DB](https://celticheroesdb.com/calculator) and
  [the Codex](https://the-codex.ch/) are calibration/reference sources;
  they are not official current-patch mechanic or item-availability proof.

## Acceptance criteria and benchmarks (not yet completed)

1. Small cases with <=5 slots, 4 candidate items each, two skills
   and one allowed swap: solver matches an exhaustive oracle on **every**
   feasible assignment and its objective, with modeled corner cases.
2. Metamorphic tests: increasing player HP or energy cannot worsen
   resource-balance *screen* results; unknown mount combat applicability
   cannot be silently activated. Source-visible shield/CD proc survives
   prefilter. Decrease swap limit may not increase feasible set.
3. Event simulator: deterministic identical seeds/results; property-based
   no double equipment slots, no free potions, energy never negative without
   explicit overdraw, buffs expire, swap effects only during active snapshot,
   heal/death and cooldown timing validated against logged game experiments.
4. Calibration: grouped holdout by encounter/session/patch, observed
   auto and skill damage distributions, accuracy, DPS errors, potion use,
   death fraction and effort. No arbitrary target "% accuracy" invented.
5. Search quality: report hypervolume/regret vs tiny exact oracle,
   diversity, unexplored effects, runtime, memory, solver gap and total
   cost per verified recommendation. Benchmark fixed budgets/time and
   seeds against naive enumeration, beam, CP-SAT, NSGA-II.
6. Explainability: for each frontier point include feasible reason,
   release/owned status, acquisition confidence, combat uncertainty,
   counterfactual nearest alternatives, what changes with mounts/shields/
   lixes/offhand skill-point swaps, and why it's excluded if unknown.
7. UX: local profile, boss selector, gear + mount/pet inventory, editable
   allowed skill swaps per skill, gold/hour and total investment sliders,
   solo/raid/QoL presets, clear "source vs estimate vs unknown" labels.
   Screen-reader accessibility, keyboard interaction and responsive layout.
8. Privacy/security: no login initially, local-only personal data by
   default, output size caps, schema validation, upstream source approval,
   dependency pin + audit, secret scanning, rate limits if ever hosted.
   Game account credentials are NEVER required.

## Legal: documented constraint, not legal advice

[DECA's Terms of Service](https://decagames.com/tos.html) prohibit
automated access to games, server scraping, unauthorized reverse engineering
and reuse of protected content without permission (subject to applicable law).
Do not build a gameplay bot, credential harvester, packet sniffer or game
client scraper. Keep own original code independently licensed; prior
community extracts may require permission for redistribution.
Before public release: audit per-source legal provenance, request publisher
permission as appropriate and distinguish raw proprietary game data from
original calculations/independently contributed observations.
Avoid republishing copyrighted game artwork, dialogue or item descriptions.

## Sequenced product implementation and stop/go

**P0: data contract:** equip/mount/consumable source attributes with
provenance and actual combat applicability; user-owned profile.
**P1: exact eligibility + tiny oracle:** gear and skill combinations across
mount/pet/shield/weapon/offhand; no mass brute-force.
**P1: simulation vertical slice:** one Rogue encounter plus
one resource-constrained Mage/Druid, real skill observations, shield vs DPS
offhand and no-lix vs haste scenario; calibrate before wider classes.
**P1: explainable Pareto frontier:** fast exact legal search, sample budget
and a few distinctive policy points; evidence quality stays visible.
**P2: personal UI:** fast local/offline, user-friendly guide outputs.
**P3: community:** versioned contribution templates, moderation, terms
review, transparent quality score and game-patch updates.

Toolbox improves only through verified reusable lessons, **not** automatic
promotion of Celtic Heroes rules into its cross-project trainer.
