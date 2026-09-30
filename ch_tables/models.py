from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Build:
    name: str
    character_class: str
    base_strength: int
    base_dexterity: int
    base_focus: int
    base_vitality: int
    total_strength: int
    total_dexterity: int
    total_focus: int
    total_vitality: int
    hp: int
    energy: int
    attack: int
    defence: int
    practical_dps: Optional[float] = None
    auto_dps: Optional[float] = None
    source_url: str = ""

    @property
    def base_stat_pool(self) -> int:
        return self.base_strength + self.base_dexterity + self.base_focus + self.base_vitality

    @property
    def vitality_share(self) -> float:
        return self.base_vitality / self.base_stat_pool

    @property
    def auto_share(self) -> Optional[float]:
        if self.practical_dps is None or self.auto_dps is None:
            return None
        return self.auto_dps / self.practical_dps


@dataclass(frozen=True)
class BossAutoProfile:
    name: str
    components: dict[str, int]
    source_url: str

    @property
    def total_raw(self) -> int:
        return sum(self.components.values())


@dataclass(frozen=True)
class PublishedBuild:
    name: str
    character_class: str
    level: int
    build_type: str
    benchmark_dps: Optional[float]
    description: str = ""
    created: str = ""
    build_url: str = ""
    source_url: str = ""

    @property
    def is_damage_build(self) -> bool:
        return self.build_type.lower() == "damage" and self.benchmark_dps is not None
