"""Auto-registration system and chat penalties for DiscordRPG"""
import discord
from discord.ext import commands
import math
from datetime import datetime, timezone, timedelta
import re
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog

# EST timezone
EST = timezone(timedelta(hours=-5))

class AutoRegisterCog(DiscordRPGCog):
    """Automatic registration and penalty system"""
    
    async def cog_load(self):
        """Register all existing members when cog loads"""
        # Don't block cog loading - do this in background
        asyncio.create_task(self.delayed_registration())
        
    async def delayed_registration(self):
        """Wait for bot to be ready, then register members"""
        try:
            await self.bot.wait_until_ready()
            await asyncio.sleep(10)  # Wait extra time for everything to be ready
            await self.auto_register_existing_members()
        except Exception as e:
            print(f"Error in delayed registration: {e}")
        
    async def auto_register_existing_members(self):
        """Register all existing server members who don't have characters"""
        try:
            print("Starting auto-registration...")
            registered_count = 0
            for guild in self.bot.guilds:
                print(f"Checking guild: {guild.name} ({len(guild.members)} members)")
                for member in guild.members:
                    if member.bot:
                        continue
                        
                    try:
                        # Atomic check and create to prevent race conditions
                        # Use INSERT OR IGNORE to handle concurrent registrations
                        existing_char = self.db.fetchone(
                            "SELECT user_id FROM profile WHERE user_id = ?",
                            (member.id,)
                        )
                        
                        if not existing_char:
                            success = await self.create_character_for_member_atomic(member)
                            if success:
                                registered_count += 1
                                print(f"Registered: {member.display_name}")
                    except Exception as e:
                        print(f"Error registering {member.name}: {e}")
                        continue
            print(f"Auto-registration completed! Registered {registered_count} members.")
        except Exception as e:
            print(f"Error in auto_register_existing_members: {e}")
            
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def register_all(self, ctx: commands.Context):
        """Manually trigger auto-registration (admin only)"""
        await ctx.send("🔄 Starting manual auto-registration...")
        await self.auto_register_existing_members()
        
        # Check results
        total_chars = len(self.db.fetchall("SELECT user_id FROM profile"))
        await ctx.send(f"✅ Auto-registration complete! Total characters: {total_chars}")
    
    async def create_character_for_member_atomic(self, member: discord.Member) -> bool:
        """Create a character for a member atomically to prevent race conditions"""
        try:
            # Use member's display name as character name
            char_name = member.display_name[:32]  # Limit to 32 chars
            
            # Use INSERT OR IGNORE to handle concurrent registrations atomically
            cursor = self.db.execute(
                """INSERT OR IGNORE INTO profile 
                   (user_id, name, level, xp, money, race, class, health, speed, luck, created_at)
                   VALUES (?, ?, 1, 0, 100, 'Human', 'Novice', 100, 1, 1, ?)""",
                (member.id, char_name, datetime.now().isoformat())
            )
            
            # Check if the insert actually happened (rowcount > 0)
            if cursor.rowcount > 0:
                self.db.commit()
                return True
            else:
                # Character already existed, created by another process
                return False
                
        except Exception as e:
            print(f"Error creating character for {member.name}: {e}")
            return False
                    
    async def create_character_for_member(self, member: discord.Member):
        """Create a character for a member automatically"""
        try:
            # Use member's display name as character name
            char_name = member.display_name[:32]  # Limit to 32 chars
            
            # Create character with default stats
            self.db.execute(
                """INSERT INTO profile (user_id, name, money, xp, level, class, race, 
                   pvpwins, pvplosses, deaths, kills, completed, luck, created_at, has_character)
                   VALUES (?, ?, 100, 0, 1, 'Novice', 'Human', 0, 0, 0, 0, 0, 1.0, ?, 1)""",
                (member.id, char_name, datetime.now(EST))
            )
            
            # Create starter items
            self.db.execute(
                "INSERT INTO inventory (owner, name, type, value, damage, armor, hand) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (member.id, "Starter Sword", "Sword", 10, 3, 0, "left")
            )
            self.db.execute(
                "INSERT INTO inventory (owner, name, type, value, damage, armor, hand) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (member.id, "Starter Shield", "Shield", 10, 0, 3, "right")
            )
            
            # Set character alignment to neutral by default
            self.db.execute(
                "UPDATE profile SET alignment = 'neutral' WHERE user_id = ?",
                (member.id,)
            )
            
            self.db.commit()
            
            # Find game channel to announce
            game_channel = None
            for channel in member.guild.text_channels:
                if channel.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                    game_channel = channel
                    break
                    
            if game_channel:
                embed = self.embed(
                    "🎮 Auto-Registered!",
                    f"**{member.display_name}** has been automatically entered into DiscordRPG as **{char_name}**!"
                )
                embed.add_field(name="To Opt Out", value="Use `!removeme` to delete your character", inline=False)
                embed.add_field(name="To Play", value="Just idle! Talking gives penalties. Use `!help` for commands", inline=False)
                await game_channel.send(embed=embed)
                
        except Exception as e:
            print(f"Error auto-registering {member.name}: {e}")
            
    @commands.command(aliases=["optout", "delete", "quit"])
    async def removeme(self, ctx: commands.Context):
        """Remove your character from DiscordRPG"""
        char = self.db.get_character(ctx.author.id)
        if not char:
            await ctx.send("❌ You don't have a character to remove!")
            return
            
        # Confirm deletion
        if not await ctx.confirm(
            f"Are you sure you want to delete **{char['name']}**?\\n"
            f"Level {char['level']} • {char['xp']:,} XP • {char['money']:,} gold\\n"
            f"This action cannot be undone!"
        ):
            await ctx.send("Character deletion cancelled.")
            return
            
        # Delete character and all related data
        self.db.execute("DELETE FROM profile WHERE user_id = ?", (ctx.author.id,))
        self.db.execute("DELETE FROM inventory WHERE owner = ?", (ctx.author.id,))
        self.db.execute("DELETE FROM adventures WHERE user_id = ?", (ctx.author.id,))
        self.db.execute("DELETE FROM market WHERE owner = ?", (ctx.author.id,))
        self.db.commit()
        
        embed = self.success_embed(
            f"Character **{char['name']}** has been deleted.\\n"
            f"Thank you for playing DiscordRPG!"
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)  # 1 use per 5 seconds per user
    async def align(self, ctx: commands.Context, alignment: str):
        """Change your alignment (good/neutral/evil)"""
        import logging
        logger = logging.getLogger('DiscordRPG')
        logger.info(f"ALIGN command called by {ctx.author.name} with alignment {alignment}")
        
        if alignment.lower() not in ['good', 'neutral', 'evil']:
            await ctx.send("❌ Alignment must be: good, neutral, or evil")
            return
            
        char = self.db.get_character(ctx.author.id)
        if not char:
            await ctx.send("❌ You need a character first!")
            return
            
        self.db.execute(
            "UPDATE profile SET alignment = ? WHERE user_id = ?",
            (alignment.lower(), ctx.author.id)
        )
        self.db.commit()
        
        effects = {
            'good': "+10% battle power, 1/12 daily blessing chance, 1/50 crit chance",
            'neutral': "No bonuses or penalties",  
            'evil': "-10% battle power, 1/8 daily steal/forsaken chance, 1/20 crit chance"
        }
        
        embed = self.embed(
            f"⚖️ Alignment Changed to {alignment.title()}",
            f"Effects: {effects[alignment.lower()]}"
        )
        await ctx.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto-register new members"""
        if member.bot:
            return
            
        await self.create_character_for_member(member)
        
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Apply penalties for talking in game channels"""
        # Skip DMs, bots, and commands
        if not message.guild or message.author.bot or message.content.startswith(self.bot.prefix):
            return
            
        # Only apply penalties in game channels
        if message.channel.name.lower() not in ['discordrpg', 'rpg', 'game', 'bot']:
            return
            
        # Skip if message is only emojis/reactions
        emoji_pattern = re.compile(r'^(<a?:[a-zA-Z0-9_]+:[0-9]+>|[\U00010000-\U0010FFFF]|\\s)+$')
        if emoji_pattern.match(message.content):
            return
            
        # Get character
        char = self.db.get_character(message.author.id)
        if not char:
            return
            
        # Calculate penalty: message_length * (1.14 ^ level)
        msg_length = len(message.content)
        penalty_seconds = int(msg_length * math.pow(1.14, char['level']))
        
        # Apply penalty to next level time
        self.db.execute(
            """INSERT INTO penalties (user_id, penalty_type, penalty_seconds, applied_at)
               VALUES (?, 'chat', ?, ?)""",
            (message.author.id, penalty_seconds, datetime.now(EST))
        )
        self.db.commit()
        
        # Don't announce every penalty (would be spammy)
        # Only announce significant penalties (over 60 seconds)
        if penalty_seconds >= 60:
            await message.channel.send(
                f"💬 **{char['name']}** penalized {penalty_seconds}s for talking ({msg_length} chars)",
                delete_after=10  # Auto-delete after 10 seconds
            )
            
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Apply penalties for nick changes"""
        if before.nick == after.nick or after.bot:
            return
            
        char = self.db.get_character(after.id)
        if not char:
            return
            
        # Nick change penalty: 30 * (1.14 ^ level)
        penalty_seconds = int(30 * math.pow(1.14, char['level']))
        
        self.db.execute(
            """INSERT INTO penalties (user_id, penalty_type, penalty_seconds, applied_at)
               VALUES (?, 'nick', ?, ?)""",
            (after.id, penalty_seconds, datetime.now(EST))
        )
        self.db.commit()
        
        # Find game channel
        for channel in after.guild.text_channels:
            if channel.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                await channel.send(
                    f"📝 **{char['name']}** penalized {penalty_seconds}s for changing nick",
                    delete_after=10
                )
                break

async def setup(bot):
    await bot.add_cog(AutoRegisterCog(bot))