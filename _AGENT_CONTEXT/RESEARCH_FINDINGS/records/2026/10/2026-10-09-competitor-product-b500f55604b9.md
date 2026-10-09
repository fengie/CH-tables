---
schema: heaven-research-finding-v1
id: kf-b500f55604b9
status: verified
observed_at: 2026-10-09T22:00:00Z
updated_at: 2026-10-09T22:00:00Z
topic: competitor-game-guides-collectors-and-build-tools
claim: context-explained-build-guides-personal-comparison-wardrobe-cost-ledger-and-historical-evidence-have-higher-near-term-value-than-generic-tiers
scope: fengie/Heaven.gg
fingerprint: b500f55604b97504eb34c2b6e9aee7999317cf30
confidence: high
source_revision: 912fd09f6fc2f79aba5a3070935e2344e1c69077
task_id: chat-2026-10-09-heaven-gg-competitor-research
agent_id: chatgpt-gpt-6
evidence_refs: ["https://www.prydwen.gg/zenless/characters/seed","https://blog.prydwen.gg/2024/01/11/honkai-star-rail-tier-list-revamp/","https://blog.prydwen.gg/2023/05/04/our-first-post-release-tier-list-update/","https://compendium.keqingmains.com/","https://keqingmains.com/2024/","https://github.com/fribbels/hsr-optimizer/blob/main/docs/guides/en/optimizer.md","https://poe.ninja/posts/dawn-of-the-hunt","https://poe.ninja/posts/defensive-stat-breakdowns","https://paimon.moe/","https://www.reddit.com/r/HonkaiStarRail/comments/1uif96d/prydwen_slander/","https://www.reddit.com/r/pathofexile2builds/comments/1q6njra/poeninja_is_a_good_tool_but_please_dont_blindly/","https://www.reddit.com/r/Aion2/comments/1wyuhx2/paying_for_dyes_sucks_but_at_least_they_give_out/","https://www.reddit.com/r/Aion2/comments/1x1mx0y/alts_are_100_necessary_for_one_reason/","https://www.reddit.com/r/Aion2/comments/1x044hm/reminder_to_always_check_out_the_black_cloud/","https://lounge.plaync.com/feed/83451?country=US&locale=en-US"]
---

# Heaven.gg — competitor reconnaissance and product gap analysis

**Research date:** October 9, 2026 (America/New_York). **Evidence type:** direct official/first-party competitor pages, competitor engineering guides, publisher notice and explicitly labeled Reddit discussion; no private data, live game capture, large-scale scraping, or claims about competitor traffic/revenue. **GitHub baseline:** fengie/Heaven.gg main at 912fd09f6fc2f79aba5a3070935e2344e1c69077. Source observed: web/index.html, web/site.js, web/build.mjs, data/reference/codex_published_build_catalog.json, data/catalog/priority_gear_lookup.json, apps/aion2-value-atlas/data/catalog.json and existing docs/OPTIMIZATION_ARCHITECTURE_2026_10_08.md. Review before implementing: intervening commits may change state.

## Prior-work boundary

Existing CH architecture, scaling and AION economics research remain authoritative on algorithms and game facts; this audit covers missing user workflows, comparison UX and competitor evidence.

## Direct observations about competing products

| Product | Observed product behavior | Lesson for Heaven.gg | Limitation of observation |
|---|---|---|---|
| **Prydwen.gg** | Named character guides split Kit / Review / Build / teams-synergy / calculations, expose separate "last review," "last build," "last teams" patch metadata (Seed page); explain content-/patch-specific combat assumptions and team-buffed vs solo values. Their HSR tier methodology explicitly discloses equipment, rank, level and team assumptions; 2023 post-release corrections stress that simulations are not actual gameplay testing. | Create readable **guide first, deep calculations on demand**; version each evidence facet independently; compare only equal scenarios and mark model assumptions near numbers. | Example is ZZZ/HSR, not proven optimal for CH or AION. |
| **KeqingMains theorycrafting/KQM Compendium** | Calculation Standard (KQMS v2.0.2) standardizes gear distributions, rotation/enemy assumptions and contexts so different theoretical results are comparable; Quick Guides, infographics and patch changelogs complement extensive guides. | **Public benchmark fixtures** and abbreviated player-friendly guide cards alongside full reproducible derivation. | Genshin standards must **not** be copied as CH mechanics. |
| **Fribbels HSR Optimizer** | Optimizes a player's actual inventory; documentation describes several import routes and their measurement/coverage accuracy limitations, then a character preset workflow; open-source rel/scorer. | Own/available gear, resource caps and practical constraints beat universal BIS ranking. Default to **manual local JSON entry/import**, *no account credential requirement*. Explicitly label optional importer coverage/error. | Import/scanners may be inaccessible or violate another publisher's restrictions; no implied permission to clone functionality/data. |
| **poe.ninja** | Public build sampling with filterable distributions, optional OAuth character listing, daily/weekly "Time Machine" snapshots and explanation of where defensive stats arise from (equipment/passives). | Version-aware snapshots and "**why this stat?**" drilldown; compare *popular builds* separately from *proven optimal*. Never request OAuth unless needed/authorized. | High-rank/player sample is highly selective. A stat breakdown for PoE cannot be treated as CH's true engine formula. |
| **Paimon.moe** | Wish history/progress/todo/ascension planner and aggregate wish stats; an ongoing collection-oriented workflow distinct from meta tier rankings. | AION fashion collectors need **Owned / Wanted / Obtainable / Expired**, repeat purchases, dye cost and acquisition checklist; research snapshot already supplies seed data. | Wish import and statistical aggregation depend on game APIs and self-selected submissions; not AION drop odds. |
| **Maxroll / warframe.market** | Both are often suggested as further research targets, but direct first-party inspection was blocked/unconfirmed in this session. | **Deferred**. Revisit only after verifying exact first-party features and reuse conditions. | Do not fabricate a competitive comparison from search snippets or user hearsay. |

## Player-community counter-evidence (NOT population-level research)

- [HSR community, June 2026](https://www.reddit.com/r/HonkaiStarRail/comments/1uif96d/prydwen_slander/): solo tier placement can hide team synergy; anecdote, not measured fault.
- [PoE2 community, January 2026](https://www.reddit.com/r/pathofexile2builds/comments/1q6njra/poeninja_is_a_good_tool_but_please_dont_blindly/): ladder builds may need unaffordable gear; popularity does not prove replicability.
- [AION dye discussion](https://www.reddit.com/r/Aion2/comments/1wyuhx2/paying_for_dyes_sucks_but_at_least_they_give_out/): fashion value includes repeated dyes and partial set costs; official verification needed.
- [AION merchant](https://www.reddit.com/r/Aion2/comments/1x044hm/reminder_to_always_check_out_the_black_cloud/) + [alt rolls](https://www.reddit.com/r/Aion2/comments/1x1mx0y/alts_are_100_necessary_for_one_reason/): merchant offers are variable, not predictable.
- [NCSOFT October 7 patch](https://lounge.plaync.com/feed/83451?country=US&locale=en-US): Founder's cosmetic sharing changed; effective-date and account scope matter.

## Product gap versus current Heaven.gg

- **Current:** CH portal shows 327 public Codex builds and raw modeled DPS, gear status, boss record snapshots. AION iframe provides sourced pack optimizer, limited shop catalog and adjustable subjectively weighted ranking. Data physically lives in GitHub; release is GitHub Pages pending owner activation at issue #6.
- **Gap:** No first-class character *guide* or rotation caveat card; no owned-vs-obtainable gear input; no encounter-matched scenario comparator; no side-by-side attribution of WHY a stat is higher; no per-facet patch/review timestamps; no AION wardrobe/wishlist/dye total-cost tracker; no longitudinal delta timeline. **Do not confuse missing UI with missing simulation code**: many CH search/validation modules already exist but are not surfaced.
- **Competing design options:** (A) monolithic account-connected multi-game recommender: high permissions, stale API risk, maintenance cost; (B) source-linked, offline-first per-game features with optional user-provided imports and versioned comparisons: low trust surface, respects current static host, incremental and testable. **Choose B** until measured user need justifies auth/server/cloud sync.

## Prioritized experiments, not automatic implementation authorization

| Rank | Item and why | Minimum independently testable slice | Benefit / effort / pitfalls |
|---|---|---|---|
| **P0** | **Trust & context badges:** build version, modeled vs measured, source, scenario/party, item availability; player can see *why* a rank appears. | Render labeled numeric proof cards + "not comparable" state when scenarios differ; browser accessibility and negative fixtures. | High / small. Make terminology consistent and avoid badge overload. |
| **P1** | **CH battle/build guide cards:** beginner and advanced tabs, encounter role, strengths/weaknesses, requirements and caveats. | 1 sourced Rogue guide + 1 non-Rogue guide, with independent review and changelog. | High / medium. Do not invent BIS or carry game-specific assumptions across classes. |
| **P1** | **Own/afford/loadout comparison:** filter 327 indexed builds against known owned slots, constraints, budget and world; show why alternatives lose. | Manual inventory JSON + source-locked scenario, feasible alternatives and Pareto table; compare tiny oracle to exact solver. | High / medium-high. Release/ownership/gear effects may be unknown. |
| **P1** | **AION wardrobe & full-spend planner:** wishlist, acquisition channel, bind scope, season expiry, membership, dye/re-dye, earnable alternatives and total wallet spend. | 5 exact sourced outfits, one pass, one merchant example (unconfirmed flagged); deterministic budget tests, tie handling and future-date filter. | High for fashion-first user / medium. Probabilities and rotating merchant stock are not known. |
| **P1** | **Patch/time-machine comparison:** review changes and methods separately; historical price/gear sources preserved. | Compare two documented dated snapshots with common item IDs; no stale cross-patch rankings. | High long-term / medium. No unsupported automated scraping. |
| **P2** | **Stat "why" breakdown + share links:** explain source item, set bonus, conditional effects and interval of model uncertainty; share JSON snapshot without private details. | Two-item effect decomposition against static input fixtures. | Medium / medium. True mechanics require game calibration. |
| **Defer** | General AI-generated guide writer, automated login/import, universal tier list, global market price scraper, full artwork mirror, aggressive frontend rewrite. | Re-evaluate after representative real-user tests/rights review. | High opportunity/security/rights costs; little proven incremental value. |

## Measurable acceptance and release gates

1. Novice selects game/class/role and explains source/assumptions without mistaking model DPS for measured results. Test directionally with 5+ participants.
2. CH "best" fails closed when gear or mechanics are unknown or scenarios mismatch.
3. AION plan includes owned looks, alternatives, re-dyes, binding and expiration; no automatic purchases.
4. Each answer links source/date/patch/method. Tests distinguish historical snapshots.
5. Keyboard/mobile navigation and AION controls are usable; benchmark speed before adding frameworks.

## Maintenance/knowledge disposition

**Stored as one competitor finding**; unique claims are user-flow/product evidence, not existing CH combat research. Keep original official and public links; no raw HTML/copyright media/reddit archive. Research next only if it changes a decision, especially official AION ownership/merchant terms and user testing. No automatic feature, scheduled agent or deployment. Proposed factory outcome: NO_FACTORY_CHANGE_NEEDED (existing pipeline already requires provenance/verification; this is domain research).
