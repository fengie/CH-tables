# Celtic Heroes skill and ability reference (evidence-based)

Updated: 2026-10-08. Scope: **community-documented**, NOT the complete verified current game binary.

## Reusable code

`ch_tables/skill_reference.py` contains:

- **93 listed skills** across Shared, Melee Shared, Warrior, Ranger, Mage, Druid and Rogue, with documented scaling attribute, class ability and evasion category where sourced.
- **43 named abilities** grouped by weapon, class, resistance/evasion training, critical, pets, mounts and gathering.
- Base timing observations for the seven selected rogue skills where a Codex build exposes them. A missing timing is stored as `None`—never zero.
- Community approximation functions for Attack, Defence, HP, Energy and *displayed* damage (STR at/below 3000).
- Case-insensitive rogue shorthand lookup and a reference validator; tests in `tests/test_skill_reference.py`.

Example:

```python
from ch_tables.skill_reference import lookup_skill, skills_for, attack, displayed_damage

assert lookup_skill("ss").scaling_stat == "Dexterity"
assert lookup_skill("rend").scaling_stat == "Strength"
print(len(skills_for("Rogue")))
print(attack(dexterity=2000, equipped_weapon_ability=3000, bonus_attack=500))
print(displayed_damage(strength=1200, equipped_weapon_ability=3000,
                       physical_damage=350, elemental_damage=390))
```

**Caveat:** `displayed_damage` is not boss DPS. It does not model auto fluctuation, boss physical/elemental mitigation, critical hit chance and damage, haste caps, lockouts, proc rates or evasions. Its high-STR formula deliberately refuses extrapolation above 3000; the cited calculator lists changed coefficients without a sufficiently unambiguous continuous piecewise definition. Do not compare high-end STR gear using that function until calibrated with observed character values.

## Sources and evidence quality

| Source | Coverage | Limitation |
|---|---|---|
| [Celtic Heroes Database skill search](https://celticheroesdb.com/search) and [All Skills](https://celticheroesdb.com/groups/all) | Searchable live item/skill catalog | Client-side search; cannot validate every rank or reverse-engineer hidden coefficients from no-JS listing |
| [Celtic Heroes fandom skill index](https://celtic-heroes.fandom.com/wiki/Skills) | All five classes: names, attributes, abilities, descriptions, evasion categories | Community wiki, historical, may omit modern skills or contain outdated statements |
| [Abilities index](https://celtic-heroes.fandom.com/wiki/Abilities) | Ability categories and training progression | Not current in-game audit |
| [Codex realistic rogue build](https://the-codex.ch/damagebuilder/realistic-rogue-build) | Current modeled snapshot of damage, timings, scaling and casts | Not raw engine formulas; item swaps and buffs change displayed outcomes |
| [CHDB stat calculator](https://celticheroesdb.com/calculator) | Approximate stat formulas | Author cautions estimates and caps may differ from game |
| [2012 patch notes](https://forum.celtic-heroes.com/forum/viewtopic.php?p=49574) | Historical skill/stat behavior | Conflicts with newer Rend data |
| [2020 mechanics discussion](https://forum.celtic-heroes.com/forum/viewtopic.php?f=4&t=103112) | Explains lack of authoritative skill coefficients | Acknowledges incomplete high-STR formula |

### Notable source conflicts

- **Rend:** 2012 patch notes list DEX; newer wiki **and current Codex** list **STR**. Registry uses STR with explicit provenance; in-game tooltip should decide if updated again.
- **Hand-to-Hand:** Historical wiki says Hand-to-Hand affects *unarmed* damage, but CHDB item listings for knuckleblades include Hand-to-Hand stats, e.g. [Spellwrought Knuckleblade](https://celticheroesdb.com/groups/2015-03-17). In-game weapon ability shown while equipping the exact **named Dhiothu knuckleblades** is decisive. **Do not substitute dagger ability** or double-count passive H2H without confirming the mainhand classification.
- **Double Attack:** The wiki describes an unavoidable double strike against foes below a skill-dependent level threshold. Its level behavior and **time spent interrupting autos** matter; do not model all casts as free +2 attacks.
- **Life Steal:** Its 1-second cast can lower theoretical DPS in rapid-auto builds. Include it for sustain and keep offensive ranking separate.

## Skill values and what is *not* known

Skill power usually depends on skill rank, class skill ability, character attributes, item bonus damage, target level/evasions/resists and timed buffs. Published Codex numbers belong to **one specific saved build** and are not universal constants. Numeric skill damage functions across *every rank and ability value* are not currently fully validated; these fields remain `None` or absent rather than invented. Item skills and new game content require separately sourced ingestion.

## Next validation measurements

1. Equip named STR knuckleblades and record item tooltip, attack speed, active mainhand weapon ability, displayed damage, Attack and Strength.
2. Read tooltips for Rend, Quick Strike, Shadowstrike, Double Attack and Life Steal at their actual skill ranks with current gear.
3. Swap one item at a time while keeping target, buffs, offhand and skill ranks fixed; log displayed stats.
4. Use real combat logs at identical targets to estimate elemental mitigation and per-cast auto interruption before deciding permanent BIS.
5. Record every new sample with server/update, build, timestamp, skill points, gear, source URL/screenshot and calculated uncertainty.

Do not scrape undocumented private APIs or store copied full game assets in the repository.
