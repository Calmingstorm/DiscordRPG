"""Item system with types, stats, and equipment handling"""
from enum import Enum
from typing import Dict, Optional, Tuple, List, Any
import random
import math

class ItemType(Enum):
    """All available item types"""
    # Weapons
    SWORD = "Sword"
    SHIELD = "Shield"
    AXE = "Axe"
    BOW = "Bow"
    SPEAR = "Spear"
    WAND = "Wand"
    DAGGER = "Dagger"
    KNIFE = "Knife"
    HAMMER = "Hammer"
    STAFF = "Staff"
    MACE = "Mace"
    CROSSBOW = "Crossbow"
    GREATSWORD = "Greatsword"
    HALBERD = "Halberd"
    KATANA = "Katana"
    SCYTHE = "Scythe"
    
    # Armor
    HELMET = "Helmet"
    CHESTPLATE = "Chestplate"
    LEGGINGS = "Leggings"
    GAUNTLETS = "Gauntlets"
    BOOTS = "Boots"

class ItemHand(Enum):
    """Which hand(s) an item can be equipped in"""
    LEFT = "left"
    RIGHT = "right"
    BOTH = "both"
    ANY = "any"

class ItemRarity(Enum):
    """Item rarity tiers for crates and drops"""
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    MAGIC = "magic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    DIVINE = "divine"
    
    @staticmethod
    def get_stat_range(rarity: 'ItemRarity') -> Tuple[int, int]:
        """Get (min, max) stat total for a rarity tier"""
        ranges = {
            ItemRarity.COMMON: (1, 9),
            ItemRarity.UNCOMMON: (10, 19),
            ItemRarity.RARE: (20, 29),
            ItemRarity.MAGIC: (30, 39),
            ItemRarity.LEGENDARY: (40, 44),
            ItemRarity.MYTHIC: (45, 49),
            ItemRarity.DIVINE: (50, 50)
        }
        return ranges.get(rarity, (1, 9))
    
    @staticmethod
    def get_material_tier(rarity: 'ItemRarity') -> str:
        """Get material type for dismantling/crafting based on rarity"""
        if rarity in [ItemRarity.COMMON, ItemRarity.UNCOMMON]:
            return 'scrap'
        elif rarity in [ItemRarity.RARE, ItemRarity.MAGIC]:
            return 'dust'
        else:  # LEGENDARY, MYTHIC, DIVINE
            return 'essence'

class Item:
    """Represents a single item with stats"""
    
    def __init__(self, item_id: int, owner_id: int, name: str, item_type: ItemType, 
                 value: int = 0, damage: int = 0, armor: int = 0, 
                 hand: ItemHand = ItemHand.ANY, equipped: bool = False,
                 health_bonus: int = 0, speed_bonus: int = 0, luck_bonus: float = 0.0,
                 crit_bonus: float = 0.0, magic_bonus: int = 0, slot_type: Optional[str] = None,
                 upgrade_level: int = 0):
        self.id = item_id
        self.owner_id = owner_id
        self.name = name
        self.type = item_type
        self.value = value
        self.damage = damage
        self.armor = armor
        self.hand = hand
        self.equipped = equipped
        
        # New armor stats
        self.health_bonus = health_bonus
        self.speed_bonus = speed_bonus
        self.luck_bonus = luck_bonus
        self.crit_bonus = crit_bonus
        self.magic_bonus = magic_bonus
        self.slot_type = slot_type
        self.upgrade_level = upgrade_level
    
    def _get_upgrade_multiplier(self) -> float:
        """Get stat multiplier based on upgrade level"""
        return 1.0 + (0.05 * self.upgrade_level)
    
    @property
    def effective_damage(self) -> int:
        """Damage with upgrade bonus applied"""
        return int(self.damage * self._get_upgrade_multiplier())
    
    @property
    def effective_armor(self) -> int:
        """Armor with upgrade bonus applied"""
        return int(self.armor * self._get_upgrade_multiplier())
    
    @property
    def effective_health_bonus(self) -> int:
        """Health bonus with upgrade bonus applied"""
        return int(self.health_bonus * self._get_upgrade_multiplier())
    
    @property
    def effective_speed_bonus(self) -> int:
        """Speed bonus with upgrade bonus applied"""
        return int(self.speed_bonus * self._get_upgrade_multiplier())
    
    @property
    def effective_luck_bonus(self) -> float:
        """Luck bonus with upgrade bonus applied"""
        return self.luck_bonus * self._get_upgrade_multiplier()
    
    @property
    def effective_crit_bonus(self) -> float:
        """Crit bonus with upgrade bonus applied"""
        return self.crit_bonus * self._get_upgrade_multiplier()
    
    @property
    def effective_magic_bonus(self) -> int:
        """Magic bonus with upgrade bonus applied"""
        return int(self.magic_bonus * self._get_upgrade_multiplier())
        
    @property
    def stat_total(self) -> int:
        """Total stats (damage + armor + all bonuses)"""
        return (self.damage + self.armor + self.health_bonus + self.speed_bonus + 
                int(self.luck_bonus * 100) + int(self.crit_bonus * 100) + self.magic_bonus)
    
    @property
    def rarity(self) -> ItemRarity:
        """Determine rarity based on stat total"""
        total = self.stat_total
        if total >= 50:
            return ItemRarity.DIVINE
        elif total >= 45:
            return ItemRarity.MYTHIC
        elif total >= 40:
            return ItemRarity.LEGENDARY
        elif total >= 30:
            return ItemRarity.MAGIC
        elif total >= 20:
            return ItemRarity.RARE
        elif total >= 10:
            return ItemRarity.UNCOMMON
        else:
            return ItemRarity.COMMON
    
    def get_sell_price(self) -> int:
        """Calculate item sell price"""
        base_price = self.value if self.value > 0 else 100
        stat_bonus = self.stat_total * 50
        rarity_mult = {
            ItemRarity.COMMON: 1.0,
            ItemRarity.UNCOMMON: 1.5,
            ItemRarity.RARE: 2.0,
            ItemRarity.MAGIC: 3.0,
            ItemRarity.LEGENDARY: 5.0,
            ItemRarity.MYTHIC: 10.0,
            ItemRarity.DIVINE: 20.0
        }
        return int(base_price + stat_bonus * rarity_mult[self.rarity])

class ItemGenerator:
    """Generates random items with appropriate stats"""
    
    # Item name prefixes based on stats
    DAMAGE_PREFIXES = [
        "Sharp", "Deadly", "Vicious", "Brutal", "Savage",
        "Piercing", "Slashing", "Crushing", "Devastating",
        "Bloodthirsty", "Merciless", "Cruel", "Fierce"
    ]
    
    ARMOR_PREFIXES = [
        "Sturdy", "Fortified", "Hardened", "Protective",
        "Defensive", "Guardian", "Shielding", "Warding",
        "Impenetrable", "Unbreaking", "Stalwart", "Resolute"
    ]
    
    MIXED_PREFIXES = [
        "Balanced", "Versatile", "Adaptive", "Dynamic",
        "Harmonious", "Unified", "Complete", "Perfect"
    ]
    
    LEGENDARY_PREFIXES = [
        "Ancient", "Mythical", "Legendary", "Epic", "Divine",
        "Celestial", "Infernal", "Eternal", "Immortal",
        "Primordial", "Forgotten", "Lost", "Sacred"
    ]
    
    # Base names for different item types
    BASE_NAMES = {
        # Weapons
        ItemType.SWORD: ["Blade", "Edge", "Sword", "Saber", "Cutlass"],
        ItemType.AXE: ["Axe", "Hatchet", "Cleaver", "Chopper"],
        ItemType.HAMMER: ["Hammer", "Maul", "Mallet", "Crusher"],
        ItemType.BOW: ["Bow", "Longbow", "Shortbow", "Recurve"],
        ItemType.STAFF: ["Staff", "Rod", "Scepter", "Cane"],
        ItemType.SHIELD: ["Shield", "Buckler", "Aegis", "Guard"],
        ItemType.DAGGER: ["Dagger", "Knife", "Stiletto", "Dirk"],
        ItemType.SPEAR: ["Spear", "Pike", "Lance", "Javelin"],
        ItemType.WAND: ["Wand", "Focus", "Catalyst", "Channel"],
        ItemType.MACE: ["Mace", "Morningstar", "Flail", "Club"],
        ItemType.KNIFE: ["Knife", "Blade", "Cutter", "Razor"],
        ItemType.CROSSBOW: ["Crossbow", "Arbalest", "Ballista"],
        ItemType.GREATSWORD: ["Greatsword", "Claymore", "Zweihander"],
        ItemType.HALBERD: ["Halberd", "Poleaxe", "Partisan"],
        ItemType.KATANA: ["Katana", "Wakizashi", "Nodachi"],
        ItemType.SCYTHE: ["Scythe", "Reaper", "Harvester"],
        
        # Armor
        ItemType.HELMET: ["Helmet", "Crown", "Circlet", "Helm", "Coif"],
        ItemType.CHESTPLATE: ["Chestplate", "Breastplate", "Cuirass", "Vest", "Mail"],
        ItemType.LEGGINGS: ["Leggings", "Greaves", "Pants", "Chausses", "Legguards"],
        ItemType.GAUNTLETS: ["Gauntlets", "Gloves", "Mittens", "Handguards", "Bracers"],
        ItemType.BOOTS: ["Boots", "Shoes", "Sabatons", "Footguards", "Treads"]
    }
    
    @staticmethod
    def get_slot_for_type(item_type: ItemType) -> str:
        """Determine which slot an item type goes into"""
        slot_mapping = {
            # Weapons
            ItemType.SWORD: 'weapon', ItemType.AXE: 'weapon', ItemType.HAMMER: 'weapon',
            ItemType.MACE: 'weapon', ItemType.DAGGER: 'weapon', ItemType.KNIFE: 'weapon',
            ItemType.SPEAR: 'weapon', ItemType.WAND: 'weapon', ItemType.STAFF: 'weapon',
            ItemType.BOW: 'weapon', ItemType.CROSSBOW: 'weapon', ItemType.GREATSWORD: 'weapon',
            ItemType.HALBERD: 'weapon', ItemType.KATANA: 'weapon', ItemType.SCYTHE: 'weapon',
            
            # Shield
            ItemType.SHIELD: 'shield',
            
            # Armor
            ItemType.HELMET: 'head',
            ItemType.CHESTPLATE: 'chest', 
            ItemType.LEGGINGS: 'legs',
            ItemType.GAUNTLETS: 'hands',
            ItemType.BOOTS: 'feet'
        }
        return slot_mapping.get(item_type, 'weapon')

    @staticmethod
    def get_hand_for_type(item_type: ItemType) -> ItemHand:
        """Determine which hand(s) an item type uses"""
        two_handed = [
            ItemType.GREATSWORD, ItemType.BOW, ItemType.CROSSBOW,
            ItemType.STAFF, ItemType.HALBERD, ItemType.SCYTHE
        ]
        left_only = [ItemType.SHIELD]
        
        if item_type in two_handed:
            return ItemHand.BOTH
        elif item_type in left_only:
            return ItemHand.LEFT
        else:
            return ItemHand.ANY
    
    @staticmethod
    def get_type_stats(item_type: ItemType) -> Dict[str, float]:
        """Get stat distribution for item type"""
        # For weapons - damage and armor ratios
        weapon_stats = {
            # Pure damage
            ItemType.SWORD: {'damage': 0.8, 'armor': 0.2},
            ItemType.AXE: {'damage': 0.9, 'armor': 0.1},
            ItemType.DAGGER: {'damage': 0.85, 'armor': 0.15},
            ItemType.SPEAR: {'damage': 0.75, 'armor': 0.25},
            ItemType.KATANA: {'damage': 0.9, 'armor': 0.1},
            ItemType.SCYTHE: {'damage': 0.95, 'armor': 0.05},
            
            # Balanced
            ItemType.HAMMER: {'damage': 0.6, 'armor': 0.4},
            ItemType.MACE: {'damage': 0.65, 'armor': 0.35},
            ItemType.KNIFE: {'damage': 0.7, 'armor': 0.3},
            
            # Range focused
            ItemType.BOW: {'damage': 0.85, 'armor': 0.15},
            ItemType.CROSSBOW: {'damage': 0.9, 'armor': 0.1},
            
            # Magic focused
            ItemType.WAND: {'damage': 0.8, 'armor': 0.2},
            ItemType.STAFF: {'damage': 0.7, 'armor': 0.3},
            
            # Defense focused
            ItemType.SHIELD: {'damage': 0.1, 'armor': 0.9},
            
            # Heavy weapons
            ItemType.GREATSWORD: {'damage': 0.85, 'armor': 0.15},
            ItemType.HALBERD: {'damage': 0.8, 'armor': 0.2},
        }
        
        # For armor - only armor/health/speed/luck/crit/magic (NO damage for armor!)
        armor_stats = {
            # Head armor - luck and magic focused
            ItemType.HELMET: {'armor': 0.4, 'luck': 0.3, 'magic': 0.2, 'health': 0.1},
            
            # Chest armor - health and armor focused  
            ItemType.CHESTPLATE: {'armor': 0.5, 'health': 0.4, 'speed': 0.1},
            
            # Leg armor - armor and health focused
            ItemType.LEGGINGS: {'armor': 0.6, 'health': 0.3, 'speed': 0.1},
            
            # Hand armor - crit and speed focused
            ItemType.GAUNTLETS: {'armor': 0.3, 'crit': 0.4, 'speed': 0.2, 'magic': 0.1},
            
            # Foot armor - speed and armor focused  
            ItemType.BOOTS: {'armor': 0.4, 'speed': 0.4, 'luck': 0.2}
        }
        
        return armor_stats.get(item_type, weapon_stats.get(item_type, {'damage': 0.5, 'armor': 0.5}))
    
    @staticmethod
    def generate_item(owner_id: int, min_stat: int = 4, max_stat: int = 50, 
                      item_type: Optional[ItemType] = None,
                      rarity: Optional[ItemRarity] = None) -> Item:
        """Generate a random item with stats"""
        # Choose random type if not specified
        if item_type is None:
            item_type = random.choice(list(ItemType))
            
        # Determine stat range based on rarity if specified
        if rarity is not None:
            stat_ranges = {
                ItemRarity.COMMON: (1, 9),
                ItemRarity.UNCOMMON: (10, 19),
                ItemRarity.RARE: (20, 29),
                ItemRarity.MAGIC: (30, 39),
                ItemRarity.LEGENDARY: (40, 44),
                ItemRarity.MYTHIC: (45, 49),
                ItemRarity.DIVINE: (50, 50)
            }
            min_stat, max_stat = stat_ranges[rarity]
            
        # Generate total stats (ensure minimum 4 to be better than starter gear)
        total_stats = random.randint(max(4, min_stat), max_stat)
        
        # Get stat distribution for this item type
        stat_ratios = ItemGenerator.get_type_stats(item_type)
        
        # Initialize all stats
        damage = 0
        armor = 0
        health_bonus = 0
        speed_bonus = 0
        luck_bonus = 0.0
        crit_bonus = 0.0
        magic_bonus = 0
        
        # Distribute stats based on item type
        for stat, ratio in stat_ratios.items():
            allocated_points = int(total_stats * ratio)
            
            if stat == 'damage':
                damage = allocated_points
            elif stat == 'armor':
                armor = allocated_points
            elif stat == 'health':
                health_bonus = allocated_points
            elif stat == 'speed':
                speed_bonus = allocated_points
            elif stat == 'luck':
                luck_bonus = allocated_points / 100.0  # Convert to percentage
            elif stat == 'crit':
                crit_bonus = allocated_points / 100.0  # Convert to percentage  
            elif stat == 'magic':
                magic_bonus = allocated_points
        
        # Generate name
        name = ItemGenerator.generate_name(item_type, damage, armor, total_stats)
        
        # Determine hand and slot
        hand = ItemGenerator.get_hand_for_type(item_type)
        slot_type = ItemGenerator.get_slot_for_type(item_type)
        
        # Calculate value
        value = total_stats * random.randint(80, 120)
        
        return Item(
            item_id=0,  # Will be assigned by database
            owner_id=owner_id,
            name=name,
            item_type=item_type,
            value=value,
            damage=damage,
            armor=armor,
            hand=hand,
            equipped=False,
            health_bonus=health_bonus,
            speed_bonus=speed_bonus,
            luck_bonus=luck_bonus,
            crit_bonus=crit_bonus,
            magic_bonus=magic_bonus,
            slot_type=slot_type
        )
    
    @staticmethod
    def generate_name(item_type: ItemType, damage: int, armor: int, total: int) -> str:
        """Generate an appropriate name for an item"""
        # Choose prefix based on stats
        if total >= 40:
            prefix = random.choice(ItemGenerator.LEGENDARY_PREFIXES)
        elif damage > armor * 2:
            prefix = random.choice(ItemGenerator.DAMAGE_PREFIXES)
        elif armor > damage * 2:
            prefix = random.choice(ItemGenerator.ARMOR_PREFIXES)
        else:
            prefix = random.choice(ItemGenerator.MIXED_PREFIXES)
            
        # Get base name
        base_names = ItemGenerator.BASE_NAMES.get(
            item_type, 
            [item_type.value]
        )
        base_name = random.choice(base_names)
        
        # Add suffix for high-tier items
        if total >= 45:
            suffixes = [
                "of Power", "of Legends", "of the Gods", "of Eternity",
                "of Destruction", "of Protection", "of the Ancients"
            ]
            return f"{prefix} {base_name} {random.choice(suffixes)}"
        else:
            return f"{prefix} {base_name}"

    @staticmethod
    def generate_armor(owner_id: int, slot: str, min_stat: int = 4, max_stat: int = 50) -> Item:
        """Generate armor for specific slot"""
        armor_types = {
            'head': ItemType.HELMET,
            'chest': ItemType.CHESTPLATE,
            'legs': ItemType.LEGGINGS,
            'hands': ItemType.GAUNTLETS,
            'feet': ItemType.BOOTS
        }
        
        item_type = armor_types.get(slot)
        if not item_type:
            # Fallback to random armor
            item_type = random.choice(list(armor_types.values()))
        
        return ItemGenerator.generate_item(owner_id, min_stat, max_stat, item_type)

    @staticmethod
    def generate_random_equipment(owner_id: int, min_stat: int = 4, max_stat: int = 50) -> Item:
        """Generate random equipment (weapon or armor) based on difficulty"""
        # 60% chance for weapons, 40% chance for armor
        if random.random() < 0.6:
            # Generate weapon
            weapon_types = [ItemType.SWORD, ItemType.AXE, ItemType.HAMMER, ItemType.MACE, 
                           ItemType.DAGGER, ItemType.KNIFE, ItemType.SPEAR, ItemType.WAND, 
                           ItemType.STAFF, ItemType.BOW, ItemType.CROSSBOW, ItemType.GREATSWORD, 
                           ItemType.HALBERD, ItemType.KATANA, ItemType.SCYTHE, ItemType.SHIELD]
            item_type = random.choice(weapon_types)
        else:
            # Generate armor
            armor_types = [ItemType.HELMET, ItemType.CHESTPLATE, ItemType.LEGGINGS, 
                          ItemType.GAUNTLETS, ItemType.BOOTS]
            item_type = random.choice(armor_types)
        
        return ItemGenerator.generate_item(owner_id, min_stat, max_stat, item_type)

    @staticmethod
    def reroll_item(item: Item) -> Dict[str, Any]:
        """
        Reroll an item's stats while preserving its rarity tier.
        Returns dict of new stats (not applied - caller should update DB)
        """
        # Get current rarity and its stat range
        current_rarity = item.rarity
        min_stat, max_stat = ItemRarity.get_stat_range(current_rarity)
        
        # Generate new total within rarity range
        new_total = random.randint(min_stat, max_stat)
        
        # Get stat distribution for this item type
        stat_ratios = ItemGenerator.get_type_stats(item.type)
        
        # Initialize all stats
        new_stats = {
            'damage': 0,
            'armor': 0,
            'health_bonus': 0,
            'speed_bonus': 0,
            'luck_bonus': 0.0,
            'crit_bonus': 0.0,
            'magic_bonus': 0
        }
        
        # Distribute stats based on item type ratios
        for stat, ratio in stat_ratios.items():
            allocated_points = int(new_total * ratio)
            
            if stat == 'damage':
                new_stats['damage'] = allocated_points
            elif stat == 'armor':
                new_stats['armor'] = allocated_points
            elif stat == 'health':
                new_stats['health_bonus'] = allocated_points
            elif stat == 'speed':
                new_stats['speed_bonus'] = allocated_points
            elif stat == 'luck':
                new_stats['luck_bonus'] = allocated_points / 100.0
            elif stat == 'crit':
                new_stats['crit_bonus'] = allocated_points / 100.0
            elif stat == 'magic':
                new_stats['magic_bonus'] = allocated_points
        
        # Generate new name based on new stats
        new_stats['name'] = ItemGenerator.generate_name(
            item.type, 
            new_stats['damage'], 
            new_stats['armor'], 
            new_total
        )
        
        # Recalculate value
        new_stats['value'] = new_total * random.randint(80, 120)
        
        return new_stats

class CrateSystem:
    """Handles crate opening and rewards"""
    
    CRATE_CONTENTS = {
        ItemRarity.COMMON: {
            "min_stat": 4,
            "max_stat": 15,
            "money_chance": 0.3,
            "money_range": (50, 200)
        },
        ItemRarity.UNCOMMON: {
            "min_stat": 10,
            "max_stat": 25,
            "money_chance": 0.25,
            "money_range": (100, 500)
        },
        ItemRarity.RARE: {
            "min_stat": 20,
            "max_stat": 35,
            "money_chance": 0.2,
            "money_range": (300, 1000)
        },
        ItemRarity.MAGIC: {
            "min_stat": 30,
            "max_stat": 42,
            "money_chance": 0.15,
            "money_range": (800, 2000)
        },
        ItemRarity.LEGENDARY: {
            "min_stat": 40,
            "max_stat": 50,
            "money_chance": 0.1,
            "money_range": (1500, 5000)
        },
        "mystery": {
            "rarities": [
                (ItemRarity.COMMON, 0.4),
                (ItemRarity.UNCOMMON, 0.3),
                (ItemRarity.RARE, 0.15),
                (ItemRarity.MAGIC, 0.1),
                (ItemRarity.LEGENDARY, 0.05)
            ]
        }
    }
    
    @staticmethod
    def open_crate(crate_type: str, owner_id: int) -> Tuple[str, Optional[Item], Optional[int]]:
        """Open a crate and get rewards. Returns (reward_type, item, money)"""
        if crate_type == "mystery":
            # Mystery crates have random rarity
            rarities = CrateSystem.CRATE_CONTENTS["mystery"]["rarities"]
            weights = [weight for _, weight in rarities]
            chosen_rarities = [rarity for rarity, _ in rarities]
            crate_rarity = random.choices(chosen_rarities, weights=weights)[0]
        else:
            # Map crate type to rarity
            crate_map = {
                "common": ItemRarity.COMMON,
                "uncommon": ItemRarity.UNCOMMON,
                "rare": ItemRarity.RARE,
                "magic": ItemRarity.MAGIC,
                "legendary": ItemRarity.LEGENDARY
            }
            crate_rarity = crate_map.get(crate_type, ItemRarity.COMMON)
            
        contents = CrateSystem.CRATE_CONTENTS[crate_rarity]
        
        # Decide between item or money
        if random.random() < contents["money_chance"]:
            # Money reward
            money = random.randint(*contents["money_range"])
            return ("money", None, money)
        else:
            # Item reward (can be weapon or armor)
            item = ItemGenerator.generate_random_equipment(
                owner_id,
                min_stat=contents["min_stat"],
                max_stat=contents["max_stat"]
            )
            return ("item", item, None)

class Inventory:
    """Manages a player's inventory and equipment"""
    
    def __init__(self, items: List[Item]):
        self.items = items
        
    @property
    def equipped_items(self) -> List[Item]:
        """Get all equipped items"""
        return [item for item in self.items if item.equipped]
    
    @property
    def total_damage(self) -> int:
        """Total damage from equipped items"""
        return sum(item.damage for item in self.equipped_items)
    
    @property
    def total_armor(self) -> int:
        """Total armor from equipped items"""
        return sum(item.armor for item in self.equipped_items)
    
    def can_equip(self, item: Item) -> Tuple[bool, str]:
        """Check if an item can be equipped"""
        equipped = self.equipped_items
        
        # Define weapon types that conflict with each other
        weapon_types = [ItemType.SWORD, ItemType.AXE, ItemType.HAMMER, ItemType.MACE, 
                       ItemType.DAGGER, ItemType.KNIFE, ItemType.SPEAR, ItemType.WAND, 
                       ItemType.STAFF, ItemType.BOW, ItemType.CROSSBOW, ItemType.GREATSWORD, 
                       ItemType.HALBERD, ItemType.KATANA, ItemType.SCYTHE]
        
        # Check weapon conflicts - only one primary weapon allowed
        if item.type in weapon_types:
            for eq_item in equipped:
                if eq_item.type in weapon_types:
                    return False, "Only one primary weapon can be equipped at a time"
        
        # Check hand conflicts
        if item.hand == ItemHand.BOTH:
            # Two-handed weapons can't be used with anything else
            if len(equipped) > 0:
                return False, "Two-handed weapons cannot be used with other items"
        else:
            # Check for existing two-handed weapon
            for eq_item in equipped:
                if eq_item.hand == ItemHand.BOTH:
                    return False, "Cannot equip items while using a two-handed weapon"
                    
            # Check specific hand conflicts
            if item.hand == ItemHand.LEFT:
                for eq_item in equipped:
                    if eq_item.hand in [ItemHand.LEFT, ItemHand.ANY]:
                        return False, "Left hand slot is already occupied"
            elif item.hand == ItemHand.RIGHT:
                for eq_item in equipped:
                    if eq_item.hand in [ItemHand.RIGHT, ItemHand.ANY]:
                        return False, "Right hand slot is already occupied"
            elif item.hand == ItemHand.ANY:
                # ANY items can go in either hand, check if both are full
                left_taken = any(eq.hand in [ItemHand.LEFT, ItemHand.ANY] for eq in equipped)
                right_taken = any(eq.hand in [ItemHand.RIGHT, ItemHand.ANY] for eq in equipped)
                if left_taken and right_taken:
                    return False, "Both hand slots are already occupied"
                    
        return True, "Can equip"
    
    def equip_item(self, item: Item) -> Tuple[bool, str]:
        """Attempt to equip an item"""
        if item not in self.items:
            return False, "Item not found in inventory"
            
        can_equip, reason = self.can_equip(item)
        if not can_equip:
            return False, reason
            
        item.equipped = True
        return True, f"Equipped {item.name}"
    
    def unequip_item(self, item: Item) -> Tuple[bool, str]:
        """Unequip an item"""
        if item not in self.items:
            return False, "Item not found in inventory"
            
        if not item.equipped:
            return False, "Item is not equipped"
            
        item.equipped = False
        return True, f"Unequipped {item.name}"