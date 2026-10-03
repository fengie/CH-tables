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

**Status:** ACTIVE  
**Owner:** issue #2 / branch `issue-2-reproducible-pipeline`  
**Source:** issue #2; current Codex Saved Builds schema; branch implementation  
**Goal:** make live scraped analysis inputs reproducible, schema-drift safe, validate-before-publish, and bounded in retained source evidence.

- [x] Select the Saved Builds table by semantic headers instead of first-table position.
- [x] Fail closed on missing/duplicate/malformed required columns or rows.
- [x] Retain content-addressed source HTML with bounded snapshot retention.
- [x] Stage raw/normalized/summary outputs and publish only after validation.
- [x] Emit a machine-readable manifest with source/output hashes, row counts, parser version, filters, and calibration sources.
- [x] Add regressions for unrelated leading tables, schema drift, failure preservation, and successful manifest publication.
- [ ] Run exact candidate CI/tests.
- [ ] Merge verified candidate to canonical `main`, verify remote main, and close issue #2.

**Execution-path note:** the current ChatGPT session exposes the canonical Toolbox skills and authenticated GitHub mutation surface but no callable Heaven/Agent Control local-runtime namespace, so the mandatory local offload lane could not be exercised. Exact candidate GitHub CI is the mechanical verification path.

**Next action:** open the implementation PR, require exact-head tests/CI, then integrate only the verified candidate and update this item to DONE.
