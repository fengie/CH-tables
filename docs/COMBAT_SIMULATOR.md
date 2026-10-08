# Discrete-event combat simulator — uncalibrated vertical slice

This is **not** a verified Celtic Heroes combat formula or "real DPS" calculator.
It is the next validation substrate after `fight_screening.py` (optimistic
resource bounds) and `build_planner.py` (additive skill-choice screening).
Its only claims concern deterministic behavior under **explicit input mechanics**.
No proprietary client extraction, server automation or login is required.

## Run

```bash
python -m ch_tables.combat_simulator --scenario data/planner/synthetic_combat_scenario.json --seed 12
python -m ch_tables.combat_simulator --scenario data/planner/synthetic_combat_scenario.json --trace-limit 30
python -m unittest tests/test_combat_simulator.py -v
```

The supplied scenario is **synthetic**; its DPS is useful for testing the
algorithm, **not** recommended game gear. `encounter_from_dict` constructs an
`Encounter` from JSON without code execution; rejecting unknown fields and
invalid numeric inputs. Mark future measured scenarios as `observed` with an
HTTPS provenance URL. Merely setting that label is not calibration proof.

## Explicit mechanics

- A stable priority event heap schedules player auto attacks, enemy attacks,
  independent pet attacks, casts, cooldown readiness, DoT ticks, effect expiry,
  potions and resource regeneration. No implicit attack-speed/armour formula.
- Casts, equipped item swaps and potion actions occupy the same player's
  action lock; autos due while busy restart one full attack interval after
  the lock. Cooldowns begin at cast start. These are assumptions, **not**
  established Celtic Heroes rules.
- Each damage number is already **post-mitigation** at the specified target;
  accuracy and crit probabilities are separately supplied. Multiplicative
  effect stacking and same-skill DoT replacement are configurable future
  calibration boundaries, not evidence of actual stacking behavior.
- Swapped skill rank/damage must be supplied from observed rank records;
  `from_build_choices()` maps existing `build_planner.Choice` data without
  inventing unobserved ranks or granting a free skill-level boost. Planner
  eligibility checking must run **before** this converter. This is an
  in-memory adapter, not a finished combined optimizer.
- HP and energy stay bounded; finite potion charges/costs and busy time are
  counted. Verified in-combat mount HP/energy can apply; unverified bonuses
  are rejected instead of silently added. Pet attack cadence/damage requires
  independent supplied measurements.
- Source-specific seeded RNG streams keep enemy variance aligned across
  candidate comparisons even when skill schedules differ. `compare_candidates`
  runs identical seeds and returns per-seed DPS, survival and gold/effort;
  it does **not** manufacture confidence intervals from synthetic samples.
- `fixed_window_dps = damage_by_T / T` is comparable across builds even if
  a player dies. `active_time_dps` is separately shown for descriptive use,
  and boss damage is capped at target HP. For real kill-time optimization,
  report kill probability and time-to-kill with censoring; do not rank solely
  by conditional DPS among victories.

## Required next validation before practical DPS recommendations

1. Collect independently recorded **same-patch** auto attack cadence,
   cast/lockout, swap delay, damage-per-rank, enemy damage, mitigation,
   hit/crit, regen and potion logs for a Rogue boss encounter.
2. Do the same for a resource-starved caster and a shield/offhand/mount
   scenario. Explicitly verify in-combat mount persistence and whether
   mounted combat excludes weapons, pets or skills before enabling it.
3. Preserve encounter/session as a grouped holdout, measure damage/time,
   potion counts, deaths and cast/auto interruption; compare measured logs
   against simulator event traces. Tune model semantics to observed timing,
   not just one headline DPS number.
4. Only then integrate this evaluator into a tiny exhaustive equipment/skill
   oracle and compare a constraint solver against it. Retain uncertainty
   and labeled unknown effects rather than assigning them invented values.

The engine deliberately does not yet model movement, aggro/party behavior,
conditional proc scripts, pet active skills, true armour resistance or
attack-speed elixir caps, mount equipment exclusions, cooldown-group sharing,
server latency, automatic resurrection or gold/hour for unverified items.
These remain explicit gaps, not hidden zero-cost assumptions.


## Held-out evidence comparison

The adjacent [combat validation harness](COMBAT_VALIDATION.md) now accepts
SHA-identified independent fight sessions and an exact frozen scenario, and
compares fixed-window DPS, potion consumption, death and kill outcomes against
seeded predictions. It deliberately never fits parameters on holdout sessions
or claims that synthetic fixtures establish real-world game accuracy.
