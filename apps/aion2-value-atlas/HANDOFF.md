# Temporary GitHub handoff — Atreia Atlas (2026-10-09)

**Status:** STAGED IN A TOOLBOX BRANCH ONLY; NOT IN TOOLBOX MAIN; NOT A NEW PRODUCT REPO; NOT A GITHUB-DRIVEN DEPLOYMENT.

## Scope and provenance
The user requested a durable GitHub handoff of an AION 2 cosmetic-first spending intelligence dashboard. Product target: `fengie/aion2-value-atlas` (not created yet). This staged copy is a recovery capsule, not an attempt to add an AION product to the Heaven Toolbox runtime. When a product repo is provisioned, extract this handoff to that repo and delete/retire the temporary staging branch after verifying identical code and preserved research.

The bundled project created locally: source commit `b9d5b70f4a7e222a2cecd8a21553da5e1b8cbdd7`, version `0.1.0`. Full original Git bundle SHA256: `052183c749d66f2bb0aea56d07fc83f34afa070da849a9552f164053b1644ad1`; full original ZIP SHA256: `28c689ae9be9f37f9ab05431d75ead00d7af8b3307cc6fc1422c67e901396546`. The originals were delivered as conversation attachments (not retrievable through the GitHub remote). `index.html` here is the runnable self-contained dashboard; HTML, supporting README, release notes, and continuity/deployment receipts are preserved on this GitHub branch.

## Functionality
Offline, no-login, single-file UI: configurable fashion/playtime/power weights; search/filter item catalog; exact-cent recharge and Mileage comparison; budget optimizations; Mileage Shop rewards, restrictions; patch timeline; evidence links; JSON export. Model-dependent 'best' scores must not be represented as verified facts. Historical AION shop snapshot as of 2026-10-09; no live in-game scrape or automatic source refresh.

## Local verification actually performed
On exact original source commit `b9d5b70`: `python -m unittest discover -s tests -v` returned six passing tests; `python scripts/build.py` rebuilt; `git diff --exit-code -- index.html` was clean. Tests covered known-source links, normalized 4,000-Quna equivalence, Quna-vs-Mileage winner, avoiding unverified double-credit, cost-constrained optimizer, final embedded JS parse. These tests are in the original ZIP/bundle; this staging branch preserves the generated runnable HTML, but does **not** claim the entire editable Python/JSON project has been transferred.

## Deployment fact, not policy compliance
Preview initially reported AppDeploy status `ready` with no frontend/network errors at https://atreia-atlas-4ko9ii.v2.appdeploy.ai/. This was done before GitHub source-of-truth and **must not** be treated as approved production deployment; user later explicitly mandated GitHub FIRST and no independent AppDeploy builds. Do not touch or redeploy that service during this handoff.

## Next actions (strict order)
1. Provide an authorized GitHub create-repository capability and create **private** `fengie/aion2-value-atlas`. Do not bypass permissions and do not assume repository creation succeeded.
2. Recover original ZIP/Git bundle from owning conversation if available; otherwise recover standalone `index.html` and citations from this branch, then reconstruct structured source and tests. Verify SHA256 on originals rather than taking a handoff claim at face value.
3. Follow `fengie/heaven-toolbox` bootstrap, research provenance, release, protection/admission, Repo AutoUpdate Contract, CI and runtime verification without copying unrelated Toolbox main code.
4. Publish from reviewed GitHub `main` only; prove deployed URL references canonical version/commit, successful tests and rollback/updates, and a mobile/desktop acceptance test.
5. Extend full cash-shop coverage item-by-item from official Global shop data, preserve temporal/region flags and uncertainties; user ranks skins/long-term gameplay above power.
6. Update owning repo with exact integration and deployment evidence. Retire this staging branch **only after** extraction and evidence check.
7. No scheduled or recurring agents; no further use of AppDeploy for this user's projects.

Factory outcome: `FACTORY_IMPROVEMENT_DEFERRED_TO_OWNER` — GitHub provisioning capability and complete code extraction remain external/unverified.
