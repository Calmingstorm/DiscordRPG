# DiscordRPG Features

## AI-Powered Features (Optional)

### Dynamic AI Events
- OpenAI-generated events every 15 minutes with unique narratives
- AI creates thematic item names that match event lore
- Event types: treasure hunts, boss fights, world events, mystery encounters
- Falls back to handcrafted templates without an OpenAI key

### AI Oracle
- Real-time help system that answers questions about game mechanics
- Context-aware — uses actual game data and character information
- Available in DMs or server channels

### Personal Quest Lines
- AI-generated multi-chapter quest arcs unique to each player
- Story choices affect outcomes and rewards

## Core Gameplay

### Character Progression
- **6-Tier Evolution**: Novice → Tier 1-5 → Immortal (42+ classes)
- **7 Class Paths**: Warrior, Thief, Mage, Ranger, Raider, Ritualist, Paragon
- **10 Playable Races**: Human, Elf, Dwarf, Orc, Halfling, Gnome, Dragonborn, Tiefling, Undead, Demon
- Convergent endgame — all paths lead to Eternal → Immortal

### Equipment System
- 16+ weapon types: swords, axes, bows, staves, daggers, and more
- 7 equipment slots: weapon + 5 armor + accessory
- 8 stat categories: damage, armor, health, speed, luck, crit, magic, special
- Quality tiers with 1-50 stat points and multiple rarity levels

## Automated Game Loops

All loops run automatically while players are online — no commands needed.

| System | Frequency | Duration | Unlock |
|--------|-----------|----------|--------|
| Adventures | 7-21 min | 5 min - 2 hr | Level 1 |
| Battles | 2-8 min | Instant (1v1 to 10v10) | Level 1 |
| Epic Adventures | 45 min | 4-8 hr | Level 10 |
| Legendary Adventures | Epic pool | 8-24 hr | Level 15 |
| Raids | 35 min | Group boss fights | Level 5 |
| AI Events | 15 min | Varies | Level 1 |

- Only online (green status) players participate
- Content scales to player level
- Multiple activities run in parallel

## Religion and Blessings

- **5 Gods**: Luminara (light), Nyxara (darkness), Terranos (earth), Aquanis (water), Pyrion (fire)
- Daily prayers build divine favor over time
- Active blessings grant temporary XP/gold multipliers
- Sacrifice items for favor with your chosen deity

## Economy

- **Global Marketplace**: Buy and sell items between players
- **Direct Trading**: Player-to-player item exchanges
- **Daily Shops**: NPC merchants with rotating stock
- **Gold Sinks**: Class evolution, equipment upgrades, gambling

## Social

- **Marriages**: Player partnerships with gameplay bonuses
- **Guilds**: Group membership and coordination
- **PvP Combat**: Direct duels with stat-based outcomes
- **Leaderboards**: Rankings by level, gold, items, and more

## Entertainment

- **Gambling**: Coin flip, dice games, luck-scaled outcomes
- **Daily Rewards**: Login bonuses with streak multipliers
- **Crate System**: Loot boxes with tiered rewards
- **Statistics**: Detailed performance tracking

## Technical

- **MariaDB/MySQL Backend**: Proper indexing, foreign keys, transactional integrity
- **Automated Backups**: Hourly + daily database dumps via mysqldump
- **Modular Architecture**: Each system is an independent cog — easy to extend or disable
- **Web Leaderboard**: PHP dashboard included in `web/` directory
- **Environment-Based Config**: All settings in `.env`, no hardcoded values
- **Graceful Degradation**: AI features fall back to templates, reconnects on DB errors
