# DiscordRPG - AI-Powered Idle RPG Bot 🎮

A comprehensive Discord bot implementing a full-featured RPG game system with automated progression, complex character systems, AI-generated events, and extensive player interactions.

## ✨ Features

### 🤖 **AI-Powered Systems**
- **Dynamic AI Events**: OpenAI-generated unique events every 15 minutes with custom narratives and themed items
- **Living Game Manual**: AI Oracle that answers questions about the game using real-time data
- **Smart Fallbacks**: Graceful degradation when AI services are unavailable

### 🎯 **Core Gameplay**
- **Automated Progression**: Players progress while online through adventures, battles, and events
- **Complex Character System**: 6-tier class evolution paths with 42+ unique classes
- **10 Unique Races**: Each with distinct bonuses and playstyles
- **Advanced Equipment**: 16+ weapon types, 5 armor slots, complex stat system

### 🌟 **Advanced Systems**
- **Epic & Legendary Adventures**: High-tier parallel adventure system (4-24 hours)
- **Religion System**: 5 gods with unique bonuses and blessing systems
- **Economy**: Global marketplace, direct trading, daily shops
- **Social Features**: Guilds, marriages, PvP tournaments
- **Gambling**: Multiple casino games with luck-based mechanics

### 📊 **Automation Features**
- **Multiple Game Loops**: Adventures (7-21min), Battles (2-8min), Raids (35min), AI Events (15min)
- **Smart Player Selection**: Automatic online player detection and participation
- **Dynamic Rewards**: Race, religion, and blessing multipliers
- **Progression Tracking**: Automatic level-ups, stat increases, and notifications

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Discord Application with Bot Token
- SQLite3
- Optional: OpenAI API Key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/discordrpg.git
   cd discordrpg
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your Discord bot token and optionally OpenAI API key
   ```

4. **Initialize database**
   ```bash
   python3 update_database.py
   ```

5. **Start the bot**
   ```bash
   python3 start.py
   ```

### Discord Bot Setup

1. Create a Discord Application at https://discord.com/developers/applications
2. Create a Bot and copy the token to your `.env` file
3. Enable the following Bot Permissions:
   - Send Messages
   - Use Slash Commands
   - Embed Links
   - Read Message History
   - Add Reactions
   - Manage Messages (for pagination)

4. Invite to your server with OAuth2 URL generator

### OpenAI Setup (Optional)

For AI-powered events and the Oracle system:

1. Get an OpenAI API key from https://platform.openai.com/
2. Set `OPENAI_ENABLED=true` in your `.env` file
3. Add your API key as `OPENAI_API_KEY=your_key_here`

Without OpenAI, the bot will use fallback templates for events.

## 🎮 How to Play

### Getting Started
1. Join a Discord server with the bot
2. Type `!create [name]` to create your character
3. Stay online (green status) to automatically participate in adventures and battles
4. Use `!help` to see all available commands

### Key Commands
- `!profile` - View your character stats and progress
- `!inventory` - Manage your equipment and items
- `!classes` - View class evolution paths
- `!evolve` - Evolve your class at levels 5, 10, 15, 20, 25, 30
- `!market` - Buy and sell items with other players
- `!epicstatus` - Check your epic adventure progress
- `!ask [question]` - Ask the AI Oracle about the game (if enabled)

### Progression System
- **Automatic Adventures**: Every 7-21 minutes while online
- **Battles**: Random PvP battles every 2-8 minutes
- **Epic Adventures**: High-tier adventures every 45 minutes (level 10+)
- **AI Events**: Unique events every 15 minutes (if OpenAI enabled)
- **Raids**: Group content every 35 minutes

## 🏗️ Architecture

### Directory Structure
```
discordrpg/
├── bot.py                 # Main bot class and startup
├── start.py              # Entry point
├── schema.sql            # Database schema
├── requirements.txt      # Python dependencies
├── classes/
│   ├── character.py      # Character classes and races
│   └── items.py          # Item generation and management
├── cogs/
│   ├── ai_events.py      # AI-powered dynamic events
│   ├── oracle.py         # AI game manual system
│   ├── character.py      # Character management
│   ├── combat.py         # PvP and battle systems
│   ├── economy.py        # Market and trading
│   ├── epic_adventures.py # High-tier adventures
│   ├── autoplay.py       # Automatic gameplay loops
│   ├── raids.py          # Group raid system
│   ├── religion.py       # Gods and blessings
│   ├── race.py           # Character races
│   └── ...               # Additional game systems
└── utils/
    └── database.py       # Database abstraction layer
```

### Key Systems

#### AI Event System
- Uses OpenAI GPT-4o-mini to generate unique events
- Creates thematic item names and narratives
- Handles 4 event types: Treasure, Mini Boss, World Event, Mystery
- Graceful fallback to hand-crafted templates

#### Class Evolution System
- 6 tiers of progression (Novice → Immortal)
- 7 distinct class paths with branching specializations
- All paths converge at Eternal (level 25) then Immortal (level 30)
- Dynamic stat bonuses based on class and tier

#### Database Design
- SQLite with proper normalization
- Transaction safety for concurrent operations
- Automatic backups and migration system
- Optimized queries with proper indexing

## 🔧 Configuration

### Environment Variables
See `.env.example` for all available configuration options.

### Game Balance
- XP Formula: `level = 1 + int((xp / 100) ** 0.5)`
- Item Stats: 1-50 total stats based on tier and rarity
- Success Rates: Modified by equipment, level, and luck
- Rewards: Scaled by race bonuses and divine blessings

### AI Configuration
- Model: GPT-4o-mini (cost-effective for frequent events)
- Rate Limiting: Handled with fallbacks
- Content Moderation: Family-friendly prompts and validation

## 📊 Monitoring

### Logging
- Comprehensive logging with rotation
- Error tracking and performance monitoring
- Event and reward logging for balance analysis

### Admin Commands
- `!aieventsstatus` - Check AI events system status
- Database backup and restoration tools
- Performance monitoring and statistics

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow existing patterns and conventions
- Add docstrings to new functions
- Keep AI prompts family-friendly
- Test with both AI enabled and disabled

### Adding New Features
- New game systems should follow the cog pattern
- Database changes require migration scripts
- AI features should have fallback implementations
- Document new commands in help system

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** - For AI-powered event generation and Oracle system
- **Discord.py** - For the excellent Discord bot framework
- **SQLite** - For reliable local database storage

## 📞 Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information about your setup and the problem

---

**Enjoy your AI-powered Discord RPG adventure!** 🎲✨