"""Source-indexed Celtic Heroes abilities, skills and conservative stat calculations.

This is a REFERENCE CATALOG, not a claim to the complete current game client.
Unknown rank-dependent skill formulas and live gear-dependent values remain unknown.
Source: https://celtic-heroes.fandom.com/wiki/Skills (historical wiki);
https://celtic-heroes.fandom.com/wiki/Abilities ;
https://the-codex.ch/damagebuilder/realistic-rogue-build (reference snapshot);
https://celticheroesdb.com/calculator (community stat formula).
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

WIKI_SKILLS_URL = "https://celtic-heroes.fandom.com/wiki/Skills"
WIKI_ABILITIES_URL = "https://celtic-heroes.fandom.com/wiki/Abilities"
CODEX_ROGUE_URL = "https://the-codex.ch/damagebuilder/realistic-rogue-build"
CALCULATOR_URL = "https://celticheroesdb.com/calculator"
HISTORICAL_REND_URL = "https://forum.celtic-heroes.com/forum/viewtopic.php?p=49574"

# Row: [skill name, attribute scaling stat (blank if none/unknown),
#       skill ability (blank if none/unknown), defender evasion category].
# "None/unknown" is intentionally distinguished only in detailed snapshots:
# the community wiki does not rigorously disambiguate those cases.
SKILL_ROWS = {
  "Shared": [
    [
      "Bandage Wounds",
      "Vitality",
      "First Aid",
      ""
    ],
    [
      "Recuperate",
      "Vitality",
      "First Aid",
      ""
    ],
    [
      "Meditate",
      "Focus",
      "First Aid",
      ""
    ],
    [
      "Signal Fire",
      "",
      "",
      ""
    ],
    [
      "Guiding Fire",
      "",
      "",
      ""
    ],
    [
      "Beacon Fire",
      "",
      "",
      ""
    ],
    [
      "Divine Flame",
      "",
      "",
      ""
    ],
    [
      "Natural Divination",
      "",
      "",
      ""
    ]
  ],
  "Melee Shared": [
    [
      "Skewer",
      "",
      "",
      "Movement Attack"
    ],
    [
      "Double Attack",
      "",
      "",
      ""
    ]
  ],
  "Warrior": [
    [
      "Giant Swing",
      "Strength",
      "Melee Combat",
      "Physical Attack"
    ],
    [
      "Pummel",
      "Strength",
      "Melee Combat",
      "Physical Attack"
    ],
    [
      "Frenzy",
      "Strength",
      "Melee Combat",
      ""
    ],
    [
      "Protective Stance",
      "Vitality",
      "Melee Combat",
      ""
    ],
    [
      "Defensive Formation",
      "Vitality",
      "Melee Combat",
      ""
    ],
    [
      "Taunt",
      "Vitality",
      "Melee Combat",
      "Mental Attack"
    ],
    [
      "Warcry",
      "Vitality",
      "Melee Combat",
      "Mental Attack"
    ],
    [
      "Sweeping Blow",
      "Strength",
      "Melee Combat",
      "Physical Attack"
    ],
    [
      "Shatter",
      "Strength",
      "Melee Combat",
      "Weakening Attack"
    ],
    [
      "Rupture",
      "Strength",
      "Melee Combat",
      "Wounding Attack"
    ],
    [
      "Enduring Guard",
      "Vitality",
      "Melee Combat",
      ""
    ],
    [
      "Shield Wall",
      "Vitality",
      "Melee Combat",
      ""
    ]
  ],
  "Ranger": [
    [
      "Sharp Shot",
      "Dexterity",
      "Ranged Combat",
      "Physical Attack"
    ],
    [
      "Steady Aim",
      "Dexterity",
      "Ranged Combat",
      ""
    ],
    [
      "Bolas",
      "",
      "Ranged Combat",
      "Movement Attack"
    ],
    [
      "Camouflage",
      "",
      "Ranged Combat",
      ""
    ],
    [
      "Rapid Shot",
      "",
      "Ranged Combat",
      ""
    ],
    [
      "Barbed Shot",
      "Dexterity",
      "Ranged Combat",
      "Wounding Attack"
    ],
    [
      "Light Heal",
      "Dexterity",
      "First Aid",
      ""
    ],
    [
      "Conceal",
      "",
      "Ranged Combat",
      ""
    ],
    [
      "Double Shot",
      "",
      "",
      ""
    ],
    [
      "Longshot",
      "Dexterity",
      "Ranged Combat",
      "Physical Attack"
    ],
    [
      "Defensive Spikes",
      "Dexterity",
      "Ranged Combat",
      ""
    ],
    [
      "Entangle",
      "Dexterity",
      "Ranged Combat",
      "Movement Attack"
    ],
    [
      "Explosive Arrow",
      "Dexterity",
      "Ranged Combat",
      "Physical Attack"
    ],
    [
      "Sharpen Weapons",
      "Dexterity",
      "Ranged Combat",
      ""
    ]
  ],
  "Mage": [
    [
      "Fire Storm",
      "Focus",
      "Fire Magic",
      "Spell Attack"
    ],
    [
      "Fire Bolt",
      "Focus",
      "Fire Magic",
      "Spell Attack"
    ],
    [
      "Lure of Fire",
      "Focus",
      "Fire Magic",
      "Weakening Attack"
    ],
    [
      "Lure of Soldiers",
      "Focus",
      "Fire Magic",
      "Weakening Attack"
    ],
    [
      "Lure of Giants",
      "Focus",
      "Fire Magic",
      "Weakening Attack"
    ],
    [
      "Lure of Assassins",
      "Focus",
      "Fire Magic",
      "Weakening Attack"
    ],
    [
      "Cloak of Fire",
      "Focus",
      "Fire Magic",
      ""
    ],
    [
      "Fire Attunement",
      "Focus",
      "Fire Magic",
      ""
    ],
    [
      "Incinerate",
      "Focus",
      "Fire Magic",
      "Wounding Attack"
    ],
    [
      "Ice Shards",
      "Focus",
      "Ice Magic",
      "Spell Attack"
    ],
    [
      "Lure of Ice",
      "Focus",
      "Ice Magic",
      "Weakening Attack"
    ],
    [
      "Lure of Magic",
      "Focus",
      "Ice Magic",
      "Weakening Attack"
    ],
    [
      "Ice Blast",
      "Focus",
      "Ice Magic",
      "Spell Attack"
    ],
    [
      "Frostbite",
      "Focus",
      "Ice Magic",
      "Wounding Attack"
    ],
    [
      "Ice Attunement",
      "Focus",
      "Ice Magic",
      ""
    ],
    [
      "Energy Well",
      "Focus",
      "Ice Magic",
      ""
    ],
    [
      "Energy Shield",
      "Focus",
      "Ice Magic",
      ""
    ],
    [
      "Energy Boost",
      "Focus",
      "Ice Magic",
      ""
    ],
    [
      "Sacrifice",
      "Focus",
      "Ice Magic",
      ""
    ],
    [
      "Freeze",
      "Focus",
      "Ice Magic",
      "Movement Attack"
    ]
  ],
  "Druid": [
    [
      "Sanctuary",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Nature's Breath",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Abundant Aura",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Spring of Life",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Fire",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Assassins",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Soldiers",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Giants",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Magic",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Ward of Ice",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Bless",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Storm Touch",
      "Focus",
      "Nature Magic",
      "Spell Attack"
    ],
    [
      "Energy Harvest",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Nature's Touch",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Strangling Vines",
      "Focus",
      "Nature Magic",
      "Wounding Attack"
    ],
    [
      "Stinging Swarm",
      "Focus",
      "Nature Magic",
      "Wounding Attack"
    ],
    [
      "Grasping Roots",
      "",
      "Nature Magic",
      "Movement Attack"
    ],
    [
      "Howling Wind",
      "Focus",
      "Nature Magic",
      "Weakening Attack"
    ],
    [
      "Shield of Bark",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Nature's Embrace",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Lightning Strike",
      "Focus",
      "Nature Magic",
      "Spell Attack"
    ],
    [
      "Abundance",
      "Focus",
      "Nature Magic",
      ""
    ],
    [
      "Rescue",
      "",
      "",
      ""
    ],
    [
      "Calm",
      "Focus",
      "Nature Magic",
      ""
    ]
  ],
  "Rogue": [
    [
      "Shadowstrike",
      "Dexterity",
      "Cunning",
      "Movement Attack"
    ],
    [
      "Assassinate",
      "Strength",
      "Cunning",
      "Physical Attack"
    ],
    [
      "Smoke Bomb",
      "Dexterity",
      "Cunning",
      "Weakening Attack"
    ],
    [
      "Life Steal",
      "Dexterity",
      "Cunning",
      "Weakening Attack"
    ],
    [
      "Expose Weakness",
      "Dexterity",
      "Cunning",
      "Weakening Attack"
    ],
    [
      "Quick Strike",
      "Strength",
      "Cunning",
      "Physical Attack"
    ],
    [
      "Sneaky Attack",
      "Strength",
      "Cunning",
      ""
    ],
    [
      "Hide",
      "",
      "Cunning",
      ""
    ],
    [
      "Poison Weapon",
      "Dexterity",
      "Cunning",
      ""
    ],
    [
      "Rend",
      "Strength",
      "Cunning",
      "Wounding Attack"
    ],
    [
      "Fast Reflexes",
      "Dexterity",
      "Cunning",
      ""
    ],
    [
      "Distract",
      "Dexterity",
      "Cunning",
      "Mental Attack"
    ],
    [
      "Riposte",
      "Strength",
      "Cunning",
      ""
    ]
  ]
}

# Grouping follows the community Abilities article. Weapon / class ability
# associations must NEVER be inferred from the skill name alone.
ABILITIES = {
  "Weapon": [
    "Hand to Hand",
    "Novelty",
    "Sword",
    "Spear",
    "Axe",
    "Blunt",
    "Bow",
    "Dagger",
    "Wand",
    "Totem",
    "Staff"
  ],
  "Class": [
    "First Aid",
    "Melee Combat",
    "Ranged Combat",
    "Fire Magic",
    "Ice Magic",
    "Nature Magic",
    "Cunning"
  ],
  "Skill evasion": [
    "Reflex",
    "Willpower",
    "Vigour",
    "Warding",
    "Fortitude"
  ],
  "Critical / bonus": [
    "Treasure Hunter",
    "Scholar",
    "Critical Strike",
    "Critical Skills"
  ],
  "Pet taming": [
    "Rabbit Taming",
    "Dog Taming",
    "Bear Taming",
    "Wolf Taming",
    "Boar Taming",
    "Spider Taming",
    "Dragon Taming",
    "Phoenix Taming"
  ],
  "Mount riding": [
    "Wolf Riding",
    "Bear Riding",
    "Tiger Riding",
    "Elk Riding",
    "Horse Riding"
  ],
  "Gathering": [
    "Fishing",
    "Cooking",
    "Cooking Mastery"
  ]
}

# Baseline timings from one snapshot of The Codex. Gear in the snapshot can
# modify cooldowns; these are base numbers, NOT universal effective cooldowns.
# Null denotes unavailable/not verified, not zero.
ROGUE_ROTATION_BASELINE = {
  "Shadowstrike": {
    "cooldown": 12,
    "cast": 0,
    "lockout": 0.01,
    "damage": "Poison",
    "notes": "Dexterity/Cunning, movement evasion; model baseline, before cooldown gear"
  },
  "Quick Strike": {
    "cooldown": 10,
    "cast": 0,
    "lockout": 0.01,
    "damage": "Pierce",
    "notes": "Strength/Cunning; no weapon-damage or weapon-delay addition"
  },
  "Life Steal": {
    "cooldown": 25,
    "cast": 1,
    "lockout": 0,
    "damage": "Poison",
    "notes": "Dexterity/Cunning; healing is primary reason to cast; could lose DPS to displaced autos"
  },
  "Double Attack": {
    "cooldown": 15,
    "cast": 1,
    "lockout": 0.5,
    "damage": "Weapon",
    "notes": "No stat/skill ability scaling directly; 2x weapon damage below skill level target threshold; guaranteed hit per wiki and Codex"
  },
  "Rend": {
    "cooldown": 19,
    "cast": 0.39,
    "lockout": 1,
    "damage": "Pierce DoT",
    "notes": "Strength/Cunning in newer wiki and current Codex; older 2012 patch notes say DEX; source conflict recorded"
  },
  "Smoke Bomb": {
    "cooldown": None,
    "cast": None,
    "lockout": None,
    "damage": "Debuff",
    "notes": "Dexterity/Cunning, weakens defence; base timings not corroborated"
  },
  "Expose Weakness": {
    "cooldown": None,
    "cast": None,
    "lockout": None,
    "damage": "Debuff",
    "notes": "Dexterity/Cunning, weakens skill evasions; wiki lists 60 s duration; base timings not corroborated"
  }
}

ROGUE_ALIASES = {
    "ss": "Shadowstrike",
    "shadow strike": "Shadowstrike",
    "qs": "Quick Strike",
    "ls": "Life Steal",
    "double": "Double Attack",
    "smoke": "Smoke Bomb",
    "expose": "Expose Weakness",
    "pw": "Poison Weapon",
    "fr": "Fast Reflexes",
}

@dataclass(frozen=True)
class Skill:
    name: str
    character_class: str
    scaling_stat: str | None
    skill_ability: str | None
    evasion: str | None
    source_url: str = WIKI_SKILLS_URL


def skills_for(character_class: str) -> tuple[Skill, ...]:
    """Known community-wiki skills for this class plus shared skills."""
    if character_class not in SKILL_ROWS or character_class in ("Shared", "Melee Shared"):
        raise ValueError(f"Unknown character class: {character_class}")
    groups = ["Shared"]
    if character_class in ("Warrior", "Ranger", "Rogue"):
        groups.append("Melee Shared")
    groups.append(character_class)
    return tuple(
        Skill(name, group, stat or None, ability or None, evasion or None)
        for group in groups for name, stat, ability, evasion in SKILL_ROWS[group]
    )


def lookup_skill(name: str, character_class: str = "Rogue") -> Skill:
    """Case-insensitive name lookup with known player shorthand."""
    key = name.strip().lower()
    if character_class == "Rogue":
        key = ROGUE_ALIASES.get(key, key).lower()
    matches = [skill for skill in skills_for(character_class)
               if skill.name.lower() == key]
    if len(matches) != 1:
        raise KeyError(f"Unknown or ambiguous skill for {character_class}: {name}")
    return matches[0]


def attack(dexterity: float, equipped_weapon_ability: float,
           bonus_attack: float = 0) -> float:
    """CHDB: attack = DEX + ability of EQUIPPED weapon + equipment attack."""
    return dexterity + equipped_weapon_ability + bonus_attack


def defence(dexterity: float, bonus_defence: float = 0) -> float:
    return 2 * dexterity + bonus_defence


def health(vitality: float, bonus_health: float = 0) -> float:
    return 6.2505 * vitality + bonus_health


def energy(focus: float, equipment_weight: float,
           bonus_energy: float = 0) -> float:
    return focus * (6.2495 - 0.025 * equipment_weight) + bonus_energy


def displayed_damage(strength: float, equipped_weapon_ability: float,
                     physical_damage: float, elemental_damage: float = 0) -> float:
    """Community estimate of displayed damage for 0 <= STR <= 3000 only.

    Source describes altered coefficients above 3000/3300 STR but not an
    unambiguous continuous function; refuse rather than invent cap arithmetic.
    Not a boss DPS formula: missing mitigation, variance, hit/crit, uptime.
    """
    if min(strength, equipped_weapon_ability, physical_damage, elemental_damage) < 0:
        raise ValueError("Damage formula inputs cannot be negative")
    if strength > 3000:
        raise ValueError("CHDB's >3000 STR breakpoint requires revalidation")
    return (
        0.159132 * sqrt(strength)
        + 0.05972 * sqrt(equipped_weapon_ability)
        + 0.96523
    ) * physical_damage + elemental_damage


def compare_flat_damage(strength: float, equipped_weapon_ability: float,
                        physical_damage: float, elemental_damage: float,
                        new_strength: float, new_ability: float,
                        new_physical: float, new_elemental: float) -> float:
    """New minus old DISPLAYED damage; not actual boss DPS."""
    old = displayed_damage(strength, equipped_weapon_ability,
                           physical_damage, elemental_damage)
    new = displayed_damage(new_strength, new_ability,
                           new_physical, new_elemental)
    return new - old


def validate_reference() -> None:
    """Fail closed on duplicate skills, missing source or mistyped columns."""
    if not (WIKI_SKILLS_URL.startswith("https://") and
            CODEX_ROGUE_URL.startswith("https://")):
        raise ValueError("Missing provenance")
    for group, rows in SKILL_ROWS.items():
        names = [r[0].casefold() for r in rows]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate skill in {group}")
        for row in rows:
            if len(row) != 4 or not row[0]:
                raise ValueError(f"Malformed skill row in {group}: {row}")
    for stat_name in ("Dexterity", "Strength"):
        if not any(r[1] == stat_name for r in SKILL_ROWS["Rogue"]):
            raise ValueError(f"Missing {stat_name} Rogue scaling examples")
