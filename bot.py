#!/usr/bin/env python3
"""
Full-featured DiscordRPG Discord Bot
Implements all major features from the original DiscordRPG
"""
import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

# EST timezone
EST = timezone(timedelta(hours=-5))

from utils.database import Database

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DiscordRPG')

class DiscordRPGBot(commands.Bot):
    """Main bot class with all DiscordRPG features"""
    
    def __init__(self):
        # Bot configuration - ENABLE PRIVILEGED INTENTS IN DISCORD DEVELOPER PORTAL
        # Go to https://discord.com/developers/applications/ -> Your App -> Bot -> Privileged Gateway Intents
        # Enable "Message Content Intent", "Server Members Intent", and "Presence Intent" for full functionality
        intents = discord.Intents.default()
        intents.message_content = True  # Required for commands to work
        intents.members = True  # Needed for auto-registration - re-enabled
        intents.dm_messages = True  # Allow DM commands
        intents.presences = True  # Required to see user status (online/offline/idle/dnd)
        
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            description="A full-featured DiscordRPG bot for Discord"
        )
        
        # Get configuration from environment
        self.token = os.getenv('DISCORD_TOKEN')
        self.prefix = os.getenv('BOT_PREFIX', '!')
        self.db_path = os.getenv('DATABASE_PATH', './discordrpg.db')
        
        if not self.token:
            logger.error("DISCORD_TOKEN not found in environment variables!")
            raise ValueError("Missing Discord token")
        
        # Database connection
        self.db: Optional[Database] = None
        
        # Cache for various data
        self.prefixes = {}  # Guild-specific prefixes
        self.cooldowns = {}  # User cooldowns
        self.adventures = {}  # Active adventures
        
        # Constants
        self.primary_color = discord.Color(0xFF6B6B)
        self.error_color = discord.Color(0xFF0000)
        self.success_color = discord.Color(0x00FF00)
            
    async def get_prefix(self, message: discord.Message) -> str:
        """Get the prefix for a guild or DM"""
        if not message.guild:
            return self.prefix  # Use default prefix in DMs
            
        if message.guild.id not in self.prefixes:
            # Load from database
            if self.db:
                row = self.db.fetchone(
                    "SELECT prefix FROM server_settings WHERE guild_id = ?",
                    (message.guild.id,)
                )
                # Convert sqlite3.Row to dict to safely access values
                prefix = self.db.row_to_dict(row)['prefix'] if row else self.prefix
                self.prefixes[message.guild.id] = prefix
            else:
                self.prefixes[message.guild.id] = self.prefix
                
        return self.prefixes[message.guild.id]
    
    async def setup_hook(self):
        """Initialize bot components"""
        # Connect to SQLite database
        self.db = Database(self.db_path)
        self.db.init_database()
        logger.info(f"Initialized SQLite database at {self.db_path}")
        
        # Load cogs
        await self.load_cogs()
        
    async def load_cogs(self):
        """Load all cog extensions"""
        # Load all available cogs
        cog_files = [
            "cogs.auto_register",  # Auto-registration and penalties
            "cogs.character",
            "cogs.help",
            "cogs.inventory",
            "cogs.combat", 
            "cogs.adventure",
            "cogs.epic_adventures",  # Epic and legendary adventures
            "cogs.economy",
            "cogs.daily",
            "cogs.gambling",
            "cogs.religion",  # Gods, prayer, and sacrifice
            "cogs.race",  # Race selection and bonuses
            "cogs.autoplay",  # Automatic gameplay system
            "cogs.raids",  # Automatic raid system
            "cogs.oracle",  # AI-powered game manual and help system
            "cogs.ai_events",  # AI-powered dynamic event generation
            "cogs.backup",  # Database backup system
            "cogs.blacksmith",  # Dismantle, reforge, upgrade items
        ]
        
        for cog in cog_files:
            try:
                await self.load_extension(cog)
                logger.info(f"Loaded cog: {cog}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog}: {e}")
                
    async def on_ready(self):
        """Bot is ready"""
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guilds")
        
        # Set status
        await self.change_presence(
            activity=discord.Game(name=f"{self.prefix}help | DiscordRPG"),
            status=discord.Status.online
        )
        
    async def on_guild_join(self, guild: discord.Guild):
        """Bot joined a new guild"""
        logger.info(f"Joined guild: {guild.name} (ID: {guild.id})")
        
        # Create server settings
        if self.db:
            self.db.execute(
                """INSERT OR IGNORE INTO server_settings (guild_id, prefix) 
                   VALUES (?, ?)""",
                (guild.id, self.prefix)
            )
            self.db.commit()
            
    async def process_commands(self, message: discord.Message):
        """Process commands with channel restrictions"""
        # Only process commands in DMs or the designated discordrpg channel
        if message.guild is not None:  # Not a DM
            if message.channel.name.lower() not in ['discordrpg', 'rpg', 'game', 'bot']:
                return  # Ignore commands in other channels
        
        await super().process_commands(message)

    async def on_command_error(self, ctx: commands.Context, error: Exception):
        """Handle command errors"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You don't have permission to use this command")
        else:
            logger.error(f"Unhandled error in {ctx.command}: {error}", exc_info=error)
            await ctx.send("❌ An unexpected error occurred")
            
    async def close(self):
        """Cleanup on bot shutdown"""
        if self.db:
            self.db.close()
        await super().close()
        
    def run(self):
        """Run the bot"""
        super().run(self.token)

# Utility functions for cogs
class DiscordRPGCog(commands.Cog):
    """Base class for DiscordRPG cogs"""
    
    def __init__(self, bot: DiscordRPGBot):
        self.bot = bot
        
    @property
    def db(self) -> Database:
        return self.bot.db
        
    def has_character(self, user_id: int) -> bool:
        """Check if user has a character"""
        char = self.db.get_character(user_id)
        return char is not None
        
    def get_character_field(self, user_id: int, field: str):
        """Get a specific field from character"""
        # Validate field name to prevent SQL injection
        valid_fields = {
            'user_id', 'name', 'level', 'xp', 'money', 'race', 'class', 'health', 
            'speed', 'luck', 'religion', 'adventure_cooldown', 'daily_streak',
            'last_daily', 'created_at'
        }
        if field not in valid_fields:
            return None
            
        row = self.db.fetchone(
            f"SELECT {field} FROM profile WHERE user_id = ?",
            (user_id,)
        )
        return self.db.row_to_dict(row)[field] if row else None
        
    def embed(self, title: str, description: str = None, 
              color: Optional[discord.Color] = None) -> discord.Embed:
        """Create a standard embed"""
        return discord.Embed(
            title=title,
            description=description,
            color=color or self.bot.primary_color,
            timestamp=datetime.now(EST)
        )
        
    def success_embed(self, description: str) -> discord.Embed:
        """Create a success embed"""
        return self.embed("✅ Success", description, self.bot.success_color)
        
    def error_embed(self, description: str) -> discord.Embed:
        """Create an error embed"""
        return self.embed("❌ Error", description, self.bot.error_color)

# Character check decorator
def has_character():
    """Check if user has a character"""
    async def predicate(ctx: commands.Context):
        if ctx.bot.db:
            char = ctx.bot.db.get_character(ctx.author.id)
            if not char:
                await ctx.send("❌ You need to create a character first! Use `!create`")
                return False
            return True
        return False
    return commands.check(predicate)

# Add confirmation method to Context
async def confirm(ctx: commands.Context, message: str, timeout: float = 30.0) -> bool:
    """Ask user to confirm an action"""
    embed = discord.Embed(
        title="❓ Confirmation",
        description=f"{message}\n\nReact with ✅ to confirm or ❌ to cancel.",
        color=0xFFAA00
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    
    def check(reaction, user):
        return (user == ctx.author and 
                str(reaction.emoji) in ["✅", "❌"] and 
                reaction.message.id == msg.id)
    
    try:
        reaction, user = await ctx.bot.wait_for('reaction_add', timeout=timeout, check=check)
        await msg.delete()
        return str(reaction.emoji) == "✅"
    except asyncio.TimeoutError:
        await msg.delete()
        return False

# Monkey patch the confirmation method onto Context
commands.Context.confirm = confirm

# Cooldown check
def cooldown_check(cooldown_name: str, seconds: int):
    """Check if user is on cooldown for specific action"""
    async def predicate(ctx: commands.Context):
        cooldowns = await ctx.bot.db.get_cooldowns(ctx.author.id)
        last_use = cooldowns.get(cooldown_name)
        
        if last_use:
            time_passed = (datetime.now(EST) - last_use).total_seconds()
            if time_passed < seconds:
                remaining = seconds - time_passed
                await ctx.send(f"⏰ You can use this again in {remaining:.0f} seconds")
                return False
                
        return True
    return commands.check(predicate)

if __name__ == "__main__":
    bot = DiscordRPGBot()
    bot.run()