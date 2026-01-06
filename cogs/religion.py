"""Religion system - gods, prayer, and sacrifice"""
import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character

class ReligionCog(DiscordRPGCog):
    """Religion and deity commands"""
    
    # Gods with their properties: (name, description, luck_multiplier, sacrifice_multiplier)
    GODS = {
        "chaos": {
            "name": "Chaos",
            "description": "God of randomness and disorder",
            "luck_multiplier": 1.2,
            "sacrifice_multiplier": 0.8,
            "emoji": "🌀"
        },
        "order": {
            "name": "Order", 
            "description": "God of structure and planning",
            "luck_multiplier": 0.9,
            "sacrifice_multiplier": 1.1,
            "emoji": "⚖️"
        },
        "war": {
            "name": "War",
            "description": "God of combat and conflict",
            "luck_multiplier": 1.0,
            "sacrifice_multiplier": 1.0,
            "emoji": "⚔️"
        },
        "nature": {
            "name": "Nature",
            "description": "God of life and growth",
            "luck_multiplier": 1.1,
            "sacrifice_multiplier": 0.9,
            "emoji": "🌿"
        },
        "death": {
            "name": "Death",
            "description": "God of endings and rebirth",
            "luck_multiplier": 0.8,
            "sacrifice_multiplier": 1.3,
            "emoji": "💀"
        }
    }
    
    @commands.command()
    @has_character()
    async def gods(self, ctx: commands.Context):
        """View available gods and their bonuses"""
        embed = self.embed("🏛️ The Pantheon", "Choose your deity wisely...")
        
        for god_key, god_info in self.GODS.items():
            embed.add_field(
                name=f"{god_info['emoji']} **{god_info['name']}**",
                value=f"{god_info['description']}\n"
                      f"Luck: {god_info['luck_multiplier']}x | "
                      f"Sacrifices: {god_info['sacrifice_multiplier']}x",
                inline=False
            )
            
        embed.add_field(
            name="⚡ How to Choose",
            value="Use `!choose <god>` to select your deity (one-time choice!)",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def choose(self, ctx: commands.Context, god: str):
        """Choose a god to follow (permanent choice!)"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Check if already has a god
        if char_data['god']:
            await ctx.send(f"❌ You already follow **{char_data['god']}**! This choice is permanent.")
            return
            
        # Validate god choice
        god_lower = god.lower()
        if god_lower not in self.GODS:
            valid_gods = ", ".join([g['name'] for g in self.GODS.values()])
            await ctx.send(f"❌ Unknown god! Choose from: {valid_gods}")
            return
            
        # Confirm choice
        god_info = self.GODS[god_lower]
        if not await ctx.confirm(
            f"Pledge your eternal loyalty to **{god_info['emoji']} {god_info['name']}**?\n"
            f"This choice is **permanent** and affects your luck and sacrifice bonuses!"
        ):
            await ctx.send("Choice cancelled.")
            return
            
        # Set god and apply luck multiplier
        new_luck = char_data['luck'] * god_info['luck_multiplier']
        self.db.update_character(
            ctx.author.id,
            god=god_info['name'],
            luck=new_luck
        )
        
        embed = self.embed(
            f"🏛️ Divine Bond Formed!",
            f"You now follow **{god_info['emoji']} {god_info['name']}**!"
        )
        embed.add_field(name="🍀 Luck Modifier", value=f"{god_info['luck_multiplier']}x", inline=True)
        embed.add_field(name="🔥 Sacrifice Bonus", value=f"{god_info['sacrifice_multiplier']}x", inline=True)
        embed.add_field(name="💫 New Luck", value=f"{new_luck:.2f}", inline=True)
        
        embed.set_footer(text="Use !pray to gain favor and !sacrifice to offer gold")
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    @commands.cooldown(1, 14400, commands.BucketType.user)  # 4 hour cooldown
    async def pray(self, ctx: commands.Context):
        """Pray to your god for favor (4 hour cooldown)"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Check if has a god
        if not char_data['god']:
            await ctx.send("❌ You haven't chosen a god yet! Use `!gods` to see options.")
            return
            
        # Get god info
        god_key = char_data['god'].lower()
        god_info = self.GODS.get(god_key, self.GODS['chaos'])
        
        # Calculate favor gain (1-5 base)
        base_favor = random.randint(1, 5)
        
        # Bonus favor based on level
        level_bonus = char_data['level'] // 10
        
        # Apply race bonus
        from cogs.race import RaceCog
        race_multipliers = RaceCog.get_race_multipliers(ctx.author.id)
        race_favor_bonus = int((base_favor + level_bonus) * race_multipliers.get('favor_gain', 1.0))
        
        # Random event chance (5%)
        event_text = ""
        if random.random() < 0.05:
            # Divine blessing
            race_favor_bonus *= 2
            event_text = f"\n✨ **{god_info['name']} is pleased!** Double favor gained!"
        elif random.random() < 0.02:
            # Super blessing (2% chance)
            race_favor_bonus *= 5
            event_text = f"\n🌟 **Divine Intervention!** {god_info['name']} grants massive favor!"
            
        total_favor = race_favor_bonus
        new_favor = char_data['favor'] + total_favor
        
        # Update favor
        self.db.update_character(ctx.author.id, favor=new_favor)
        
        # Prayer messages based on god
        prayers = {
            "chaos": [
                "You whisper mad prophecies to the void...",
                "You dance chaotically under the stars...",
                "You throw dice while chanting backwards..."
            ],
            "order": [
                "You kneel in perfect symmetry and recite ancient laws...",
                "You arrange stones in precise patterns while praying...",
                "You meditate on the cosmic balance..."
            ],
            "war": [
                "You clash weapons together in rhythmic prayer...",
                "You perform ritual combat moves in devotion...",
                "You chant battle hymns to the sky..."
            ],
            "nature": [
                "You plant seeds while whispering growth prayers...",
                "You commune with animals in sacred groves...",
                "You dance barefoot on living earth..."
            ],
            "death": [
                "You light candles for the departed souls...",
                "You meditate in ancient crypts...",
                "You whisper names of the forgotten..."
            ]
        }
        
        prayer_text = random.choice(prayers.get(god_key, prayers['chaos']))
        
        embed = self.embed(
            f"{god_info['emoji']} Prayer to {god_info['name']}",
            f"*{prayer_text}*"
        )
        embed.add_field(name="🙏 Favor Gained", value=f"+{total_favor}", inline=True)
        embed.add_field(name="💫 Total Favor", value=f"{new_favor}", inline=True)
        
        if event_text:
            embed.add_field(name="🎉 Special Event", value=event_text, inline=False)
            
        embed.set_footer(text="Pray again in 4 hours • Use !sacrifice to offer gold")
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    @commands.cooldown(1, 43200, commands.BucketType.user)  # 12 hour cooldown
    async def sacrifice(self, ctx: commands.Context, amount: int):
        """Sacrifice gold to your god for favor (12 hour cooldown)"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Check if has a god
        if not char_data['god']:
            await ctx.send("❌ You haven't chosen a god yet! Use `!gods` to see options.")
            return
            
        # Validate amount
        if amount < 100:
            await ctx.send("❌ Minimum sacrifice is 100 gold!")
            return
            
        if amount > char_data['money']:
            await ctx.send(f"❌ You don't have enough gold! You have {char_data['money']:,} gold.")
            return
            
        # Get god info
        god_key = char_data['god'].lower()
        god_info = self.GODS.get(god_key, self.GODS['chaos'])
        
        # Calculate favor gain
        base_favor = amount / 1000  # 1 favor per 1000 gold
        multiplied_favor = base_favor * god_info['sacrifice_multiplier']
        
        # Apply race bonus
        from cogs.race import RaceCog
        race_multipliers = RaceCog.get_race_multipliers(ctx.author.id)
        race_favor_bonus = multiplied_favor * race_multipliers.get('favor_gain', 1.0)
        final_favor = int(max(1, race_favor_bonus))  # Minimum 1 favor
        
        # Special events
        event_text = ""
        bonus_reward = None
        
        # Large sacrifice bonus (10k+ gold)
        if amount >= 10000:
            if random.random() < 0.2:  # 20% chance
                # Luck blessing
                luck_bonus = 0.05
                new_luck = char_data['luck'] + luck_bonus
                self.db.update_character(ctx.author.id, luck=new_luck)
                event_text = f"🍀 **Divine Blessing!** +{luck_bonus} luck!"
                bonus_reward = "luck"
        
        # Mega sacrifice bonus (50k+ gold)
        if amount >= 50000:
            if random.random() < 0.3:  # 30% chance
                # Double favor
                final_favor *= 2
                event_text = f"💫 **{god_info['name']} is greatly pleased!** Double favor!"
                
        # Update character
        new_money = char_data['money'] - amount
        new_favor = char_data['favor'] + final_favor
        self.db.update_character(
            ctx.author.id,
            money=new_money,
            favor=new_favor
        )
        
        # Sacrifice messages based on god
        sacrifices = {
            "chaos": "You toss gold into a swirling vortex...",
            "order": "You place gold on perfectly balanced scales...",
            "war": "You melt gold into weapons for eternal warriors...",
            "nature": "You bury gold beneath ancient trees...",
            "death": "You place gold coins on the eyes of statues..."
        }
        
        sacrifice_text = sacrifices.get(god_key, "You offer gold to the divine...")
        
        embed = self.embed(
            f"🔥 Sacrifice to {god_info['emoji']} {god_info['name']}",
            f"*{sacrifice_text}*"
        )
        embed.add_field(name="💰 Gold Offered", value=f"{amount:,}", inline=True)
        embed.add_field(name="🙏 Favor Gained", value=f"+{final_favor}", inline=True)
        embed.add_field(name="💫 Total Favor", value=f"{new_favor}", inline=True)
        
        if event_text:
            embed.add_field(name="🎉 Divine Response", value=event_text, inline=False)
            
        # Show multiplier info
        if god_info['sacrifice_multiplier'] != 1.0:
            embed.add_field(
                name="📊 God Bonus",
                value=f"{god_info['sacrifice_multiplier']}x sacrifice effectiveness",
                inline=False
            )
            
        embed.set_footer(text="Sacrifice again in 12 hours • Larger sacrifices may grant special rewards")
        await ctx.send(embed=embed)
    
    @commands.command(aliases=["blessing", "blessings"])
    @has_character()
    async def bless(self, ctx: commands.Context, blessing_type: str = None):
        """Purchase divine blessings with accumulated favor"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Check if has a god
        if not char_data['god']:
            await ctx.send("❌ You haven't chosen a god yet! Use `!gods` to see options.")
            return
        
        # Available blessings with favor costs and effects
        blessings = {
            "fortune": {
                "name": "🍀 Fortune's Blessing",
                "description": "Increases luck by 0.25 for 2 hours",
                "cost": 25,
                "duration": 7200,  # 2 hours in seconds
                "effect": "luck",
                "value": 0.25
            },
            "prosperity": {
                "name": "💰 Prosperity Blessing",
                "description": "Increases gold find by 50% for 1 hour",
                "cost": 30,
                "duration": 3600,  # 1 hour
                "effect": "gold_mult",
                "value": 1.5
            },
            "wisdom": {
                "name": "📚 Wisdom Blessing",
                "description": "Increases XP gain by 75% for 1.5 hours",
                "cost": 40,
                "duration": 5400,  # 1.5 hours
                "effect": "xp_mult", 
                "value": 1.75
            },
            "protection": {
                "name": "🛡️ Protection Blessing",
                "description": "Prevents XP/gold loss on next penalty for 6 hours",
                "cost": 50,
                "duration": 21600,  # 6 hours
                "effect": "protection",
                "value": 1
            },
            "divination": {
                "name": "🔮 Divination Blessing",
                "description": "Guarantees adventure success for next adventure",
                "cost": 35,
                "duration": 3600,  # 1 hour or until used
                "effect": "adventure_success",
                "value": 1
            },
            "valor": {
                "name": "⚔️ Valor Blessing",
                "description": "Increases battle power by 25% for 2 hours",
                "cost": 45,
                "duration": 7200,  # 2 hours
                "effect": "battle_mult",
                "value": 1.25
            }
        }
        
        # Show all blessings if no specific one requested
        if not blessing_type:
            embed = self.embed(
                f"✨ Divine Blessings",
                f"Spend your accumulated favor for divine assistance!\n"
                f"**Your favor:** {char_data['favor']}"
            )
            
            for key, blessing in blessings.items():
                embed.add_field(
                    name=blessing['name'],
                    value=f"{blessing['description']}\n**Cost:** {blessing['cost']} favor",
                    inline=True
                )
            
            embed.add_field(
                name="💡 Usage",
                value="Use `!bless <type>` to purchase a blessing\nTypes: " + ", ".join(blessings.keys()),
                inline=False
            )
            
            # Show active blessings if any
            active_blessings = self.db.fetchall(
                "SELECT * FROM divine_blessings WHERE user_id = ? AND expires_at > ?",
                (ctx.author.id, datetime.now())
            )
            
            if active_blessings:
                active_text = "\n".join([
                    f"**{b['effect']}** - {(datetime.fromisoformat(b['expires_at']) - datetime.now()).seconds // 60}m remaining"
                    for b in active_blessings
                ])
                embed.add_field(name="🌟 Active Blessings", value=active_text, inline=False)
            
            await ctx.send(embed=embed)
            return
        
        # Validate blessing type
        if blessing_type.lower() not in blessings:
            await ctx.send(f"❌ Unknown blessing type! Use `!bless` to see available options.")
            return
            
        blessing = blessings[blessing_type.lower()]
        
        # Check favor cost
        if char_data['favor'] < blessing['cost']:
            await ctx.send(f"❌ Not enough favor! Need {blessing['cost']}, you have {char_data['favor']}.")
            return
        
        # Check if blessing already active
        existing = self.db.fetchone(
            "SELECT * FROM divine_blessings WHERE user_id = ? AND effect = ? AND expires_at > ?",
            (ctx.author.id, blessing['effect'], datetime.now())
        )
        
        if existing:
            await ctx.send(f"❌ You already have an active {blessing['name']}!")
            return
        
        # Purchase blessing
        expires_at = datetime.now() + timedelta(seconds=blessing['duration'])
        new_favor = char_data['favor'] - blessing['cost']
        
        # Update favor
        self.db.update_character(ctx.author.id, favor=new_favor)
        
        # Add blessing to database
        self.db.execute(
            """INSERT INTO divine_blessings (user_id, effect, value, expires_at, blessing_name)
               VALUES (?, ?, ?, ?, ?)""",
            (ctx.author.id, blessing['effect'], blessing['value'], expires_at, blessing['name'])
        )
        self.db.commit()
        
        # Get god info for themed response
        god_key = char_data['god'].lower()
        god_info = self.GODS.get(god_key, self.GODS['chaos'])
        
        embed = self.embed(
            f"✨ Divine Blessing Granted!",
            f"{god_info['emoji']} **{god_info['name']}** bestows {blessing['name']} upon you!"
        )
        
        embed.add_field(name="💫 Effect", value=blessing['description'], inline=False)
        embed.add_field(name="⏰ Duration", value=f"{blessing['duration'] // 3600}h {(blessing['duration'] % 3600) // 60}m", inline=True)
        embed.add_field(name="💰 Cost", value=f"{blessing['cost']} favor", inline=True) 
        embed.add_field(name="🙏 Remaining Favor", value=f"{new_favor}", inline=True)
        
        # Special god-themed blessing messages
        blessing_messages = {
            "chaos": "Reality bends to your chaotic will!",
            "order": "Divine law strengthens your resolve!",
            "war": "Battle-tested power flows through you!",
            "nature": "The living world lends you its strength!",
            "death": "Ancient secrets whisper in your mind!"
        }
        
        embed.add_field(
            name="🗣️ Divine Message",
            value=f"*{blessing_messages.get(god_key, 'Divine energy flows through you!')}*",
            inline=False
        )
        
        embed.set_footer(text="Blessing effects apply automatically to all activities")
        await ctx.send(embed=embed)
    
    def get_active_blessings(self, user_id: int) -> dict:
        """Get all active blessings for a user"""
        current_time = datetime.now()
        blessings = self.db.fetchall(
            "SELECT * FROM divine_blessings WHERE user_id = ? AND expires_at > ?",
            (user_id, current_time)
        )
        
        # Clean up expired blessings
        self.db.execute(
            "DELETE FROM divine_blessings WHERE user_id = ? AND expires_at <= ?",
            (user_id, current_time)
        )
        self.db.commit()
        
        # Convert to multipliers dict
        active = {
            "luck": 1.0,
            "xp_mult": 1.0,
            "gold_mult": 1.0,
            "battle_mult": 1.0,
            "protection": False,
            "adventure_success": False
        }
        
        for blessing in blessings:
            effect = blessing['effect']
            value = blessing['value']
            
            if effect in ['luck', 'xp_mult', 'gold_mult', 'battle_mult']:
                if effect == 'luck':
                    active[effect] += value  # Add to luck (additive)
                else:
                    active[effect] = max(active[effect], value)  # Take highest multiplier
            elif effect in ['protection', 'adventure_success']:
                active[effect] = True
                
        return active

async def setup(bot):
    await bot.add_cog(ReligionCog(bot))