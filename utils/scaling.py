"""
XP and reward scaling utilities for DiscordRPG.

This module provides consistent scaling formulas across all game systems.
The design uses:
- Additive base components (tier + difficulty + level + race)
- Content-relative multipliers (rewards scale based on content vs player level)
- Multiplicative blessings applied at the end (for impactful premium buffs)
"""
import math
import random
from typing import Dict, Tuple


def xp_to_next_level(current_level: int) -> int:
    """
    Calculate XP needed to advance from current_level to current_level + 1.

    Based on level formula: level = 1 + int((xp / 100) ** 0.5)
    Therefore: xp = (level - 1)² * 100
    XP for next level = level² * 100 - (level-1)² * 100 = (2*level - 1) * 100

    Args:
        current_level: The player's current level

    Returns:
        int: XP needed to reach next level
    """
    return (2 * current_level - 1) * 100


# Content tier base XP values (+20% boost for better progression feel)
TIER_BASE_XP = {
    'basic': 600,
    'epic': 1080,
    'legendary': 1680,
    'mythic_1': 2400,
    'mythic_2': 3360,
    # Numeric tier multipliers mapped to tiers
    1.0: 600,
    1.5: 1080,
    2.0: 1680,
    3.0: 2400,
    4.0: 3360,
}

# Content tier base gold values
TIER_BASE_GOLD = {
    'basic': 300,
    'epic': 600,
    'legendary': 1000,
    'mythic_1': 1500,
    'mythic_2': 2200,
    1.0: 300,
    1.5: 600,
    2.0: 1000,
    3.0: 1500,
    4.0: 2200,
}


def get_content_relative_multiplier(difficulty: int, player_level: int) -> float:
    """
    Calculate content-relative multiplier based on difficulty vs player level.

    - At-level content (difficulty ~= level): 1.0x rewards
    - Challenging content (difficulty > level): up to 1.4x bonus
    - Outleveled content (difficulty < level): down to 0.3x

    Returns:
        float: Multiplier between 0.3 and 1.4
    """
    relative_difficulty = difficulty / max(1, player_level)

    if relative_difficulty >= 1.0:
        # Challenging content: up to +40% bonus
        return 1 + min(0.4, (relative_difficulty - 1) * 0.4)
    else:
        # Outleveled content: down to 30% effectiveness
        return max(0.3, relative_difficulty)


def get_level_bonus(player_level: int, base_factor: float = 150) -> int:
    """
    Calculate logarithmic level bonus.

    Uses natural log for slow, steady growth that never explodes.

    Args:
        player_level: The player's current level
        base_factor: Scaling factor (default 150)

    Returns:
        int: Additive XP bonus from level
    """
    return int(base_factor * math.log(1 + player_level))


def calculate_xp_reward(
    player_level: int,
    difficulty: int,
    tier,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0,
    difficulty_per_xp: float = 14.4  # +20% boost
) -> int:
    """
    Calculate XP reward using the hybrid scaling system.

    Components (additive):
    1. Base XP from content tier
    2. Difficulty bonus (flat, scales with content)
    3. Level bonus (logarithmic growth)
    4. Race bonus (additive conversion from multiplier)

    Then applied:
    5. Content-relative modifier
    6. Blessing multiplier (multiplicative at end)

    Args:
        player_level: Player's current level
        difficulty: Content difficulty rating
        tier: Content tier (string like 'epic' or float like 2.0)
        race_xp_bonus: Race XP multiplier (e.g., 1.3 for Orc)
        blessing_xp_mult: Blessing multiplier (e.g., 1.75 for Wisdom)
        difficulty_per_xp: XP per difficulty point (default 12)

    Returns:
        int: Final XP reward
    """
    # 1. Base XP from content tier
    base_xp = TIER_BASE_XP.get(tier, 500)

    # 2. Difficulty bonus (flat)
    difficulty_bonus = int(difficulty * difficulty_per_xp)

    # 3. Level bonus (logarithmic)
    level_bonus = get_level_bonus(player_level)

    # 4. Race bonus (converted from multiplier to additive)
    race_addition = int(base_xp * (race_xp_bonus - 1))

    # 5. Content-relative modifier
    content_mult = get_content_relative_multiplier(difficulty, player_level)

    # Combine additive components, apply content modifier
    pre_blessing_xp = int((base_xp + difficulty_bonus + level_bonus + race_addition) * content_mult)

    # 6. Blessing multiplier applied last (multiplicative)
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)  # Always at least 1 XP


def calculate_gold_reward(
    player_level: int,
    difficulty: int,
    tier,
    race_gold_bonus: float = 1.0,
    blessing_gold_mult: float = 1.0,
    difficulty_per_gold: float = 8.0
) -> int:
    """
    Calculate gold reward using the hybrid scaling system.

    Same structure as XP but with gold-specific base values.

    Args:
        player_level: Player's current level
        difficulty: Content difficulty rating
        tier: Content tier (string like 'epic' or float like 2.0)
        race_gold_bonus: Race gold multiplier (e.g., 1.2 for Dwarf)
        blessing_gold_mult: Blessing multiplier (e.g., 1.5 for Prosperity)
        difficulty_per_gold: Gold per difficulty point (default 8)

    Returns:
        int: Final gold reward
    """
    # 1. Base gold from content tier
    base_gold = TIER_BASE_GOLD.get(tier, 300)

    # 2. Difficulty bonus (flat)
    difficulty_bonus = int(difficulty * difficulty_per_gold)

    # 3. Level bonus (logarithmic, lower factor for gold)
    level_bonus = get_level_bonus(player_level, base_factor=100)

    # 4. Race bonus (converted from multiplier to additive)
    race_addition = int(base_gold * (race_gold_bonus - 1))

    # 5. Content-relative modifier
    content_mult = get_content_relative_multiplier(difficulty, player_level)

    # Combine additive components, apply content modifier
    pre_blessing_gold = int((base_gold + difficulty_bonus + level_bonus + race_addition) * content_mult)

    # 6. Blessing multiplier applied last (multiplicative)
    final_gold = int(pre_blessing_gold * blessing_gold_mult)

    return max(1, final_gold)  # Always at least 1 gold


def calculate_battle_xp(
    player_level: int,
    opponent_level: int,
    is_winner: bool,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0,
    battle_type: str = '1v1'
) -> int:
    """
    Calculate battle XP reward.

    Uses opponent level as "difficulty" for content-relative scaling.
    Winners get significantly more than losers.

    Args:
        player_level: Player's current level
        opponent_level: Opponent's level (or average for team battles)
        is_winner: Whether this player won
        race_xp_bonus: Race XP multiplier
        blessing_xp_mult: Blessing multiplier
        battle_type: '1v1', '3v3', '5v5', or '10v10'

    Returns:
        int: Final XP reward
    """
    # Base XP for battles (+20% boost)
    battle_bases = {
        '1v1': (180, 48),      # (winner, loser)
        '3v3': (240, 66),
        '5v5': (336, 90),
        '10v10': (480, 132)
    }
    winner_base, loser_base = battle_bases.get(battle_type, (180, 48))

    base_xp = winner_base if is_winner else loser_base

    # Level bonus (smaller for battles)
    level_bonus = get_level_bonus(player_level, base_factor=50)

    # Race bonus
    race_addition = int(base_xp * (race_xp_bonus - 1))

    # Content-relative: opponent level vs player level
    content_mult = get_content_relative_multiplier(opponent_level, player_level)

    # Combine
    pre_blessing_xp = int((base_xp + level_bonus + race_addition) * content_mult)

    # Blessing
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)


def calculate_raid_xp(
    player_level: int,
    boss_level: int,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0,
    raid_class_mult: float = 1.0
) -> int:
    """
    Calculate raid XP reward per participant.

    Uses boss level to determine tier and as difficulty.

    Args:
        player_level: Player's current level
        boss_level: Raid boss level
        race_xp_bonus: Race XP multiplier
        blessing_xp_mult: Blessing multiplier
        raid_class_mult: Raider class bonus multiplier

    Returns:
        int: Final XP reward
    """
    # Determine tier from boss level
    if boss_level <= 40:
        tier = 'basic'
    elif boss_level <= 100:
        tier = 'epic'
    elif boss_level <= 300:
        tier = 'legendary'
    elif boss_level <= 750:
        tier = 'mythic_1'
    else:
        tier = 'mythic_2'

    # Base from tier
    base_xp = TIER_BASE_XP.get(tier, 500)

    # Boss level as difficulty bonus
    difficulty_bonus = int(boss_level * 8)

    # Level bonus
    level_bonus = get_level_bonus(player_level, base_factor=100)

    # Race bonus
    race_addition = int(base_xp * (race_xp_bonus - 1))

    # Content-relative: boss level vs player level
    content_mult = get_content_relative_multiplier(boss_level, player_level)

    # Combine
    pre_blessing_xp = int((base_xp + difficulty_bonus + level_bonus + race_addition) * content_mult)

    # Raider class bonus (additive to be consistent)
    if raid_class_mult > 1.0:
        pre_blessing_xp = int(pre_blessing_xp * raid_class_mult)

    # Blessing
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)


def calculate_event_xp(
    player_level: int,
    event_type: str,
    is_winner: bool,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0
) -> int:
    """
    Calculate AI event XP reward.

    Group boss victories give 3-5% of XP needed for next level.
    Solo events and losses give smaller, fixed rewards.

    Args:
        player_level: Player's current level
        event_type: 'solo' or 'group'
        is_winner: Whether player succeeded/won
        race_xp_bonus: Race XP multiplier
        blessing_xp_mult: Blessing multiplier

    Returns:
        int: Final XP reward
    """
    xp_needed = xp_to_next_level(player_level)

    if event_type == 'group' and is_winner:
        # Group boss victory: 3-5% of next level (variable)
        percent = random.uniform(0.03, 0.05)
        base_xp = int(xp_needed * percent)
    elif event_type == 'group':
        # Group boss defeat: 1-1.5% consolation
        percent = random.uniform(0.01, 0.015)
        base_xp = int(xp_needed * percent)
    elif is_winner:
        # Solo event win: 1.5-2.5% of next level
        percent = random.uniform(0.015, 0.025)
        base_xp = int(xp_needed * percent)
    else:
        # Solo event loss: 0.5-1% consolation
        percent = random.uniform(0.005, 0.01)
        base_xp = int(xp_needed * percent)

    # Apply race bonus (additive)
    race_addition = int(base_xp * (race_xp_bonus - 1))
    pre_blessing_xp = base_xp + race_addition

    # Blessing multiplier applied last
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)


def calculate_quest_chapter_xp(
    player_level: int,
    chapter_number: int,
    total_chapters: int,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0
) -> int:
    """
    Calculate personal quest chapter XP reward.

    Later chapters give more XP. Final chapter gives bonus.

    Args:
        player_level: Player's current level
        chapter_number: Current chapter (1-indexed)
        total_chapters: Total chapters in quest
        race_xp_bonus: Race XP multiplier
        blessing_xp_mult: Blessing multiplier

    Returns:
        int: Final XP reward
    """
    # Base XP scales with chapter progress
    chapter_mult = 1 + (chapter_number - 1) * 0.25  # 1.0, 1.25, 1.5 for 3 chapters

    # Final chapter bonus
    if chapter_number == total_chapters:
        chapter_mult *= 1.5

    base_xp = int(480 * chapter_mult)  # +20% boost

    # Level bonus
    level_bonus = get_level_bonus(player_level, base_factor=80)

    # Race bonus
    race_addition = int(base_xp * (race_xp_bonus - 1))

    # Quest difficulty scales with player level (at-level content)
    # Give slight bonus for doing quests
    content_mult = 1.1

    # Combine
    pre_blessing_xp = int((base_xp + level_bonus + race_addition) * content_mult)

    # Blessing
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)


def calculate_daily_xp(
    player_level: int,
    streak: int,
    race_xp_bonus: float = 1.0,
    blessing_xp_mult: float = 1.0
) -> int:
    """
    Calculate daily reward XP.

    Streak-based with level bonus for relevance at high levels.

    Args:
        player_level: Player's current level
        streak: Current daily streak (1-10)
        race_xp_bonus: Race XP multiplier
        blessing_xp_mult: Blessing multiplier

    Returns:
        int: Final XP reward
    """
    # Base XP from streak (capped at 10) - +20% boost
    capped_streak = min(10, streak)
    base_xp = 240 + (capped_streak * 96)  # 336 to 1200

    # Level bonus (makes dailies relevant at high levels)
    level_bonus = get_level_bonus(player_level, base_factor=60)

    # Race bonus
    race_addition = int(base_xp * (race_xp_bonus - 1))

    # Dailies are always "at-level" (no content-relative modifier)

    # Combine
    pre_blessing_xp = base_xp + level_bonus + race_addition

    # Blessing
    final_xp = int(pre_blessing_xp * blessing_xp_mult)

    return max(1, final_xp)


def get_tier_from_difficulty(difficulty: int) -> float:
    """
    Determine content tier multiplier from difficulty level.

    Args:
        difficulty: Content difficulty rating

    Returns:
        float: Tier multiplier (1.0, 1.5, 2.0, 3.0, or 4.0)
    """
    if difficulty <= 15:
        return 1.0    # Basic
    elif difficulty <= 25:
        return 1.5    # Epic
    elif difficulty <= 50:
        return 2.0    # Legendary
    elif difficulty <= 100:
        return 3.0    # Mythic 1
    else:
        return 4.0    # Mythic 2
