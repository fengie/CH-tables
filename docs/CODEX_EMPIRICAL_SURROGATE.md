# Codex empirical calibration — what 5% can and cannot mean

**Scope:** Codex *model-to-model* empirical prior. **Not** current-patch in-game DPS calibration, a gear-optimizer stat law, a validated boss-mitigation model, or a source of skill rank curves.

## Reproducible experiment (2026-10-08 snapshot)

Input: [`data/reference/codex_skill_panel_observations.json`](../data/reference/codex_skill_panel_observations.json), from 12 independently saved Codex builds (122 skill observations, including five explicit 0/0 utility/healing panels excluded from ratio training; 117 containing both positive `Max Damage` and `Avg Damage`). The original source URLs and response hashes are embedded in the snapshot. Source: [The Codex damage builder](https://the-codex.ch/damagebuilder). Its results are community **modeled** values, not independent player hit logs. Do not represent this evidence as observed game mechanics.

We make one deliberately narrow prediction: **Given a skill name and its reported Codex Max Damage, predict its Codex Avg Damage**. For each held-out *entire build*, take the median `Avg Damage / Max Damage` ratio for that skill from **other** builds. If the skill was never observed elsewhere, use the global training-only median. The medians are robust against outliers, require no arbitrary hyperparameter search and cannot leak rows from a held-out build. Every inference reports the number of other-build skill examples; unsupported skills use a low-confidence global prior.

### Retrospective leave-one-build-out result

| Estimator / diagnostic | N | Mean absolute percentage error |
| --- | ---: | ---: |
| Global Max→Avg ratio | 117 | 5.12% |
| Skill-specific median with global fallback | 117 | **4.03%** |
| Naively transferring a skill's *Max Damage* from a different build | 88 | **57.25%** |

These figures use the 12 *already available* source builds. They are preliminary retrospective error estimates, **not an unseen prospective test**. Even the skill-aware estimator is within 5% for only about **59%** of individual skill rows; the 4.03% figure is an **average**, not a pointwise guarantee. In addition, `Avg Damage` and `Max Damage` are **both outputs of the same Codex calculator**, so apparent precision partly recovers its internal damage-range convention, not the true game engine.

Importantly, simply estimating Codex `Avg Damage` once `Max Damage` is known **does not solve** the user's core problem of predicting the effect of unseen gear, skill ranks, shields, DoTs, buffs, mounts or rotation uptime. The poor 57% raw-Max transfer result shows why training only on build identifiers and one skill would be misleading. An actual new-build optimizer additionally needs measured or source-derived stat/rank curves, active equipment and source-consistent encounter mitigation, then an independent held-out **total practical DPS** test. Do not extrapolate beyond available stats/versions or use these ratios as true probabilities.

## Run without network

```bash
python -m ch_tables.codex_surrogate --input data/reference/codex_skill_panel_observations.json --output data/planner/codex_panel_surrogate_report.json
python -m unittest tests.test_codex_surrogate -v
```

The report binds to the SHA-256 of canonical JSON input and carries full per-build grouped errors, a global baseline and the intentionally difficult Max Damage transfer diagnostic. If the dataset or scraper schema drifts, the parser fails closed. No fitted game stats are silently shipped as live-DPS truth.

## Scientific next step

Enlarge the number of independent public, consented or appropriately licensed build snapshots **by source and version**, not by duplicating correlated skill rows. Fit and compare a hierarchical, regularized stat- and rank-aware model against small mechanistic candidates using **nested grouped validation**, reserving newly collected builds for a prospective test. The final output must report error for both per-skill damage and full encounter practical DPS by class/boss/equipment family. Pre-register the 5% target; do not tune on the evaluation holdouts. A simple robust model that validates is preferable to XGBoost or a neural net that memorizes gear combinations.

Sources: [Codex](https://the-codex.ch/builds), [scikit-learn grouped cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html), and existing project [scaling research](SCALING_RESEARCH.md).
