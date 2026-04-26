# DiscordRPG

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2.svg)](https://discordpy.readthedocs.io/)
[![MariaDB](https://img.shields.io/badge/database-MariaDB%20%2F%20MySQL-003545.svg)](https://mariadb.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A ridiculous, full-stack idle RPG for Discord.**

DiscordRPG turns a server into a persistent fantasy grind machine.

Character creation, class evolution, race bonuses, loot, raids, PvP, markets, gods, gambling, achievements, and rotating objectives are all in the box.

So are optional AI-authored events and a PHP leaderboard.

The box is not small.

It all sits on top of the same MariaDB database.

Players can actively command their heroes or let the idle loops keep the murder-economy moving while they lurk online.

This is not a toy `!roll d20` bot. This is a tiny MMO wearing a Discord bot trench coat.

## What You Get

- **Idle progression that actually moves** — adventures, battles, raids, rewards, and online-player loops keep the world alive.
- **42+ classes across 6 evolution tiers** — seven specialization paths, level gates, combat multipliers, and class flavor.
- **10 playable races** — stat bonuses, identity, and build variety from the first character choice.
- **Loot with teeth** — weapons, shields, armor slots, rarity scaling, crates, stat rolls, and item leaderboards.
- **Economy systems** — gold, shops, trading, player market listings, withdrawals, and casino-grade bad decisions.
- **Social chaos** — guilds, marriages, PvP battles, tournaments, raids, and leaderboards.
- **Religion system** — choose a god, pray, sacrifice, earn favor, and buy divine blessings like consequences are optional.
- **Progression hooks** — achievements, daily/weekly objective boards, streaks, dailies, voting rewards, and richer loot tables.
- **Optional AI content** — OpenAI-powered world events, oracle answers, and personal quest lines when configured.
- **Web dashboard** — PHP leaderboards and guide pages backed by the live MariaDB data.
- **Operator-friendly guts** — modular cogs, `.env` config, setup script, database schema, backups, and systemd-friendly startup.

## Screenshots / Vibe

DiscordRPG is embed-heavy and command-driven: profiles, item cards, race info, raid status, markets, blessings, and leaderboards are all rendered directly in Discord.

The web dashboard gives your server a public trophy wall for rankings, stats, and top gear.

If your players like numbers going up, this bot supplies the numbers, the buttons, the loot confetti, and the occasional divine lawsuit.

## Quick Start

```bash
git clone https://github.com/Calmingstorm/DiscordRPG.git
cd DiscordRPG
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Discord token and MariaDB/MySQL credentials
python3 setup.py
python3 start.py
```

Full deployment notes live in [INSTALL.md](INSTALL.md), including MariaDB setup, systemd service configuration, and web leaderboard deployment.

## Configuration

DiscordRPG is configured through `.env`:

```env
DISCORD_TOKEN=your_discord_bot_token_here
BOT_PREFIX=!

DB_HOST=localhost
DB_USER=discordrpg
DB_PASS=your_database_password_here
DB_NAME=discordrpg

OPENAI_ENABLED=false
OPENAI_API_KEY=your_openai_api_key_here
```

Required:

- A Discord bot token
- MariaDB or MySQL
- Python dependencies from `requirements.txt`

Optional:

- OpenAI API key for AI events, oracle responses, and personal quest lines
- A web server with PHP for the included leaderboard dashboard
- systemd for long-running production service management

## Command Sampler

| Command | What it does |
| --- | --- |
| `!create <name>` | Create your character |
| `!profile` | View stats, resources, gear, blessings, and progress |
| `!inventory` / `!equipment` | Inspect and manage gear |
| `!equip`, `!remove`, `!sell`, `!crate` | Handle loot like a proper goblin |
| `!classes` / `!evolve` | Browse and advance class paths |
| `!races`, `!race`, `!changerace` | Pick or inspect racial bonuses |
| `!daily`, `!streak`, `!vote` | Claim repeatable rewards |
| `!quests`, `!claimquests` | Work the objective board |
| `!achievements`, `!achievementboard` | Track long-term unlocks and flex publicly |
| `!status`, `!epicadventures`, `!epicstatus` | Run automated and long-form adventures |
| `!battle`, `!tournament`, `!battles` | PvP and competitive violence |
| `!raids`, `!raidstatus` | Group boss fights and raid rewards |
| `!market`, `!offer`, `!buy`, `!trade`, `!shop` | Economy and player trading |
| `!gods`, `!choose`, `!pray`, `!sacrifice`, `!bless` | Religion and divine buffs |
| `!coinflip`, `!slots`, `!blackjack`, `!diceroll`, `!gamble` | Gambling, because hubris scales |
| `!ask` | Ask the optional AI oracle |
| `!quest`, `!questhistory`, `!abandonquest` | Optional AI personal quest lines |
| `!leaderboard`, `!online`, `!info`, `!help` | Server status, rankings, and guidance |

Exact availability depends on enabled cogs, permissions, and optional AI configuration.

## Systems Overview

### Characters and Builds

Players start with a character, choose a race, level through activity, and evolve through class tiers.

Equipment, blessings, race bonuses, class multipliers, and achievements all feed into the character sheet.

Builds feel like builds instead of cosmetic hats stapled to a random number generator.

### Loot and Items

The item system supports weapons, armor slots, shields, rarity tiers, scaling stats, generated names, crates, equipment management, selling, trading, and item leaderboards.

There is enough loot surface area here for players to argue about optimal gear, which is the highest form of community engagement and also a warning sign.

### Idle Loops and Events

The bot can run automated progression for online players: adventures, battle opportunities, raid activity, and timed systems.

Optional AI events add generated narratives and themed loot without making the entire bot dependent on an LLM.

### Economy and Social Play

Players can shop, list items, trade directly, gamble, fight, join raids, climb leaderboards, and generally convert time into status.

The point is simple: give the server reasons to check in, compare numbers, and start suspiciously passionate arguments about swords.

### Web Leaderboards

The `web/` directory contains a PHP dashboard that reads from the same MariaDB database as the bot.

Deploy it beside the bot or on a separate web host with database access to publish rankings, top items, game stats, and guide content.

## Project Layout

```text
DiscordRPG/
├── bot.py                  # Main bot class, intents, cog loading, lifecycle
├── start.py                # Runtime entry point
├── setup.py                # Interactive environment/database setup
├── schema.sql              # MariaDB/MySQL schema
├── requirements.txt        # Python dependencies
├── .env.example            # Configuration template
├── classes/
│   ├── character.py        # Classes, races, stats, evolution data
│   └── items.py            # Item generation, slots, rarity, stat rolls
├── cogs/
│   ├── achievements.py     # Achievements and achievement leaderboard
│   ├── autoplay.py         # Idle progression loops and status
│   ├── character.py        # Character, profile, evolution, cosmetic commands
│   ├── combat.py           # PvP battles and tournaments
│   ├── daily.py            # Daily rewards, streaks, voting, leaderboard
│   ├── economy.py          # Market, trading, shop, offers
│   ├── epic_adventures.py  # Long-duration adventure tiers
│   ├── gambling.py         # Casino commands
│   ├── inventory.py        # Inventory, equipment, crates, item management
│   ├── oracle.py           # Optional AI oracle
│   ├── personal_quests.py  # Optional AI quest lines
│   ├── quests_board.py     # Daily/weekly objective board
│   ├── raids.py            # Raid bosses and rewards
│   ├── race.py             # Race browsing and selection
│   ├── religion.py         # Gods, prayers, sacrifices, blessings
│   └── backup.py           # Database backup and restore tooling
├── utils/
│   ├── achievements.py     # Achievement definitions and helpers
│   ├── database.py         # MariaDB query layer
│   ├── loot.py             # Loot tables and drop helpers
│   └── scaling.py          # Balance and scaling calculations
└── web/
    ├── index.php           # Main leaderboard dashboard
    ├── top-items.php       # Item leaderboard
    ├── guide.php           # Game guide
    └── db_config.php       # Web DB config loader
```

## Production Notes

- Enable Discord privileged intents for message content, members, and presence if you use the full feature set.
- Keep `.env` private. The gods can see secrets, GitHub should not.
- Run MariaDB/MySQL with regular backups. The bot includes backup commands, but operators should still have real database hygiene.
- Use systemd, Docker, or another supervisor for long-running deployments.
- Review `INSTALL.md` before exposing the web dashboard.

## More Documentation

- [FEATURES.md](FEATURES.md) — expanded feature breakdown
- [INSTALL.md](INSTALL.md) — installation and deployment guide
- [schema.sql](schema.sql) — database schema
- [LICENSE](LICENSE) — MIT license

## License

MIT. Build the fantasy treadmill of your dreams. Try not to let the economy hyperinflate before Tuesday.
