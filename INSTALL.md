# Installation Guide

## Quick Start (5 minutes)

### 1. Prerequisites
- Python 3.8 or higher
- Discord Developer Application
- Git (optional, for cloning)

### 2. Download & Setup
```bash
# Clone or download the repository
git clone https://github.com/yourusername/discordrpg.git
cd discordrpg

# Install dependencies
pip install -r requirements.txt

# Run setup script
python3 setup.py
```

### 3. Discord Bot Configuration
1. Go to https://discord.com/developers/applications
2. Create a New Application
3. Go to the "Bot" section
4. Create a Bot and copy the Token
5. Edit `.env` file and paste your token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

### 4. Discord Bot Permissions
When inviting the bot to your server, it needs these permissions:
- Send Messages
- Embed Links
- Add Reactions
- Read Message History
- Use Slash Commands
- Manage Messages (for pagination)

### 5. Start the Bot
```bash
python3 start.py
```

### 6. Test the Bot
In your Discord server:
```
!create YourCharacterName
!help
```

## Optional: AI Features

To enable AI-powered events and the Oracle system:

1. Get an OpenAI API key from https://platform.openai.com/
2. Edit `.env`:
   ```
   OPENAI_ENABLED=true
   OPENAI_API_KEY=your_openai_key_here
   ```
3. Restart the bot

Without OpenAI, the bot still works fully - AI features will use fallback templates.

## Troubleshooting

### Bot won't start
- Check your `.env` file has a valid Discord token
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check the console for error messages

### Database issues
- Delete `discordrpg.db` and run `python3 setup.py` again
- Make sure SQLite3 is available on your system

### Bot not responding in Discord
- Check the bot is online in your server
- Ensure the bot has proper permissions
- Try commands in a channel named `discordrpg`, `rpg`, `game`, or `bot`

### AI features not working
- Verify `OPENAI_ENABLED=true` in `.env`
- Check your OpenAI API key is valid
- The bot will fall back to templates if AI is unavailable

## Advanced Configuration

See the [README.md](README.md) for detailed configuration options and game mechanics.

## Support

- Check existing GitHub issues
- Create a new issue with detailed error information
- Include your Python version, OS, and any error messages