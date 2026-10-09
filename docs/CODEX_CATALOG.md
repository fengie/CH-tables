# Codex complete public Saved Builds catalog — 2026-10-08 snapshot

**Scope achieved:** all **327** entries visible across four pages (100/100/100/27) in [Codex Saved Builds](https://the-codex.ch/builds) were captured through its ordinary read-only browser controls, not by using internal APIs. **306 damage-type builds** (300 with numeric DPS and six unscored `N/A DPS` entries) and **21 tanks**. Unique detail URLs, class, level, type, calculator benchmark, short description and date are preserved with the source URL and complete pagination record.

The pinned factual snapshot is \`data/reference/codex_published_build_catalog.json\`. The complete raw CSV is \`data/raw/codex_builds_latest.csv\`. The level-220+ model-relative subset remains in \`data/normalized/builds_normalized.csv\`, and class statistics in \`data/normalized/class_summary.csv\`. Note: the filtered normalized CSV is **not** the full catalog; tanks and lower levels remain available in raw/SQLite.

Run offline, including the existing **122 skill-panel observations** collected separately from **12** Codex build pages:

\`\`\`bash
python -m ch_tables.codex_catalog
python -m unittest discover -s tests -v
\`\`\`

This produces \`data/normalized/codex_catalog.sqlite\` with indexed \`codex_builds\`, \`codex_skill_panels\`, and \`import_meta\` tables, plus a SHA-256 generation manifest. Original Codex build URLs remain source IDs; skill panels not in the public listing remain available as unlisted records, never mis-joined to another build. The transaction stages CSV, SQLite and manifest and commits the manifest last, with rollback on publication errors.

**Do not run the legacy \`python -m ch_tables.scrape\` as an all-build refresher.** The site paginates; the legacy single-page fetch now fails closed when a source explicitly announces more entries than it renders. Update the pinned snapshot by the same visible, verified pagination protocol before publishing another generation. Never manufacture missing pages or silently shrink a complete catalog.

**Not complete yet:** this snapshot covers saved-build *listing metadata*, not complete gear inventories, exact skill ranks, every detail page, boss/damage formulas, privately stored builds, leaderboards, or all of the publisher's underlying assets. Only 12 independent detail-page skill snapshots have been indexed; no full-game DPS error guarantee follows from Codex's modeled numbers. Fetch future detailed pages with cautious site-respecting access, permission where redistribution is unclear, source identity, versioning and completeness checks. Avoid bulk copying copyrighted page HTML, user identities beyond display names, or inaccessible/private data.

## Expanding detailed skill-panel coverage

A separate incremental tool, \`ch_tables.codex_detail_refresh\`, uses only the
pinned public catalog as its URL allowlist, prioritizes class diversity, and
skips detail pages already represented in the \`codex_skill_panel_observations.json\`
source archive. By default it visits **at most 12 new public damage-build pages**
with a **minimum 1-second delay** (default 1.5 seconds), validates and merges
all original observations, and atomically replaces the snapshot only if valid new
skill panels were found:

\`\`\`bash
python -m ch_tables.codex_detail_refresh --limit 12 --delay 1.5
python -m ch_tables.codex_catalog
\`\`\`

Any 429 ends the batch without an automatic retry; malformed or empty detail
pages are logged as failures rather than fabricated values. No blind wholesale
network sweep, login, client attachment or raw page HTML redistribution. This
is a local, on-demand refresh, **not** proof that 306 published damage-build
detail pages were actually ingested. Tank details require a separate domain-
specific parser; the skill parser does not misclassify tank profiles as damage.

