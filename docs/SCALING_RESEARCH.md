# Celtic Heroes scaling research and evidence protocol

Updated 2026-10-08. This project distinguishes facts, community estimates, and still-unidentified formulas. **Unknown coefficients are not automatically inferred from one build.**

## Data inventories

- ch_tables/skill_reference.py: 93 community-indexed skill entries and 43 named abilities; numeric rank curves are not established from this alone.
- data/reference/rogue_codex_snapshot_2026_10_08.json: five Rogue skill observations from one Codex build, with effective skill-swap stats. Never treat these as coefficient training data.
- data/reference/raid_boss_resistances_2026_10_08.json: eight source-derived historical raid boss combat records, not current-server measurements.
- data/catalog/catalog_manifest.json: 23,752 unique upstream item records; 3,203 relevant endgame/rogue candidates selected by a broad, inspectable filter.
- data/catalog/rogue_endgame_items.json: raw numeric/categorical item stats plus provenance. Not a universal list of obtainable items.
- data/catalog/priority_gear_lookup.json and item_stat_schema.json: generated equipment candidates and source-field audit, never a fabricated BIS ranking.

The item source is pinned to celtichero2026/CH-Encyclopedia commit fb6d99ba035dd28e5df08e6303f653da0de9a024. Public extracted data is not a substitute for the current game; copyright and game materials belong to DECA Games.

## Structural identifiability: critical rule

Observing an unchanged character repeatedly does not identify skill coefficients.
We must vary Strength, the **active mainhand** weapon ability, physical and elemental damage, skill rank, and character skill ability *independently*.
Otherwise, many parameter sets produce identical screenshots.

Collect observation rows with strength, weapon_ability, physical, elemental,
displayed, group/session, patch, character and a verifiable source.
Keep skill rank, enemy, buffs and rotation details in separate structured tables.
Never compare tooltip maximum to actual per-hit average or mix patches.

## Stat formula baseline

Celtic Heroes Database community approximation:

    DisplayedDamage = Physical * (0.96523 + 0.159132 sqrt(STR)
                          + 0.05972 sqrt(active weapon ability)) + Elemental

High-STR differences above 3000/3300 have source-noted coefficient changes
with an uncertain continuation rule. ch_tables/calibration.py tests a
**continuous segmented square-root hypothesis**, NOT a verified high-STR game law:

    y = b0 + b1 sqrt(STR) + b2 sqrt(ability)
            + b3 max(0, sqrt(STR)-sqrt(3000))
            + b4 max(0, sqrt(STR)-sqrt(3300))

where y = (displayed - elemental) / physical.
Only fit the extra hinge terms when sufficient distinct measurements
exist on both sides of their breakpoints. Compare against independent
segment fits to test possible discontinuities.

Attack = DEX + active weapon ability + gear Attack.
Defence = 2*DEX + bonus Defence.
Health approximately 6.2505*VIT + bonus HP.
Energy approximately FOC*(6.2495 - 0.025*equipment weight) + bonus Energy.
Source: https://celticheroesdb.com/calculator

## Chosen statistical methods

**Small controlled studies:** Huber IRLS robust regression, identifiable
design-matrix validation, patch separation and no hidden extrapolation.
Implemented in ch_tables/calibration.py using Python stdlib.

**Generalization:** grouped holdouts (leave an entire experiment session
or boss out). Do not randomly split adjacent swings: they share stats,
items, server lag and buffs and would leak correlated conditions.
Report out-of-session MAE, not just in-sample fit.
Docs: https://scikit-learn.org/stable/modules/cross_validation.html

**Uncertainty:** session-level bootstrap (not per-hit bootstrap), 95%
percentile intervals, sample sizes and identification failures. Do not
report numerical precision unsupported by the input.

**Nonlinear candidate skill curves:** evaluate sqrt, linear,
monotonic saturation, and piecewise power functions for each *skill rank*
using robust bounded SciPy least_squares(loss='soft_l1') after enough
independent samples exist. Use sklearn isotonic regression as a
diagnostic only when data density is large, and disallow extrapolation.
Consider adjacent-rank hierarchical partial pooling only when within-rank
measurements identify base effects.
Docs: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html
and https://scikit-learn.org/stable/modules/isotonic.html

**Active learning:** the next_experiment helper scores feasible new
one-variable equipment swaps for added matrix information (greedy
D-optimal design). Repeat control configurations to detect drift.

**Applied damage:** estimate target-specific resistance, attack hit chance,
skill evasion chance and critical chance separately. Boss defence or
resistance VALUES are not damage reduction percentages. Use recorded
successes/attempts to fit calibrated binomial-logit rates. Do not
infer probabilities from a single hit.

**Practical DPS:** discrete-event scheduling must account for cooldowns,
animation/cast lockouts, interrupted autos, DoT refresh/downtime, buffs,
energy restoration, survivability and per-boss mitigation. A high
Double Attack tooltip does not prove a net gain over the autos it displaces.

## Specific user build constraints

DEX-only freely allocated points, support Expose raid gear stays separate.
Named Strength Dhiothu knuckleblades for personal-use fist auto DPS,
soon full Doch Gul; keep personal skill roster Shadowstrike, Quick Strike,
Life Steal, Double Attack, Rend, Smoke Bomb, Expose Weakness.
Do not recommend repeatedly reapplying Poison Weapon or Fast Reflexes;
the player dislikes maintenance. Value the Imperial Proteus bracelet's
HP/Energy. Disregard Dagger ability unless in-game weapon classification
requires it (verify the actual active Hand-to-Hand ability). Strength from
gear remains valuable to physical autos, Quick Strike and Rend.

Rogue Doch Gul full set bonus, per CH Encyclopedia curated documentation:
+1080 Quick Strike and +3600 Sneaky Attack, plus inherited Exalted Aura.
The Sneaky component is unused in this user's fist skill roster.

## Highest-information measurements to collect

1. Exact named-knuckles tooltip and active weapon ability; raw and
   modified attack speed; base and effective stat screen.
2. Fix all other gear and buffs; independently vary STR across 8-12
   values, including 2900-3100 and 3250-3450 when feasible.
3. Vary **Hand-to-Hand only**, and separately flat pierce, fire and poison.
4. Hold rank fixed while changing DEX and Cunning for Shadowstrike,
   Life Steal, Smoke Bomb and Expose; STR/Cunning for Quick Strike and Rend.
5. Measure 30-60 hits at each controlled setting, including misses and
   crits, on identical targets. Repeat several independent sessions.
6. Quantify Double Attack's net auto interruption on named knuckles,
   not simply its gross damage value.
7. Only publish fitted equations after a held-out in-game verification.

Sources: https://celticheroesdb.com/calculator ;
https://forum.celtic-heroes.com/forum/viewtopic.php?f=4&t=103112 ;
https://celtic-heroes.fandom.com/wiki/Abilities ;
https://the-codex.ch/ ;
https://github.com/celtichero2026/CH-Encyclopedia

Unknown level/rank-specific skill coefficients, unpublished
item properties and live gear balance are explicitly **unresolved**.
