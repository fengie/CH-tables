"""Rank existing Codex skill *observations* within their original build.

These are snapshot damage/cooldown indices, NOT universal skill DPS rankings,
level-rank curves, or validated rotation simulations. DoT overlaps and buff
benefits may make ranking comparisons invalid.

python -m ch_tables.skill_priorities
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path


# Role exclusions are deliberately conservative: a tooltip "Avg Damage"
# next to a debuff is not proof that the debuff directly deals that damage.
# Such effects require team-rotation evaluation, not damage/cooldown ranking.
SUPPORT_OR_MAINTENANCE_SKILLS = frozenset({
    "Expose Weakness", "Smoke Bomb", "Poison Weapon", "Fast Reflexes",
    "Steady Aim", "Sharpen Weapons", "Bolas", "Rapid Shot",
    "Defensive Spikes", "Bark", "Shield of Bark", "Bless",
    "Frenzy", "Warcry", "Taunt", "Distract", "Play Dead",
    "Hide", "Conceal", "Camouflage", "Camo", "Shield Wall",
    "Nature's Embrace", "Nature's Touch", "Abundance", "Energy Well",
    "Ice Attunement", "Fire Attunement", "Energy Shield", "Energy Boost",
    "Lure of Ice", "Lure of Fire", "Lure of Assassins", "Lure of Soldiers",
    "Lure of Giants", "Lure of Magic",
})


def snapshot_comparison(observations: list[dict]) -> dict:
    buckets = defaultdict(list)
    non_direct = defaultdict(list)
    for observation in observations:
        if not observation.get("source_url") or not observation.get("skill_name"):
            continue
        metrics = observation.get("numeric_metrics") or {}
        timing = observation.get("timing_s") or {}
        cd = timing.get("effective_cooldown_s") or timing.get("cooldown_s")
        avg = metrics.get("Avg Damage")
        if not isinstance(cd, (float, int)) or cd <= 0 or \
           not isinstance(avg, (float, int)) or avg < 0:
            continue
        cast = timing.get("cast_s")
        lockout = timing.get("lockout_s")
        lost = metrics.get("Dmg Lost")
        # Dmg Lost is a Codex-generated estimate. Its semantics may change,
        # and source may not include it for every skill.
        gross = avg / cd
        net = (avg - lost) / cd if isinstance(lost, (int, float)) else None
        entry = {
            "skill": observation["skill_name"],
            "cooldown_effective_s": cd,
            "observed_average_damage": avg,
            "gross_damage_per_cooldown_s": round(gross, 5),
            "codex_net_after_reported_lost_auto": round(net, 5)
            if net is not None else None,
            "reported_lost_auto_per_cast": lost,
            "cast_s": cast,
            "lockout_s": lockout,
            "skill_ability": observation.get("skill_ability"),
            "scaling_attribute": observation.get("scaling_attribute"),
            "evidence_kind": "single_saved_build_model",
            "strictly_comparable_to_other_characters": False,
        }
        if observation["skill_name"] in SUPPORT_OR_MAINTENANCE_SKILLS:
            # Do NOT show an unverified direct-damage rank for this skill.
            entry["rankable_direct_damage"] = False
            entry["reason"] = "Support/buff skill: damage field may be inherited or indirect"
            non_direct[observation["source_url"]].append(entry)
        else:
            entry["rankable_direct_damage"] = True
            buckets[observation["source_url"]].append(entry)
    ranking = {}
    for source in sorted(set(buckets) | set(non_direct)):
        skills = buckets[source]
        skills.sort(key=lambda x: -x["gross_damage_per_cooldown_s"])
        net_ranked = sorted(
            (row for row in skills if
             row["codex_net_after_reported_lost_auto"] is not None),
            key=lambda x: -x["codex_net_after_reported_lost_auto"],
        )
        ranking[source] = {
            "sample_size": len(skills),
            "by_gross_damage_cooldown": skills,
            "by_source_modeled_net_after_auto_loss": net_ranked,
            "support_and_maintenance_not_ranked": non_direct[source],
            "limitations": [
                "A skill\'s gross damage divided by cooldown is NOT rotation DPS.",
                "Source-modeled net DPS is a screening index, not practical rotation DPS.",
                "A skill may occupy cast time or interrupt autos or other skills.",
                "DoT double-counting, overlap, and support/debuff value are not modeled.",
                "Different builds contain incompatible stats, buffs and gear swaps.",
                "Skills with zero immediate damage may have major indirect value.",
                "Cooldown may reflect gear from an individual saved build.",
            ],
        }
    return ranking


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--observations", type=Path, default=Path(
        "data/reference/codex_skill_panel_observations.json"))
    parser.add_argument("--output", type=Path, default=Path(
        "data/planner/skill_snapshot_rankings.json"))
    args = parser.parse_args()
    root = json.loads(args.observations.read_text(encoding="utf-8"))
    rankings = snapshot_comparison(root["observations"])
    if not rankings:
        raise ValueError("No comparisons from sourced skill panel observations")
    output = {
        "schema_version": 1,
        "observations_source": str(args.observations),
        "published_saved_builds": len(rankings),
        "method": "within_saved_build_observed_avg_damage_over_effective_cooldown",
        "not_final_build_advice": True,
        "builds": rankings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False,
                                      indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"builds": len(rankings),
                      "ranked_skills": sum(len(x["by_gross_damage_cooldown"])
                                           for x in rankings.values())}))


if __name__ == "__main__":
    main()
