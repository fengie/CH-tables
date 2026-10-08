"""Sourced companion species, tier stats and public-item pet candidates.

Guide observations are dated; game records can be test-only or unused.
No pet skill damage formula, rarity probability or price is invented.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import argparse
import json
from pathlib import Path
import re

from .game_query import load_records

GUIDE = "https://forum.celtic-heroes.com/forum/viewtopic.php?f=169&p=747139&t=94901"
PET_GUIDES = {
    "eagle": "https://celticheroes.blogspot.com/2020/07/eagle-pet-guide.html",
    "wolf": "https://celticheroes.blogspot.com/2020/07/wolf-pet-guide.html",
    "chicken": "https://celticheroes.blogspot.com/2020/07/chicken-pet-guide.html",
    "phoenix": "https://celticheroes.blogspot.com/2020/07/phoenix-pet-guide.html",
}
ROGUE_COMPARISON = "https://forum.celtic-heroes.com/forum/viewtopic.php?f=4&p=800208&t=100882"
SPECIES = {
    "Rabbit": ("Natural Focus", ("Focus", "Vitality"), "heal_energy"),
    "Dog": ("Canine Bite", ("Vitality",), "physical_debuff"),
    "Wolf": ("Rake", ("Strength", "Attack"), "damage_over_time"),
    "Spider": ("Pounce", ("Dexterity", "Attack"), "damage"),
    "Boar": ("Feral Protection", ("Vitality", "Defence"), "reflect"),
    "Chicken": ("Fowl Fortune", ("Dexterity", "Attack"), "healing"),
    "Eagle": ("Crushing Talons", ("Focus",), "damage_evasion_debuff"),
    "Dragon": (None, (), "damage"),
    "Phoenix": ("Elemental Breath", ("Focus", "Vitality"), "resist_debuff"),
    "Seedling": (None, ("Strength", "Dexterity"), "group_support"),
    "Imp": (None, (), "damage"),
}
# Published guides explicitly describe 0,40,...200 for Eagle, Wolf,
# Chicken and Phoenix; no blanket application to all species/patches.
SIZES = ("Tiny", "Small", "Medium", "Large", "Huge", "Giant")
LEVELS = (0, 40, 80, 120, 160, 200)


@dataclass(frozen=True)
class PetTier:
    species: str
    color: str
    size: str
    level_requirement: int
    attributes: dict[str, int]
    skill: str | None
    source_url: str
    token_cost: int | None = None
    rarity_probability: float | None = None


def source_pet_tiers() -> list[PetTier]:
    """Only the public numerical color+tier tables transcribed below."""
    result = []
    examples = [
        ("Wolf", "Brown", "Strength", (10, 20, 40, 60, 90, 120),
         "Attack", (20, 40, 80, 120, 160, 200)),
        ("Chicken", "Brown", "Dexterity", (10, 20, 40, 60, 90, 120),
         "Attack", (20, 40, 80, 120, 160, 200)),
        ("Eagle", "Brown", "Focus", (10, 20, 40, 60, 90, 120),
         "Magic Resistance", (10, 20, 40, 60, 90, 120)),
        ("Phoenix", "Red", "Focus", (20, 40, 80, 120, 180, 240),
         "Vitality", (20, 40, 80, 120, 180, 240)),
    ]
    for species, color, a, aa, b, bb in examples:
        for i, (size, level) in enumerate(zip(SIZES, LEVELS)):
            result.append(PetTier(
                species, color, size, level,
                {a: aa[i], b: bb[i]},
                SPECIES[species][0],
                PET_GUIDES[species],
                token_cost=32 if i == 5 and color == "Brown" else None,
            ))
    return result


def candidate_pet_items(items: list[dict]) -> tuple[list[dict], dict]:
    """Explicit slot='Pet' -> candidate; name-only -> unverified candidate.

    Avoid matching boss names and monster drops containing 'Wolf' or
    'Dragon': for name-only require pet-titled item or standard size prefix.
    """
    selected = []
    counts = {"explicit_pet_slot": 0, "name_only_possible_pet": 0}
    for item in items:
        name = str(item.get("name", ""))
        stats = item.get("stats") if isinstance(item.get("stats"), dict) else {}
        slot = str(stats.get("slot", "")).casefold()
        if slot == "pet":
            evidence = "explicit_pet_slot"
        elif (re.search(r"\bpet\b", name, re.I) or
              re.match(r"^(Tiny|Small|Medium|Large|Huge|Giant|Spirit)\s+", name, re.I)) \
                and any(re.search(r"\b" + re.escape(species) + r"\b", name, re.I)
                        for species in SPECIES):
            evidence = "name_only_possible_pet"
        else:
            continue
        species = next((s for s in SPECIES
                        if re.search(r"\b" + re.escape(s) + r"\b", name, re.I)), None)
        selected.append({
            "item_id": item["id"],
            "name": name,
            "species": species,
            "matching_evidence": evidence,
            "stats": stats,
            "released_to_players": "unverified",
        })
        counts[evidence] += 1
    return selected, counts


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=Path, default=Path("data/game"))
    p.add_argument("--output", type=Path, default=Path("data/pets"))
    args = p.parse_args()
    items = list(load_records("items", root=args.data))
    candidates, counts = candidate_pet_items(items)
    args.output.mkdir(parents=True, exist_ok=True)
    obj = {
        "schema_version": 1,
        "public_pet_species": [
            {"name": name, "skill": vals[0], "main_stats": vals[1],
             "role": vals[2], "source_url": GUIDE if name not in (
                 "Phoenix", "Seedling", "Imp") else (
                 PET_GUIDES.get("phoenix") if name == "Phoenix" else ROGUE_COMPARISON
             )}
            for name, vals in SPECIES.items()
        ],
        "measured_tiers": [asdict(x) for x in source_pet_tiers()],
        "candidate_item_records": candidates,
        "candidate_counts": counts,
        "source_items": len(items),
        "notes": [
            "Candidate pet items are NOT confirmation of released pets.",
            "The 32-token guide statement covers tier-1 breeding through Giant, "
            "not every premium/color pet line.",
            "Only published colors, tiers and fields are populated.",
            "Pet skill expected damage requires controlled observations.",
            "Reconstructed item name matching is a low-confidence candidate signal.",
        ],
    }
    path = args.output / "pets_and_tiers.json"
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    print(json.dumps({
        "species": len(SPECIES),
        "sourced_tier_records": len(obj["measured_tiers"]),
        "candidate_items": len(candidates),
        "by_evidence": counts,
    }))


if __name__ == "__main__":
    main()
