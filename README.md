# CH-tables

Celtic Heroes class/boss data utilities and reproducible DPS/uplink-time analysis.

This repository contains:

- modular sourced build records;
- a scraper for The Codex Saved Builds dataset;
- normalization/aggregation for generic class comparison;
- effective-DPS and uptime calculations;
- Rich console tables;
- CSV/JSON dataset export;
- boss damage-composition data and provenance.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Refresh the community build sample first:

```powershell
python -m ch_tables.scrape
python main.py
```

All external source URLs are stored as their original URLs with no ChatGPT or tracking query parameters.

> The Codex is a community/fan resource and is not an official DECA Games stat sheet. Generated aggregate tables describe the sampled published builds, not every player or a controlled population.
