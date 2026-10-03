# CH-tables

Celtic Heroes class/boss data utilities, normalized class samples, and reproducible effective-DPS analysis.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Refresh the community build sample:

```powershell
python -m ch_tables.scrape
python main.py
```

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Missing-data policy

The report no longer prints a blank/N/A merely because a target build page is missing a derived metric.

1. Direct values are preferred and labeled **SOURCE**.
2. If a useful derived metric is missing, it may be reconstructed only from sourced comparable data.
3. Reconstructed values are labeled **ESTIMATE** in the tables.
4. The model, calibration sample, formulas, sample size, empirical range, and original source URLs are printed.
5. Estimates are never silently presented as observed facts.

### Warrior example

The Surya8 Saved Builds entry exposes a benchmark DPS of **11,982.1**, while its current detail page does not expose a populated Practical Rotation Guide value.

The fallback uses three Warrior builds that expose both Overall Rotation DPS and Practical DPS:

- Draga — https://the-codex.ch/damagebuilder/draga
- yuhhh — https://the-codex.ch/damagebuilder/yuhhh
- Gwyn Shields DPS — https://the-codex.ch/damagebuilder/gwyn-shields-dps

For each calibration build:

```text
practical_ratio = practical_dps / overall_dps
```

The target estimate is:

```text
Surya8 practical DPS
    = Surya8 benchmark DPS
    * median(calibration practical_ratio)
```

The practical auto share is estimated with the median practical auto share of the same Warrior calibration sample.

With the current calibration data this gives approximately:

```text
Surya8 estimated practical DPS: 11,529.7
Empirical practical-DPS range:  11,503.3 - 11,557.3
Estimated practical auto share: 48.9%
Observed auto-share range:       40.6% - 50.7%
Estimated auto DPS:              5,638.0
Calibration n:                   3
```

Because the calibration sample is small, the code reports its observed min/max range instead of claiming a misleading high-confidence population interval.

## Data sources

Original source URLs live in `ch_tables/sources.py`.

The Codex is an unofficial community resource, not an official DECA Games stat sheet:

- https://the-codex.ch/
- https://the-codex.ch/builds

The generic class summary describes the sampled published builds after filtering to comparable damage builds at level 220+, not the entire player population.

## Current plans & progress

Canonical ledger: [`_AGENT_CONTEXT/PROJECT_PLAN.md`](_AGENT_CONTEXT/PROJECT_PLAN.md)

No active tracked work. Add the first durable item when substantive work begins.
