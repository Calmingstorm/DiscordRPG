"""Achievement catalog and unlock evaluation for DiscordRPG."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class Achievement:
    """A single player achievement definition."""

    key: str
    name: str
    description: str
    points: int
    category: str
    icon: str = "🏆"
    hidden: bool = False


ACHIEVEMENTS: tuple[Achievement, ...] = (
    Achievement("first_steps", "First Steps", "Create a character.", 5, "Progression", "🌱"),
    Achievement("level_5", "Awakened", "Reach level 5.", 10, "Progression", "✨"),
    Achievement("level_10", "Veteran", "Reach level 10.", 20, "Progression", "⚔️"),
    Achievement("level_25", "Ascendant", "Reach level 25.", 50, "Progression", "🔥"),
    Achievement("level_50", "Mythic", "Reach level 50.", 100, "Progression", "🌌"),
    Achievement("level_100", "Legend Beyond Death", "Reach level 100.", 250, "Progression", "👑"),
    Achievement("first_adventure", "Road Dust", "Complete your first adventure.", 10, "Adventure", "🗺️"),
    Achievement("adventures_10", "Trail Tested", "Complete 10 adventures.", 25, "Adventure", "🥾"),
    Achievement("adventures_50", "World Walker", "Complete 50 adventures.", 75, "Adventure", "🌍"),
    Achievement("adventures_100", "Cartographer's Nightmare", "Complete 100 adventures.", 150, "Adventure", "🧭"),
    Achievement("first_win", "Blooded", "Win your first PvP battle.", 15, "Combat", "🩸"),
    Achievement("pvp_10", "Arena Regular", "Win 10 PvP battles.", 40, "Combat", "🏟️"),
    Achievement("pvp_50", "Duelist of Ruin", "Win 50 PvP battles.", 120, "Combat", "🗡️"),
    Achievement("gold_1000", "Coin Purse", "Hold 1,000 gold.", 10, "Economy", "💰"),
    Achievement("gold_10000", "Dragon's Favorite Snack", "Hold 10,000 gold.", 40, "Economy", "🐉"),
    Achievement("gold_100000", "Walking Treasury", "Hold 100,000 gold.", 150, "Economy", "🏦"),
    Achievement("daily_3", "Routine Adventurer", "Build a 3-day daily streak.", 15, "Daily", "📅"),
    Achievement("daily_7", "Weekbound", "Build a 7-day daily streak.", 40, "Daily", "🕯️"),
    Achievement("daily_30", "The Grind Has You Now", "Build a 30-day daily streak.", 120, "Daily", "⛓️"),
    Achievement("first_crate", "Box Gremlin", "Own any unopened crate.", 10, "Loot", "📦"),
    Achievement("rare_crate", "Rare Taste", "Own a rare or better crate.", 25, "Loot", "💎"),
    Achievement("choose_god", "Kneel, Apparently", "Choose a god.", 10, "Religion", "🙏"),
    Achievement("divine_favor_100", "Divine Errand Runner", "Reach 100 favor with your god.", 35, "Religion", "⚡"),
)

_BY_KEY = {achievement.key: achievement for achievement in ACHIEVEMENTS}


def get_achievement(key: str) -> Optional[Achievement]:
    """Return an achievement by key."""
    return _BY_KEY.get(key)


def all_achievements() -> tuple[Achievement, ...]:
    """Return every achievement in display order."""
    return ACHIEVEMENTS


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def evaluate_profile(profile: Dict[str, Any], unlocked: Iterable[str] = ()) -> List[Achievement]:
    """Return achievements newly satisfied by a profile snapshot."""
    unlocked_set: Set[str] = set(unlocked)

    level = _int(profile.get("level"), 1)
    completed = _int(profile.get("completed"))
    pvpwins = _int(profile.get("pvpwins"))
    money = _int(profile.get("money"))
    streak = _int(profile.get("streak"))
    favor = _int(profile.get("favor"))
    crates = sum(_int(profile.get(f"crates_{rarity}")) for rarity in ("common", "uncommon", "rare", "magic", "legendary", "mystery"))
    rare_crates = sum(_int(profile.get(f"crates_{rarity}")) for rarity in ("rare", "magic", "legendary", "mystery"))

    checks = {
        "first_steps": True,
        "level_5": level >= 5,
        "level_10": level >= 10,
        "level_25": level >= 25,
        "level_50": level >= 50,
        "level_100": level >= 100,
        "first_adventure": completed >= 1,
        "adventures_10": completed >= 10,
        "adventures_50": completed >= 50,
        "adventures_100": completed >= 100,
        "first_win": pvpwins >= 1,
        "pvp_10": pvpwins >= 10,
        "pvp_50": pvpwins >= 50,
        "gold_1000": money >= 1_000,
        "gold_10000": money >= 10_000,
        "gold_100000": money >= 100_000,
        "daily_3": streak >= 3,
        "daily_7": streak >= 7,
        "daily_30": streak >= 30,
        "first_crate": crates >= 1,
        "rare_crate": rare_crates >= 1,
        "choose_god": bool(profile.get("god")),
        "divine_favor_100": favor >= 100,
    }

    return [achievement for achievement in ACHIEVEMENTS if checks.get(achievement.key, False) and achievement.key not in unlocked_set]


def achievement_points(keys: Iterable[str]) -> int:
    """Calculate total points for a set of achievement keys."""
    return sum(_BY_KEY[key].points for key in keys if key in _BY_KEY)
