"""Conservative extraction of *observed* skill panels from public Codex builds.

Important: A saved build is one correlated loadout, not a randomized
experiment and NOT a recovered client formula. Network traffic is bounded
to a small curated set of public URLs with a delay per request.
"""
from __future__ import annotations

import argparse
from bs4 import BeautifulSoup, NavigableString, Tag
from datetime import date
import hashlib
import json
from pathlib import Path
import re
from time import sleep
import requests

SOURCE_URLS = (
    "https://the-codex.ch/damagebuilder/rogue-main-build",
    "https://the-codex.ch/damagebuilder/realistic-rogue-build",
    "https://the-codex.ch/damagebuilder/surya8",
    "https://the-codex.ch/damagebuilder/suzz",
    "https://the-codex.ch/damagebuilder/high-tier-ice",
    "https://the-codex.ch/damagebuilder/draga",
    "https://the-codex.ch/damagebuilder/yuhhh",
    "https://the-codex.ch/damagebuilder/gwyn-shields-dps",
)
KNOWN_ABILITIES = (
    "Cunning", "Melee Combat", "Ranged Combat", "Nature Magic",
    "Fire Magic", "Ice Magic", "First Aid", "Hand to Hand",
    "Dagger", "Bow", "Sword", "Axe", "Blunt", "Spear",
    "Elk Riding", "Wolf Riding", "Bear Riding",
)
PRIMARY_STATS = ("Strength", "Dexterity", "Focus", "Vitality")
METRICS = (
    "Max Damage", "Base Skill", "Direct Dmg", "Avg Damage",
    "Dmg Lost", "Healing", "Debuff Value", "Health", "Energy",
)
NUMBER = re.compile(r"(?<!\w)-?\d[\d,]*(?:\.\d+)?")
COOLDOWN = re.compile(r"\bCooldown\s*:", re.IGNORECASE)


def parse_integer(s: str) -> int | float | None:
    match = NUMBER.search(s.strip())
    if not match:
        return None
    n = float(match.group().replace(",", ""))
    return int(n) if n.is_integer() else n


def parse_stat_pair(text: str) -> dict | None:
    nums = re.findall(r"-?\d[\d,]*(?:\.\d+)?", text)
    if not nums:
        return None
    return {
        "base": parse_integer(nums[0]),
        "effective": parse_integer(nums[1]) if len(nums) >= 2 else None,
    }


def skill_tokens(head: Tag, max_text_nodes: int = 220) -> list[str]:
    found = []
    for node in head.next_elements:
        if isinstance(node, Tag) and node.name in ("h2", "h3"):
            break
        if isinstance(node, NavigableString):
            t = str(node).strip()
            if t and t not in ("\u200b",):
                found.append(t)
                if len(found) >= max_text_nodes:
                    break
    return found


def parse_skills_html(html: str, source_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    observations = []
    seen = set()
    for head in soup.find_all("h3"):
        name = head.get_text(" ", strip=True)
        if not name or len(name) > 65:
            continue
        tokens = skill_tokens(head)
        ci = next((i for i, token in enumerate(tokens) if COOLDOWN.search(token)), None)
        if ci is None:
            continue
        raw_cooldown = tokens[ci]
        # A stat is accepted only if the immediately following token contains
        # numeric values and precedes the first Max Damage block.
        limit = next((j for j in range(ci, len(tokens))
                      if tokens[j].strip() == "Max Damage"), min(ci + 24, len(tokens)))
        pre_damage = tokens[ci + 1:limit]
        ability = None
        scaling = None
        for i, t in enumerate(pre_damage[:-1]):
            if ability is None and t in KNOWN_ABILITIES:
                ability = {"name": t, "value": parse_stat_pair(pre_damage[i + 1])}
            if scaling is None and t in PRIMARY_STATS:
                scaling = {"stat": t, "value": parse_stat_pair(pre_damage[i + 1])}
        vals = {}
        for i, token in enumerate(tokens):
            if token.strip() in METRICS and i + 1 < len(tokens):
                num = parse_integer(tokens[i + 1])
                if num is not None:
                    vals[token.strip()] = num
        if "Max Damage" not in vals and "Debuff Value" not in vals and "Healing" not in vals:
            continue
        identity = (source_url, name)
        if identity in seen:
            continue
        seen.add(identity)
        observations.append({
            "source_url": source_url, "skill_name": name,
            "cooldown_cast_lockout_text": raw_cooldown,
            "skill_ability": ability, "scaling_attribute": scaling,
            "numeric_metrics": vals,
            "model_provenance": "single_saved_build_not_engine_coefficients",
        })
    return observations


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path,
                    default=Path("data/reference/codex_skill_panel_observations.json"))
    args = ap.parse_args()
    snapshots = []
    observations = []
    errors = []
    for i, url in enumerate(SOURCE_URLS):
        if i:
            sleep(0.6)
        try:
            response = requests.get(url, timeout=22, headers={
                "User-Agent": "CH-tables-research/1.0 (public noncommercial source indexing)"
            })
            response.raise_for_status()
            html = response.text
            parsed = parse_skills_html(html, url)
            if not parsed:
                raise ValueError("No server-rendered skill panels found")
            observations.extend(parsed)
            snapshots.append({
                "url": url, "html_sha256": hashlib.sha256(response.content).hexdigest(),
                "skills": len(parsed),
            })
            print(url, len(parsed))
        except (requests.RequestException, ValueError) as ex:
            errors.append({"url": url, "error": str(ex)[:180]})
    if len(snapshots) < 4 or len(observations) < 15:
        raise ValueError(f"Insufficient sourced skill observations; failures={errors}")
    payload = {
        "schema": 1, "collected_on": date.today().isoformat(),
        "source_method": "read_only_public_saved_build_HTML",
        "warning": "NOT exact current engine coefficients; item-swap effects "
                   "and cross-build confounding are present.",
        "snapshots": snapshots, "errors": errors,
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = args.output.with_suffix(".json.tmp")
    stage.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    stage.replace(args.output)
    print(json.dumps({"sources": len(snapshots),
                      "observations": len(observations), "errors": errors}))


if __name__ == "__main__":
    main()
