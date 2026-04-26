"""Loot tables for adventure and reward systems."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from classes.items import ItemGenerator, ItemType


@dataclass(frozen=True)
class LootDrop:
    """A generated loot result ready to persist."""

    name: str
    item_type: str
    value: int
    damage: int
    armor: int
    hand: str
    health_bonus: int
    speed_bonus: int
    luck_bonus: float
    crit_bonus: float
    magic_bonus: int
    slot_type: str
    rarity: str


RARITY_ROLLS: Tuple[Tuple[str, float, int, int], ...] = (
    ("common", 0.55, 1, 6),
    ("uncommon", 0.25, 4, 10),
    ("rare", 0.13, 8, 16),
    ("magic", 0.05, 14, 24),
    ("legendary", 0.018, 24, 38),
    ("mythic", 0.002, 36, 55),
)

TYPE_BY_RARITY: Dict[str, Tuple[ItemType, ...]] = {
    "common": (ItemType.SWORD, ItemType.SHIELD, ItemType.CHESTPLATE, ItemType.BOOTS),
    "uncommon": (ItemType.SWORD, ItemType.AXE, ItemType.SHIELD, ItemType.CHESTPLATE, ItemType.BOOTS, ItemType.GAUNTLETS),
    "rare": (ItemType.SWORD, ItemType.AXE, ItemType.DAGGER, ItemType.BOW, ItemType.WAND, ItemType.CHESTPLATE, ItemType.HELMET, ItemType.HELMET, ItemType.GAUNTLETS),
    "magic": (ItemType.STAFF, ItemType.WAND, ItemType.STAFF, ItemType.SPEAR, ItemType.HELMET, ItemType.GAUNTLETS, ItemType.LEGGINGS),
    "legendary": (ItemType.STAFF, ItemType.STAFF, ItemType.AXE, ItemType.BOW, ItemType.HELMET, ItemType.GAUNTLETS, ItemType.LEGGINGS),
    "mythic": (ItemType.STAFF, ItemType.STAFF, ItemType.AXE, ItemType.BOW, ItemType.HELMET, ItemType.GAUNTLETS),
}

PREFIXES: Dict[str, Tuple[str, ...]] = {
    "common": ("Weathered", "Iron", "Plain", "Sturdy"),
    "uncommon": ("Keen", "Reinforced", "Veteran", "Gleaming"),
    "rare": ("Runed", "Dragonbone", "Stormforged", "Moonlit"),
    "magic": ("Arcane", "Soulbound", "Starfallen", "Witchfire"),
    "legendary": ("Godslayer", "Eternal", "Worldsplitter", "Doom-Sung"),
    "mythic": ("Ragnarok", "Void-Crowned", "Mimir's", "Yggdrasil"),
}

SUFFIXES: Dict[str, Tuple[str, ...]] = {
    "common": ("of Practice", "of Dust", "of Beginnings"),
    "uncommon": ("of Grit", "of the Road", "of Resolve"),
    "rare": ("of the Deep Road", "of Crows", "of Broken Kings"),
    "magic": ("of the Astral Forge", "of Hexes", "of the Ninth Rune"),
    "legendary": ("of the Last Saga", "of Divine Debt", "of the Dead Sun"),
    "mythic": ("of the One-Eyed God", "of Ending Winters", "of the World Tree"),
}


def roll_rarity(luck: float = 1.0) -> str:
    """Roll item rarity, with luck nudging higher rarity odds."""
    luck = max(0.5, min(float(luck or 1.0), 3.0))
    weighted = []
    for rarity, base_weight, _min_stat, _max_stat in RARITY_ROLLS:
        multiplier = luck if rarity in {"rare", "magic", "legendary", "mythic"} else 1.0
        weighted.append((rarity, base_weight * multiplier))
    total = sum(weight for _, weight in weighted)
    roll = random.random() * total
    upto = 0.0
    for rarity, weight in weighted:
        upto += weight
        if roll <= upto:
            return rarity
    return "common"


def generate_loot(owner_id: int, player_level: int = 1, luck: float = 1.0, rarity: Optional[str] = None) -> LootDrop:
    """Generate a loot item scaled by player level and luck."""
    rarity = rarity or roll_rarity(luck)
    rarity_info = next((entry for entry in RARITY_ROLLS if entry[0] == rarity), RARITY_ROLLS[0])
    _name, _weight, min_stat, max_stat = rarity_info
    level_bonus = max(0, int(player_level or 1) // 5)
    item_type = random.choice(TYPE_BY_RARITY.get(rarity, TYPE_BY_RARITY["common"]))
    item = ItemGenerator.generate_item(
        owner_id,
        min_stat=min_stat + level_bonus,
        max_stat=max_stat + level_bonus,
        item_type=item_type,
    )
    item.name = f"{random.choice(PREFIXES[rarity])} {item.type.value} {random.choice(SUFFIXES[rarity])}"
    item.value = int(item.value * (1 + level_bonus * 0.05))
    return LootDrop(
        name=item.name,
        item_type=item.type.value,
        value=item.value,
        damage=item.damage,
        armor=item.armor,
        hand=item.hand.value,
        health_bonus=item.health_bonus,
        speed_bonus=item.speed_bonus,
        luck_bonus=item.luck_bonus,
        crit_bonus=item.crit_bonus,
        magic_bonus=item.magic_bonus,
        slot_type=item.slot_type,
        rarity=rarity,
    )


def loot_summary(drop: LootDrop, item_id: int) -> str:
    """Human-readable loot summary."""
    stats = []
    if drop.damage:
        stats.append(f"{drop.damage} damage")
    if drop.armor:
        stats.append(f"{drop.armor} armor")
    if drop.health_bonus:
        stats.append(f"+{drop.health_bonus} HP")
    if drop.speed_bonus:
        stats.append(f"+{drop.speed_bonus} speed")
    if drop.magic_bonus:
        stats.append(f"+{drop.magic_bonus} magic")
    if drop.crit_bonus:
        stats.append(f"+{drop.crit_bonus:.1%} crit")
    if drop.luck_bonus:
        stats.append(f"+{drop.luck_bonus:.2f} luck")
    stat_text = ", ".join(stats) if stats else "utility item"
    return f"`#{item_id}` **{drop.name}** ({drop.rarity}) — {stat_text}"
