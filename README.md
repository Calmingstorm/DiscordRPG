# DiscordRPG

A full-featured Discord RPG bot with automated progression, AI-generated events, 42+ classes, 10 races, and idle gameplay. Players progress while online through adventures, battles, raids, and dynamic AI events.

## Features

**AI-Powered Systems** (optional, requires OpenAI key)
- Dynamic AI events every 15 minutes with unique narratives and themed loot
- AI Oracle — a living game manual that answers player questions with real-time data
- AI-generated multi-chapter personal quest lines

**Core Gameplay**
- Automated idle progression — adventures, battles, raids run while players are online
- 6-tier class evolution system with 42+ classes across 7 specialization paths
- 10 playable races with distinct stat bonuses
- 16+ weapon types, 7 equipment slots, 8 stat categories
- Epic and legendary adventure tiers (4-24 hour durations)

**Economy & Social**
- Global marketplace and direct player-to-player trading
- Religion system with 5 gods, prayers, sacrifices, and divine blessings
- Gambling, daily rewards with streaks, crate system
- Guilds, marriages, PvP combat, and leaderboards

**Web Leaderboards**
- PHP-based web dashboard showing player rankings, item leaderboards, game stats
- Included in `web/` directory, connects to the same MariaDB database

**Infrastructure**
- MariaDB/MySQL backend with proper indexing and foreign keys
- Automated database backups (hourly + daily via mysqldump)
- Modular cog architecture — each system is an independent module
- Runs as a systemd service with auto-restart

## Quick Start

```bash
git clone https://github.com/Calmingstorm/DiscordRPG.git
cd DiscordRPG
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Discord token and database credentials
python3 setup.py
python3 start.py
```

See [INSTALL.md](INSTALL.md) for full setup instructions including MariaDB, systemd service, and web leaderboard deployment.

## Directory Structure

```
DiscordRPG/
├── bot.py                  # Main bot class and entry config
├── start.py                # Entry point
├── setup.py                # Interactive setup script
├── schema.sql              # MariaDB database schema
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
├── classes/
│   ├── character.py        # Character class definitions and evolution
│   └── items.py            # Item generation and stat system
├── cogs/
│   ├── auto_register.py    # Auto-registration on join
│   ├── character.py        # Character management commands
│   ├── inventory.py        # Equipment and item management
│   ├── combat.py           # PvP battle system
│   ├── epic_adventures.py  # Epic/legendary adventure tier
│   ├── economy.py          # Market, trading, shops
│   ├── daily.py            # Daily rewards and streaks
│   ├── gambling.py         # Casino games
│   ├── religion.py         # Gods, prayer, blessings
│   ├── race.py             # Race selection and bonuses
│   ├── autoplay.py         # Automated game loops
│   ├── raids.py            # Group raid bosses
│   ├── oracle.py           # AI game manual (OpenAI)
│   ├── ai_events.py        # AI dynamic events (OpenAI)
│   ├── personal_quests.py  # AI quest lines (OpenAI)
│   ├── backup.py           # Automated DB backups
│   └── help.py             # Help command
├── utils/
│   ├── database.py         # MariaDB connection and query layer
│   └── scaling.py          # Balance and scaling calculations
└── web/
    ├── db_config.php       # Database config (reads from .env)
    ├── index.php           # Main leaderboard dashboard
    ├── top-items.php       # Equipment leaderboard
    └── guide.php           # Game guide
```

## Commands

| Command | Description |
|---------|-------------|
| `!create [name]` | Create a character |
| `!profile` | View your stats |
| `!inventory` | Manage equipment |
| `!classes` / `!evolve` | View and evolve your class |
| `!race` | Choose or view your race |
| `!market` | Browse the player marketplace |
| `!pray` / `!sacrifice` | Interact with your god |
| `!epicstatus` | Check epic adventure progress |
| `!quest` | View your personal quest |
| `!ask [question]` | Ask the AI Oracle (if enabled) |
| `!help` | Full command list |

Players progress automatically while online — no commands needed for basic gameplay.

## Configuration

All configuration is in `.env`. See [.env.example](.env.example) for all options.

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Your Discord bot token |
| `DB_HOST` | Yes | MariaDB/MySQL host |
| `DB_USER` | Yes | Database username |
| `DB_PASS` | Yes | Database password |
| `DB_NAME` | Yes | Database name |
| `BOT_PREFIX` | No | Command prefix (default: `!`) |
| `OPENAI_ENABLED` | No | Enable AI features (default: `false`) |
| `OPENAI_API_KEY` | No | OpenAI API key for AI features |

The bot works fully without OpenAI — AI features fall back to handcrafted templates.

## License

MIT License. See [LICENSE](LICENSE) for details.
