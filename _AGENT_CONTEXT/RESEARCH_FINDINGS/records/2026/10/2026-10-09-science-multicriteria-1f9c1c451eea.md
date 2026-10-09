---
schema: heaven-research-finding-v1
id: kf-1f9c1c451eea
status: verified
observed_at: 2026-10-09T22:00:00Z
updated_at: 2026-10-09T22:00:00Z
topic: scientific-multiobjective-recommendations-calibration-provenance
claim: explainable-constrained-pareto-selection-with-patch-pinned-evidence-honest-uncertainty-and-empirical-calibration-beats-universal-score
scope: fengie/Heaven.gg
fingerprint: 1f9c1c451eead0ebb16d54e99711e038bf66f78f
confidence: high
source_revision: 912fd09f6fc2f79aba5a3070935e2344e1c69077
task_id: chat-2026-10-09-heaven-gg-scientific-research
agent_id: chatgpt-gpt-6
evidence_refs: ["https://doi.org/10.1007/s10462-020-09851-4","https://pmc.ncbi.nlm.nih.gov/articles/PMC10073543/","https://doi.org/10.1007/s10479-024-05941-6","https://www.sciencedirect.com/science/article/pii/S2193943821000923","https://www.sciencedirect.com/science/article/pii/S0020025521007155","https://doi.org/10.1038/sdata.2016.18","https://www.w3.org/TR/prov-o/","https://www.tandfonline.com/doi/abs/10.1057/jos.2012.20","https://itl.nist.gov/div898/handbook/eda/section3/eda334.htm","https://www.w3.org/WAI/WCAG22/quickref/","https://doi.org/10.1145/3754459","https://research.google/pubs/transparent-scrutable-and-explainable-user-models-for-personalized-recommendation/","https://www.mdpi.com/2078-2489/14/7/401","https://ojs.aaai.org/index.php/ICWSM/article/view/42667","https://compendium.keqingmains.com/"]
---

# Heaven.gg — research-based recommendation and model integrity design

**Research date:** October 9, 2026. **Target:** CH encounter-specific gear/build advice and AION 2 cosmetics/time/budget comparisons. **Source revision checked:** 912fd09f6fc2f79aba5a3070935e2344e1c69077. **Evidence classes:** peer-reviewed method papers, NIST/W3C standards, first-party game/theorycrafting methods. Findings about our game are *engineering implications*, not experimental proof of improved user engagement.

## What the science actually establishes

| Source / strength | Supported principle | Careful Heaven.gg application |
|---|---|---|
| Monti et al., systematic review, *AI Review* (2021), DOI 10.1007/s10462-020-09851-4 | Preference is multi-criteria; reducing judgments to a single rating loses attribute information. | Keep separate cosmetics, playtime, budget, performance, clicks, survivability objectives. Single score optional, never objective truth. |
| Jannach et al., *Frontiers Big Data* (2023) multi-objective recommendation survey | Stakeholders, long/short-term goals and beyond-accuracy metrics can conflict. | Reveal which dimension improved, which worsened, and whether player cares. Distinguish power from fun and convenience. |
| Misitano et al., *Annals OR* (2024) DOI 10.1007/s10479-024-05941-6 | Pareto solutions do not have intrinsic total ordering; iterative user preferences enable tradeoff evaluation. | Compute feasible nondominated options first; ask for optional weights only to choose among them, with a sensitivity plot. No "best" without a scenario and weights. |
| Benabbou & Perny, *EURO J Decision Processes* (2018), DOI 10.1007/s40070-018-0085-4 | Incremental weight elicitation can find strong choices with fewer user questions under mathematical assumptions. | Initial three explicit sliders suffice; later compare two feasible options if preferences remain ambiguous. Avoid complex Bayesian tooling until justified. |
| Shavazipour et al., *Information Sciences* (2021) DOI 10.1016/j.ins.2021.07.025 | Scenario-sensitive heatmaps/visualizations help users inspect multiobjective uncertainty. | Display compact cost–performance/effort matrix; let players switch patch/server/gear scenario; show missing data rather than color-coded pseudo-certainty. |
| Sargent, *Journal of Simulation* (2013), DOI 10.1057/jos.2012.20 | Conceptual, verification, operational and input-data validity are different obligations. | Unit tests and synthetic simulator oracle certify code, **not** actual Celtic Heroes DPS; independent recorded encounter holdouts needed before claiming game calibration. |
| NIST/SEMATECH statistics handbook, bootstrap plot | Resampling estimates *sampling variability* under assumptions, not a substitute for independence or representative sampling. | Session-level/bootstrap over independently observed combats/trades, not repeated adjacent hits from one encounter; record sample size and dependence. |
| Wilkinson et al., FAIR Principles, *Scientific Data* (2016), DOI 10.1038/sdata.2016.18 | Findable, accessible, interoperable, reusable (including provenance/licenses) research outputs. | Stable item/source IDs; Git source and revision; observation timestamp+region+patch+currency+account scope; ability to reproduce any shown decision. |
| W3C PROV-O Recommendation (2013) | Model primary-source lineage and derived-from relations. | Use a small JSON observation/provenance schema first; do **not** import a full ontology/RDF stack merely because a standard exists. |
| Balog et al., SIGIR (2019), transparent/scrutable user models | Exposing and adjusting the recommendation model improves users' ability to correct their preference assumptions. | Explicit, locally stored optional "fashion-first / power-first / low-effort" profiles; show the math and allow editing. |
| Dokoupil & Peska, *ACM TORS* (2026), DOI 10.1145/3754459 | User-perceived recommendation qualities can differ from accuracy-only objectives. | Evaluate usefulness and satisfaction, not just recommended DPS. But do not infer our app's outcomes from a different domain. |
| Feng et al., *ICWSM* (2026), DOI 10.1609/icwsm.v20i1.42667 | Contextualized LLM explanations can affect preference/engagement under controlled movie-domain conditions; verbosity has diminishing value. | Prefer precise deterministic source-derived reasons; no need for unverified LLM recommendation system. Game-domain generalization untested. |
| W3C WCAG 2.2 Quick Ref | Interactive controls need keyboard access, focus visibility, semantic labels and readable responsive content. | Test two top-level tabs, nested AION controls, compare widgets, color-independent status and small-screen table behavior. |

**Sources:** [Monti](https://doi.org/10.1007/s10462-020-09851-4), [multiobjective survey](https://pmc.ncbi.nlm.nih.gov/articles/PMC10073543/), [interactive OR experiment](https://doi.org/10.1007/s10479-024-05941-6), [incremental elicitation](https://www.sciencedirect.com/science/article/pii/S2193943821000923), [scenario charts](https://www.sciencedirect.com/science/article/pii/S0020025521007155), [Sargent V&V](https://www.tandfonline.com/doi/abs/10.1057/jos.2012.20), [NIST bootstrap](https://itl.nist.gov/div898/handbook/eda/section3/eda334.htm), [FAIR](https://doi.org/10.1038/sdata.2016.18), [PROV-O](https://www.w3.org/TR/prov-o/), [Balog SIGIR](https://research.google/pubs/transparent-scrutable-and-explainable-user-models-for-personalized-recommendation/), [ACM TORS](https://doi.org/10.1145/3754459), [ICWSM](https://ojs.aaai.org/index.php/ICWSM/article/view/42667), [WCAG](https://www.w3.org/WAI/WCAG22/quickref/).

## Decision contract, not an unverified algorithm

**Recommendation = scenario + feasible candidates + objective vector + source quality + preference + reproducible explanation.** An example CH vector: practical damage, sustain, death probability, potion cost, swap frequency, required item acquisition. AION vector: distinct wanted looks, real-money price incl membership and repeated dyes, in-game hours, account-wide value, owned duplicates, permanence. Do **not** assign a universal number to personal aesthetic preference; user wishlist/ratings are inputs.

- **Feasibility first:** class/level/slots, release status, owned inventory, patch, expiry, bind scope and budget are hard constraints. Missing requirement is **unknown/ineligible**, not a free zero-cost assumption.
- **Nondominance:** A dominates B only when it is no worse on **each reliable comparable dimension** (including conditional interactions) and strictly better in one. This does NOT mean removing candidates with unknown set effects. Existing CH OPT-002 exact Pareto code and independent tiny oracle remain canonical: reuse, don't rebuild.
- **Preferences:** for remaining feasible points, expose editable direction/weight and baseline units. If an AION shopper rates fashion 5, playtime 4 and power 1, state this *preference*, never claim measured psychological utility. Mark arbitrary score normalization.
- **Sensitivity:** show how results change as budget/weights/patch/gold-value/time-available vary. Ties, close calls and recommendation flips are valuable information. Provide a "no clear winner" path.
- **Uncertain inputs:** unknown price/drop odds/item release/mileage second-credit **must not** be filled with zero or unjustified random numbers. Run interval/scenario analysis when credible independent bounds exist; otherwise show unknown and the specific measurement that would resolve it.
- **Sampling validity:** players on public build leaderboards are self-selected, and higher scores may require rare gear. Never convert raw popularity to a probability of winning, "best for everyone," or causal evidence.
- **Validation ladder:** deterministic math tests → independent tiny exhaustive oracle → simulated scenario tests → paired-seed and cross-version stability → independent in-game observed holdouts with timestamps/source hashes → actual user decision study. Only the last two inform claims of game/UX validity.
- **Data and temporal schema:** observation_id, game, region/server, patch/version, observed_at, effective_from/to, canonical product/item id, channel, currency, exact integer price units, restrictions, primary URL, original SHA/snapshot hash, fact/estimate/opinion class, reviewer, status. Keep source observations separate from inferred calculation output; never overwrite historical rows silently.
- **Security/rights:** no third-party game art clone, mass account scraping, hidden credential capture or rehosting entire guides; use outbound source attribution, small derived facts and permission-aware refresh.
- **Presentation:** for each top comparison show 2–4 plain-language causes ("+20 modeled damage conditional on this fixed gear set"; "requires rare unverified item"; "reduces dyes but sacrifices one wishlist skin"), not an unexplained colored grade.

## Low-cost implementation plan with guardrails

1. Define one versioned decision provenance schema spanning both games, retaining per-game units; fixture-test region/patch/unknown/currency mismatch and hash the underlying observations. Don't merge identical names without stable IDs.
2. Surface linked eligibility, uncertainty and "why" breakdown from the existing source-backed CH/AION JSON. Do not replace the large existing simulators or use an LLM where deterministic rules suffice.
3. Add bounded interactive "what if" scenarios and Pareto visualizations with explicit unavailable-data states and named objective units. Test stable tie, nontransitive comparisons, dominance of **known** dimensions only, no ranking against mismatched patches.
4. Test a real, smaller end-to-end decision with a player against the plain baseline; record time-to-decision, correct understanding of caveats, willingness to revise choice, number of unexplained results. Predefine success targets before measuring. Experimental papers suggest methods, but do not prove Heaven.gg's KPI improvements.
5. Only then increase dataset depth and art richness. Prioritize full shop coverage and historically grounded game observations over complex speculative ML infrastructure.

## Explicit alternatives rejected for now

- **Single "God-tier" score:** short but misleading across class, boss, ownership, cosmetic taste and uncertain data. Offer default preset views instead.
- **Immediate deep-learning recommender:** no representative labeled training set or efficacy evidence, opaque and maintenance-heavy; deterministic explanations are enough for current scope.
- **First-party-game autopurchasing or password import:** unnecessary trust boundary for a guide. Keep read-only/manual data input until explicit separate consent and API terms verification.
- **Unlimited scraping of competitor guides/data:** copyright, rate-limit, and publisher trust risk; cite first-party URLs and observe reuse terms.
- **Per-hit confidence intervals from one fight:** pseudo-replication. Group by session/character/patch and report inability to estimate when n is inadequate.

## Research limitations and next falsifiable actions

This is a **source-based design review, not a systematic meta-analysis** of all possible papers or an A/B test. No field experiment, no permission to extract competitor proprietary data, no confirmed AION live shop refresh, and no CH calibration run occurred. Some 2026 results come from other applications, and user outcomes cannot be assumed. The scientific review is robust on methodological direction, not quantitatively predictive about this app.

Before declaring a "best" CH loadout, capture two independent same-patch encounter logs with controlled gear/session metadata and compare a preregistered simulator prediction to held-out results. Before declaring the best cosmetic purchase, get in-client official region/bind/dye rules and a complete date-scoped catalog. Before declaring the UI superior to Prydwen, do comparative task testing rather than claiming brand parity.

Factory decision: **NO_FACTORY_CHANGE_NEEDED**. These are project-level insights already covered by Toolbox generic verification, provenance and research rules; do not expand mandatory global prompt bytes.
