"""Character classes and race system"""
from enum import Enum
from typing import Dict, Optional, Tuple
import math

class CharacterClass(Enum):
    """All character classes with their evolution paths"""
    # Base classes
    NOVICE = "Novice"
    
    # Warrior path
    WARRIOR = "Warrior"
    SWORDSMAN = "Swordsman"
    KNIGHT = "Knight"
    WARLORD = "Warlord"
    BERSERKER = "Berserker"
    PALADIN = "Paladin"
    
    # Thief path
    THIEF = "Thief"
    ROGUE = "Rogue"
    ASSASSIN = "Assassin"
    BANDIT = "Bandit"
    SHADOW = "Shadow"
    NIGHTBLADE = "Nightblade"
    
    # Mage path
    MAGE = "Mage"
    WIZARD = "Wizard"
    WARLOCK = "Warlock"
    SORCERER = "Sorcerer"
    ARCHMAGE = "Archmage"
    NECROMANCER = "Necromancer"
    
    # Ranger path
    RANGER = "Ranger"
    HUNTER = "Hunter"
    TRACKER = "Tracker"
    BOWMASTER = "Bowmaster"
    BEASTMASTER = "Beastmaster"
    MARKSMAN = "Marksman"
    
    # Raider path
    RAIDER = "Raider"
    VIKING = "Viking"
    CHIEFTAIN = "Chieftain"
    RAVAGER = "Ravager"
    CONQUEROR = "Conqueror"
    WARCHIEF = "Warchief"
    
    # Ritualist path
    RITUALIST = "Ritualist"
    MYSTIC = "Mystic"
    SHAMAN = "Shaman"
    ORACLE = "Oracle"
    SAGE = "Sage"
    PROPHET = "Prophet"
    
    # Paragon (Premium)
    PARAGON = "Paragon"
    CHAMPION = "Champion"
    HERO = "Hero"
    LEGEND = "Legend"
    ETERNAL = "Eternal"
    IMMORTAL = "Immortal"

class Race(Enum):
    """Available races with their bonuses"""
    HUMAN = "Human"          # Balanced and adaptable
    ELF = "Elf"              # Enhanced luck and divine favor
    DWARF = "Dwarf"          # Gold finding specialists
    ORC = "Orc"              # Fast XP gain through combat
    HALFLING = "Halfling"    # Ultimate luck
    GNOME = "Gnome"          # Luck and divine balance
    DRAGONBORN = "Dragonborn" # Well-rounded abilities
    TIEFLING = "Tiefling"    # Luck and gold, reduced divine favor
    UNDEAD = "Undead"        # Supernatural luck, no divine favor
    DEMON = "Demon"          # Maximum luck and gold, no divine favor

class ClassEvolution:
    """Handles class evolution paths and requirements"""
    
    # Evolution paths: current class -> (evolution options at each tier)
    EVOLUTION_PATHS = {
        # Tier 1 (Level 5)
        CharacterClass.NOVICE: [
            CharacterClass.WARRIOR,
            CharacterClass.THIEF,
            CharacterClass.MAGE,
            CharacterClass.RANGER,
            CharacterClass.RAIDER,
            CharacterClass.RITUALIST,
            CharacterClass.PARAGON  # Premium only
        ],
        
        # Tier 2 (Level 10)
        CharacterClass.WARRIOR: [CharacterClass.SWORDSMAN, CharacterClass.KNIGHT],
        CharacterClass.THIEF: [CharacterClass.ROGUE, CharacterClass.ASSASSIN],
        CharacterClass.MAGE: [CharacterClass.WIZARD, CharacterClass.WARLOCK],
        CharacterClass.RANGER: [CharacterClass.HUNTER, CharacterClass.TRACKER],
        CharacterClass.RAIDER: [CharacterClass.VIKING, CharacterClass.CHIEFTAIN],
        CharacterClass.RITUALIST: [CharacterClass.MYSTIC, CharacterClass.SHAMAN],
        CharacterClass.PARAGON: [CharacterClass.CHAMPION],
        
        # Tier 3 (Level 15)
        CharacterClass.SWORDSMAN: [CharacterClass.WARLORD],
        CharacterClass.KNIGHT: [CharacterClass.PALADIN],
        CharacterClass.ROGUE: [CharacterClass.BANDIT],
        CharacterClass.ASSASSIN: [CharacterClass.SHADOW],
        CharacterClass.WIZARD: [CharacterClass.SORCERER],
        CharacterClass.WARLOCK: [CharacterClass.NECROMANCER],
        CharacterClass.HUNTER: [CharacterClass.BOWMASTER],
        CharacterClass.TRACKER: [CharacterClass.BEASTMASTER],
        CharacterClass.VIKING: [CharacterClass.RAVAGER],
        CharacterClass.CHIEFTAIN: [CharacterClass.CONQUEROR],
        CharacterClass.MYSTIC: [CharacterClass.ORACLE],
        CharacterClass.SHAMAN: [CharacterClass.SAGE],
        CharacterClass.CHAMPION: [CharacterClass.HERO],
        
        # Tier 4 (Level 20)
        CharacterClass.WARLORD: [CharacterClass.BERSERKER],
        CharacterClass.PALADIN: [CharacterClass.BERSERKER],  # Alternative path
        CharacterClass.BANDIT: [CharacterClass.NIGHTBLADE],
        CharacterClass.SHADOW: [CharacterClass.NIGHTBLADE],  # Alternative path
        CharacterClass.SORCERER: [CharacterClass.ARCHMAGE],
        CharacterClass.NECROMANCER: [CharacterClass.ARCHMAGE],  # Alternative path
        CharacterClass.BOWMASTER: [CharacterClass.MARKSMAN],
        CharacterClass.BEASTMASTER: [CharacterClass.MARKSMAN],  # Alternative path
        CharacterClass.RAVAGER: [CharacterClass.WARCHIEF],
        CharacterClass.CONQUEROR: [CharacterClass.WARCHIEF],  # Alternative path
        CharacterClass.ORACLE: [CharacterClass.PROPHET],
        CharacterClass.SAGE: [CharacterClass.PROPHET],  # Alternative path
        CharacterClass.HERO: [CharacterClass.LEGEND],
        
        # Tier 5 (Level 25)
        CharacterClass.BERSERKER: [CharacterClass.ETERNAL],
        CharacterClass.NIGHTBLADE: [CharacterClass.ETERNAL],
        CharacterClass.ARCHMAGE: [CharacterClass.ETERNAL],
        CharacterClass.MARKSMAN: [CharacterClass.ETERNAL],
        CharacterClass.WARCHIEF: [CharacterClass.ETERNAL],
        CharacterClass.PROPHET: [CharacterClass.ETERNAL],
        CharacterClass.LEGEND: [CharacterClass.ETERNAL],
        
        # Tier 6 (Level 30)
        CharacterClass.ETERNAL: [CharacterClass.IMMORTAL],
    }
    
    @staticmethod
    def can_evolve(level: int) -> bool:
        """Check if a character can evolve at their level"""
        # Can evolve if level is at or above an evolution threshold
        return level >= 5
    
    @staticmethod
    def get_evolutions(current_class: CharacterClass) -> list[CharacterClass]:
        """Get available evolution options for a class"""
        return ClassEvolution.EVOLUTION_PATHS.get(current_class, [])

class ClassStats:
    """Class-specific stat bonuses and abilities"""
    
    @staticmethod
    def get_class_bonuses(char_class: CharacterClass, level: int) -> Dict[str, float]:
        """Get stat bonuses for a specific class"""
        bonuses = {
            "attack_mult": 1.0,
            "defense_mult": 1.0,
            "magic_mult": 1.0,
            "speed_mult": 1.0,
            "luck_mult": 1.0,
            "raid_mult": 1.0,
            "steal_chance": 0.0,
            "crit_chance": 0.05,
            "dodge_chance": 0.05,
            "lifesteal": 0.0,
            "favor_mult": 1.0
        }
        
        # Evolution tier (0-6)
        tier = 0
        if level >= 30:
            tier = 6
        elif level >= 25:
            tier = 5
        elif level >= 20:
            tier = 4
        elif level >= 15:
            tier = 3
        elif level >= 10:
            tier = 2
        elif level >= 5:
            tier = 1
            
        # Warrior line - Defense focused
        if char_class.value.endswith(("Warrior", "Swordsman", "Knight", "Warlord", "Berserker", "Paladin")):
            bonuses["defense_mult"] += 0.1 * tier
            bonuses["attack_mult"] += 0.05 * tier
            if "Berserker" in char_class.value:
                bonuses["attack_mult"] += 0.2
                bonuses["lifesteal"] = 0.15
            elif "Paladin" in char_class.value:
                bonuses["defense_mult"] += 0.2
                bonuses["magic_mult"] += 0.1
                
        # Thief line - Steal and crit focused
        elif char_class.value.endswith(("Thief", "Rogue", "Assassin", "Bandit", "Shadow", "Nightblade")):
            bonuses["steal_chance"] = 0.08 * tier
            bonuses["crit_chance"] += 0.05 * tier
            bonuses["dodge_chance"] += 0.03 * tier
            bonuses["speed_mult"] += 0.1 * tier
            if "Assassin" in char_class.value:
                bonuses["crit_chance"] += 0.15
            elif "Shadow" in char_class.value:
                bonuses["dodge_chance"] += 0.2
                
        # Mage line - Magic damage focused
        elif char_class.value.endswith(("Mage", "Wizard", "Warlock", "Sorcerer", "Archmage", "Necromancer")):
            bonuses["magic_mult"] += 0.15 * tier
            bonuses["attack_mult"] += 0.1 * tier
            if "Necromancer" in char_class.value:
                bonuses["lifesteal"] = 0.2
            elif "Archmage" in char_class.value:
                bonuses["magic_mult"] += 0.3
                
        # Ranger line - Pet and item bonuses
        elif char_class.value.endswith(("Ranger", "Hunter", "Tracker", "Bowmaster", "Beastmaster", "Marksman")):
            bonuses["attack_mult"] += 0.08 * tier
            bonuses["speed_mult"] += 0.12 * tier
            bonuses["luck_mult"] += 0.05 * tier
            if "Marksman" in char_class.value:
                bonuses["crit_chance"] += 0.25
                
        # Raider line - Raid focused
        elif char_class.value.endswith(("Raider", "Viking", "Chieftain", "Ravager", "Conqueror", "Warchief")):
            bonuses["raid_mult"] += 0.1 * tier
            bonuses["attack_mult"] += 0.12 * tier
            if "Warchief" in char_class.value:
                bonuses["raid_mult"] += 0.3
                
        # Ritualist line - Favor focused
        elif char_class.value.endswith(("Ritualist", "Mystic", "Shaman", "Oracle", "Sage", "Prophet")):
            bonuses["favor_mult"] += 0.05 * tier
            bonuses["magic_mult"] += 0.08 * tier
            bonuses["luck_mult"] += 0.03 * tier
            if "Prophet" in char_class.value:
                bonuses["favor_mult"] += 0.3
                bonuses["luck_mult"] += 0.2
                
        # Paragon line - All-rounder premium class
        elif char_class.value.endswith(("Paragon", "Champion", "Hero", "Legend", "Eternal", "Immortal")):
            bonuses["attack_mult"] += 0.1 * tier
            bonuses["defense_mult"] += 0.1 * tier
            bonuses["magic_mult"] += 0.05 * tier
            bonuses["speed_mult"] += 0.05 * tier
            bonuses["luck_mult"] += 0.02 * tier
            bonuses["raid_mult"] += 0.05 * tier
            if "Immortal" in char_class.value:
                bonuses["lifesteal"] = 0.1
                bonuses["dodge_chance"] += 0.1
                
        return bonuses

class RaceStats:
    """Race-specific stat bonuses"""
    
    @staticmethod
    def get_race_bonuses(race: Race) -> Dict[str, float]:
        """Get stat bonuses for a specific race"""
        bonuses = {
            "hp_bonus": 0,
            "attack_bonus": 0,
            "defense_bonus": 0,
            "magic_bonus": 0,
            "speed_bonus": 0,
            "luck_bonus": 0,
            "xp_mult": 1.0,
            "gold_mult": 1.0
        }
        
        if race == Race.HUMAN:
            # Balanced and adaptable - small XP bonus
            bonuses["xp_mult"] = 1.1
            
        elif race == Race.ELF:
            # Enhanced luck and divine favor
            bonuses["luck_bonus"] = 2
            bonuses["magic_bonus"] = 3
            bonuses["gold_mult"] = 0.9
            
        elif race == Race.DWARF:
            # Gold finding specialists
            bonuses["defense_bonus"] = 2
            bonuses["gold_mult"] = 1.4
            bonuses["speed_bonus"] = -1
            
        elif race == Race.ORC:
            # Fast XP gain through combat
            bonuses["attack_bonus"] = 3
            bonuses["xp_mult"] = 1.3
            bonuses["luck_bonus"] = -2
            
        elif race == Race.HALFLING:
            # Ultimate luck
            bonuses["luck_bonus"] = 4
            bonuses["gold_mult"] = 1.1
            bonuses["xp_mult"] = 0.8
            
        elif race == Race.GNOME:
            # Luck and divine balance
            bonuses["luck_bonus"] = 3
            bonuses["magic_bonus"] = 2
            bonuses["xp_mult"] = 0.9
            
        elif race == Race.DRAGONBORN:
            # Well-rounded abilities
            bonuses["attack_bonus"] = 1
            bonuses["defense_bonus"] = 1
            bonuses["xp_mult"] = 1.1
            bonuses["gold_mult"] = 1.1
            
        elif race == Race.TIEFLING:
            # Luck and gold, reduced divine favor
            bonuses["luck_bonus"] = 2
            bonuses["magic_bonus"] = 2
            bonuses["gold_mult"] = 1.2
            
        elif race == Race.UNDEAD:
            # Supernatural luck, no divine favor
            bonuses["luck_bonus"] = 5
            bonuses["hp_bonus"] = -10
            bonuses["xp_mult"] = 0.7
            
        elif race == Race.DEMON:
            # Maximum luck and gold, no divine favor
            bonuses["luck_bonus"] = 6
            bonuses["gold_mult"] = 1.3
            bonuses["xp_mult"] = 0.8
            
        return bonuses

class Character:
    """Complete character with all stats and progression"""
    
    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name
        self.char_class = CharacterClass.NOVICE
        self.race = Race.HUMAN
        self.level = 1
        self.xp = 0
        self.money = 100
        
        # Base stats
        self.hp = 100
        self.max_hp = 100
        self.base_attack = 10
        self.base_defense = 10
        self.base_magic = 10
        self.base_speed = 10
        self.luck = 1.0
        
        # Combat stats
        self.pvp_wins = 0
        self.pvp_losses = 0
        self.kills = 0
        self.deaths = 0
        
        # Social
        self.marriage_id = None
        self.guild_id = None
        
        # Religion
        self.god = None
        self.favor = 0
        
        # Other
        self.reset_points = 2
        self.raid_stats = 0
        self.completed_adventures = 0
        self.description = ""
        self.background_url = "https://i.imgur.com/default.png"
        self.color = 0x000000
        
    @property
    def xp_required(self) -> int:
        """XP required for next level"""
        # Using the same formula as the actual leveling system: level = 1 + int((xp / 100) ** 0.5)
        # So next_level_xp = ((current_level) ** 2) * 100
        return (self.level ** 2) * 100
    
    @property
    def total_stats(self) -> Dict[str, float]:
        """Calculate total stats including class and race bonuses"""
        # Get bonuses
        class_bonuses = ClassStats.get_class_bonuses(self.char_class, self.level)
        race_bonuses = RaceStats.get_race_bonuses(self.race)
        
        # Calculate final stats
        stats = {
            "hp": self.max_hp + race_bonuses["hp_bonus"],
            "attack": int((self.base_attack + race_bonuses["attack_bonus"]) * class_bonuses["attack_mult"]),
            "defense": int((self.base_defense + race_bonuses["defense_bonus"]) * class_bonuses["defense_mult"]),
            "magic": int((self.base_magic + race_bonuses["magic_bonus"]) * class_bonuses["magic_mult"]),
            "speed": int((self.base_speed + race_bonuses["speed_bonus"]) * class_bonuses["speed_mult"]),
            "luck": self.luck * class_bonuses["luck_mult"] + (race_bonuses["luck_bonus"] / 100),
            "raid_power": int(self.raid_stats * class_bonuses["raid_mult"]),
            "steal_chance": class_bonuses["steal_chance"],
            "crit_chance": class_bonuses["crit_chance"],
            "dodge_chance": class_bonuses["dodge_chance"],
            "lifesteal": class_bonuses["lifesteal"],
            "favor_mult": class_bonuses["favor_mult"],
            "xp_mult": race_bonuses["xp_mult"],
            "gold_mult": race_bonuses["gold_mult"]
        }
        
        return stats
    
    def gain_xp(self, amount: int) -> Tuple[bool, int]:
        """Gain XP and check for level up. Returns (leveled_up, levels_gained)"""
        stats = self.total_stats
        actual_xp = int(amount * stats["xp_mult"])
        self.xp += actual_xp
        
        levels_gained = 0
        while self.xp >= self.xp_required:
            self.xp -= self.xp_required
            self.level += 1
            levels_gained += 1
            
            # Stat increases on level up
            self.max_hp += 10
            self.hp = self.max_hp
            self.base_attack += 2
            self.base_defense += 2
            self.base_magic += 1
            self.base_speed += 1
            
        return levels_gained > 0, levels_gained
    
    def can_evolve(self) -> bool:
        """Check if character can evolve their class"""
        return ClassEvolution.can_evolve(self.level)
    
    def get_evolution_options(self) -> list[CharacterClass]:
        """Get available class evolution options"""
        return ClassEvolution.get_evolutions(self.char_class)
    
    def evolve_class(self, new_class: CharacterClass) -> bool:
        """Evolve to a new class if valid"""
        if new_class in self.get_evolution_options():
            self.char_class = new_class
            return True
        return False
    
    def change_race(self, new_race: Race) -> bool:
        """Change race (costs a reset point)"""
        if self.reset_points > 0:
            self.race = new_race
            self.reset_points -= 1
            return True
        return False