"""Static sourced records used for reproducible examples.

The detailed builds are representative saved builds, not population averages.
Every record stores its original source URL.
"""

from .models import BossAutoProfile, Build
from .sources import BLOODTHORN, DHIOTHU, MAGE_BUILD, RANGER_BUILD, ROGUE_BUILD, WARRIOR_BUILD


ROGUE = Build(
    name="Rogue main build", character_class="Rogue",
    base_strength=710, base_dexterity=5, base_focus=10, base_vitality=500,
    total_strength=4222, total_dexterity=1447, total_focus=750, total_vitality=1680,
    hp=12000, energy=6188, attack=17757, defence=4654,
    practical_dps=12997.7, auto_dps=5745.8, source_url=ROGUE_BUILD,
)

RANGER = Build(
    name="SUZZ", character_class="Ranger",
    base_strength=1250, base_dexterity=5, base_focus=10, base_vitality=10,
    total_strength=5572, total_dexterity=3257, total_focus=635, total_vitality=1595,
    hp=11469, energy=5469, attack=27239, defence=8324,
    practical_dps=13631.6,
    # Source page reports 6,837,104 practical auto damage over 900 seconds.
    auto_dps=6837104 / 900,
    source_url=RANGER_BUILD,
)

WARRIOR = Build(
    name="Surya8", character_class="Warrior",
    base_strength=1165, base_dexterity=5, base_focus=10, base_vitality=10,
    total_strength=5622, total_dexterity=850, total_focus=735, total_vitality=1687,
    hp=12044, energy=6094, attack=20687, defence=3460,
    # The builds index gives a benchmark DPS, but this detailed table leaves it
    # unset rather than pretending it is identical to the practical-rotation metric.
    practical_dps=None, auto_dps=None, source_url=WARRIOR_BUILD,
)

MAGE = Build(
    name="High Tier Ice", character_class="Mage",
    base_strength=5, base_dexterity=5, base_focus=1180, base_vitality=10,
    total_strength=510, total_dexterity=1006, total_focus=7502, total_vitality=2581,
    hp=17631, energy=49613, attack=3356, defence=3872,
    practical_dps=7298.9,
    # Source page reports 83,288 practical auto damage over 900 seconds.
    auto_dps=83288 / 900,
    source_url=MAGE_BUILD,
)

REPRESENTATIVE_BUILDS = [ROGUE, RANGER, WARRIOR, MAGE]

DHIOTHU_AUTO = BossAutoProfile(
    name="Dhiothu",
    components={"Crushing": 9500, "Magic": 10000, "True": 1500},
    source_url=DHIOTHU,
)

BLOODTHORN_AUTO = BossAutoProfile(
    name="Bloodthorn",
    components={"Slashing": 4000, "Poison": 5000, "Chaos": 7750, "True": 800},
    source_url=BLOODTHORN,
)

BOSS_AUTOS = [DHIOTHU_AUTO, BLOODTHORN_AUTO]
