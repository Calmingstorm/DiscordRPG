# Installation Guide

## Prerequisites

- Python 3.8+
- MariaDB 10.5+ or MySQL 8.0+
- A Discord bot token ([create one here](https://discord.com/developers/applications))
- Git

Optional:
- OpenAI API key (for AI events, oracle, and personal quests)
- PHP 8.0+ with Apache/Nginx (for web leaderboard)

## 1. Clone and Install Dependencies

```bash
git clone https://github.com/Calmingstorm/DiscordRPG.git
cd DiscordRPG
pip install -r requirements.txt
```

## 2. Set Up MariaDB

```bash
# Install MariaDB (Ubuntu/Debian)
sudo apt install mariadb-server
sudo systemctl enable --now mariadb

# Secure installation
sudo mysql_secure_installation
```

Create the database and user:

```sql
sudo mysql -u root -p

CREATE DATABASE discordrpg CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'discordrpg'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON discordrpg.* TO 'discordrpg'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

Initialize the schema:

```bash
mysql -u discordrpg -p discordrpg < schema.sql
```

## 3. Configure the Bot

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```ini
DISCORD_TOKEN=your_discord_bot_token_here
BOT_PREFIX=!
DB_HOST=localhost
DB_USER=discordrpg
DB_PASS=your_secure_password
DB_NAME=discordrpg
```

Or run the interactive setup which checks everything for you:

```bash
python3 setup.py
```

## 4. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and name it
3. Go to **Bot** → click **Add Bot**
4. Copy the token and paste it in your `.env`
5. Enable these Privileged Gateway Intents:
   - **Presence Intent** (required for online detection)
   - **Server Members Intent** (required for auto-registration)
   - **Message Content Intent** (required for commands)

### Bot Invite Permissions

When generating an invite URL (OAuth2 → URL Generator), select these permissions:

- Send Messages
- Embed Links
- Add Reactions
- Read Message History
- Use Slash Commands
- Manage Messages (for pagination cleanup)

## 5. Start the Bot

```bash
python3 start.py
```

Test it in your Discord server:

```
!create YourCharacterName
!profile
!help
```

## Running as a systemd Service

For production deployments, run the bot as a system service:

```bash
sudo tee /etc/systemd/system/discordrpg.service > /dev/null << 'EOF'
[Unit]
Description=DiscordRPG Discord Bot
After=network-online.target mariadb.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/discordrpg
ExecStart=/usr/bin/python3 /opt/discordrpg/start.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=discordrpg
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now discordrpg
```

Adjust `WorkingDirectory` and `ExecStart` to match your install path. Logs are available via `journalctl -u discordrpg -f`.

## Optional: AI Features

To enable AI-powered dynamic events, the Oracle system, and personal quest lines:

1. Get an API key from [OpenAI](https://platform.openai.com/)
2. Edit `.env`:
   ```ini
   OPENAI_ENABLED=true
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. Restart the bot

Without OpenAI, the bot works fully — AI features fall back to handcrafted templates.

## Optional: Web Leaderboard

The `web/` directory contains a PHP leaderboard dashboard that connects to the same MariaDB database.

### Setup with Apache

```bash
# Install PHP and Apache (if not already installed)
sudo apt install apache2 php php-mysql libapache2-mod-php

# Copy web files to your web root
sudo cp -r web/ /var/www/html/discordrpg/

# The web app reads credentials from the bot's .env file.
# Edit web/db_config.php and update the $env_path variable to point
# to your actual .env file location:
sudo nano /var/www/html/discordrpg/db_config.php
```

In `db_config.php`, update the path:

```php
$env_path = '/path/to/your/DiscordRPG/.env';
```

The leaderboard will be available at `http://your-server/discordrpg/`.

### Pages

- `index.php` — Player leaderboard (level, gold, XP rankings)
- `top-items.php` — Equipment leaderboard (best items by stat)
- `guide.php` — Game guide for players

## Automated Backups

The bot includes a backup cog (`cogs/backup.py`) that creates database dumps using `mysqldump`:

- **Hourly backups**: Kept for 24 hours
- **Daily backups**: Kept for 30 days
- Backups are stored in a `backups/` directory (excluded from git)

The backup system runs automatically — no additional configuration needed. Requires `mysqldump` to be available on the system (installed with the MariaDB client package).

## Troubleshooting

### Bot won't start
- Check `.env` has a valid Discord token
- Verify MariaDB is running: `systemctl status mariadb`
- Test DB connection: `mysql -u discordrpg -p discordrpg -e "SELECT 1"`
- Check dependencies: `pip install -r requirements.txt`

### Bot not responding in Discord
- Verify the bot is online in your server member list
- Ensure all three Privileged Gateway Intents are enabled
- Check the bot has proper channel permissions
- The bot auto-detects channels named `discordrpg`, `rpg`, `game`, or `bot`

### Database errors
- Ensure the schema is loaded: `mysql -u discordrpg -p discordrpg < schema.sql`
- Check MariaDB charset: database should use `utf8mb4`

### AI features not working
- Verify `OPENAI_ENABLED=true` in `.env`
- Check your OpenAI API key is valid and has credits
- The bot logs AI errors — check `journalctl -u discordrpg` for details
- AI features degrade gracefully to templates if the API is unavailable

## Support

- Check [existing issues](https://github.com/Calmingstorm/DiscordRPG/issues) on GitHub
- Open a new issue with your Python version, OS, and error output
