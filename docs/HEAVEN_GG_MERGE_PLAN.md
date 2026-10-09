# heaven.gg consolidation decision and handoff

Date: October 9, 2026 · America/New_York

## Source state
- CH repository: `fengie/CH-tables`, exact starting SHA `9d03cb3c58be38eec43cb21ea374d00615713fdf`, public; many active datasets, tests, local CLI and auto-update policy.
- AION 2: October 9 self-contained source `b9d5b70` originally created in ChatGPT and staged in `fengie/heaven-toolbox` branch `handoff/aion2-value-atlas-20261009` (exact staged SHA `2a714040`); canonical product repo had never been created.
- User's desired new canonical name: `fengie/heaven.gg` (does not currently exist).

## Architecture choice
Use additive independent app in `apps/aion2-value-atlas` and preserve CH root and git history. Alternative of moving entire CH root into `games/celtic-heroes` rejected for now because it breaks command paths, asset sources and existing CI/auto-update; can migrate in a separately tested PR after rename.

## Trust limits / user priorities
No credentials or private game data; CH is a public repo; imported AION source is publicly sourced shop prices, community links and research. Third-party game assets not sublicensed. The AION data is an incomplete time-stamped Global US shop snapshot, not guaranteed current; no speculative double-counting of mileage. Fashion and long-term play rank ahead of raw power. The previous independent AppDeploy preview is historical/unapproved and **must not** count as GitHub-backed deploy.

## Tests and operational acceptance
Root Python tests discover `tests/test_aion2_atlas_integration.py` which runs nested AION 2 tests with correct working directory; those test data source FKs, integer-cents normalization, budget optimizer accounting, and final JavaScript syntax (requires Node). Existing CH tests and update policy remain mandatory. Confirm built HTML matches deterministic Python build and exact remote tree post-merge; then rename destination with supported authenticated repository tooling and update policy to match exact `github.repository`.

## Known blocker and concrete next action
GitHub connector has no repo creation/rename capability and local shell has no network credentials. This PR is therefore *merger of projects in source*, not completion of repository rename, remote Git history graft, or GitHub-backed website deployment. When authorized repo management becomes available, execute rename/create, update origin/policy/workflows with CI and verify authoritative `main`.

No deletion, force-push, security gate relaxation, AppDeploy or scheduled agents.
