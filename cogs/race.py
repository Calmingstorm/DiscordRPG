"""Race system for DiscordRPG"""
import discord
from discord.ext import commands
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog
from utils.database import Database

class RaceCog(DiscordRPGCog):
    """Race selection and management"""
    
    @staticmethod
    def get_race_multipliers(user_id: int) -> dict:
        """Get race multipliers for a user"""
        from utils.database import Database
        db = Database()
        char = db.get_character(user_id)
        if not char:
            return {"luck": 1.0, "xp_gain": 1.0, "gold_find": 1.0, "favor_gain": 1.0}
        
        race_name = char.get('race', 'Human').lower()
        if race_name in RaceCog.RACES:
            return RaceCog.RACES[race_name]["bonuses"]
        
        # Default to human bonuses
        return {"luck": 1.0, "xp_gain": 1.1, "gold_find": 1.0, "favor_gain": 1.0}
    
    RACES = {
        "human": {
            "name": "Human",
            "description": "Balanced and adaptable, humans excel in all areas without specialization",
            "bonuses": {
                "luck": 1.0,
                "xp_gain": 1.1,
                "gold_find": 1.0,
                "favor_gain": 1.0
            }
        },
        "elf": {
            "name": "Elf", 
            "description": "Graceful and magical beings with enhanced luck and favor with the gods",
            "bonuses": {
                "luck": 1.2,
                "xp_gain": 1.0,
                "gold_find": 0.9,
                "favor_gain": 1.3
            }
        },
        "dwarf": {
            "name": "Dwarf",
            "description": "Stout warriors skilled in crafting and finding treasure",
            "bonuses": {
                "luck": 0.9,
                "xp_gain": 0.9,
                "gold_find": 1.4,
                "favor_gain": 0.8
            }
        },
        "orc": {
            "name": "Orc",
            "description": "Brutal fighters who gain experience quickly through combat",
            "bonuses": {
                "luck": 0.8,
                "xp_gain": 1.3,
                "gold_find": 0.8,
                "favor_gain": 0.7
            }
        },
        "halfling": {
            "name": "Halfling",
            "description": "Small and lucky folk blessed by fortune",
            "bonuses": {
                "luck": 1.4,
                "xp_gain": 0.8,
                "gold_find": 1.1,
                "favor_gain": 1.1
            }
        },
        "gnome": {
            "name": "Gnome", 
            "description": "Tiny inventors with incredible luck and divine favor",
            "bonuses": {
                "luck": 1.3,
                "xp_gain": 0.9,
                "gold_find": 1.0,
                "favor_gain": 1.2
            }
        },
        "dragonborn": {
            "name": "Dragonborn",
            "description": "Proud descendants of dragons with balanced abilities",
            "bonuses": {
                "luck": 1.0,
                "xp_gain": 1.1,
                "gold_find": 1.1,
                "favor_gain": 0.9
            }
        },
        "tiefling": {
            "name": "Tiefling",
            "description": "Infernal beings with enhanced luck but reduced divine favor",
            "bonuses": {
                "luck": 1.2,
                "xp_gain": 1.0,
                "gold_find": 1.2,
                "favor_gain": 0.5
            }
        },
        "undead": {
            "name": "Undead",
            "description": "Cursed beings immune to divine favor but with supernatural luck",
            "bonuses": {
                "luck": 1.5,
                "xp_gain": 0.7,
                "gold_find": 0.9,
                "favor_gain": 0.0
            }
        },
        "demon": {
            "name": "Demon",
            "description": "Evil entities with incredible luck and gold finding but no divine favor",
            "bonuses": {
                "luck": 1.6,
                "xp_gain": 0.8,
                "gold_find": 1.3,
                "favor_gain": 0.0
            }
        }
    }
    
    @commands.command()
    async def races(self, ctx: commands.Context):
        """Show all available races and their bonuses"""
        embed = self.embed(
            "🧬 Available Races",
            "Choose your character's race to gain unique bonuses. **Race selection is permanent!**"
        )
        
        for race_key, race_data in self.RACES.items():
            bonuses = race_data["bonuses"]
            bonus_text = []
            
            if bonuses["luck"] != 1.0:
                bonus_text.append(f"Luck: {bonuses['luck']:.1f}x")
            if bonuses["xp_gain"] != 1.0:
                bonus_text.append(f"XP Gain: {bonuses['xp_gain']:.1f}x")  
            if bonuses["gold_find"] != 1.0:
                bonus_text.append(f"Gold Find: {bonuses['gold_find']:.1f}x")
            if bonuses["favor_gain"] != 1.0:
                bonus_text.append(f"Favor Gain: {bonuses['favor_gain']:.1f}x")
            
            embed.add_field(
                name=race_data['name'],
                value=f"{race_data['description']}\n**Bonuses:** {' • '.join(bonus_text) if bonus_text else 'Balanced'}",
                inline=False
            )
        
        embed.add_field(
            name="📝 How to Choose",
            value="Use `!race <name>` (e.g., `!race elf`) to select your race. This choice is **permanent** and cannot be changed!",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def race(self, ctx: commands.Context, race_name: str = None):
        """Select your character's race (permanent choice)"""
        if not race_name:
            await ctx.send("❌ Please specify a race! Use `!races` to see available options.")
            return
        
        # Check if player exists
        db = Database()
        player = db.get_profile(ctx.author.id)
        if not player:
            await ctx.send("❌ You need to create a character first! Use `!create <name>` to join the game.")
            return
        
        # Check if race is valid
        race_name = race_name.lower()
        if race_name not in self.RACES:
            await ctx.send(f"❌ Invalid race `{race_name}`! Use `!races` to see available options.")
            return
        
        # Check if player already has a non-human race
        if player.race != "Human":
            await ctx.send(f"❌ You've already chosen your race: **{player.race}**. Race selection is permanent!")
            return
        
        race_data = self.RACES[race_name]
        
        # Confirmation message
        embed = self.embed(
            f"🧬 Select {race_data['name']}?",
            f"**{race_data['description']}**"
        )
        
        bonuses = race_data["bonuses"]
        bonus_text = []
        
        if bonuses["luck"] != 1.0:
            bonus_text.append(f"Luck: {bonuses['luck']:.1f}x")
        if bonuses["xp_gain"] != 1.0:
            bonus_text.append(f"XP Gain: {bonuses['xp_gain']:.1f}x")  
        if bonuses["gold_find"] != 1.0:
            bonus_text.append(f"Gold Find: {bonuses['gold_find']:.1f}x")
        if bonuses["favor_gain"] != 1.0:
            bonus_text.append(f"Favor Gain: {bonuses['favor_gain']:.1f}x")
        
        embed.add_field(
            name="🎯 Racial Bonuses",
            value=' • '.join(bonus_text) if bonus_text else 'Balanced (no bonuses)',
            inline=False
        )
        
        embed.add_field(
            name="⚠️ Important",
            value="**This choice is PERMANENT and cannot be changed!**\nReact with ✅ to confirm or ❌ to cancel.",
            inline=False
        )
        
        message = await ctx.send(embed=embed)
        await message.add_reaction("✅")
        await message.add_reaction("❌")
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == message.id)
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                embed = self.embed("❌ Race Selection Cancelled", "You can choose a race anytime with `!race <name>`.")
                await message.edit(embed=embed)
                return
            
            # Update player's race
            db.update_profile(ctx.author.id, race=race_data['name'])
            
            embed = self.embed(
                f"🧬 Race Selected: {race_data['name']}!",
                f"**{player.name}** is now a **{race_data['name']}**!\n\n{race_data['description']}"
            )
            
            if bonus_text:
                embed.add_field(
                    name="🎯 Your Racial Bonuses",
                    value=' • '.join(bonus_text),
                    inline=False
                )
            
            embed.add_field(
                name="💡 Tip",
                value="These bonuses are now permanently applied to your character!",
                inline=False
            )
            
            await message.edit(embed=embed)
            
        except asyncio.TimeoutError:
            embed = self.embed("⏰ Selection Timed Out", "Race selection cancelled. Use `!race <name>` to try again.")
            await message.edit(embed=embed)
    
    @commands.command()
    async def raceinfo(self, ctx: commands.Context, race_name: str = None):
        """Get detailed information about a specific race"""
        if not race_name:
            await ctx.send("❌ Please specify a race! Use `!races` to see all available races.")
            return
        
        race_name = race_name.lower()
        if race_name not in self.RACES:
            await ctx.send(f"❌ Invalid race `{race_name}`! Use `!races` to see available options.")
            return
        
        race_data = self.RACES[race_name]
        bonuses = race_data["bonuses"]
        
        embed = self.embed(
            f"🧬 {race_data['name']} Information",
            race_data['description']
        )
        
        # Show detailed bonuses
        bonus_details = []
        if bonuses["luck"] != 1.0:
            bonus_details.append(f"**Luck:** {bonuses['luck']:.1f}x (affects gambling, item finds, critical hits)")
        if bonuses["xp_gain"] != 1.0:
            bonus_details.append(f"**XP Gain:** {bonuses['xp_gain']:.1f}x (experience from adventures and battles)")  
        if bonuses["gold_find"] != 1.0:
            bonus_details.append(f"**Gold Find:** {bonuses['gold_find']:.1f}x (gold from all sources)")
        if bonuses["favor_gain"] != 1.0:
            bonus_details.append(f"**Favor Gain:** {bonuses['favor_gain']:.1f}x (favor from prayers and sacrifices)")
        
        if bonus_details:
            embed.add_field(
                name="🎯 Racial Bonuses",
                value='\n'.join(bonus_details),
                inline=False
            )
        else:
            embed.add_field(
                name="🎯 Racial Bonuses", 
                value="Balanced - no specific bonuses or penalties",
                inline=False
            )
        
        embed.add_field(
            name="📝 How to Select",
            value=f"Use `!race {race_name}` to choose this race (permanent choice!)",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RaceCog(bot))