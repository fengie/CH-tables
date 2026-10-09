# heaven.gg — combined game intelligence hub

> **Migration candidate, not renamed yet.** This branch lives in `fengie/CH-tables`. The final requested repository `fengie/heaven.gg` does not yet exist.

| Game | Repository area | Focus |
|---|---|---|
| **Celtic Heroes** | Existing root `ch_tables/`, `data/`, `docs/`, `tests/` | Class, skill, boss, gear and combat-model research |
| **AION 2** | [`apps/aion2-value-atlas/`](apps/aion2-value-atlas/) | Cosmetics, shop price comparisons, Quna/Mileage, historical patches |

All existing Celtic Heroes files remain in place so its CLI, evidence sets and CI continue to function. The AION 2 app has independent data and tests, and never treats another game's prices/patches as authoritative.

## Repo cutover

1. Complete the exact-head PR tests; do not force-push or bypass review.
2. Rename/create the destination `fengie/heaven.gg` using an authorized GitHub repository management capability. This GitHub connector cannot do that.
3. Reconfigure the repo auto-update policy from `fengie/CH-tables` to the new canonical GitHub identity; confirm GitHub Actions, references, CLI entrypoints, and runbooks.
4. Publish any website ONLY from verified GitHub `main`, with provenance and post-deployment acceptance. Do not independently deploy through AppDeploy.
5. Preserve original CH Git history; original AION source ancestry is `b9d5b70` (locally supplied, cannot be grafted using the current GitHub connector). Do not delete the original repositories without explicit authorization.

Research/financial uncertainty remains explicitly dated and sourced. No recurring agents created.
