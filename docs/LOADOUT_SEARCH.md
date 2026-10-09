# Interaction-aware exact equipment search (uncalibrated)

This module is an **exact optimizer for explicitly encoded numbers and conditions**, not a verified Celtic Heroes build or combat formula. It addresses the small-case constraint/oracle milestone of OPT-002. It is an optional downstream tool after `loadout_foundation.py` eligibility and the combat scenario's measured/calibrated inputs exist.

## Contracts

`SearchSpec` requires one `metric_basis` (character, patch, target, stat conventions and scenario), a class/level context, an explicit list of required equipment slots, and six finite nonnegative objective weights corresponding to the six metrics in `loadout_foundation.METRICS`. Each item is used in exactly one slot. Offhands and shields compete for one canonical `offhand` slot. An item without eligible class/release documentation (or explicit owned override), matching measurement basis, known acquisition price (if unowned), or known effects is **excluded** from default scored recommendations. Research can opt into unknown effects, but results are flagged as incomplete evidence and are still not game-validated.

All selected items must be within the same measurement basis. Unverified mount in-combat bonus persistence is prohibited by `permitted`; **mount + mainhand/offhand/pet is also prohibited unless the caller supplies an explicit affirmative compatibility verification** (`mount_combinations_verified=True`). Game patch and conflict-specific exclusions should use `incompatible_pairs` when independently evidenced. Unknown mount mechanics cannot be treated as positive combat value.

`Interaction` expresses *verified, scenario-specific* effects triggered by exact item IDs and/or set-family piece-count thresholds. Both positive and negative six-dimensional adjustments are supported. If a conditional effect's value is unknown, do not guess it or represent it as an empty rule. The optimizer reports `skill_bonus_levels` but **does not convert them to damage or healing** without a calibrated rank curve; the existing `build_planner` remains authoritative for rank allocation.

## Algorithms and proof

- `optimize_loadouts(spec, top_k)` uses a deterministic, bounded branch-and-bound search. The upper bound is the highest achievable remaining independent-slot weighted score plus **all positive conditional interaction rewards**, even those that may not activate. This deliberate overestimation guarantees *no false optimality pruning* when effects are negative, conditional, or both. Cheap minimum remaining acquisition cost gives an additional safe branch cutoff.
- `exhaustive_oracle(spec, top_k)` separately enumerates tiny feasible product spaces. The two paths must agree on exact score, item selection and tie order before a solver change is trusted.
- Every node has a budget. If the maximum is reached, `certified_exact=false` and its winners are explicitly **unproven partial candidates**. A complete enumeration with no winner means no eligible loadout under the modeled constraints.
- `optimize_loadouts()` still gives the top-K of a **weighted additive research proxy**. `pareto_loadouts()` now returns the unweighted nondominated set across all six supplied metric dimensions (maximize) and acquisition gold (minimize). It never reports this as empirical DPS. Both share eligibility, interaction, pricing, and compatibility gates. The weights affect scalar-search ranking and Pareto's traversal order only, not Pareto membership. Calibrated event-simulation outcomes remain a future dependency.

## Example API

```python
from ch_tables.loadout_foundation import BuildContext, EquipmentCandidate
from ch_tables.loadout_search import SearchSpec, optimize_loadouts

# Real use requires documented eligible item entries with all six scenario-
# consistent metrics. This illustrative snippet is intentionally synthetic.
head = EquipmentCandidate(
    'synthetic-helm', 'head', 'armor', (10, 20, 0, 0, 0, 0),
    cost_gold=0, class_scope='all', metric_basis='toy-scenario',
    unknown_effects=False, released_documented=True)
problem = SearchSpec(
    (head,), BuildContext('rogue', 220), ('head',),
    'toy-scenario', (1, 0.2, 0, 0, 0, 0), budget_gold=0)
result = optimize_loadouts(problem)
assert result.certified_exact
print(result.as_dict())
```

Run `python -m unittest tests/test_loadout_search.py -v`. The regression suite includes seeded randomized exact-oracle comparisons, negative interaction bonuses, set thresholds, skill-point bonus preservation, defensive offhand vs damage offhand, resource profiles, class/release/budget/basis filtering, mount combat compatibility, and search-exhaustion honesty.

## Still required for practical BIS

1. Independent same-patch in-game Rogue/caster observations and calibration of `combat_simulator.py` mechanics via `combat_validation.py`.
2. Proof of real slot, mount/pet, set, proc, consumable and swap behavior for every candidate; no source-only developmental gear in recommendations.
3. Use the event-simulation engine as a true nonlinear complete-build evaluator (e.g. rank breakpoints, survivability, pets, consumables), then benchmark an admissible bound or an explicitly heuristic alternative, marking missing optimality certificates honestly.
4. Extend the **already implemented exact additive-metric Pareto engine** to calibrated nonlinear encounter outputs (survival, actual DPS, consumables, micromanagement and robustness), including a correctness oracle for the enriched evaluator.

No proprietary game-client access, packet capture, account credentials, fabricated prices, or copyrighted asset redistribution is performed here.

## Pareto frontier (complete when certified)

`ch_tables.loadout_pareto.pareto_loadouts(spec, max_frontier=2000)`
returns the nondominated, affordable loadouts under **seven objectives**:
six modeled scenario metrics maximized (`damage_proxy`, HP, energy, HP regen,
energy regen, incoming-DPS reduction) and acquisition cost minimized.
It is deliberately independent of arbitrary weights, so a shield or
energy-restoring bracelet is not dropped simply because a DPS-only profile
would rank a different offhand first.

```python
from ch_tables.loadout_pareto import pareto_loadouts
frontier = pareto_loadouts(problem, max_frontier=2000)
if not frontier.certified_exact:
    raise RuntimeError("Incomplete Pareto search: " + str(frontier.stop_reason))
for candidate in frontier.frontier:
    print(candidate.item_ids, candidate.metrics, candidate.gold_cost)
```

The search enumerates one eligible item per required slot while checking
proven mount combinations, item incompatibilities, release/class limits,
exact source/metric basis, gold budget, full set thresholds and both
positive and negative conditional adjustments. It prunes a subtree **only
when a feasible incumbent dominates the most optimistic metric vector of
that subtree at its lowest possible gold cost**. Bounds include the positive
component of every conditional interaction, including effects that might not
activate, and are conservatively widened for floating-point rounding.

Tied seven-objective vectors use a deterministic item-ID representative.
A maximum node or frontier cap yields `certified_exact=false` plus
`stop_reason=node_limit|frontier_limit`; a partial list is **never** a
certified full frontier. There is no promise that arbitrary large catalogs
have compact fronts. `exhaustive_pareto_oracle` and separately coded
unpruned tiny-case regression fixtures check correctness, including 170
randomized interaction/cost cases; an additional 500 deterministic adversarial
cases were checked in local research. In a dominated synthetic 12-slot,
40-items/slot benchmark, the bound closed 481 search nodes; this is a
toy algorithm check, not game-data scalability evidence.

Run `python -m unittest tests/test_loadout_pareto.py -v`.

**Scientific boundary:** damage is still `damage_proxy`, not practical
event-simulated DPS; survival, potion burden, swap inputs, mobility, unknown
proc mechanics and market price uncertainties need measured model
coefficients before cross-objective game recommendations can be trusted.
