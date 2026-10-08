# Project Plan — Canonical Work Ledger

This file is the repository's durable current-work ledger. It follows the cross-repository contract in `fengie/heaven-toolbox@main:_AGENT_TRAINING/PROJECT_PLAN_CONTRACT.md`.

## Operating rules

- Allowed statuses: `PLANNED`, `READY`, `ACTIVE`, `BLOCKED`, `DEFERRED`, `DONE`, `SUPERSEDED`.
- Nonterminal items record source/evidence, owner or `unclaimed`, acceptance criteria/goal, and one concrete next action.
- Checkboxes become complete only from canonical-main or exact referenced evidence.
- Update this ledger after material ownership/status/blocker changes, after integration, and before handoff.
- Do not fabricate roadmap items to make a quiet repository appear active.

## Current plans & progress

### DATA-002 — Reproducible staged scrape pipeline

**Status:** DONE  
**Owner:** completed via issue #2 / PR #3  
**Source:** issue #2; current Codex Saved Builds schema; branch implementation  
**Goal:** make live scraped analysis inputs reproducible, schema-drift safe, validate-before-publish, and bounded in retained source evidence.

- [x] Select the Saved Builds table by semantic headers instead of first-table position.
- [x] Fail closed on missing/duplicate/malformed required columns or rows.
- [x] Retain content-addressed source HTML with bounded snapshot retention.
- [x] Stage raw/normalized/summary outputs and publish only after validation.
- [x] Emit a machine-readable manifest with source/output hashes, row counts, parser version, filters, and calibration sources.
- [x] Add regressions for unrelated leading tables, schema drift, failure preservation, and successful manifest publication.
- [x] Exact head `b78033f49d254ece4fac7fc82f4a172f93fea260` passed Tests run `37128924361`.
- [x] Merged as `2b1fd85a4468ce813bd101b5bfa34e6a2a680d8b` and verified remote `main` readback.

**Execution-path note:** the current ChatGPT session exposes the canonical Toolbox skills and authenticated GitHub mutation surface but no callable Heaven/Agent Control local-runtime namespace, so the mandatory local offload lane could not be exercised. Exact candidate GitHub CI is the mechanical verification path.

**Next action:** none for DATA-002; future schema changes must update parser fixtures/version and preserve the same fail-closed publication contract.


### OPT-001 — Equip/mount/consumable feasibility and research benchmark

**Priority:** P1  
**Status:** ACTIVE  
**Owner:** unclaimed for next implementation phase  
**Source:** personal user request October 8, 2026; `docs/OPTIMIZATION_ARCHITECTURE_2026_10_08.md`; Heaven Toolbox source `deddf600`.  
**Goal:** interaction-safe candidate screening and measured fight feasibility including mounts, shield/offhand, sustain, QoL, consumables and acquisition limits.

- [x] Document modular search/simulation/contracts, source uncertainty, legality and bounded phases.
- [x] Implement candidate interaction signatures and no-false-pruning tests.
- [x] Implement explicitly optimistic health/energy/potion/haste fight screen and adversarial tests.
- [ ] Validate mount stat persistence, combat availability and offhand classes/slots against in-game sources.
- [ ] Calibrate one Rogue and one resource-limited caster encounter before any real-DPS claims.

**Next action:** collect exact current-patch mount/CG offhand/runic shield, rotation and resource-regen observations, add sourced fixtures, then build a small exact oracle versus constraint solver.

### OPT-002 — Dynamic multi-objective simulator and planner UI

**Priority:** P1  
**Status:** ACTIVE  
**Owner:** implementation slice via GitHub candidate; in-game calibration remains unclaimed  
**Source:** `docs/OPTIMIZATION_ARCHITECTURE_2026_10_08.md`.  
**Acceptance:** seeded event-simulation fixtures agree with game observations; search agrees with exhaustive oracle for tiny cases; clear Pareto results with safe, priced gear sources and quality indicators.  
**Implemented slice:** `ch_tables/combat_simulator.py` models deterministic priority-queue events, resource caps, enemy/auto/pet attacks, cast/action occupation, finite potions, swaps, DoT refresh and buff expiry; a planner Choice adapter and paired-seed evaluation are included. `tests/test_combat_simulator.py` has 16 locally passing standard-library regression tests. `data/planner/synthetic_combat_scenario.json` is explicitly NOT real game data. See `docs/COMBAT_SIMULATOR.md`. Full OPT-002 acceptance is still pending.  
**Next action:** collect same-patch real Rogue and resource-limited caster traces to validate action timing/mitigation/mount/skill mechanics; compare predictions on grouped session holdouts before any practical-DPS claims. Then build tiny exact oracle/solver and Pareto comparison.

### OPT-003 — Tooling case-study feedback

**Priority:** P2  
**Status:** ACTIVE  
**Owner:** unclaimed  
**Source:** `fengie/heaven-toolbox` project-training/provenance guidance and October 8 multi-repo user request.  
**Acceptance:** narrow cross-project evidence/case study saved in Toolbox, without copying CH-specific assumptions or adding broad unvalidated mandatory policies.  
**Next action:** run measured end-to-end development throughput/rework benchmark from two actual Toolbox projects and promote only verified wins.
