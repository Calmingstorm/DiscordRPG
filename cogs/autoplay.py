"""Automatic gameplay system - runs adventures, battles, and events"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemGenerator, ItemRarity
from utils.scaling import (
    calculate_xp_reward, calculate_gold_reward, calculate_battle_xp,
    get_tier_from_difficulty, get_level_bonus
)

logger = logging.getLogger('DiscordRPG.AutoPlay')

class AutoPlayCog(DiscordRPGCog):
    """Automatic gameplay for all registered characters"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.game_channel = None  # Will be set to main game channel
        self.initial_trigger_done = False  # Track if we've done the initial quick trigger
        
    def create_item_in_db(self, item) -> int:
        """Helper to create items with all stats in database"""
        return self.db.create_item(
            item.owner_id, item.name, item.type.value,
            item.value, item.damage, item.armor, item.hand.value,
            item.health_bonus, item.speed_bonus, item.luck_bonus,
            item.crit_bonus, item.magic_bonus, item.slot_type
        )

    async def update_quest_progress(self, user_id: int, objective_type: str, amount: int = 1):
        """Helper to update personal quest progress"""
        try:
            quest_cog = self.bot.get_cog('PersonalQuestsCog')
            if quest_cog:
                await quest_cog.check_and_update_progress(user_id, objective_type, amount)
        except Exception as e:
            logger.debug(f"Quest progress update failed: {e}")
    
    def calculate_adventure_power(self, user_id: int) -> int:
        """Calculate adventure power from equipment"""
        items = self.db.get_equipped_items(user_id)
        return sum(item['damage'] + item['armor'] for item in items)
        
    def is_user_online(self, user: discord.User) -> bool:
        """Check if user is online (green status) in any guild"""
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member and member.status == discord.Status.online:
                return True
        return False
        
    async def cog_load(self):
        """Start automatic game loops when cog loads"""
        logger.info("AutoPlay cog loading - waiting for bot to be ready...")
        await asyncio.sleep(5)  # Wait for bot to be ready
        logger.info("Starting AutoPlay loops...")
        
        # Start adventure loop with initial random interval (7-21 minutes) - 30% increase in frequency
        initial_adventure_interval = random.randint(7, 21) * 60
        self.auto_adventure_loop.change_interval(seconds=initial_adventure_interval)
        self.auto_adventure_loop.start()
        
        # Start battle loop with initial random interval (1-5 minutes)
        initial_battle_interval = random.randint(1, 5) * 60
        self.auto_battle_loop.change_interval(seconds=initial_battle_interval)
        self.auto_battle_loop.start()
        self.auto_events_loop.start()
        self.level_up_check.start()
        self.initial_activity_check.start()
        self.level_fix_loop.start()
        logger.info("All AutoPlay loops started successfully!")
        
    def cog_unload(self):
        """Stop loops when cog unloads"""
        self.auto_adventure_loop.cancel()
        self.auto_battle_loop.cancel() 
        self.auto_events_loop.cancel()
        self.level_up_check.cancel()
        self.initial_activity_check.cancel()
        self.level_fix_loop.cancel()
        
    async def get_game_channel(self):
        """Get or create the main game channel"""
        if self.game_channel:
            return self.game_channel
        
        # Wait for bot to be ready if needed
        if not self.bot.is_ready():
            await self.bot.wait_until_ready()
            
        # Look for existing game channel
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                if channel.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                    self.game_channel = channel
                    return channel
                    
            # Create channel if none found
            try:
                self.game_channel = await guild.create_text_channel(
                    'discordrpg',
                    topic='🎮 Automatic DiscordRPG gameplay happens here!'
                )
                await self.game_channel.send(
                    "🎮 **DiscordRPG Auto-Game Started!**\n"
                    "Use `!create` to join the automatic adventure!"
                )
                return self.game_channel
            except discord.Forbidden:
                # Use first available channel
                self.game_channel = guild.text_channels[0]
                return self.game_channel
                
        return None
        
    @tasks.loop()  # Dynamic interval
    async def auto_adventure_loop(self):
        """Automatically send characters on adventures"""
        try:
            channel = await self.get_game_channel()
            if not channel:
                return
                
            # Get all characters not currently on adventures AND are online
            available_chars = []
            all_chars = self.db.fetchall(
                """SELECT user_id, name, level FROM profile 
                   WHERE user_id NOT IN (SELECT user_id FROM adventures WHERE status = 'active')"""
            )
            
            # Filter for online users only
            for char in all_chars:
                user = self.bot.get_user(char['user_id'])
                if user and self.is_user_online(user):
                    # Ensure dict format
                    available_chars.append(self.db.row_to_dict(char))
            
            if not available_chars:
                return
                
            # Send 10-20 random characters on adventures
            num_adventures = min(random.randint(10, 20), len(available_chars))
            selected = random.sample(available_chars, num_adventures)
            
            if selected:
                # If multiple adventures starting, use single embed; otherwise individual messages
                if len(selected) > 1:
                    # Create single dynamic embed for multiple adventure starts
                    adventure_embed = self.embed(
                        "🗺️ Adventure Departures!",
                        "Heroes set out on new quests..."
                    )
                    
                    adventure_list = []
                    for char in selected:
                        # Choose adventure duration and difficulty based on level
                        # Cap effective level for difficulty calculation to prevent runaway scaling
                        capped_level = min(char['level'], 200)
                        if capped_level < 10:
                            duration = random.randint(5, 15)
                            difficulty = random.randint(1, capped_level + 2)
                        elif capped_level < 25:
                            duration = random.randint(15, 45)
                            difficulty = random.randint(max(1, capped_level - 2), capped_level + 5)
                        elif capped_level < 50:
                            duration = random.randint(30, 120)
                            difficulty = random.randint(max(1, capped_level - 5), capped_level + 10)
                        else:
                            duration = random.randint(60, 240)
                            difficulty = random.randint(max(1, capped_level - 10), capped_level + 15)
                        # Hard cap difficulty to prevent extreme values
                        difficulty = min(difficulty, 215)
                            
                        # Start adventure with error handling
                        adventure_types = [
                            "Forest Exploration", "Cave Diving", "Monster Hunt", "Treasure Quest",
                            "Dungeon Raid", "Dragon Slaying", "Artifact Search", "Bandit Clearing",
                            "Ancient Ruins", "Crystal Mining", "Beast Taming", "Shadow Realm"
                        ]
                        
                        adventure_type = random.choice(adventure_types)
                        start_time = datetime.now()  # Use local time instead of UTC
                        end_time = start_time + timedelta(minutes=duration)
                        
                        try:
                            self.db.execute(
                                """INSERT INTO adventures (user_id, adventure_name, difficulty, started_at, finish_at, status)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (char['user_id'], adventure_type, difficulty, start_time, end_time, 'active')
                            )
                            # Add to list for embed only if insert succeeded
                            adventure_list.append(f"• **{char['name']}** → {adventure_type} ({duration}m)")
                        except Exception as e:
                            logger.error(f"Failed to create adventure for {char['name']}: {e}")
                            continue
                    
                    self.db.commit()
                    
                    # Update embed with all departures at once
                    adventure_embed.add_field(
                        name=f"📋 {len(selected)} Adventurers Departing",
                        value="\n".join(adventure_list),
                        inline=False
                    )
                    adventure_embed.add_field(
                        name="⏱️ Status",
                        value="All adventurers have begun their journeys!",
                        inline=False
                    )
                    
                    await channel.send(embed=adventure_embed)
                else:
                    # Single adventure - use individual message
                    char = selected[0]
                    # Choose adventure duration and difficulty based on level
                    # Cap effective level for difficulty calculation
                    capped_level = min(char['level'], 200)
                    if capped_level < 10:
                        duration = random.randint(5, 15)
                        difficulty = random.randint(1, capped_level + 2)
                    elif capped_level < 25:
                        duration = random.randint(15, 45)
                        difficulty = random.randint(max(1, capped_level - 2), capped_level + 5)
                    elif capped_level < 50:
                        duration = random.randint(30, 120)
                        difficulty = random.randint(max(1, capped_level - 5), capped_level + 10)
                    else:
                        duration = random.randint(60, 240)
                        difficulty = random.randint(max(1, capped_level - 10), capped_level + 15)
                    # Hard cap difficulty
                    difficulty = min(difficulty, 215)

                    adventure_types = [
                        "Forest Exploration", "Cave Diving", "Monster Hunt", "Treasure Quest",
                        "Dungeon Raid", "Dragon Slaying", "Artifact Search", "Bandit Clearing",
                        "Ancient Ruins", "Crystal Mining", "Beast Taming", "Shadow Realm"
                    ]
                    
                    adventure_type = random.choice(adventure_types)
                    start_time = datetime.now()
                    end_time = start_time + timedelta(minutes=duration)
                    
                    try:
                        self.db.execute(
                            """INSERT INTO adventures (user_id, adventure_name, difficulty, started_at, finish_at, status)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (char['user_id'], adventure_type, difficulty, start_time, end_time, 'active')
                        )
                        self.db.commit()
                        
                        # Create individual adventure embed
                        adventure_embed = self.embed(
                            "🗺️ Adventure Departure!",
                            f"**{char['name']}** sets out on a new quest..."
                        )
                        adventure_embed.add_field(
                            name="📋 Adventure",
                            value=f"• **{char['name']}** → {adventure_type} ({duration}m)",
                            inline=False
                        )
                        adventure_embed.add_field(
                            name="⏱️ Status",
                            value="The adventurer has begun their journey!",
                            inline=False
                        )
                        adventure_embed.color = discord.Color.blue()
                        await channel.send(embed=adventure_embed)
                    except Exception as e:
                        logger.error(f"Failed to create single adventure for {char['name']}: {e}")
                
        except Exception as e:
            logger.error(f"Error in auto_adventure_loop: {e}")
            
        # Set next random interval between 7-21 minutes (30% increase in frequency)
        next_interval = random.randint(7, 21) * 60  # Convert to seconds
        self.auto_adventure_loop.change_interval(seconds=next_interval)
            
    @tasks.loop()  # Dynamic interval
    async def auto_battle_loop(self):
        """Automatically create battles between characters - supports 1v1, 3v3, and 5v5"""
        try:
            channel = await self.get_game_channel()
            if not channel:
                return
                
            # Get characters available for battle (online, not in adventure, similar levels)
            available_chars = []
            all_chars = self.db.fetchall(
                """SELECT user_id, name, level FROM profile 
                   WHERE user_id NOT IN (SELECT user_id FROM adventures WHERE status = 'active')
                   ORDER BY level"""
            )
            
            # Filter for online users only
            for char in all_chars:
                user = self.bot.get_user(char['user_id'])
                if user and self.is_user_online(user):
                    # Ensure dict format
                    available_chars.append(self.db.row_to_dict(char))
                    
            chars = available_chars
            
            if len(chars) < 2:
                return
                
            # Determine battle type based on available players (more balanced distribution)
            if len(chars) >= 20:
                # More balanced: 25% for 10v10, 25% for 5v5, 30% for 3v3, 20% for 1v1
                battle_type = random.choices(['10v10', '5v5', '3v3', '1v1'], weights=[25, 25, 30, 20])[0]
            elif len(chars) >= 10:
                # More balanced: 35% for 5v5, 40% for 3v3, 25% for 1v1
                battle_type = random.choices(['5v5', '3v3', '1v1'], weights=[35, 40, 25])[0]
            elif len(chars) >= 6:
                # Slightly favor variety: 55% chance for 3v3, 45% for 1v1
                battle_type = random.choices(['3v3', '1v1'], weights=[55, 45])[0]
            else:
                # Only 1v1 possible
                battle_type = '1v1'
                
            # Execute the appropriate battle type
            if battle_type == '1v1':
                await self.run_1v1_battle(chars, channel)
            elif battle_type == '3v3':
                await self.run_3v3_battle(chars, channel)
            elif battle_type == '5v5':
                await self.run_5v5_battle(chars, channel)
            elif battle_type == '10v10':
                await self.run_10v10_battle(chars, channel)
            
        except Exception as e:
            logger.error(f"Error in auto_battle_loop: {e}")
            
        # Set next random interval between 2-8 minutes (adjusted for group battles)
        next_interval = random.randint(2, 8) * 60  # Convert to seconds
        self.auto_battle_loop.change_interval(seconds=next_interval)
            
    async def simulate_battle(self, char1: Dict, char2: Dict) -> Dict:
        """Simulate a battle between two characters"""
        # Get character stats
        char1_data = self.db.get_character(char1['user_id'])
        char2_data = self.db.get_character(char2['user_id'])
        
        # Calculate combat power (level + equipment + armor bonuses + some randomness)
        char1_items = self.db.get_equipped_items(char1['user_id'])
        char2_items = self.db.get_equipped_items(char2['user_id'])
        
        # Calculate equipment power including armor bonuses
        char1_equipment = sum(item['damage'] + item['armor'] for item in char1_items)
        char1_armor_bonuses = sum(
            item.get('health_bonus', 0) + item.get('speed_bonus', 0) + 
            int(item.get('luck_bonus', 0) * 100) + int(item.get('crit_bonus', 0) * 100) + 
            item.get('magic_bonus', 0) for item in char1_items
        )
        char1_power = char1['level'] * 10 + char1_equipment + char1_armor_bonuses + random.randint(-20, 20)
        
        char2_equipment = sum(item['damage'] + item['armor'] for item in char2_items)
        char2_armor_bonuses = sum(
            item.get('health_bonus', 0) + item.get('speed_bonus', 0) + 
            int(item.get('luck_bonus', 0) * 100) + int(item.get('crit_bonus', 0) * 100) + 
            item.get('magic_bonus', 0) for item in char2_items
        )
        char2_power = char2['level'] * 10 + char2_equipment + char2_armor_bonuses + random.randint(-20, 20)
        
        if char1_power >= char2_power:
            return {'winner': char1, 'loser': char2, 'power_diff': char1_power - char2_power}
        else:
            return {'winner': char2, 'loser': char1, 'power_diff': char2_power - char1_power}
    
    async def run_1v1_battle(self, chars, channel):
        """Run a 1v1 auto battle with the original format"""
        # Group by similar levels (within 5 levels)
        level_groups = {}
        for char in chars:
            level_range = (char['level'] // 5) * 5  # Group by 5s: 0-4, 5-9, 10-14, etc
            if level_range not in level_groups:
                level_groups[level_range] = []
            level_groups[level_range].append(char)
            
        # Pick a random group with at least 2 characters
        valid_groups = [g for g in level_groups.values() if len(g) >= 2]
        if not valid_groups:
            return
            
        group = random.choice(valid_groups)
        fighter1, fighter2 = random.sample(group, 2)
        
        # Simulate battle
        result = await self.simulate_battle(fighter1, fighter2)
        
        # Get race multipliers and blessing bonuses
        from cogs.race import RaceCog
        winner_multipliers = RaceCog.get_race_multipliers(result['winner']['user_id'], self.db)
        loser_multipliers = RaceCog.get_race_multipliers(result['loser']['user_id'], self.db)

        # Get divine blessing bonuses
        winner_blessing_mult = 1.0
        loser_blessing_mult = 1.0
        winner_gold_blessing = 1.0
        religion_cog = self.bot.get_cog('ReligionCog')
        if religion_cog:
            winner_blessings = religion_cog.get_active_blessings(result['winner']['user_id'])
            loser_blessings = religion_cog.get_active_blessings(result['loser']['user_id'])
            winner_blessing_mult = winner_blessings['xp_mult']
            loser_blessing_mult = loser_blessings['xp_mult']
            winner_gold_blessing = winner_blessings['gold_mult']

        # Calculate XP using new scaling system
        winner_xp = calculate_battle_xp(
            player_level=result['winner']['level'],
            opponent_level=result['loser']['level'],
            is_winner=True,
            race_xp_bonus=winner_multipliers['xp_gain'],
            blessing_xp_mult=winner_blessing_mult,
            battle_type='1v1'
        )
        loser_xp = calculate_battle_xp(
            player_level=result['loser']['level'],
            opponent_level=result['winner']['level'],
            is_winner=False,
            race_xp_bonus=loser_multipliers['xp_gain'],
            blessing_xp_mult=loser_blessing_mult,
            battle_type='1v1'
        )

        # Gold for winner (base + level bonus, with race/blessing multipliers)
        base_gold = 150 + random.randint(50, 150) + get_level_bonus(result['winner']['level'], 80)
        winner_gold = int(base_gold * winner_multipliers['gold_find'] * winner_gold_blessing)
        
        winner_char = self.db.get_character(result['winner']['user_id'])
        loser_char = self.db.get_character(result['loser']['user_id'])
        
        self.db.update_character(
            result['winner']['user_id'],
            xp=winner_char['xp'] + winner_xp,
            money=winner_char['money'] + winner_gold,
            pvpwins=winner_char['pvpwins'] + 1
        )

        self.db.update_character(
            result['loser']['user_id'],
            xp=loser_char['xp'] + loser_xp,
            pvplosses=loser_char['pvplosses'] + 1
        )

        # Update quest progress for battles
        await self.update_quest_progress(result['winner']['user_id'], 'pvp_wins', 1)
        await self.update_quest_progress(result['winner']['user_id'], 'battles_total', 1)
        await self.update_quest_progress(result['loser']['user_id'], 'battles_total', 1)
        await self.update_quest_progress(result['winner']['user_id'], 'xp_gain', winner_xp)
        await self.update_quest_progress(result['loser']['user_id'], 'xp_gain', loser_xp)
        await self.update_quest_progress(result['winner']['user_id'], 'gold_earn', winner_gold)

        # Chance for item reward - winners and losers
        winner_item_text = ""
        loser_item_text = ""
        
        # Winner item chance (30%) - can now get armor!
        if random.random() < 0.3:
            item = ItemGenerator.generate_random_equipment(
                result['winner']['user_id'],
                max(4, result['winner']['level'] + 2),
                result['winner']['level'] + 8
            )
            self.create_item_in_db(item)
            winner_item_text = f"\n🎁 Found: **{item.name}**"
            await self.update_quest_progress(result['winner']['user_id'], 'items_acquire', 1)

        # Loser item chance (5% - much smaller chance)
        if random.random() < 0.05:
            item = ItemGenerator.generate_random_equipment(
                result['loser']['user_id'],
                max(3, result['loser']['level']),
                result['loser']['level'] + 4
            )
            self.create_item_in_db(item)
            loser_item_text = f"\n🎁 Found: **{item.name}**"
            await self.update_quest_progress(result['loser']['user_id'], 'items_acquire', 1)
            
        # Create embed for clean display
        embed = self.embed(
            "⚔️ Auto Battle!",
            f"**{result['winner']['name']}** defeated **{result['loser']['name']}**!"
        )
        embed.add_field(
            name="🏆 Winner",
            value=f"**{result['winner']['name']}**\n+{winner_xp} XP, +{winner_gold} gold{winner_item_text}",
            inline=True
        )
        embed.add_field(
            name="💪 Loser", 
            value=f"**{result['loser']['name']}**\n+{loser_xp} XP{loser_item_text}",
            inline=True
        )
        embed.color = discord.Color.blue()
        
        await channel.send(embed=embed)
    
    async def run_3v3_battle(self, chars, channel):
        """Run a 3v3 team battle with dynamic embed updates"""
        # Select 6 players for 3v3
        fighters = random.sample(chars, 6)
        team_a = fighters[:3]
        team_b = fighters[3:6]
        
        team_a_names = [f['name'] for f in team_a]
        team_b_names = [f['name'] for f in team_b]
        
        # Create initial embed
        battle_embed = self.embed(
            "⚔️ 3v3 Team Battle!",
            "Two teams clash in tactical combat!"
        )
        battle_embed.add_field(
            name="⚔️ Team Alpha",
            value=', '.join(team_a_names),
            inline=True
        )
        battle_embed.add_field(
            name="🛡️ Team Beta", 
            value=', '.join(team_b_names),
            inline=True
        )
        battle_embed.add_field(
            name="📊 Battle Status",
            value="🔄 **Preparing for combat...**",
            inline=False
        )
        battle_embed.color = discord.Color.orange()
        
        # Send initial embed and get message object for editing
        battle_message = await channel.send(embed=battle_embed)
        
        await asyncio.sleep(2)
        
        # Team combat narrative with embed updates
        team_events = [
            "⚔️ The teams circle each other, planning their tactical approach!",
            "🛡️ Warriors coordinate their attacks in perfect formation!",
            "✨ Spells and steel clash as the teams engage in fierce combat!",
            "💥 The battlefield rings with the sounds of tactical warfare!"
        ]
        
        # Update embed with combat progression
        for i, event in enumerate(random.sample(team_events, 2)):
            battle_embed.set_field_at(
                2,  # Battle Status field
                name="📊 Battle Status", 
                value=f"⚡ **{event}**",
                inline=False
            )
            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(2)
        
        # Calculate team powers and determine winner
        team_a_power = sum(self.calculate_battle_power(f) for f in team_a)
        team_b_power = sum(self.calculate_battle_power(f) for f in team_b)
        
        # Team coordination affects power
        team_a_roll = team_a_power * random.uniform(0.85, 1.15) * 0.8
        team_b_roll = team_b_power * random.uniform(0.85, 1.15) * 0.8
        
        winning_team = team_a if team_a_roll > team_b_roll else team_b
        losing_team = team_b if team_a_roll > team_b_roll else team_a
        
        # Apply rewards to all participants
        winner_rewards = []
        loser_rewards = []
        
        for member in winning_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            winner_xp, winner_gold, item_text = await self.apply_team_rewards(member, "3v3", True)
            winner_rewards.append(f"**{member_dict['name']}**: +{winner_xp} XP, +{winner_gold} gold{item_text}")
            
        for member in losing_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            loser_xp, _, item_text = await self.apply_team_rewards(member, "3v3", False)
            loser_rewards.append(f"**{member_dict['name']}**: +{loser_xp} XP{item_text}")
        
        # Update embed with final results
        battle_embed.title = "🏆 3v3 Victory!"
        battle_embed.description = f"**Team {'Alpha' if winning_team == team_a else 'Beta'}** wins the battle!"
        battle_embed.color = discord.Color.gold()
        
        # Replace battle status with winner info
        battle_embed.set_field_at(
            2,
            name="🏆 Winners",
            value="\n".join(winner_rewards),
            inline=False
        )
        
        # Add participants field
        battle_embed.add_field(
            name="💪 Participants", 
            value="\n".join(loser_rewards),
            inline=False
        )
        
        # Final update to show results
        await battle_message.edit(embed=battle_embed)
    
    async def run_5v5_battle(self, chars, channel):
        """Run a 5v5 epic battle"""
        # Select 10 players for 5v5
        fighters = random.sample(chars, 10)
        team_a = fighters[:5]
        team_b = fighters[5:10]
        
        team_a_names = [f['name'] for f in team_a]
        team_b_names = [f['name'] for f in team_b]
        
        # Create initial embed for 5v5 battle
        battle_embed = self.embed(
            "⚔️ EPIC 5v5 BATTLE!",
            "Two mighty armies clash in legendary combat!"
        )
        battle_embed.add_field(
            name="⚔️ Army Alpha",
            value=f"{', '.join(team_a_names[:3])} +{len(team_a)-3} more",
            inline=True
        )
        battle_embed.add_field(
            name="🛡️ Army Beta", 
            value=f"{', '.join(team_b_names[:3])} +{len(team_b)-3} more",
            inline=True
        )
        battle_embed.add_field(
            name="📊 Battle Status",
            value="🔄 **Armies assembling for war...**",
            inline=False
        )
        battle_embed.color = discord.Color.purple()
        
        # Send initial embed and get message object for editing
        battle_message = await channel.send(embed=battle_embed)
        
        await asyncio.sleep(3)
        
        # Dynamic combat narrative with embed updates
        combat_events = [
            "⚔️ The armies charge across the battlefield with thunderous war cries!",
            "🛡️ Shield walls collide as warriors clash in fierce melee!",
            "✨ Magical energies surge as mages unleash devastating spells!",
            "🏹 Archers rain arrows while cavalry charges the flanks!",
            "💥 The ground trembles under the weight of epic combat!"
        ]
        
        # Update embed with combat progression
        for i, event in enumerate(random.sample(combat_events, 3)):
            battle_embed.set_field_at(
                2,  # Battle Status field
                name="📊 Battle Status", 
                value=f"⚡ **{event}**",
                inline=False
            )
            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(2)
        
        # Calculate army powers
        team_a_power = sum(self.calculate_battle_power(f) for f in team_a)
        team_b_power = sum(self.calculate_battle_power(f) for f in team_b)
        
        # Larger coordination penalty for 5v5
        team_a_roll = team_a_power * random.uniform(0.8, 1.2) * 0.75
        team_b_roll = team_b_power * random.uniform(0.8, 1.2) * 0.75
        
        winning_team = team_a if team_a_roll > team_b_roll else team_b
        losing_team = team_b if team_a_roll > team_b_roll else team_a
        
        # Apply rewards to all participants
        winner_rewards = []
        loser_rewards = []
        
        for member in winning_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            winner_xp, winner_gold, item_text = await self.apply_team_rewards(member, "5v5", True)
            winner_rewards.append(f"**{member_dict['name']}**: +{winner_xp} XP, +{winner_gold} gold{item_text}")
            
        for member in losing_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            loser_xp, _, item_text = await self.apply_team_rewards(member, "5v5", False)
            loser_rewards.append(f"**{member_dict['name']}**: +{loser_xp} XP{item_text}")
        
        # Update embed with final results
        battle_embed.title = "🏆 LEGENDARY VICTORY!"
        battle_embed.description = f"**Army {'Alpha' if winning_team == team_a else 'Beta'}** achieves glorious victory!"
        battle_embed.color = discord.Color.gold()
        
        # Replace battle status with winner info
        battle_embed.set_field_at(
            2,
            name="👑 Victorious Army",
            value="\n".join(winner_rewards),
            inline=False
        )
        
        # Add participants field
        battle_embed.add_field(
            name="⚔️ Brave Warriors", 
            value="\n".join(loser_rewards),
            inline=False
        )
        
        # Final update to show results
        await battle_message.edit(embed=battle_embed)
    
    async def run_10v10_battle(self, chars, channel):
        """Run a 10v10 massive battlefield"""
        # Select 20 players for 10v10
        fighters = random.sample(chars, 20)
        team_a = fighters[:10]
        team_b = fighters[10:20]
        
        team_a_names = [f['name'] for f in team_a]
        team_b_names = [f['name'] for f in team_b]
        
        # Create initial embed for 10v10 battle
        battle_embed = self.embed(
            "⚔️ MASSIVE 10v10 BATTLEFIELD!",
            "Two enormous armies clash in the ultimate battle!"
        )
        battle_embed.add_field(
            name="⚔️ Legion Alpha",
            value=f"{', '.join(team_a_names[:4])} +{len(team_a)-4} more warriors",
            inline=True
        )
        battle_embed.add_field(
            name="🛡️ Legion Beta", 
            value=f"{', '.join(team_b_names[:4])} +{len(team_b)-4} more warriors",
            inline=True
        )
        battle_embed.add_field(
            name="📊 Battle Status",
            value="🔄 **Legions marshalling for ultimate war...**",
            inline=False
        )
        battle_embed.color = discord.Color.dark_purple()
        
        # Send initial embed and get message object for editing
        battle_message = await channel.send(embed=battle_embed)
        
        await asyncio.sleep(4)
        
        # Epic combat narrative for massive battles with embed updates
        massive_combat_events = [
            "💥 The battlefield erupts as 20 warriors clash in ultimate warfare!",
            "⚔️ Legions charge with earth-shaking roars across the massive arena!",
            "🔥 The sky darkens with arrows, spells, and weapons of war!",
            "🌩️ Thunder crashes as legendary warriors unleash their full power!",
            "⚡ The very ground splits under the fury of this epic confrontation!",
            "🛡️ Heroes and villains alike fight with everything they possess!"
        ]
        
        # Update embed with combat progression
        for i, event in enumerate(random.sample(massive_combat_events, 4)):
            battle_embed.set_field_at(
                2,  # Battle Status field
                name="📊 Battle Status", 
                value=f"⚡ **{event}**",
                inline=False
            )
            await battle_message.edit(embed=battle_embed)
            await asyncio.sleep(2)
        
        # Calculate legion powers
        team_a_power = sum(self.calculate_battle_power(f) for f in team_a)
        team_b_power = sum(self.calculate_battle_power(f) for f in team_b)
        
        # Massive coordination penalty for 10v10
        team_a_roll = team_a_power * random.uniform(0.75, 1.25) * 0.65
        team_b_roll = team_b_power * random.uniform(0.75, 1.25) * 0.65
        
        winning_team = team_a if team_a_roll > team_b_roll else team_b
        losing_team = team_b if team_a_roll > team_b_roll else team_a
        
        # Apply rewards to all participants
        winner_rewards = []
        loser_rewards = []
        
        for member in winning_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            winner_xp, winner_gold, item_text = await self.apply_team_rewards(member, "10v10", True)
            winner_rewards.append(f"**{member_dict['name']}**: +{winner_xp} XP, +{winner_gold} gold{item_text}")
            
        for member in losing_team:
            # Ensure dict format for name access
            member_dict = self.db.row_to_dict(member) if hasattr(member, '_fields') else member
            loser_xp, _, item_text = await self.apply_team_rewards(member, "10v10", False)
            loser_rewards.append(f"**{member_dict['name']}**: +{loser_xp} XP{item_text}")
        
        # Update embed with final results
        battle_embed.title = "🏆 ULTIMATE CONQUEST!"
        battle_embed.description = f"**Legion {'Alpha' if winning_team == team_a else 'Beta'}** dominates the battlefield!"
        battle_embed.color = discord.Color.gold()
        
        # Replace battle status with winner info
        battle_embed.set_field_at(
            2,
            name="👑 Conquering Legion",
            value="\n".join(winner_rewards),
            inline=False
        )
        
        # Add participants field
        battle_embed.add_field(
            name="⚔️ Valiant Warriors", 
            value="\n".join(loser_rewards),
            inline=False
        )
        
        # Final update to show results
        await battle_message.edit(embed=battle_embed)
    
    def calculate_battle_power(self, char):
        """Calculate battle power for a character"""
        # Ensure dict format
        if hasattr(char, '_fields'):  # Legacy row object guard
            char_dict = self.db.row_to_dict(char)
        else:
            char_dict = char
            
        char_items = self.db.get_equipped_items(char_dict['user_id'])
        base_power = char_dict['level'] * 10 + sum(item['damage'] + item['armor'] for item in char_items) + random.randint(-20, 20)
        
        # Apply divine blessing bonuses
        from cogs.religion import ReligionCog
        religion_cog = self.bot.get_cog('ReligionCog')
        if religion_cog:
            blessing_bonuses = religion_cog.get_active_blessings(char_dict['user_id'])
            battle_multiplier = blessing_bonuses.get('battle_mult', 1.0)
            base_power = int(base_power * battle_multiplier)
        
        return base_power
    
    async def apply_team_rewards(self, member, battle_type, is_winner):
        """Apply team battle rewards and return formatted values"""
        # Ensure dict format
        if hasattr(member, '_fields'):  # Legacy row object guard
            member_dict = self.db.row_to_dict(member)
        else:
            member_dict = member
        
        # Get player info
        player_level = member_dict.get('level', 1)

        # Get race multipliers
        from cogs.race import RaceCog
        multipliers = RaceCog.get_race_multipliers(member_dict['user_id'], self.db)

        # Get divine blessing bonuses
        blessing_xp_mult = 1.0
        blessing_gold_mult = 1.0
        religion_cog = self.bot.get_cog('ReligionCog')
        if religion_cog:
            blessing_bonuses = religion_cog.get_active_blessings(member_dict['user_id'])
            blessing_xp_mult = blessing_bonuses['xp_mult']
            blessing_gold_mult = blessing_bonuses['gold_mult']

        # Calculate XP using new scaling system (opponent_level approximated as player_level for team battles)
        xp_reward = calculate_battle_xp(
            player_level=player_level,
            opponent_level=player_level,  # Team battles are roughly same-level
            is_winner=is_winner,
            race_xp_bonus=multipliers['xp_gain'],
            blessing_xp_mult=blessing_xp_mult,
            battle_type=battle_type
        )

        # Gold for winners
        if is_winner:
            gold_bases = {'3v3': 200, '5v5': 280, '10v10': 400}
            base_gold = gold_bases.get(battle_type, 200) + random.randint(50, 200) + get_level_bonus(player_level, 60)
            gold_reward = int(base_gold * multipliers['gold_find'] * blessing_gold_mult)
        else:
            gold_reward = 0
        
        # Update character
        char_data = self.db.get_character(member_dict['user_id'])
        
        if is_winner:
            self.db.update_character(
                member_dict['user_id'],
                xp=char_data['xp'] + xp_reward,
                money=char_data['money'] + gold_reward,
                pvpwins=char_data['pvpwins'] + 1
            )
        else:
            self.db.update_character(
                member_dict['user_id'],
                xp=char_data['xp'] + xp_reward,
                pvplosses=char_data['pvplosses'] + 1
            )

        # Track quest progress for team battles
        await self.update_quest_progress(member_dict['user_id'], 'battles_total', 1)
        await self.update_quest_progress(member_dict['user_id'], 'xp_gain', xp_reward)
        if is_winner:
            await self.update_quest_progress(member_dict['user_id'], 'pvp_wins', 1)
            await self.update_quest_progress(member_dict['user_id'], 'gold_earn', gold_reward)

        # Item chances - winners and losers
        item_text = ""
        if is_winner and random.random() < 0.25:  # 25% chance for winners
            item = ItemGenerator.generate_random_equipment(
                member_dict['user_id'],
                max(4, member_dict['level'] + 2),
                member_dict['level'] + 8
            )
            self.create_item_in_db(item)
            item_text = f"\n🎁 Found: **{item.name}**"
        elif not is_winner and random.random() < 0.05:  # 5% chance for losers (much lower)
            item = ItemGenerator.generate_random_equipment(
                member_dict['user_id'],
                max(3, member_dict['level']),
                member_dict['level'] + 4
            )
            self.create_item_in_db(item)
            item_text = f"\n🎁 Found: **{item.name}**"
        
        return xp_reward, gold_reward if is_winner else 0, item_text
            
    @tasks.loop(minutes=22.5)  # 50% increase in frequency (was 45 minutes)
    async def auto_events_loop(self):
        """Random events that affect all or some characters"""
        try:
            channel = await self.get_game_channel()
            if not channel:
                logger.warning("No game channel found for events")
                return
                
            # Only affect online players
            all_chars = self.db.fetchall("SELECT user_id, name, level, money FROM profile")
            chars = []
            for char in all_chars:
                user = self.bot.get_user(char['user_id'])
                if user and self.is_user_online(user):
                    # Ensure dict format
                    chars.append(self.db.row_to_dict(char))
                    
            if not chars:
                logger.info(f"No online players for events (total chars: {len(all_chars)})")
                return
                
            event_type = random.choice([
                'treasure_rain', 'monster_invasion', 'lucky_day', 'merchant_visit',
                'blessing', 'cursed_fog', 'festival', 'dragon_attack'
            ])
            
            logger.info(f"Triggering event: {event_type} for {len(chars)} online players")
            
            if event_type == 'treasure_rain':
                # Everyone gets bonus gold
                bonus = random.randint(100, 500)
                for char in chars:
                    char_data = self.db.get_character(char['user_id'])
                    self.db.update_character(char['user_id'], money=char_data['money'] + bonus)
                    
                await channel.send(
                    f"💰 **Treasure Rain!** All adventurers found {bonus} gold scattered by the wind!"
                )
                
            elif event_type == 'monster_invasion':
                # Random characters get into automatic battles
                if len(chars) >= 2:
                    defenders = random.sample(chars, min(random.randint(2, 4), len(chars)))
                    xp_bonus = random.randint(30, 100)
                    
                    for char in defenders:
                        char_data = self.db.get_character(char['user_id'])
                        self.db.update_character(char['user_id'], xp=char_data['xp'] + xp_bonus)
                    
                    # Create embed for monster invasion
                    invasion_embed = self.embed(
                        "👹 Monster Invasion!",
                        "Brave defenders have repelled the monster attack!"
                    )
                    
                    defender_names = ", ".join([d['name'] for d in defenders])
                    invasion_embed.add_field(
                        name=f"🛡️ Defenders ({len(defenders)})",
                        value=defender_names,
                        inline=False
                    )
                    
                    invasion_embed.add_field(
                        name="🎁 Reward",
                        value=f"**{xp_bonus}** XP",
                        inline=True
                    )
                    
                    invasion_embed.color = discord.Color.purple()
                    await channel.send(embed=invasion_embed)
                    
            elif event_type == 'lucky_day':
                # Random character gets a rare item (could be armor!)
                lucky_char = random.choice(chars)
                # Ensure dict format
                if hasattr(lucky_char, '_fields'):
                    lucky_char_dict = self.db.row_to_dict(lucky_char)
                else:
                    lucky_char_dict = lucky_char
                    
                item = ItemGenerator.generate_random_equipment(
                    lucky_char_dict['user_id'], 
                    max(5, lucky_char_dict['level'] + 3),  # Minimum 5 stats for lucky items
                    lucky_char_dict['level'] + 12
                )
                
                self.create_item_in_db(item)
                
                await channel.send(
                    f"🍀 **Lucky Day!** **{lucky_char_dict['name']}** found a rare **{item.name}**!"
                )
                
            elif event_type == 'merchant_visit':
                # Traveling merchant offers deals
                discount = random.randint(20, 50)  # 20-50% discount
                gold_bonus = random.randint(50, 200) 
                selected_players = random.sample(chars, min(random.randint(3, 8), len(chars)))
                
                for char in selected_players:
                    char_data = self.db.get_character(char['user_id'])
                    self.db.update_character(char['user_id'], money=char_data['money'] + gold_bonus)
                
                # Create embed for merchant visit
                merchant_embed = self.embed(
                    "🏪 Traveling Merchant!",
                    "A mysterious merchant has arrived with amazing deals!"
                )
                
                customer_names = ", ".join([p['name'] for p in selected_players])
                merchant_embed.add_field(
                    name=f"💰 Lucky Customers ({len(selected_players)})",
                    value=customer_names,
                    inline=False
                )
                
                merchant_embed.add_field(
                    name="🎁 Earnings",
                    value=f"**{gold_bonus}** gold each",
                    inline=True
                )
                
                merchant_embed.color = discord.Color.gold()
                await channel.send(embed=merchant_embed)
                
            elif event_type == 'blessing':
                # Divine blessing affects all players
                xp_bonus = random.randint(25, 75)
                for char in chars:
                    char_data = self.db.get_character(char['user_id'])
                    self.db.update_character(char['user_id'], xp=char_data['xp'] + xp_bonus)
                    
                await channel.send(
                    f"✨ **Divine Blessing!** The gods smile upon all adventurers! Everyone gains {xp_bonus} XP!"
                )
                
            elif event_type == 'cursed_fog':
                # Cursed fog - some lose gold, some gain XP for surviving
                if len(chars) >= 3:
                    affected = random.sample(chars, min(random.randint(2, 6), len(chars)))
                    survivors = random.sample(affected, max(1, len(affected) // 2))
                    
                    # Survivors gain XP
                    xp_bonus = random.randint(40, 120)
                    for survivor in survivors:
                        char_data = self.db.get_character(survivor['user_id'])
                        self.db.update_character(survivor['user_id'], xp=char_data['xp'] + xp_bonus)
                    
                    # Create embed for cursed fog
                    fog_embed = self.embed(
                        "🌫️ Cursed Fog!",
                        "A mysterious fog has descended upon the realm!"
                    )
                    
                    survivor_names = ", ".join([s['name'] for s in survivors])
                    fog_embed.add_field(
                        name=f"🧭 Survivors ({len(survivors)})",
                        value=survivor_names,
                        inline=False
                    )
                    
                    fog_embed.add_field(
                        name="🎁 Reward",
                        value=f"**{xp_bonus}** XP for navigation",
                        inline=True
                    )
                    
                    fog_embed.color = discord.Color.dark_gray()
                    await channel.send(embed=fog_embed)
                    
            elif event_type == 'festival':
                # Festival - everyone gets moderate rewards
                gold_bonus = random.randint(150, 400)
                xp_bonus = random.randint(20, 60)
                
                for char in chars:
                    char_data = self.db.get_character(char['user_id'])
                    self.db.update_character(char['user_id'], 
                                           money=char_data['money'] + gold_bonus,
                                           xp=char_data['xp'] + xp_bonus)
                
                await channel.send(
                    f"🎪 **Grand Festival!** All adventurers celebrate! Everyone gains {gold_bonus} gold and {xp_bonus} XP!"
                )
                
            elif event_type == 'dragon_attack':
                # Dragon attack - high risk, high reward
                if len(chars) >= 4:
                    brave_heroes = random.sample(chars, min(random.randint(3, 8), len(chars)))
                    
                    # High XP and gold for facing the dragon
                    xp_reward = random.randint(80, 200)
                    gold_reward = random.randint(300, 800)
                    
                    # Chance for rare items
                    for hero in brave_heroes:
                        char_data = self.db.get_character(hero['user_id'])
                        self.db.update_character(hero['user_id'], 
                                               money=char_data['money'] + gold_reward,
                                               xp=char_data['xp'] + xp_reward)
                        
                        # 30% chance for dragon-themed rare item (could be armor!)
                        if random.random() < 0.3:
                            item = ItemGenerator.generate_random_equipment(
                                hero['user_id'],
                                max(6, hero['level'] + 4),  # High quality dragon loot
                                hero['level'] + 15
                            )
                            item.name = f"Dragon {item.name}"  # Dragon prefix
                            item.value *= 2  # Double value for dragon loot
                            self.create_item_in_db(item)
                    
                    # Create embed showing all participants
                    dragon_embed = self.embed(
                        "🐉 Dragon Attack!",
                        "A mighty dragon has been defeated by brave heroes!"
                    )
                    
                    # Show all heroes, not truncated
                    hero_names = ", ".join([h['name'] for h in brave_heroes])
                    dragon_embed.add_field(
                        name=f"🛡️ Brave Heroes ({len(brave_heroes)})",
                        value=hero_names,
                        inline=False
                    )
                    
                    dragon_embed.add_field(
                        name="🎁 Rewards",
                        value=f"**{xp_reward}** XP, **{gold_reward}** gold",
                        inline=True
                    )
                    
                    dragon_embed.add_field(
                        name="🐲 Dragon Loot",
                        value="Legendary items for the brave!",
                        inline=True
                    )
                    
                    dragon_embed.color = discord.Color.red()
                    await channel.send(embed=dragon_embed)
        
        except Exception as e:
            logger.error(f"Error in auto_events_loop: {e}")
            
    @tasks.loop(minutes=10)  # Check for completed adventures every 10 minutes
    async def level_up_check(self):
        """Check for completed adventures and level ups"""
        try:
            channel = await self.get_game_channel()
            if not channel:
                return
                
            # Check completed adventures
            completed = self.db.fetchall(
                """SELECT a.*, p.name FROM adventures a
                   JOIN profile p ON a.user_id = p.user_id  
                   WHERE a.status = 'active' AND a.finish_at <= ?""",
                (datetime.now(),)  # Use local time instead of UTC
            )
            
            # Filter for online users only
            online_completed = []
            for adventure in completed:
                user = self.bot.get_user(adventure['user_id'])
                if user and self.is_user_online(user):
                    # Ensure dict format
                    online_completed.append(self.db.row_to_dict(adventure))
            
            if online_completed:
                # If multiple completions, use single embed; otherwise individual embeds
                if len(online_completed) > 1:
                    # Create single dynamic embed for multiple completions
                    completion_embed = self.embed(
                        "🏁 Adventure Returns!",
                        "Heroes return from their quests..."
                    )
                    
                    completion_list = []
                    level_ups = []
                    
                    for adventure in online_completed:
                        char_data = self.db.get_character(adventure['user_id'])
                        
                        # Calculate success chance based on character power (same as adventure.py)
                        equipment_bonus = self.calculate_adventure_power(adventure['user_id'])
                        base_chance = 60  # Base 60% success
                        level_bonus = max(0, char_data['level'] - adventure['difficulty']) * 5  # +5% per level above difficulty
                        equipment_chance = min(20, equipment_bonus // 10)  # Up to +20% from equipment
                        luck_bonus = (char_data['luck'] - 1.0) * 10  # Luck modifier
                        
                        success_chance = min(95, base_chance + level_bonus + equipment_chance + luck_bonus)
                        
                        # Check for Divination Blessing (guaranteed adventure success)
                        blessing_used = False
                        religion_cog = self.bot.get_cog('ReligionCog')
                        if religion_cog:
                            blessing_bonuses = religion_cog.get_active_blessings(adventure['user_id'])
                            if blessing_bonuses['adventure_success']:
                                success = True  # Guarantee success
                                blessing_used = True
                                # Consume the blessing (one-time use)
                                self.db.execute(
                                    "DELETE FROM divine_blessings WHERE user_id = ? AND effect = 'adventure_success'",
                                    (adventure['user_id'],)
                                )
                                self.db.commit()
                        
                        if not blessing_used:
                            success = random.random() < (success_chance / 100)
                        
                        if success:
                            # Dynamic reward scaling based on adventure difficulty and player level
                            difficulty = adventure['difficulty']
                            player_level = char_data['level']

                            # Keep effective_difficulty for item generation
                            effective_difficulty = min(difficulty, 200)

                            # Get tier from difficulty
                            tier = get_tier_from_difficulty(difficulty)

                            # Get race multipliers
                            from cogs.race import RaceCog
                            race_multipliers = RaceCog.get_race_multipliers(adventure['user_id'], self.db)

                            # Get divine blessing bonuses (multiplicative for XP/gold)
                            blessing_xp_mult = 1.0
                            blessing_gold_mult = 1.0
                            religion_cog = self.bot.get_cog('ReligionCog')
                            if religion_cog:
                                blessing_bonuses = religion_cog.get_active_blessings(adventure['user_id'])
                                blessing_xp_mult = blessing_bonuses['xp_mult']
                                blessing_gold_mult = blessing_bonuses['gold_mult']

                            # Calculate rewards using new scaling system
                            final_xp = calculate_xp_reward(
                                player_level=player_level,
                                difficulty=difficulty,
                                tier=tier,
                                race_xp_bonus=race_multipliers['xp_gain'],
                                blessing_xp_mult=blessing_xp_mult
                            )
                            final_gold = calculate_gold_reward(
                                player_level=player_level,
                                difficulty=difficulty,
                                tier=tier,
                                race_gold_bonus=race_multipliers['gold_find'],
                                blessing_gold_mult=blessing_gold_mult
                            )

                            # Add small random variance
                            final_xp += random.randint(20, 100)
                            final_gold += random.randint(50, 200)
                            
                            # Update character
                            new_money = char_data['money'] + final_gold
                            new_xp_total = char_data['xp'] + final_xp
                            
                            # Check for level up
                            old_level = char_data['level']
                            new_level = min(999, 1 + int((new_xp_total / 100) ** 0.5))
                            
                            self.db.update_character(
                                adventure['user_id'],
                                money=new_money,
                                xp=new_xp_total,
                                level=new_level,
                                completed=char_data['completed'] + 1
                            )

                            # Update quest progress for adventure completion
                            await self.update_quest_progress(adventure['user_id'], 'adventures', 1)
                            await self.update_quest_progress(adventure['user_id'], 'xp_gain', final_xp)
                            await self.update_quest_progress(adventure['user_id'], 'gold_earn', final_gold)

                            # Check for item reward
                            item_bonus = ""
                            item_chance = 0.1 + (effective_difficulty * 0.01)  # Reduced scaling
                            if random.random() < item_chance:
                                # Cap item stats to reasonable values based on effective difficulty
                                min_stat = max(4, min(50, effective_difficulty // 4))
                                max_stat = min(100, effective_difficulty // 2 + 10)
                                # Ensure min <= max
                                max_stat = max(min_stat, max_stat)

                                item = ItemGenerator.generate_item(
                                    adventure['user_id'],
                                    min_stat=min_stat,
                                    max_stat=max_stat
                                )

                                self.create_item_in_db(item)
                                item_bonus = f" + **{item.name}**"
                                # Update quest progress for item acquisition
                                await self.update_quest_progress(adventure['user_id'], 'items_acquire', 1)
                            
                            completion_text = f"• **{adventure['name']}** → {final_xp} XP, {final_gold} gold{item_bonus}"
                            
                            # Track level ups
                            if new_level > old_level:
                                level_ups.append(f"🎉 **{adventure['name']}** → Level {new_level}!")
                        else:
                            # Failure - consolation XP scaled by level
                            consolation_xp = random.randint(10, 30) + (char_data['level'] * 2)  # Much more generous
                            new_xp_total = char_data['xp'] + consolation_xp
                            new_level = min(999, 1 + int((new_xp_total / 100) ** 0.5))
                            
                            self.db.update_character(adventure['user_id'], xp=new_xp_total, level=new_level)
                            completion_text = f"• **{adventure['name']}** → ❌ Failed! (+{consolation_xp} XP)"
                        
                        # Mark adventure as completed
                        self.db.execute(
                            "UPDATE adventures SET status = 'completed' WHERE user_id = ? AND finish_at = ?",
                            (adventure['user_id'], adventure['finish_at'])
                        )
                        
                        completion_list.append(completion_text)
                    
                    self.db.commit()
                    
                    # Send single embed with all completions (truncate if too long)
                    completion_text = "\n".join(completion_list)
                    if len(completion_text) > 1020:  # Leave some buffer for safety
                        # Show first few and indicate truncation
                        truncated_list = []
                        char_count = 0
                        shown_count = 0
                        
                        for completion in completion_list:
                            if char_count + len(completion) + 1 > 900:  # Leave room for truncation message
                                break
                            truncated_list.append(completion)
                            char_count += len(completion) + 1  # +1 for newline
                            shown_count += 1
                        
                        remaining = len(completion_list) - shown_count
                        if remaining > 0:
                            truncated_list.append(f"... and {remaining} more adventures!")
                        completion_text = "\n".join(truncated_list)
                    
                    completion_embed.add_field(
                        name=f"📋 {len(online_completed)} Adventures Completed",
                        value=completion_text,
                        inline=False
                    )
                    
                    if level_ups:
                        level_up_text = "\n".join(level_ups)
                        if len(level_up_text) > 1020:  # Truncate if too long
                            truncated_level_ups = []
                            char_count = 0
                            
                            for level_up in level_ups:
                                if char_count + len(level_up) + 1 > 900:
                                    remaining = len(level_ups) - len(truncated_level_ups)
                                    truncated_level_ups.append(f"... and {remaining} more level ups!")
                                    break
                                truncated_level_ups.append(level_up)
                                char_count += len(level_up) + 1
                            
                            level_up_text = "\n".join(truncated_level_ups)
                        
                        completion_embed.add_field(
                            name="🌟 Level Ups!",
                            value=level_up_text,
                            inline=False
                        )
                    
                    completion_embed.add_field(
                        name="⏱️ Status",
                        value="All adventurers have returned successfully!",
                        inline=False
                    )
                    
                    completion_embed.color = discord.Color.green()
                    await channel.send(embed=completion_embed)
                else:
                    # Single completion - use individual embed
                    adventure = online_completed[0]
                    char_data = self.db.get_character(adventure['user_id'])
                    
                    # Calculate success chance (same logic as multi-completion)
                    equipment_bonus = self.calculate_adventure_power(adventure['user_id'])
                    base_chance = 60
                    level_bonus = max(0, char_data['level'] - adventure['difficulty']) * 5
                    equipment_chance = min(20, equipment_bonus // 10)
                    luck_bonus = (char_data['luck'] - 1.0) * 10
                    
                    success_chance = min(95, base_chance + level_bonus + equipment_chance + luck_bonus)
                    
                    # Check for Divination Blessing (guaranteed adventure success)
                    blessing_used = False
                    religion_cog = self.bot.get_cog('ReligionCog')
                    if religion_cog:
                        blessing_bonuses = religion_cog.get_active_blessings(adventure['user_id'])
                        if blessing_bonuses['adventure_success']:
                            success = True  # Guarantee success
                            blessing_used = True
                            # Consume the blessing (one-time use)
                            self.db.execute(
                                "DELETE FROM divine_blessings WHERE user_id = ? AND effect = 'adventure_success'",
                                (adventure['user_id'],)
                            )
                            self.db.commit()
                    
                    if not blessing_used:
                        success = random.random() < (success_chance / 100)
                    
                    if success:
                        difficulty = adventure['difficulty']
                        player_level = char_data['level']

                        # Get tier from difficulty
                        tier = get_tier_from_difficulty(difficulty)

                        # Get race multipliers
                        from cogs.race import RaceCog
                        race_multipliers = RaceCog.get_race_multipliers(adventure['user_id'], self.db)

                        # Get divine blessing bonuses
                        blessing_xp_mult = 1.0
                        blessing_gold_mult = 1.0
                        religion_cog = self.bot.get_cog('ReligionCog')
                        if religion_cog:
                            blessing_bonuses = religion_cog.get_active_blessings(adventure['user_id'])
                            blessing_xp_mult = blessing_bonuses['xp_mult']
                            blessing_gold_mult = blessing_bonuses['gold_mult']

                        # Calculate rewards using new scaling system
                        final_xp = calculate_xp_reward(
                            player_level=player_level,
                            difficulty=difficulty,
                            tier=tier,
                            race_xp_bonus=race_multipliers['xp_gain'],
                            blessing_xp_mult=blessing_xp_mult
                        )
                        final_gold = calculate_gold_reward(
                            player_level=player_level,
                            difficulty=difficulty,
                            tier=tier,
                            race_gold_bonus=race_multipliers['gold_find'],
                            blessing_gold_mult=blessing_gold_mult
                        )

                        # Add small random variance
                        final_xp += random.randint(20, 100)
                        final_gold += random.randint(50, 200)

                        # Keep effective_difficulty for item generation
                        effective_difficulty = min(difficulty, 200)
                        
                        # Update character
                        new_money = char_data['money'] + final_gold
                        new_xp_total = char_data['xp'] + final_xp
                        old_level = char_data['level']
                        new_level = min(999, 1 + int((new_xp_total / 100) ** 0.5))
                        
                        self.db.update_character(
                            adventure['user_id'], 
                            money=new_money,
                            xp=new_xp_total,
                            level=new_level,
                            completed=char_data['completed'] + 1
                        )
                        
                        # Check for item reward
                        item_text = ""
                        item_chance = 0.1 + (effective_difficulty * 0.01)  # Reduced scaling
                        if random.random() < item_chance:
                            # Cap item stats to reasonable values
                            min_stat = max(4, min(50, effective_difficulty // 4))
                            max_stat = min(100, effective_difficulty // 2 + 10)
                            max_stat = max(min_stat, max_stat)

                            item = ItemGenerator.generate_item(
                                adventure['user_id'],
                                min_stat=min_stat,
                                max_stat=max_stat
                            )

                            self.create_item_in_db(item)
                            item_text = f"\n🎁 Found: **{item.name}**"
                        
                        completion_embed = self.embed(
                            f"✅ Adventure Success!",
                            f"**{adventure['name']}** completed their **{adventure['adventure_name']}**!"
                        )
                        completion_embed.add_field(
                            name="💰 Rewards",
                            value=f"{final_xp} XP, {final_gold} gold",
                            inline=True
                        )
                        completion_embed.color = discord.Color.green()
                    else:
                        # Failure - consolation XP scaled by level  
                        consolation_xp = random.randint(10, 30) + (char_data['level'] * 2)
                        new_xp_total = char_data['xp'] + consolation_xp
                        old_level = char_data['level']
                        new_level = min(999, 1 + int((new_xp_total / 100) ** 0.5))
                        
                        self.db.update_character(adventure['user_id'], xp=new_xp_total, level=new_level)
                        
                        completion_embed = self.embed(
                            f"❌ Adventure Failed!",
                            f"**{adventure['name']}** failed their **{adventure['adventure_name']}**!"
                        )
                        completion_embed.add_field(
                            name="🎗️ Consolation",
                            value=f"{consolation_xp} XP",
                            inline=True
                        )
                        completion_embed.color = discord.Color.red()
                        item_text = ""
                    
                    # Mark adventure as completed
                    self.db.execute(
                        "UPDATE adventures SET status = 'completed' WHERE user_id = ? AND finish_at = ?",
                        (adventure['user_id'], adventure['finish_at'])
                    )
                    
                    if new_level > old_level:
                        completion_embed.add_field(
                            name="🎉 Level Up!",
                            value=f"Now level {new_level}!",
                            inline=True
                        )
                    
                    if item_text:
                        completion_embed.add_field(
                            name="🎁 Bonus Item",
                            value=item_text.replace("\n🎁 Found: **", "").replace("**", ""),
                            inline=False
                        )
                    
                    self.db.commit()
                    await channel.send(embed=completion_embed)
                
        except Exception as e:
            logger.error(f"Error in level_up_check: {e}")
            
    @tasks.loop(seconds=30)  # Check every 30 seconds for new players
    async def initial_activity_check(self):
        """Trigger quick activity for new players within 60 seconds"""
        try:
            if self.initial_trigger_done:
                return  # Already did the initial trigger
                
            channel = await self.get_game_channel()
            if not channel:
                return
                
            # Check if we have 2+ characters and this is early in the game
            char_count = len(self.db.fetchall("SELECT user_id FROM profile"))
            completed_adventures = len(self.db.fetchall("SELECT id FROM adventures WHERE status = 'completed'"))
            
            # Trigger if we have 2+ chars and less than 3 completed adventures (early game)
            if char_count >= 2 and completed_adventures < 3:
                self.initial_trigger_done = True
                
                # Wait 30-60 seconds, then trigger first activities
                await asyncio.sleep(random.randint(30, 60))
                
                await channel.send("🎮 **Auto-Game Starting!** The adventure begins...")
                
                # Trigger first adventure
                await self.auto_adventure_loop()
                await asyncio.sleep(3)
                
                # Trigger first battle if we have 2+ characters
                if char_count >= 2:
                    await self.auto_battle_loop()
                    await asyncio.sleep(3)
                    
                # Trigger welcome event
                await self.auto_events_loop()
                
                await channel.send("🤖 **Auto-play is now active!** The game will continue automatically.")
                
        except Exception as e:
            logger.error(f"Error in initial_activity_check: {e}")

    @commands.command()
    async def trigger_adventure(self, ctx: commands.Context):
        """Manually trigger adventure check (for debugging)"""
        await ctx.send("🔍 Manually triggering adventure check...")
        await self.auto_adventure_loop()


    @commands.command()
    @commands.has_permissions(administrator=True)
    async def autoplay(self, ctx: commands.Context, action: str = "status"):
        """Control the automatic gameplay system (admin only)"""
        if action.lower() == "status":
            embed = self.embed(
                "🤖 Auto-Play Status",
                "Automatic gameplay system status"
            )
            
            embed.add_field(
                name="Active Loops",
                value=f"🗺️ Adventures: {'✅' if self.auto_adventure_loop.is_running() else '❌'}\n"
                      f"⚔️ Battles: {'✅' if self.auto_battle_loop.is_running() else '❌'}\n"
                      f"🎉 Events: {'✅' if self.auto_events_loop.is_running() else '❌'}\n"
                      f"📈 Level Checks: {'✅' if self.level_up_check.is_running() else '❌'}",
                inline=False
            )
            
            # Count active characters and adventures
            total_chars = len(self.db.fetchall("SELECT user_id FROM profile"))
            active_adventures = len(self.db.fetchall("SELECT user_id FROM adventures WHERE status = 'active'"))
            
            embed.add_field(
                name="Statistics", 
                value=f"👥 Total Characters: {total_chars}\n🗺️ Active Adventures: {active_adventures}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        elif action.lower() == "start":
            if not self.auto_adventure_loop.is_running():
                self.auto_adventure_loop.start()
            if not self.auto_battle_loop.is_running():
                self.auto_battle_loop.start()
            if not self.auto_events_loop.is_running():
                self.auto_events_loop.start()
            if not self.level_up_check.is_running():
                self.level_up_check.start()
                
            await ctx.send("✅ **Auto-play system started!** The game will now run automatically.")
            
        elif action.lower() == "stop":
            self.auto_adventure_loop.cancel()
            self.auto_battle_loop.cancel()
            self.auto_events_loop.cancel()
            self.level_up_check.cancel()
            
            await ctx.send("⏹️ **Auto-play system stopped.** Manual commands only.")
            
        else:
            await ctx.send("❌ Use: `!autoplay status/start/stop`")

    @tasks.loop(minutes=5)  # Check every 5 minutes
    async def level_fix_loop(self):
        """Fix any level mismatches based on XP"""
        try:
            # Get all characters
            all_chars = self.db.fetchall("SELECT user_id, name, xp, level FROM profile")
            
            fixed_count = 0
            for char in all_chars:
                # Calculate what level they should be
                correct_level = min(999, 1 + int((char['xp'] / 100) ** 0.5))
                
                # If level is wrong, fix it
                if char['level'] != correct_level:
                    self.db.update_character(char['user_id'], level=correct_level)
                    fixed_count += 1
                    
                    # Announce level fix if it's an increase
                    if correct_level > char['level']:
                        channel = await self.get_game_channel()
                        if channel:
                            await channel.send(
                                f"🔧 **Level Correction!** {char['name']} is now level {correct_level} "
                                f"(was {char['level']}, has {char['xp']} XP)"
                            )
            
            if fixed_count > 0:
                logger.info(f"Fixed levels for {fixed_count} characters")
                
        except Exception as e:
            logger.error(f"Error in level_fix_loop: {e}")

    @commands.command()
    @has_character()
    async def status(self, ctx: commands.Context):
        """Check your current adventure status and complete if finished"""
        # Check for active adventure
        active_adventure = self.db.fetchone(
            "SELECT * FROM adventures WHERE user_id = ? AND status = 'active'",
            (ctx.author.id,)
        )
        
        if not active_adventure:
            await ctx.send("❌ You're not currently on an adventure! Auto-play will start one for you soon.")
            return
        
        # Check if adventure is completed
        finish_time = active_adventure['finish_at']
        if isinstance(finish_time, str):
            finish_time = datetime.fromisoformat(finish_time)
        current_time = datetime.now()

        if current_time >= finish_time:
            # Adventure is complete - process completion
            char_data = self.db.get_character(ctx.author.id)
            
            # Use same completion logic as auto loop
            difficulty = active_adventure['difficulty']
            player_level = char_data['level']

            # Keep effective_difficulty for item generation
            effective_difficulty = min(difficulty, 200)

            # Get tier from difficulty
            tier = get_tier_from_difficulty(difficulty)

            # Calculate success chance
            equipment_bonus = self.calculate_adventure_power(ctx.author.id)
            base_chance = 60
            level_bonus_chance = max(0, char_data['level'] - difficulty) * 5
            equipment_chance = min(20, equipment_bonus // 10)
            luck_bonus = (char_data['luck'] - 1.0) * 10

            success_chance = min(95, base_chance + level_bonus_chance + equipment_chance + luck_bonus)

            # Check for Divination Blessing (guaranteed adventure success)
            blessing_used = False
            blessing_xp_mult = 1.0
            blessing_gold_mult = 1.0
            from cogs.religion import ReligionCog
            religion_cog = self.bot.get_cog('ReligionCog')
            if religion_cog:
                blessing_bonuses = religion_cog.get_active_blessings(ctx.author.id)
                blessing_xp_mult = blessing_bonuses['xp_mult']
                blessing_gold_mult = blessing_bonuses['gold_mult']
                if blessing_bonuses['adventure_success']:
                    success = True  # Guarantee success
                    blessing_used = True
                    # Consume the blessing (one-time use)
                    self.db.execute(
                        "DELETE FROM divine_blessings WHERE user_id = ? AND effect = 'adventure_success'",
                        (ctx.author.id,)
                    )
                    self.db.commit()

            if not blessing_used:
                success = random.random() < (success_chance / 100)

            if not success:
                # Adventure failed
                self.db.execute(
                    "UPDATE adventures SET status = 'completed' WHERE id = ?",
                    (active_adventure['id'],)
                )
                self.db.commit()

                embed = self.embed(
                    "💀 Adventure Failed!",
                    f"You failed **{active_adventure['adventure_name']}**..."
                )
                embed.add_field(
                    name="💔 Result",
                    value="No rewards earned. Better luck next time!",
                    inline=False
                )
                await ctx.send(embed=embed)
                return

            # Get race multipliers
            from cogs.race import RaceCog
            race_multipliers = RaceCog.get_race_multipliers(ctx.author.id, self.db)

            # Calculate rewards using new scaling system
            final_xp = calculate_xp_reward(
                player_level=player_level,
                difficulty=difficulty,
                tier=tier,
                race_xp_bonus=race_multipliers['xp_gain'],
                blessing_xp_mult=blessing_xp_mult
            )
            final_gold = calculate_gold_reward(
                player_level=player_level,
                difficulty=difficulty,
                tier=tier,
                race_gold_bonus=race_multipliers['gold_find'],
                blessing_gold_mult=blessing_gold_mult
            )

            # Add small random variance
            final_xp += random.randint(20, 100)
            final_gold += random.randint(50, 200)

            # Update character
            new_xp = char_data['xp'] + final_xp
            new_gold = char_data['money'] + final_gold
            old_level = char_data['level']
            new_level = min(999, 1 + int((new_xp / 100) ** 0.5))
            
            self.db.update_character(
                ctx.author.id,
                xp=new_xp,
                money=new_gold,
                level=new_level
            )
            
            # Mark adventure as completed
            self.db.execute(
                "UPDATE adventures SET status = 'completed' WHERE id = ?",
                (active_adventure['id'],)
            )
            self.db.commit()
            
            # Check for item reward
            item_text = ""
            item_chance = 0.1 + (effective_difficulty * 0.01)  # Reduced scaling
            if random.random() < item_chance:
                # Cap item stats to reasonable values
                min_stat = max(4, min(50, effective_difficulty // 4))
                max_stat = min(100, effective_difficulty // 2 + 10)
                max_stat = max(min_stat, max_stat)

                item = ItemGenerator.generate_item(
                    ctx.author.id,
                    min_stat=min_stat,
                    max_stat=max_stat
                )

                self.create_item_in_db(item)
                item_text = f"\n🎁 Found: **{item.name}**"
                # Update quest progress for item acquisition
                await self.update_quest_progress(ctx.author.id, 'items_acquire', 1)
            
            # Update quest progress
            await self.update_quest_progress(ctx.author.id, 'adventures', 1)
            await self.update_quest_progress(ctx.author.id, 'xp_gain', final_xp)
            await self.update_quest_progress(ctx.author.id, 'gold_earn', final_gold)
            
            # Update completed adventures count
            self.db.update_character(
                ctx.author.id,
                completed=char_data['completed'] + 1
            )
            
            # Create completion embed
            embed = self.embed(
                "🎉 Adventure Complete!",
                f"You completed **{active_adventure['adventure_name']}**!"
            )
            embed.add_field(
                name="🎁 Rewards",
                value=f"**XP:** {final_xp:,}\n**Gold:** {final_gold:,}",
                inline=True
            )
            
            if new_level > old_level:
                embed.add_field(
                    name="🎉 Level Up!",
                    value=f"Now level {new_level}!",
                    inline=True
                )
            
            if item_text:
                embed.add_field(
                    name="🎁 Item Found",
                    value=item_text.replace("\n🎁 Found: **", "").replace("**", ""),
                    inline=False
                )
            
            embed.color = discord.Color.green()
            await ctx.send(embed=embed)
            
        else:
            # Adventure still in progress
            remaining = finish_time - current_time
            hours = int(remaining.total_seconds() // 3600)
            minutes = int((remaining.total_seconds() % 3600) // 60)
            
            # Calculate progress percentage
            start_time = active_adventure['started_at']
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            total_duration = finish_time - start_time
            elapsed = current_time - start_time
            progress_percent = (elapsed.total_seconds() / total_duration.total_seconds()) * 100
            
            # Progress bar
            filled = int(progress_percent // 10)
            progress_bar = "🟩" * filled + "⬜" * (10 - filled)
            
            # Calculate expected rewards using new scaling system (without bonuses)
            char_data = self.db.get_character(ctx.author.id)
            difficulty = active_adventure['difficulty']
            player_level = char_data['level']

            # Get tier from difficulty
            tier = get_tier_from_difficulty(difficulty)

            # Calculate base rewards (no race/blessing bonuses for preview)
            base_xp = calculate_xp_reward(
                player_level=player_level,
                difficulty=difficulty,
                tier=tier,
                race_xp_bonus=1.0,
                blessing_xp_mult=1.0
            )
            base_gold = calculate_gold_reward(
                player_level=player_level,
                difficulty=difficulty,
                tier=tier,
                race_gold_bonus=1.0,
                blessing_gold_mult=1.0
            )
            
            embed = self.embed(
                "🗺️ Adventure in Progress",
                f"**{active_adventure['adventure_name']}**"
            )
            embed.add_field(
                name="⏱️ Time Remaining",
                value=f"{hours}h {minutes}m",
                inline=True
            )
            embed.add_field(
                name="📊 Progress",
                value=f"{progress_bar} {progress_percent:.1f}%",
                inline=False
            )
            embed.add_field(
                name="🎁 Expected Rewards",
                value=f"**Base XP:** {base_xp:,}\n**Base Gold:** {base_gold:,}",
                inline=True
            )
            embed.add_field(
                name="🎯 Difficulty",
                value=f"Level {active_adventure['difficulty']}",
                inline=True
            )
            embed.color = discord.Color.blue()
            embed.set_footer(text=f"Returns at {finish_time.strftime('%Y-%m-%d %H:%M')}")
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AutoPlayCog(bot))