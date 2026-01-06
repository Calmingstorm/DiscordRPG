"""Epic and Legendary Adventures - High-tier parallel adventure system"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemGenerator, ItemRarity

logger = logging.getLogger('DiscordRPG.EpicAdventures')

class EpicAdventuresCog(DiscordRPGCog):
    """Epic and Legendary adventures that run parallel to regular adventures"""
    
    # Epic adventure definitions (4-8 hours, level 10+ required)
    EPIC_ADVENTURES = {
        "Dragon's Lair Expedition": {
            "description": "Journey to the ancient dragon's lair to claim its hoard",
            "min_level": 10,
            "duration_hours": (4, 6),
            "base_xp": 2500,
            "base_gold": 5000,
            "item_quality": (10, 20),
            "success_rate": 0.7
        },
        "Demon Lord's Fortress": {
            "description": "Assault the fortress of a powerful demon lord",
            "min_level": 10,
            "duration_hours": (4, 6),
            "base_xp": 2800,
            "base_gold": 4500,
            "item_quality": (11, 21),
            "success_rate": 0.65
        },
        "Lost City of Gold": {
            "description": "Explore the legendary lost city filled with treasures",
            "min_level": 10,
            "duration_hours": (5, 7),
            "base_xp": 2000,
            "base_gold": 8000,
            "item_quality": (10, 19),
            "success_rate": 0.75
        },
        "Titan's Challenge": {
            "description": "Face the trials of the ancient titans",
            "min_level": 12,
            "duration_hours": (5, 8),
            "base_xp": 3500,
            "base_gold": 6000,
            "item_quality": (12, 22),
            "success_rate": 0.6
        },
        "Void Realm Exploration": {
            "description": "Enter the dangerous void realm between worlds",
            "min_level": 11,
            "duration_hours": (4, 7),
            "base_xp": 3000,
            "base_gold": 5500,
            "item_quality": (11, 23),
            "success_rate": 0.68
        }
    }
    
    # Legendary adventure definitions (8-24 hours, level 15+ required)
    LEGENDARY_ADVENTURES = {
        "Godslayer Quest": {
            "description": "Challenge a fallen god for ultimate power",
            "min_level": 15,
            "duration_hours": (12, 24),
            "base_xp": 10000,
            "base_gold": 20000,
            "item_quality": (15, 30),
            "success_rate": 0.5
        },
        "World Tree Ascension": {
            "description": "Climb the World Tree to reach the realm of immortals",
            "min_level": 15,
            "duration_hours": (10, 20),
            "base_xp": 8000,
            "base_gold": 15000,
            "item_quality": (14, 28),
            "success_rate": 0.55
        },
        "Chaos Dimension Rift": {
            "description": "Seal the rift to the chaos dimension before it consumes the world",
            "min_level": 18,
            "duration_hours": (14, 24),
            "base_xp": 12000,
            "base_gold": 25000,
            "item_quality": (16, 32),
            "success_rate": 0.45
        },
        "Phoenix Rebirth Ritual": {
            "description": "Witness and survive the rebirth of the eternal phoenix",
            "min_level": 16,
            "duration_hours": (8, 16),
            "base_xp": 9000,
            "base_gold": 18000,
            "item_quality": (15, 29),
            "success_rate": 0.6
        },
        "Underworld Conquest": {
            "description": "Descend to the deepest underworld to challenge Death itself",
            "min_level": 20,
            "duration_hours": (16, 24),
            "base_xp": 15000,
            "base_gold": 30000,
            "item_quality": (17, 35),
            "success_rate": 0.4
        }
    }
    
    def __init__(self, bot):
        super().__init__(bot)
        
    async def cog_load(self):
        """Start checking for completed epic adventures"""
        if not self.check_epic_completions.is_running():
            self.check_epic_completions.start()
        if not self.auto_epic_adventures.is_running():
            self.auto_epic_adventures.start()
            
    async def cog_unload(self):
        """Stop the completion checker"""
        if self.check_epic_completions.is_running():
            self.check_epic_completions.cancel()
        if self.auto_epic_adventures.is_running():
            self.auto_epic_adventures.cancel()
    
    def create_item_in_db(self, item) -> int:
        """Helper to create items with all stats in database"""
        return self.db.create_item(
            item.owner_id, item.name, item.type.value,
            item.value, item.damage, item.armor, item.hand.value,
            item.health_bonus, item.speed_bonus, item.luck_bonus,
            item.crit_bonus, item.magic_bonus, item.slot_type
        )
    
    
    @commands.command(aliases=['epicstat', 'epicinfo'])
    @has_character()
    async def epicstatus(self, ctx: commands.Context):
        """Check your epic/legendary adventure status"""
        # Check active epic adventure
        active = self.db.fetchone(
            "SELECT * FROM epic_adventures WHERE user_id = ? AND status = 'active'",
            (ctx.author.id,)
        )
        
        if not active:
            # Show readiness status instead
            char_data = self.db.get_character(ctx.author.id)
            
            embed = self.embed(
                "📊 Epic Adventure Status",
                "No active epic or legendary adventure"
            )
            
            if char_data['level'] >= 15:
                embed.add_field(
                    name="✅ Ready for Adventures",
                    value="You are eligible for **epic and legendary** adventures!\n"
                          "Stay **online** (green status) to be automatically selected every 45 minutes.",
                    inline=False
                )
            elif char_data['level'] >= 10:
                embed.add_field(
                    name="✅ Ready for Adventures", 
                    value="You are eligible for **epic** adventures!\n"
                          "Stay **online** (green status) to be automatically selected every 45 minutes.\n"
                          f"*Reach level 15 to unlock legendary adventures*",
                    inline=False
                )
            else:
                embed.add_field(
                    name="❌ Not Eligible",
                    value=f"You need to reach level 10 to participate in epic adventures.\n"
                          f"**Current level:** {char_data['level']}\n"
                          f"**Levels to go:** {10 - char_data['level']}",
                    inline=False
                )
                
            # Show recent completion count
            recent_count = len(self.db.fetchall(
                "SELECT id FROM epic_adventures WHERE user_id = ? AND status = 'completed' AND started_at > datetime('now', '-7 days')",
                (ctx.author.id,)
            ))
            
            embed.add_field(
                name="📈 Recent Activity",
                value=f"**{recent_count}** epic adventures completed in the last 7 days",
                inline=False
            )
                
            embed.color = discord.Color.blue()
            await ctx.send(embed=embed)
            return
        
        # Show active adventure
        finish_time = datetime.fromisoformat(active['finish_at'])
        remaining = finish_time - datetime.now()
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        progress_percent = ((datetime.now() - datetime.fromisoformat(active['started_at'])).total_seconds() / 
                          (finish_time - datetime.fromisoformat(active['started_at'])).total_seconds() * 100)
        
        # Progress bar
        filled = int(progress_percent // 10)
        progress_bar = "🟩" * filled + "⬜" * (10 - filled)
        
        embed = self.embed(
            f"{'🌟' if active['adventure_type'] == 'epic' else '⚡'} {active['adventure_type'].title()} Adventure in Progress",
            f"**{active['adventure_name']}**"
        )
        embed.add_field(
            name="⏱️ Time Remaining",
            value=f"{hours}h {minutes}m",
            inline=True
        )
        embed.add_field(
            name="📊 Progress",
            value=f"{progress_bar} {progress_percent:.1f}%",
            inline=True
        )
        embed.add_field(
            name="🎁 Expected Rewards",
            value=f"**Base XP:** {active['base_xp_reward']:,}\n**Base Gold:** {active['base_gold_reward']:,}",
            inline=False
        )
        embed.color = discord.Color.purple() if active['adventure_type'] == 'epic' else discord.Color.gold()
        embed.set_footer(text=f"Returns at {finish_time.strftime('%Y-%m-%d %H:%M')}")
        
        await ctx.send(embed=embed)
    
    @tasks.loop(minutes=5)
    async def check_epic_completions(self):
        """Check for completed epic/legendary adventures"""
        try:
            # Find main channel
            channel = None
            for guild in self.bot.guilds:
                for chan in guild.text_channels:
                    if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                        channel = chan
                        break
                if channel:
                    break
                    
            if not channel:
                return
            
            # Get completed adventures
            completed = self.db.fetchall(
                """SELECT * FROM epic_adventures 
                   WHERE status = 'active' AND finish_at <= ?""",
                (datetime.now(),)
            )
            
            for adventure in completed:
                # Get character data
                char = self.db.get_profile(adventure['user_id'])
                if not char:
                    continue
                
                # Determine success based on adventure type
                adventure_def = (self.EPIC_ADVENTURES.get(adventure['adventure_name']) or 
                               self.LEGENDARY_ADVENTURES.get(adventure['adventure_name']))
                
                if not adventure_def:
                    success_rate = 0.6  # Default
                else:
                    success_rate = adventure_def['success_rate']
                
                # Add luck bonus
                luck_bonus = (char.luck - 1.0) * 0.1
                success_rate = min(0.95, success_rate + luck_bonus)
                
                success = random.random() < success_rate
                
                if success:
                    # Calculate rewards with multipliers
                    from cogs.race import RaceCog
                    race_multipliers = RaceCog.get_race_multipliers(char.user_id)
                    
                    # Get divine blessing bonuses
                    from cogs.religion import ReligionCog
                    religion_cog = self.bot.get_cog('ReligionCog')
                    if religion_cog:
                        blessing_bonuses = religion_cog.get_active_blessings(char.user_id)
                        # Apply blessing multipliers
                        race_multipliers['xp_gain'] *= blessing_bonuses['xp_mult']
                        race_multipliers['gold_find'] *= blessing_bonuses['gold_mult']
                    
                    # Base rewards with variance
                    xp_variance = random.uniform(0.8, 1.2)
                    gold_variance = random.uniform(0.8, 1.2)
                    
                    final_xp = int(adventure['base_xp_reward'] * xp_variance * race_multipliers['xp_gain'])
                    final_gold = int(adventure['base_gold_reward'] * gold_variance * race_multipliers['gold_find'])
                    
                    # Update character
                    new_xp = char.xp + final_xp
                    new_gold = char.money + final_gold
                    new_level = min(50, 1 + int((new_xp / 100) ** 0.5))
                    
                    # Update character stats
                    self.db.update_character(
                        char.user_id,
                        xp=new_xp,
                        money=new_gold,
                        level=new_level
                    )
                    
                    # Generate epic/legendary items
                    items_found = []
                    num_items = random.randint(1, 3) if adventure['adventure_type'] == 'epic' else random.randint(2, 4)
                    
                    for _ in range(num_items):
                        item = ItemGenerator.generate_random_equipment(
                            char.user_id,
                            adventure['item_quality_min'],
                            adventure['item_quality_max']
                        )
                        
                        # Add epic/legendary prefix
                        if adventure['adventure_type'] == 'epic':
                            item.name = f"Epic {item.name}"
                            item.value = int(item.value * 1.5)
                        else:
                            item.name = f"Legendary {item.name}"
                            item.value = int(item.value * 2)
                        
                        self.create_item_in_db(item)
                        items_found.append(item.name)
                    
                    # Success embed
                    embed = self.embed(
                        f"{'🌟' if adventure['adventure_type'] == 'epic' else '⚡'} {adventure['adventure_type'].title()} Adventure Complete!",
                        f"**{char.name}** returns triumphant from **{adventure['adventure_name']}**!"
                    )
                    embed.add_field(
                        name="✨ Success!",
                        value=f"The {adventure['adventure_type']} quest was completed successfully!",
                        inline=False
                    )
                    embed.add_field(
                        name="🎁 Rewards",
                        value=f"**XP:** {final_xp:,}\n**Gold:** {final_gold:,}",
                        inline=True
                    )
                    embed.add_field(
                        name="🎁 Items Found",
                        value='\n'.join([f"• {item}" for item in items_found]),
                        inline=True
                    )
                    
                    if new_level > char.level:
                        embed.add_field(
                            name="🎉 Level Up!",
                            value=f"Now level {new_level}!",
                            inline=False
                        )
                    
                    embed.color = discord.Color.green()
                    
                else:
                    # Failed adventure - smaller rewards
                    from cogs.race import RaceCog
                    race_multipliers = RaceCog.get_race_multipliers(char.user_id)
                    
                    final_xp = int(adventure['base_xp_reward'] * 0.2 * race_multipliers['xp_gain'])
                    final_gold = int(adventure['base_gold_reward'] * 0.1 * race_multipliers['gold_find'])
                    
                    self.db.update_character(
                        char.user_id,
                        xp=char.xp + final_xp,
                        money=char.money + final_gold
                    )
                    
                    # Failure embed
                    embed = self.embed(
                        f"💀 {adventure['adventure_type'].title()} Adventure Failed",
                        f"**{char.name}** returns defeated from **{adventure['adventure_name']}**..."
                    )
                    embed.add_field(
                        name="❌ Failed",
                        value=f"The {adventure['adventure_type']} quest proved too difficult!",
                        inline=False
                    )
                    embed.add_field(
                        name="💔 Consolation Rewards",
                        value=f"**XP:** {final_xp:,}\n**Gold:** {final_gold:,}",
                        inline=True
                    )
                    embed.color = discord.Color.red()
                
                # Mark as completed
                self.db.execute(
                    "UPDATE epic_adventures SET status = 'completed' WHERE id = ?",
                    (adventure['id'],)
                )
                self.db.commit()
                
                # Send result
                await channel.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Error checking epic adventure completions: {e}")
    
    @tasks.loop(minutes=45)
    async def auto_epic_adventures(self):
        """Automatically send high-level online players on epic adventures"""
        try:
            # Find main channel
            channel = None
            for guild in self.bot.guilds:
                for chan in guild.text_channels:
                    if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                        channel = chan
                        break
                if channel:
                    break
                    
            if not channel:
                return
            
            # Get eligible online players not on epic adventures
            all_high_level = self.db.fetchall(
                """SELECT user_id, name, level FROM profile 
                   WHERE level >= 10 
                   AND user_id NOT IN (
                       SELECT user_id FROM epic_adventures WHERE status = 'active'
                   )"""
            )
            
            if not all_high_level:
                return
            
            # Filter for online users
            online_eligible = []
            for char in all_high_level:
                user = self.bot.get_user(char['user_id'])
                if user:
                    # Check if online in any guild
                    for guild in self.bot.guilds:
                        member = guild.get_member(user.id)
                        if member and member.status == discord.Status.online:
                            online_eligible.append(char)
                            break
            
            if not online_eligible:
                return
            
            # Select 2-6 players for epic adventures (increased from 1-3)
            num_selected = min(random.randint(2, 6), len(online_eligible))
            selected = random.sample(online_eligible, num_selected)
            
            embeds_sent = []
            
            for char in selected:
                # Decide epic vs legendary based on level
                if char['level'] >= 15 and random.random() < 0.4:
                    # 40% chance for legendary if eligible
                    adventure_type = 'legendary'
                    adventures_dict = self.LEGENDARY_ADVENTURES
                else:
                    adventure_type = 'epic'
                    adventures_dict = self.EPIC_ADVENTURES
                
                # Filter by level
                available = {
                    name: data for name, data in adventures_dict.items()
                    if char['level'] >= data['min_level']
                }
                
                if not available:
                    continue
                
                # Choose adventure
                adventure_name = random.choice(list(available.keys()))
                adventure_data = available[adventure_name]
                
                # Calculate duration
                min_hours, max_hours = adventure_data['duration_hours']
                duration_hours = random.uniform(min_hours, max_hours)
                start_time = datetime.now()
                end_time = start_time + timedelta(hours=duration_hours)
                
                # Insert into database with proper duplicate checking
                try:
                    # Double-check for active adventures (since we removed the DB constraint)
                    existing_active = self.db.fetchone(
                        "SELECT id FROM epic_adventures WHERE user_id = ? AND status = 'active'",
                        (char['user_id'],)
                    )
                    
                    if existing_active:
                        logger.info(f"Skipped epic adventure for {char['name']} - already has active adventure (id: {existing_active['id']})")
                        continue
                    
                    # Insert new adventure
                    self.db.execute(
                        """INSERT INTO epic_adventures 
                           (user_id, adventure_type, adventure_name, difficulty, started_at, finish_at, 
                            base_xp_reward, base_gold_reward, item_quality_min, item_quality_max, status)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')""",
                        (char['user_id'], adventure_type, adventure_name, 
                         3 if adventure_type == 'legendary' else 2,
                         start_time, end_time,
                         adventure_data['base_xp'], adventure_data['base_gold'],
                         adventure_data['item_quality'][0], adventure_data['item_quality'][1])
                    )
                        
                except Exception as e:
                    logger.error(f"Failed to create epic adventure for {char['name']}: {e}")
                    continue
                
                embeds_sent.append({
                    'name': char['name'],
                    'adventure': adventure_name,
                    'type': adventure_type,
                    'duration': duration_hours
                })
            
            self.db.commit()
            
            if embeds_sent:
                # Send combined notification
                embed = self.embed(
                    f"{'⚡' if any(e['type'] == 'legendary' for e in embeds_sent) else '🌟'} Epic Adventures Begun!",
                    "High-level heroes embark on epic quests!"
                )
                
                adventure_list = []
                for sent in embeds_sent:
                    type_emoji = '⚡' if sent['type'] == 'legendary' else '🌟'
                    adventure_list.append(
                        f"{type_emoji} **{sent['name']}** → {sent['adventure']} ({sent['duration']:.1f}h)"
                    )
                
                embed.add_field(
                    name=f"🗺️ {len(embeds_sent)} Adventures Started",
                    value='\n'.join(adventure_list),
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Epic Adventure System",
                    value="Epic and legendary adventures automatically start every 45 minutes for eligible online players (level 10+ for epic, 15+ for legendary)!",
                    inline=False
                )
                
                embed.color = discord.Color.purple()
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in auto epic adventures: {e}")
    
    @commands.command()
    async def epicadventures(self, ctx: commands.Context):
        """Information about the epic and legendary adventure system"""
        embed = self.embed(
            "🌟⚡ Epic & Legendary Adventures",
            "High-tier adventures that run parallel to regular adventures!"
        )
        
        embed.add_field(
            name="🌟 Epic Adventures",
            value="• **Required:** Level 10+\n• **Duration:** 4-8 hours\n• **Rewards:** 2,000-3,500 XP, 4,500-8,000 gold\n• **Items:** Quality 10-23\n• **Frequency:** Automatic selection",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Legendary Adventures", 
            value="• **Required:** Level 15+\n• **Duration:** 8-24 hours\n• **Rewards:** 8,000-15,000 XP, 15,000-30,000 gold\n• **Items:** Quality 14-35\n• **Frequency:** Automatic selection",
            inline=False
        )
        
        embed.add_field(
            name="✨ Special Features",
            value="• Run **parallel** to regular adventures\n• Can do regular adventures while on epic/legendary\n• Only **one** epic/legendary at a time\n• Higher risk but **massive rewards**\n• **Automatic selection every 45 minutes**",
            inline=False
        )
        
        embed.add_field(
            name="📊 How it Works",
            value="• **Automatic:** Eligible online players are selected\n• **Frequency:** Every 45 minutes, 2-6 eligible players\n• **Selection:** Must be level 10+ and online (green status)\n• **Check status:** Use `!epicstatus` to see your progress",
            inline=False
        )
        
        embed.color = discord.Color.purple()
        embed.set_footer(text="Reach level 10 to begin your epic journey!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EpicAdventuresCog(bot))