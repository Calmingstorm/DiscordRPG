# DiscordRPG Feature Compendium

DiscordRPG is a persistent Discord idle RPG with enough systems to make a spreadsheet blush. This document is the operator/player-facing tour of what is currently in the box.

## Core Loop

1. Create a character.
2. Pick a race and class path.
3. Gain experience, gold, loot, achievements, and objective progress.
4. Equip better gear, evolve your class, pray to a god, gamble irresponsibly, and raid with the server.
5. Repeat until the leaderboard becomes a personality disorder.

The bot supports both active commands and automated progression for online players, so the game keeps breathing between command bursts.

## Character Progression

- Character creation with persistent MariaDB-backed profiles
- 10 playable races with distinct stat modifiers
- 42+ classes across 6 evolution tiers
- 7 specialization paths for long-term build identity
- Level, experience, gold, stats, PvP record, class bonuses, descriptions, profile color, and social fields
- Class evolution commands with level gates and visible upgrade paths
- Race browsing, race selection, and race-change support

## Loot and Equipment

- Generated weapons, shields, and armor
- 16+ weapon families including swords, axes, hammers, bows, staves, daggers, spears, wands, crossbows, greatswords, halberds, katanas, and scythes
- Equipment slots for weapon, shield, head, chest, legs, hands, and feet
- One-handed, two-handed, and shield hand rules
- Rarity and stat scaling
- Generated item names and type-specific stat distributions
- Inventory, equipment, item inspection, selling, giving, crates, and item leaderboards

## Achievements and Objectives

- Achievement tracking with categories, icons, unlock state, and leaderboard support
- Daily/weekly-style objective board
- Claimable objective rewards
- Additional progression pressure for players who need checklists to feel alive

## Idle and Adventure Systems

- Automated progression loops for online players
- Adventure triggering and status commands
- Epic and legendary adventure tiers with long-duration reward cadence
- Raid boss lifecycle and raid status tools
- Online player visibility

## Combat and Raids

- Player-versus-player battles
- Battle status and battle history/status commands
- Tournament support
- Raid bosses with participant tracking, damage/reward handling, MVP-style outcomes, and consolation rewards

## Economy

- Player marketplace
- Item offers and purchases
- Direct player trades
- Shop and shop purchase commands
- Withdrawals and gold movement
- Gambling commands: coin flip, slots, blackjack, dice, and general gamble entry point
- Daily rewards, streaks, voting rewards, and economy leaderboards

## Religion

- 5 gods with individual flavor and modifiers
- Choose a deity
- Pray for favor and effects
- Sacrifice gold for divine favor
- Purchase blessings
- Active blessing display on profiles
- Divine event text and deity-specific scaling hooks

## Optional AI Systems

AI features are optional and controlled through environment configuration.

- **Dynamic AI events** — periodic generated event narratives and themed rewards
- **AI Oracle** — in-game manual/question answering with live game context
- **Personal quest lines** — AI-generated multi-step quest arcs for individual players

If `OPENAI_ENABLED=false`, the core RPG still runs. Sensible architecture, a rare mercy.

## Web Dashboard

The included PHP dashboard reads the same MariaDB database used by the bot.

- Player rankings
- Item leaderboard
- Game stats
- Guide page
- `.env`-aware database configuration

## Operations

- MariaDB/MySQL backend
- Schema file included
- Python setup helper
- Modular discord.py cog architecture
- Backup, restore, and backup status commands
- systemd-friendly runtime via `start.py`
- `.env.example` for clean configuration onboarding

## Command Families

- Character: `create`, `profile`, `evolve`, `classes`, `classbonuses`, `description`, `background`, `color`, `online`
- Race: `races`, `race`, `raceinfo`, `changerace`
- Inventory: `inventory`, `equipment`, `equip`, `remove`, `item`, `sell`, `give`, `crate`
- Combat: `battle`, `tournament`, `battlestatus`, `battles`, `smite`
- Raids/adventures: `raids`, `raidstatus`, `epicadventures`, `epicstatus`, `trigger_adventure`, `autoplay`, `status`
- Economy: `market`, `offer`, `buy`, `withdraw`, `shop`, `buyshop`, `trade`
- Religion: `gods`, `choose`, `pray`, `sacrifice`, `bless`
- Progression: `achievements`, `achievementlist`, `achievementboard`, `quests`, `claimquests`, `daily`, `streak`, `vote`, `leaderboard`
- AI: `ask`, `quest`, `questhistory`, `abandonquest`, `queststatus`, `aieventsstatus`
- Admin/ops: `backup`, `backups`, `restore`, `backup_status`, `register_all`, `removeme`, `align`
- Utility: `help`, `ping`, `info`

## Design Philosophy

DiscordRPG aims to be:

- **Persistent** — progress survives restarts and lives in a real database.
- **Social** — leaderboards, raids, markets, trades, PvP, and public profiles create server texture.
- **Composable** — each system is a cog, so operators can reason about the beast without opening one cursed megafile.
- **Expandable** — new commands, loot tables, objectives, events, classes, and web pages can be added without burning the village down.
