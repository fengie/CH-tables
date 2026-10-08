# Combat observations and held-out validation (v1)

**Status:** executable validation harness, **no current-patch in-game validation**.
This is a continuation of [COMBAT_SIMULATOR.md](COMBAT_SIMULATOR.md), not a
new claim that modeled rotations predict Celtic Heroes damage correctly.

## One scoped workflow

1. Record the *exact* class/build, boss, game patch, equipment/skill policy,
   potion choices, mount state, scenario horizon, and client conditions.
   Preserve the original observations locally. Never upload accounts, private
   messages, usernames, player IDs, or unauthorized client/server captures.
2. Create a `combat_simulator` JSON scenario with post-mitigation attack
   damage, hit/crit rates, timing and other measured inputs. Pin its canonical
   SHA-256 **before** collecting independent holdout sessions. This version
   cannot prove when the pin was created; use a dated external evidence record
   to substantiate chronology, if needed.
3. Record independent full fight windows. `duration_s` is **the prechosen
   horizon**, `elapsed_s` is time until death/kill or full window, and
   `total_damage` is total damage done by that time (zero afterward).
   Count **actual** health/energy potions used. Source each session by a
   SHA-256 of the original locally retained log/recording. Split by recording
   *session*, not individual attack row; never reuse a recording in two splits.
4. Mark training/calibration sessions `calibration` and untouched sessions
   `holdout`. The v1 evaluator **does not fit** model parameters: `calibration`
   sessions are explicitly excluded. The input model must be frozen from
   independent training/evidence before reading holdouts. A label or hash is
   not an independently verified claim that this happened.
5. Compare held-out **fixed-window DPS** (damage/T), survival, boss-kill
   fractions, and potion counts against the distribution from seeded event
   simulations. The 5–95% simulated band describes *model variability* only;
   it is **not** a confidence interval for the real game nor evidence of
   correctness. Bias/MAE should guide later mechanic investigation.

Runs are only comparable when patch, boss, loadout, character, world and action
policy are held fixed. These are identified in the bundle and locked scenario,
not inferred by magic from source files. Inconsistent, stale or missing context
must be rejected upstream. Survival risk and expected time-to-kill are not
interchangeable with conditional DPS among only successful kills.

## Reproducible synthetic CLI smoke test

```bash
python -m ch_tables.combat_validation \
  --scenario data/planner/synthetic_validation_scenario.json \
  --observations data/planner/synthetic_validation_observations.json \
  --seeds 64
python -m unittest discover -s tests -v
```

Both example files are explicitly **toy values** and contain no real player
logs. Expected status is `synthetic_regression_only`. The observation JSON
contract has `schema_version=1`, `evidence_kind=synthetic|recorded_gameplay`,
nonempty `patch_id`, `boss_id` and anonymous `build_id`, the canonical
`scenario_sha256`, identical `frozen_model_sha256`, and `sessions` entries with
`session_id`, `recording_sha256`, `split`, `duration_s`, `elapsed_s`,
`total_damage`, `end_reason`, `hp_potions`, `energy_potions`.

Gameplay mode requires `combat_simulator.Encounter.evidence=observed` and a
source URL for its scenario inputs; this is a **source-presence gate**, not
verification that the measurements or game mechanics are correct. The locally
retained recordings are not ingested or republished. No implicit inference of
missing skill rank curves, hit/crit behavior, current mount mechanics,
attack-speed caps, armour, movement or lag occurs.

**Next scientific blocker:** Obtain independent same-patch Rogue and
energy-starved caster encounter recordings with accurate timing, enough
sessions for meaningful holdout coverage, and explicit source verification;
refine mechanic parameters on calibration sessions **without viewing holdouts**,
then execute this harness. Before calling a model reliable, also compare
ability-level traces (casts, interruptions, autos and DoTs) and evaluate
uncertainty across players and conditions. A perfect toy result is not game
validation.
