"""Help system for DiscordRPG"""
import discord
from discord.ext import commands

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog

class HelpCog(DiscordRPGCog):
    """Help and information commands"""
    
    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context, command_name: str = None):
        """Get help for commands"""
        
        if command_name:
            # Show help for specific command
            command = ctx.bot.get_command(command_name)
            if not command:
                await ctx.send(f"❌ Command `{command_name}` not found!")
                return
                
            embed = self.embed(
                f"Help: {command.name}",
                command.help or "No description available"
            )
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            if command.signature:
                embed.add_field(name="Usage", value=f"`{ctx.prefix}{command.name} {command.signature}`", inline=False)
                
            await ctx.send(embed=embed)
            return
            
        # Show general help
        embed = self.embed(
            "🎮 DiscordRPG Commands",
            "**Welcome to DiscordRPG!** A full-featured automatic RPG experience."
        )
        
        # Character Management
        char_commands = [
            "`!create [name]` - Join the game",
            "`!profile [@user]` - View character stats",
            "`!classes` - View class evolution tree", 
            "`!classbonuses [class]` - Show class benefits",
            "`!evolve` - Evolve your class",
            "`!races` - View available races",
            "`!race <name>` - Select race (permanent!)",
            "`!align <good/neutral/evil>` - Set alignment",
            "`!removeme` - Delete character"
        ]
        embed.add_field(
            name="👤 **Character**",
            value="\n".join(char_commands),
            inline=True
        )
        
        # Equipment & Items
        item_commands = [
            "`!inventory` - View your items & crates",
            "`!equipment` - View equipped gear",
            "`!equip <id>` - Equip an item",
            "`!sell <id>` - Sell item to merchant",
            "`!give <user> <id>` - Give item to player",
            "`!crate <type>` - Open a crate"
        ]
        embed.add_field(
            name="⚔️ **Equipment**",
            value="\n".join(item_commands),
            inline=True
        )
        
        # Economy & Trading
        economy_commands = [
            "`!market` - Browse marketplace",
            "`!buy <id>` - Purchase item",
            "`!offer <id> <price>` - List item for sale",
            "`!withdraw <id>` - Remove item from market", 
            "`!daily` - Daily login rewards"
        ]
        embed.add_field(
            name="💰 **Economy**",
            value="\n".join(economy_commands),
            inline=True
        )
        
        # Gambling & Games
        gambling_commands = [
            "`!gamble <amount>` - 40% chance double money",
            "`!coinflip <amount> <h/t>` - 50/50 coin toss",
            "`!slots <amount>` - Slot machine game",
            "`!blackjack <amount>` - Play blackjack",
            "`!diceroll <amount>` - Roll vs house"
        ]
        embed.add_field(
            name="🎰 **Gambling**",
            value="\n".join(gambling_commands),
            inline=True
        )
        
        # Religion & Gods
        religion_commands = [
            "`!gods` - View available deities",
            "`!choose <god>` - Pick deity (permanent!)",
            "`!pray` - Gain favor (4hr cooldown)",
            "`!sacrifice <gold>` - Offer gold for favor (12hr cd)",
            "`!bless [type]` - Spend favor on divine blessings"
        ]
        embed.add_field(
            name="🏛️ **Religion**",
            value="\n".join(religion_commands),
            inline=True
        )
        
        # Combat & PvP
        combat_commands = [
            "`!battle <@user> [bet]` - Challenge player (with optional gold bet)",
            "`!battles` - Battle system guide",
            "`!battlestatus` - Check battle system",
            "`!tournament <prize>` - Host tournament",
            "`!smite @user` - Divine smiting (20k gold)",
            "`!online` - See online players"
        ]
        embed.add_field(
            name="⚔️ **Combat**",
            value="\n".join(combat_commands),
            inline=True
        )
        
        # Adventures
        adventure_commands = [
            "`!epicstatus` - Check epic/legendary status",
            "`!epicadventures` - Epic system info"
        ]
        embed.add_field(
            name="🗺️ **Adventures**",
            value="\n".join(adventure_commands),
            inline=True
        )

        # Personal Quests
        quest_commands = [
            "`!quest` - View active quest progress",
            "`!questhistory` - View completed quests",
            "`!abandonquest` - Abandon current quest"
        ]
        embed.add_field(
            name="📜 **Personal Quests**",
            value="\n".join(quest_commands),
            inline=True
        )

        # Raids & Events
        raid_commands = [
            "`!raids` - Raid system info",
            "`!raidstatus` - Check active raids"
        ]
        embed.add_field(
            name="🏰 **Raids**",
            value="\n".join(raid_commands),
            inline=True
        )
        
        # System & Info
        system_commands = [
            "`!autoplay status` - Check auto-game",
            "`!status` - Check adventure status",
            "`!help <command>` - Command details",
            "`!ask <question>` - Living Game Manual",
            "`!ping` - Check bot latency"
        ]
        
        embed.add_field(
            name="🔧 **System**",
            value="\n".join(system_commands),
            inline=True
        )
        
        # Quick Start Guide
        embed.add_field(
            name="🚀 **Quick Start**",
            value="1. `!create` to join • 2. **Stay online** (green status) for auto-progression • 3. `!profile` to track progress • 4. `!evolve` at level 5+",
            inline=False
        )
        
        # Auto-play reminder
        embed.add_field(
            name="🤖 **Auto-Play System**",
            value="🟢 **MUST BE ONLINE** (green Discord status) for adventures/battles/raids • Away/DND/Invisible = NO progression",
            inline=False
        )
        
        embed.set_footer(text="💡 Use !help <command> for detailed help on any command")
        await ctx.send(embed=embed)
        
    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Check bot latency"""
        latency = round(ctx.bot.latency * 1000)
        embed = self.embed(
            "🏓 Pong!",
            f"Bot latency: **{latency}ms**"
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    async def info(self, ctx: commands.Context):
        """Show bot information"""
        embed = self.embed(
            "🎮 DiscordRPG Bot",
            "A full-featured DiscordRPG implementation for Discord"
        )
        embed.add_field(name="Language", value="Python", inline=True)
        embed.add_field(name="Library", value="discord.py", inline=True)
        embed.add_field(name="Database", value="SQLite", inline=True)
        embed.add_field(name="Servers", value=len(ctx.bot.guilds), inline=True)
        embed.add_field(name="Users", value="Many!", inline=True)
        
        embed.add_field(
            name="Features Implemented",
            value="• Character creation & customization\n• 50+ classes with evolution\n• 10 races with bonuses\n• Equipment system\n• Profile system",
            inline=False
        )
        
        embed.add_field(
            name="Coming Soon",
            value="• Combat & battles\n• Guilds & alliances\n• Economy & trading\n• Adventures & quests\n• Special events",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCog(bot))