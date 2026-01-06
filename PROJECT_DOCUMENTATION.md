# Discord RPG Bot - Complete Project Documentation

**Last Updated:** 2026-01-06  
**Bot Version:** Full-featured DiscordRPG with AI Events  
**Author Documentation Created by:** Claude Code Assistant

---

## 🎯 Project Overview

This is a comprehensive Discord bot implementing a full-featured RPG game system with automated progression, complex character systems, and extensive player interactions. The bot is designed as an "idle RPG" where players progress automatically while online, with optional manual interactions.

### Key Features
- **Automated Progression**: Online players automatically participate in adventures and battles
- **AI-Powered Events**: Dynamic OpenAI-generated events with unique narratives and rewards
- **Complex Character System**: 6-tier class evolution paths, 10 unique races with bonuses
- **Advanced Equipment**: 16+ weapon types, 5 armor slots, complex stat bonuses
- **Economy System**: Global marketplace, direct trading, daily shops
- **Religion System**: 5 gods with unique bonuses and blessing systems
- **Social Features**: Guilds, marriages, PvP tournaments
- **Gaming Elements**: Multiple gambling games with luck modifiers

---

## 🏗️ Architecture Overview

### **Core Components**

#### Bot Structure (`bot.py`)
- **Main Class**: `DiscordRPGBot` extends `commands.Bot`
- **Base Cog Class**: `DiscordRPGCog` provides common utilities
- **Database Integration**: Single SQLite instance shared across all cogs
- **Dynamic Loading**: Automatically loads all cogs from `/cogs/` directory
- **Event Handling**: Processes Discord events and command routing

#### Database System (`utils/database.py`)
- **Backend**: SQLite with foreign key constraints
- **Connection**: Single persistent connection with row factory
- **Helper Methods**: Common CRUD operations and utilities
- **Transaction Support**: Proper commit/rollback for data integrity
- **Row Conversion**: `row_to_dict()` for consistent data handling

#### Cog Organization
```
/cogs/
├── character.py      # Character creation, profiles, evolution
├── adventure.py      # Regular adventure system (disabled)
├── epic_adventures.py # Epic/legendary adventures  
├── combat.py         # PvP battles and tournaments
├── economy.py        # Market, trading, shops
├── inventory.py      # Equipment, items, crates
├── religion.py       # Gods, prayers, blessings
├── race.py           # Character races and bonuses
├── daily.py          # Daily rewards and streaks
├── autoplay.py       # Automated gameplay systems
├── gambling.py       # Casino games and betting
├── raids.py          # Group raid battles
├── oracle.py         # AI-powered game manual (OpenAI)
├── ai_events.py      # Dynamic AI event generation (OpenAI)
├── auto_register.py  # Auto character creation
├── backup.py         # Database backup/restore
└── help.py           # Help system
```

---

## 💾 Database Schema

### **Core Tables**

#### Characters (`profile`)
```sql
user_id (PK), name, money, xp, level, class, race, 
pvpwins, pvplosses, deaths, kills, completed,
god, favor, luck, marriage, guild, background, 
description, colour, donations, raidstats,
atkmultiply, defmultiply, crates_*, last_date, 
streak, vote_ban, has_character, reset_points,
last_adventure, adventure_alert, alignment, created_at
```

#### Items (`inventory`) 
```sql
id (PK), owner (FK), name, value, type, damage, armor,
hand, equipped, health_bonus, speed_bonus, luck_bonus,
crit_bonus, magic_bonus, slot_type, created_at
```

#### Adventures (`adventures`)
```sql
id (PK), user_id (FK), adventure_name, difficulty,
started_at, finish_at, status
```

#### Market (`market`)
```sql
id (PK), item_id (FK), price, listed_at
```

### **Key Relationships**
- **Users ↔ Profile**: 1:1 relationship via Discord user_id
- **Profile → Inventory**: 1:N (users own multiple items)  
- **Inventory → Market**: 1:1 (items can be listed for sale)
- **Profile → Adventures**: 1:N (multiple active adventures)
- **Profile → Guilds**: N:1 (members belong to guilds)

---

## 🎮 Game Mechanics

### **Character Progression**

#### Level System
- **Formula**: `level = min(50, 1 + int((xp / 100) ** 0.5))`
- **Level Cap**: 50 (expandable in code)
- **XP Sources**: Adventures, combat, daily rewards, gambling wins
- **Level Benefits**: Stat increases, class evolution access, better gear access

#### Class Evolution (6 Tiers)
```
Tier 0: Novice (Starting class)
Tier 1: Warrior, Thief, Mage, Ranger, Raider, Ritualist, Paragon*
Tier 2: Swordsman/Knight, Rogue/Assassin, Wizard/Warlock, etc.
Tier 3: Warlord, Bandit, Sorcerer, Bowmaster, etc.  
Tier 4: Berserker, Nightblade, Archmage, Marksman, etc.
Tier 5: [Paragon path] Legend → Eternal
Tier 6: [Paragon path] Immortal
*Paragon = Premium class path
```

#### Race System (10 Races)
- **Human**: Balanced, 1.1x XP multiplier
- **Elf**: +2 luck, +3 magic, 0.9x gold
- **Dwarf**: +2 defense, 1.4x gold, -1 speed  
- **Orc**: +3 attack, 1.3x XP, -2 luck
- **Halfling**: +4 luck, 1.1x gold, 0.8x XP
- **Gnome**: +3 luck, +2 magic, 0.9x XP
- **Dragonborn**: +1 attack/defense, 1.1x XP/gold
- **Tiefling**: +2 luck/magic, 1.2x gold
- **Undead**: +5 luck, -10 HP, 0.7x XP, no divine favor
- **Demon**: +6 luck, 1.3x gold, 0.8x XP, no divine favor

### **Equipment System**

#### Item Types & Slots
- **Weapons** (16 types): Sword, Axe, Hammer, Bow, Staff, Wand, etc.
- **Armor** (5 slots): Helmet, Chestplate, Leggings, Gauntlets, Boots
- **Special**: Shield (left hand only)

#### Item Stats
- **Primary**: Damage, Armor
- **Armor Bonuses**: Health, Speed, Luck, Crit Chance, Magic Power
- **Hand Requirements**: Left, Right, Both, Any
- **Slot Conflicts**: Smart equipping handles hand/slot management

#### Item Generation
- **Stat Budget**: 4-50 points distributed by item type
- **Rarity Tiers**: Common → Uncommon → Rare → Magic → Legendary → Mythic → Divine
- **Dynamic Names**: Prefix + Base + Suffix system based on stats

### **Adventure System**

#### Automated Adventures
- **Frequency**: Every 7-21 minutes for online players
- **Duration**: 5-120 minutes based on character level
- **Types**: 12 different adventure themes
- **Rewards**: XP, gold, items based on success and level

#### Epic Adventures  
- **Requirements**: Level 10+ for Epic, Level 15+ for Legendary
- **Duration**: 4-8 hours (Epic), 8-24 hours (Legendary)
- **Frequency**: Every 45 minutes for eligible players
- **Parallel System**: Can run alongside regular adventures

### **Combat System**

#### Battle Types
- **Auto Battles**: 1v1, 3v3, 5v5, 10v10 every 2-8 minutes
- **Manual PvP**: Player-initiated with optional gold wagers
- **Tournaments**: Bracket-style with prize pools
- **Raids**: Group battles vs bosses every 35 minutes

#### Power Calculation
```
Base Power = Level × 10
+ Equipment Stats (damage + armor + bonuses)  
+ Class Bonuses (attack/defense multipliers)
+ Race Bonuses (stat bonuses)
+ Divine Bonuses (blessing effects)
+ Random Factor (±15%)
```

### **Economy System**

#### Market System
- **Global Marketplace**: All servers share items
- **Listing Fee**: 5% of asking price  
- **Price Limits**: Maximum 10,000,000 gold per item
- **Seller Notifications**: DM alerts for sales

#### Daily Shop
- **Refresh**: Daily based on bot creation date
- **Content**: 3 items with level-appropriate stats
- **Pricing**: Based on item stats and rarity multipliers

### **Religion System**

#### Gods & Bonuses
- **Chaos**: 1.2x luck, 0.8x sacrifice efficiency  
- **Order**: 0.9x luck, 1.1x sacrifice efficiency
- **War**: 1.0x balanced bonuses
- **Nature**: 1.1x luck, 0.9x sacrifice efficiency
- **Death**: 0.8x luck, 1.3x sacrifice efficiency

#### Divine Activities
- **Prayer**: 4-hour cooldown, 1-5 base favor + bonuses
- **Sacrifice**: 12-hour cooldown, 1 favor per 1,000 gold + god multiplier
- **Blessings**: Temporary buffs (1-6 hours) for favor points

---

## 🤖 Automated Systems

### **Auto-Play Requirements**
- **Online Status**: Must show as online (green) in Discord
- **Character Requirement**: Must have created character
- **Automatic Participation**: No opt-out, but only affects online players

### **Auto-Play Loops**

#### Adventure Loop
- **Frequency**: Random 7-21 minutes
- **Selection**: 3-5 random online players
- **Batch Processing**: Creates multiple adventures simultaneously
- **Duration**: Level-based (5-120 minutes)

#### Battle Loop  
- **Frequency**: Random 2-8 minutes
- **Battle Types**: 1v1 (30%), 3v3 (30%), 5v5 (25%), 10v10 (15%)
- **Selection**: Random online players
- **Rewards**: XP, gold, items based on battle size

#### Epic Adventure Loop
- **Frequency**: Every 45 minutes
- **Requirements**: Level 10+ for epic, 15+ for legendary
- **Duration**: 4-8 hours epic, 8-24 hours legendary
- **Parallel**: Runs alongside regular adventures

#### AI Events Loop (OpenAI-Powered)
- **Frequency**: Every 15 minutes with random delays
- **Requirements**: OpenAI enabled in .env configuration
- **Event Types**: Treasure hunts (40%), Mini bosses (30%), World events (20%), Mystery (10%)
- **Participation**: 2-20 online players depending on event type
- **AI Generation**: Unique narratives, boss personalities, treasure scenarios
- **Fallback**: Template events when AI unavailable
- **Parallel**: Completely independent of all existing systems

#### Raid Loop
- **Frequency**: Every 35 minutes  
- **Requirements**: 10+ online level 10+ players
- **Boss Generation**: Random stats based on participant count
- **Group Rewards**: Shared XP and gold

#### Event Loop
- **Frequency**: Every 22.5 minutes
- **Global Events**: Affects all online players simultaneously
- **Event Types**: Luck bonuses, XP bonuses, item drops, etc.

---

## 📊 Command Reference

### **Character Management**
- `!create [name]` - Create new character
- `!profile [@user]` - View character stats  
- `!evolve` - Class evolution at milestone levels
- `!classes` - View evolution tree
- `!race <name>` - Select character race
- `!align <good/neutral/evil>` - Set alignment

### **Equipment & Inventory**
- `!inventory [page]` - View items (paginated)
- `!equipment` - View equipped items
- `!equip <id>` - Equip item by ID
- `!remove <id>` - Unequip item
- `!sell <id>` - Sell item to merchant
- `!crate <type>` - Open loot crates

### **Economy & Trading**  
- `!market [page]` - Browse marketplace
- `!offer <id> <price>` - List item for sale
- `!buy <id>` - Purchase marketplace item
- `!shop` - Visit daily item shop
- `!trade <user> <my_item> <their_item>` - Direct trading

### **Combat & Battles**
- `!battle <user> [bet]` - Challenge player to battle
- `!tournament <prize>` - Host tournament
- `!raids` - Raid system information

### **Religion & Gods**
- `!gods` - View available deities
- `!choose <god>` - Select deity (permanent)
- `!pray` - Pray for favor (4h cooldown)
- `!sacrifice <amount>` - Sacrifice gold for favor
- `!bless [type]` - Purchase divine blessings

### **Gambling Games**
- `!coinflip <amount> <h/t>` - 50/50 coin flip
- `!slots <amount>` - Slot machine
- `!blackjack <amount>` - Interactive blackjack
- `!diceroll <amount>` - Dice vs house
- `!gamble <amount>` - High-risk doubling

### **Daily & Rewards**
- `!daily` - Claim daily rewards
- `!streak` - View daily streak status
- `!leaderboard <category>` - Top 10 rankings

### **Information**
- `!help [command]` - Command help
- `!online` - View online/offline players
- `!autoplay status` - Auto-system status

### **Admin Commands**
- `!backup` - Create database backup
- `!restore <filename>` - Restore from backup  
- `!register_all` - Auto-register all server members

---

## 🔧 Technical Implementation

### **Critical Code Patterns**

#### Database Access
```python
# Always use row_to_dict() for sqlite3.Row objects
row = self.db.fetchone("SELECT * FROM profile WHERE user_id = ?", (user_id,))
if row:
    data = self.db.row_to_dict(row)
    return data['field_name']
```

#### Error Handling
```python
try:
    # Database operations
    self.db.execute("INSERT ...", params)
    self.db.commit()
    return True
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return False
```

#### Async/Sync Patterns
- **Database operations**: Synchronous (SQLite)
- **Discord API**: Asynchronous (discord.py)
- **Mixed usage**: Wrap sync operations in async functions

### **Important Fixes Applied**
1. **SQL Injection Prevention**: Whitelisted inputs in `set_cooldown()`
2. **Race Condition Fixes**: Atomic operations in daily claims and auto-registration
3. **sqlite3.Row Handling**: Proper conversion to dictionaries
4. **Path Traversal Protection**: Input validation in backup restoration
5. **Error Recovery**: Comprehensive try/catch with logging

### **Performance Considerations**
- **Single Database Connection**: Shared across all cogs
- **Pagination**: Large datasets (inventory, market) use pagination
- **Indexing**: Key database fields indexed for performance
- **Caching**: Prefix and cooldown caching for frequently accessed data

---

## 🚨 Known Issues & Limitations

### **Current Issues**
1. **No Connection Pooling**: Single SQLite connection may be bottleneck
2. **Memory Growth**: Caches (prefixes, cooldowns) never cleaned
3. **Synchronous Database**: May block event loop under heavy load
4. **Hard-coded Values**: Many game constants not easily configurable

### **Potential Improvements**
1. **Database Migration**: PostgreSQL for better concurrency
2. **Connection Pooling**: Async database adapter
3. **Configuration System**: External config files for game balance
4. **Caching Strategy**: Redis for distributed caching
5. **Monitoring**: Comprehensive logging and metrics

---

## 🔄 Deployment & Maintenance

### **Setup Requirements**
- Python 3.8+ with discord.py and python-dotenv
- SQLite database (auto-created from schema.sql)
- Discord bot token in .env file
- Proper Discord bot permissions and intents

### **Bot Permissions Required**
- Send Messages, Read Message History
- Use External Emojis, Add Reactions
- Embed Links, Attach Files
- Read Members (for auto-registration)
- Administrator (for backup commands)

### **Monitoring Points**
- Database file size and backup frequency
- Bot response times and error rates  
- Auto-play loop health and character counts
- Memory usage and cache sizes

### **Backup Strategy**
- Automatic hourly backups via backup cog
- Manual backup commands for administrators
- Compressed storage with metadata
- Restoration with double confirmation

---

## 📈 Game Balance & Economy

### **XP & Level Progression**
- **Early Levels (1-10)**: Fast progression for engagement
- **Mid Levels (10-30)**: Steady progression with class evolution milestones
- **High Levels (30-50)**: Slow progression for end-game content
- **Level 50 Cap**: Prevents infinite scaling, focus shifts to equipment

### **Economic Balance**
- **Gold Sources**: Adventures, battles, daily rewards, gambling, market sales
- **Gold Sinks**: Market taxes, item purchases, blessing costs, gambling losses
- **Inflation Control**: Level-based rewards, percentage fees, market dynamics

### **Item Progression**
- **Starter Gear**: 3 damage/armor for new players
- **Adventure Rewards**: 4-50 stat items based on character level
- **Crate System**: Guaranteed rarity brackets for progression
- **Market Dynamics**: Player-driven economy with supply/demand

---

## 🎯 Future Development Ideas

### **Potential Features**
1. **Guild System Expansion**: Guild wars, shared resources, guild raids
2. **Pet System**: Companion animals with stats and evolution
3. **Crafting System**: Combine items to create better equipment
4. **Seasonal Events**: Limited-time content with exclusive rewards
5. **Prestige System**: Post-level-50 progression with reset benefits

### **Technical Enhancements**
1. **Web Dashboard**: Player statistics and leaderboards
2. **Mobile Integration**: Discord slash commands optimization
3. **Cross-Server Features**: Global leaderboards and competitions
4. **Analytics System**: Player behavior tracking and balance analysis
5. **Moderation Tools**: Anti-cheat systems and player reporting

---

## 📝 Development Notes

### **Code Style & Patterns**
- **Inheritance**: All cogs extend `DiscordRPGCog` base class
- **Error Handling**: Graceful degradation with user feedback
- **Database**: Consistent use of helper methods and conversions
- **Commands**: Decorators for character requirements and cooldowns

### **Testing Approach**
- **Manual Testing**: Discord server with test accounts
- **Database Testing**: Backup/restore for safe experimentation  
- **Load Testing**: Multiple online accounts for auto-play testing
- **Integration Testing**: Cross-cog feature interactions

### **Debugging Tips**
- **Database Issues**: Check foreign key constraints and data types
- **Auto-Play Problems**: Verify online status detection logic
- **Permission Errors**: Ensure bot has required Discord permissions
- **Race Conditions**: Look for non-atomic operations in concurrent code

---

This documentation provides a complete reference for understanding, maintaining, and extending the Discord RPG bot. The system is designed to be modular and extensible, with clear separation of concerns across different game systems.

**Remember**: Always create database backups before making significant changes, and test thoroughly with multiple accounts to verify auto-play functionality.