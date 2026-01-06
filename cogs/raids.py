"""Auto-raid system - periodic group raids with bosses"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.character import Character, CharacterClass, Race
from classes.items import ItemGenerator, ItemType

class RaidBoss:
    """Raid boss with stats and mechanics"""
    
    def __init__(self, name: str, level: int, hp: int, attack: int, defense: int, 
                 min_players: int = 20, max_players: int = 40, 
                 xp_reward: int = 500, gold_reward: int = 2000,
                 special_ability: str = None):
        self.name = name
        self.level = level
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.min_players = min_players
        self.max_players = max_players
        self.xp_reward = xp_reward
        self.gold_reward = gold_reward
        self.special_ability = special_ability

class RaidsCog(DiscordRPGCog):
    """Auto-raid system with periodic boss battles"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.active_raid = None
        self.raid_channel = None
        
        # Define raid bosses
        self.raid_bosses = [
            RaidBoss("Ancient Dragon", 25, 15000, 800, 600, 25, 40, 750, 3500, "Dragon Breath"),
            RaidBoss("Lich King", 30, 20000, 900, 700, 30, 40, 900, 4000, "Death Coil"),
            RaidBoss("Kraken", 20, 12000, 750, 500, 20, 35, 600, 2800, "Tentacle Slam"),
            RaidBoss("Shadow Lord", 35, 25000, 1000, 800, 35, 40, 1100, 5000, "Shadow Blast"),
            RaidBoss("Demon Prince", 28, 18000, 850, 650, 25, 38, 850, 3800, "Infernal Strike"),
            RaidBoss("Frost Giant", 22, 14000, 700, 800, 22, 35, 650, 3000, "Ice Storm"),
            RaidBoss("Void Reaper", 40, 30000, 1200, 900, 35, 40, 1300, 6000, "Void Rend"),
            RaidBoss("Elder Wyrm", 32, 22000, 950, 750, 30, 40, 1000, 4500, "Ancient Roar"),
            RaidBoss("Chaos Beast", 26, 16000, 800, 550, 24, 36, 750, 3200, "Chaos Strike"),
            RaidBoss("Undead Colossus", 38, 28000, 1100, 1000, 32, 40, 1200, 5500, "Bone Crush")
        ]
        
    async def cog_load(self):
        """Start the raid loop when cog loads"""
        await self.setup_raid_channel()
        if not self.auto_raids.is_running():
            self.auto_raids.start()
    
    async def cog_unload(self):
        """Stop the raid loop when cog unloads"""
        if self.auto_raids.is_running():
            self.auto_raids.stop()
    
    async def setup_raid_channel(self):
        """Find or create the raid channel"""
        for guild in self.bot.guilds:
            # Look for existing discordrpg channel
            for channel in guild.text_channels:
                if channel.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                    self.raid_channel = channel
                    return
                    
    @tasks.loop(minutes=35)  # Final frequency: 30% increase then 10% decrease from original 45 minutes
    async def auto_raids(self):
        """Automatically start raids periodically"""
        try:
            if self.active_raid:
                return  # Don't start new raid if one is active
                
            # Get all online characters
            online_players = await self.get_online_players()
            if len(online_players) < 10:  # Need minimum players
                return
                
            # Start a raid
            await self.start_raid(online_players)
            
        except Exception as e:
            print(f"Auto-raid error: {e}")
    
    @auto_raids.before_loop
    async def before_auto_raids(self):
        """Wait for bot to be ready"""
        await self.bot.wait_until_ready()
        # Random initial delay of 5-15 minutes
        delay = random.randint(300, 900)
        await asyncio.sleep(delay)
    
    async def get_online_players(self) -> List[Dict]:
        """Get all online players with characters"""
        all_chars = self.db.fetchall("SELECT user_id, name, level FROM profile ORDER BY level DESC")
        online_players = []
        
        for char in all_chars:
            user = self.bot.get_user(char['user_id'])
            if user:
                # Check if user is online in any guild
                for guild in self.bot.guilds:
                    member = guild.get_member(user.id)
                    if member and member.status == discord.Status.online:
                        online_players.append(char)
                        break
                        
        return online_players
    
    async def start_raid(self, available_players: List[Dict]):
        """Start a new raid with selected players"""
        if not self.raid_channel:
            await self.setup_raid_channel()
            if not self.raid_channel:
                return
                
        # Select random boss
        boss = random.choice(self.raid_bosses)
        
        # Select raid participants (20-40 players)
        num_raiders = min(len(available_players), random.randint(boss.min_players, boss.max_players))
        raiders = random.sample(available_players, num_raiders)
        
        self.active_raid = {
            'boss': boss,
            'raiders': raiders,
            'start_time': datetime.now(),
            'boss_hp': boss.hp
        }
        
        # Announce raid start
        embed = self.embed(
            f"🔥 RAID ALERT: {boss.name}",
            f"A **{boss.name}** (Level {boss.level}) has appeared!\n\n"
            f"**{len(raiders)} brave warriors** have been automatically selected to face this threat!"
        )
        embed.add_field(name="👹 Boss Stats", 
                        value=f"**HP:** {boss.hp:,}\n**Attack:** {boss.attack}\n**Defense:** {boss.defense}", 
                        inline=True)
        embed.add_field(name="⚔️ Raiders", 
                        value=f"{len(raiders)} players\n**Avg Level:** {sum(r['level'] for r in raiders) // len(raiders)}", 
                        inline=True)
        embed.add_field(name="🎁 Rewards", 
                        value=f"**XP:** {boss.xp_reward} per player\n**Gold:** {boss.gold_reward} per player\n**Items:** Legendary loot!", 
                        inline=True)
        
        raider_list = ", ".join([r['name'] for r in raiders])
        embed.add_field(name="👥 Participants", value=raider_list, inline=False)
        
        embed.set_footer(text="The raid will commence automatically! Stay online to participate.")
        embed.color = discord.Color.red()
        
        await self.raid_channel.send(embed=embed)
        
        # Wait a moment for drama, then start the battle
        await asyncio.sleep(10)
        await self.run_raid_battle()
    
    async def run_raid_battle(self):
        """Run the actual raid battle mechanics"""
        raid = self.active_raid
        boss = raid['boss']
        raiders = raid['raiders']
        
        # Calculate total raid power
        total_raid_power = 0
        raider_stats = []
        
        for raider_data in raiders:
            # Get full character data and stats
            char_data = self.db.get_character(raider_data['user_id'])
            char = Character(raider_data['user_id'], raider_data['name'])
            char.level = char_data['level']
            char.char_class = CharacterClass(char_data['class'])
            char.race = Race(char_data['race'])
            char.luck = char_data['luck']
            char.raid_stats = char_data['raidstats']
            
            # Get equipped items for power calculation
            items = self.db.get_equipped_items(raider_data['user_id'])
            total_damage = sum(item['damage'] for item in items)
            total_armor = sum(item['armor'] for item in items)
            
            # Add new armor bonuses to raid power
            health_bonus = sum(item.get('health_bonus', 0) for item in items)
            speed_bonus = sum(item.get('speed_bonus', 0) for item in items)
            luck_bonus = sum(item.get('luck_bonus', 0.0) for item in items)
            crit_bonus = sum(item.get('crit_bonus', 0.0) for item in items)
            magic_bonus = sum(item.get('magic_bonus', 0) for item in items)
            
            stats = char.total_stats
            equipment_power = total_damage + total_armor + health_bonus + speed_bonus + int(luck_bonus * 100) + int(crit_bonus * 100) + magic_bonus
            raider_power = (stats['attack'] + stats['defense'] + equipment_power) * stats.get('raid_mult', 1.0)
            total_raid_power += raider_power
            
            raider_stats.append({
                'data': char_data,
                'power': raider_power,
                'stats': stats
            })
        
        # Raid battle calculation
        # Boss scales with number of raiders but raiders have advantage in numbers
        boss_effective_power = boss.attack + boss.defense + (boss.hp / 10)
        raid_success_chance = min(85, max(15, (total_raid_power / boss_effective_power) * 60))
        
        # Add luck bonus to success chance
        avg_luck = sum(rs['stats']['luck'] for rs in raider_stats) / len(raider_stats)
        luck_bonus = (avg_luck - 1.0) * 10
        raid_success_chance += luck_bonus
        
        # Determine outcome
        success = random.randint(1, 100) <= raid_success_chance
        
        # Battle narrative
        await asyncio.sleep(3)
        
        # Combat updates
        await self.raid_channel.send(f"⚔️ **The raid begins!** {len(raiders)} warriors charge into battle against the {boss.name}!")
        await asyncio.sleep(3)
        
        if boss.special_ability:
            await self.raid_channel.send(f"💥 **{boss.name} uses {boss.special_ability}!** The ground trembles with dark power...")
            await asyncio.sleep(3)
        
        # Random combat events
        combat_events = [
            f"🛡️ The raiders form defensive lines against the {boss.name}'s assault!",
            f"⚔️ Weapons clash as heroes strike at the massive beast!",
            f"✨ Magical energies surge across the battlefield!",
            f"🏃 Quick raiders dodge devastating attacks!",
            f"💪 The strongest warriors hold the front line!"
        ]
        
        for i in range(3):
            await self.raid_channel.send(random.choice(combat_events))
            await asyncio.sleep(2)
        
        # Battle outcome
        if success:
            await self.handle_raid_victory(raider_stats, boss)
        else:
            await self.handle_raid_defeat(raider_stats, boss)
        
        # Clear active raid
        self.active_raid = None
    
    async def handle_raid_victory(self, raider_stats: List[Dict], boss: RaidBoss):
        """Handle successful raid completion"""
        embed = self.embed(
            f"🏆 RAID VICTORY!",
            f"**The {boss.name} has been defeated!**\n\nThe combined might of {len(raider_stats)} heroes has triumphed over this legendary foe!"
        )
        embed.color = discord.Color.green()
        
        # Distribute rewards
        total_xp_given = 0
        total_gold_given = 0
        items_awarded = 0
        mvp_power = 0
        mvp_name = ""
        
        # Store individual rewards for display
        individual_rewards = []
        
        for raider in raider_stats:
            char_data = raider['data']
            user_id = char_data['user_id']
            
            # Track MVP
            if raider['power'] > mvp_power:
                mvp_power = raider['power']
                mvp_name = char_data['name']
            
            # Base rewards
            xp_reward = boss.xp_reward + random.randint(50, 150)
            gold_reward = boss.gold_reward + random.randint(200, 800)
            
            # Bonus for higher level bosses
            level_bonus = boss.level * 10
            xp_reward += level_bonus
            gold_reward += level_bonus
            
            # Apply raid multiplier for Raider classes
            if raider['stats'].get('raid_mult', 1.0) > 1.0:
                xp_reward = int(xp_reward * raider['stats']['raid_mult'])
                gold_reward = int(gold_reward * raider['stats']['raid_mult'])
            
            # Update character
            new_money = char_data['money'] + gold_reward
            new_xp = char_data['xp'] + xp_reward
            new_raid_stats = char_data['raidstats'] + 1
            
            self.db.update_character(user_id, 
                                   money=new_money, 
                                   xp=new_xp, 
                                   raidstats=new_raid_stats)
            
            total_xp_given += xp_reward
            total_gold_given += gold_reward
            
            # Track individual rewards
            player_reward = {
                'name': char_data['name'],
                'xp': xp_reward,
                'gold': gold_reward,
                'item': None
            }
            
            # 30% chance for special loot per player
            if random.randint(1, 100) <= 30:
                # Generate high-quality raid item
                item = ItemGenerator.generate_item(
                    user_id,
                    min_stat=max(8, boss.level - 5),
                    max_stat=boss.level + 10,
                    item_type=random.choice(list(ItemType))
                )
                item.name = f"{boss.name}'s {item.name}"
                
                self.db.create_item(
                    user_id, item.name, item.type.value,
                    item.value * 2, item.damage, item.armor, item.hand.value
                )
                items_awarded += 1
                player_reward['item'] = item.name
            
            individual_rewards.append(player_reward)
        
        # Results
        embed.add_field(
            name="💰 Rewards Distributed",
            value=f"**Total XP:** {total_xp_given:,}\n**Total Gold:** {total_gold_given:,}\n**Legendary Items:** {items_awarded}",
            inline=True
        )
        embed.add_field(
            name="🏅 MVP",
            value=f"**{mvp_name}**\nMost Valuable Player!",
            inline=True
        )
        embed.add_field(
            name="📊 Raid Stats",
            value=f"**Success Rate:** High\n**Participants:** {len(raider_stats)}\n**Boss Level:** {boss.level}",
            inline=True
        )
        
        embed.set_footer(text=f"All participants have been rewarded! Next raid in ~35 minutes.")
        
        await self.raid_channel.send(embed=embed)
        
        # Send individual rewards in a follow-up embed
        rewards_embed = self.embed(
            "🎁 Individual Raid Rewards",
            f"Loot distribution for defeating {boss.name}:"
        )
        rewards_embed.color = discord.Color.gold()
        
        # Sort by item recipients first, then by XP
        individual_rewards.sort(key=lambda x: (x['item'] is not None, x['xp']), reverse=True)
        
        # Create reward text in chunks to avoid field limits
        reward_chunks = []
        current_chunk = []
        
        for reward in individual_rewards:
            reward_text = f"**{reward['name']}**: {reward['xp']} XP, {reward['gold']} gold"
            if reward['item']:
                reward_text += f"\n   🎁 *{reward['item']}*"
            current_chunk.append(reward_text)
            
            # Split into chunks of 10 players each
            if len(current_chunk) >= 10:
                reward_chunks.append("\n".join(current_chunk))
                current_chunk = []
        
        # Add remaining players
        if current_chunk:
            reward_chunks.append("\n".join(current_chunk))
        
        # Add fields for each chunk
        for i, chunk in enumerate(reward_chunks[:3]):  # Max 3 fields (30 players shown)
            field_name = f"⚔️ Raiders {i*10 + 1}-{min((i+1)*10, len(individual_rewards))}"
            rewards_embed.add_field(
                name=field_name,
                value=chunk,
                inline=False
            )
        
        # If there are more than 30 players, note it
        if len(individual_rewards) > 30:
            rewards_embed.add_field(
                name="📜 And More...",
                value=f"Plus {len(individual_rewards) - 30} additional raiders!",
                inline=False
            )
        
        await self.raid_channel.send(embed=rewards_embed)
    
    async def handle_raid_defeat(self, raider_stats: List[Dict], boss: RaidBoss):
        """Handle failed raid attempt"""
        embed = self.embed(
            f"💀 RAID FAILED",
            f"**The {boss.name} has proven too powerful!**\n\nDespite the valiant efforts of {len(raider_stats)} heroes, the boss remains victorious..."
        )
        embed.color = discord.Color.red()
        
        # Smaller consolation rewards
        total_xp_given = 0
        total_gold_given = 0
        
        for raider in raider_stats:
            char_data = raider['data']
            user_id = char_data['user_id']
            
            # Consolation rewards (much smaller)
            xp_reward = boss.xp_reward // 3 + random.randint(25, 75)
            gold_reward = boss.gold_reward // 4 + random.randint(100, 300)
            
            # Update character (no raid stats increase on defeat)
            new_money = char_data['money'] + gold_reward
            new_xp = char_data['xp'] + xp_reward
            
            self.db.update_character(user_id, money=new_money, xp=new_xp)
            
            total_xp_given += xp_reward
            total_gold_given += gold_reward
        
        embed.add_field(
            name="💔 Consolation Rewards",
            value=f"**Total XP:** {total_xp_given:,}\n**Total Gold:** {total_gold_given:,}",
            inline=True
        )
        embed.add_field(
            name="🔥 Boss Remains",
            value=f"**{boss.name}** still lurks...\nIt may return in future raids!",
            inline=True
        )
        embed.add_field(
            name="💪 Try Again",
            value=f"Grow stronger and face\nthe next raid challenge!",
            inline=True
        )
        
        embed.set_footer(text=f"Better luck next time! Next raid in ~35 minutes.")
        
        await self.raid_channel.send(embed=embed)
    
    @commands.command()
    @has_character()
    async def raidstatus(self, ctx: commands.Context):
        """Check current raid status"""
        if not self.active_raid:
            # Show when next raid might occur
            embed = self.embed(
                "🏰 No Active Raids",
                "No raids are currently active. Raids occur automatically every ~35 minutes when enough players are online."
            )
            embed.add_field(
                name="⏰ Next Raid",
                value="Check back later! Raids need at least 10 online players.",
                inline=False
            )
        else:
            raid = self.active_raid
            boss = raid['boss']
            embed = self.embed(
                f"🔥 ACTIVE RAID: {boss.name}",
                f"A raid against **{boss.name}** is currently in progress!"
            )
            embed.add_field(
                name="👹 Boss",
                value=f"**Level {boss.level}**\n{boss.hp:,} HP",
                inline=True
            )
            embed.add_field(
                name="⚔️ Raiders",
                value=f"{len(raid['raiders'])} participants",
                inline=True
            )
            
        await ctx.send(embed=embed)
    
    @commands.command()
    async def raids(self, ctx: commands.Context):
        """Show information about the raid system"""
        embed = self.embed(
            "🏰 Raid System",
            "Raids are **automatic group events** that occur every ~35 minutes when enough players are online."
        )
        
        embed.add_field(
            name="🎯 How Raids Work",
            value="• Automatic selection of 20-40 online players\n• Fight powerful bosses as a group\n• Success depends on combined power\n• Better rewards for higher level bosses",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Rewards",
            value="• **Victory:** High XP, gold, legendary items\n• **Defeat:** Smaller consolation rewards\n• **Raid Stats:** Track successful raids\n• **MVP:** Best contributor gets recognition",
            inline=False
        )
        
        embed.add_field(
            name="💡 Tips",
            value="• Stay online (green status) to participate\n• Raider classes get bonus rewards\n• Higher level = better raid contribution\n• Equipment boosts your raid power",
            inline=False
        )
        
        # Show some example bosses
        boss_examples = random.sample(self.raid_bosses, 3)
        boss_list = "\n".join([f"**{b.name}** (Lv.{b.level})" for b in boss_examples])
        embed.add_field(
            name="👹 Example Bosses",
            value=boss_list,
            inline=True
        )
        
        embed.add_field(
            name="⏰ Frequency", 
            value="Every 35 minutes\n(when 10+ players online)",
            inline=True
        )
        
        embed.set_footer(text="Use !raidstatus to check for active raids")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RaidsCog(bot))