"""Adventure and quest system"""
import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemGenerator

class AdventureCog(DiscordRPGCog):
    """Adventure and quest commands"""
    
    # Adventure types with (name, min_minutes, max_minutes, min_reward, max_reward, difficulty)
    ADVENTURES = [
        # Short adventures (5-60 minutes)
        ("Help a farmer with lost sheep", 5, 10, 50, 150, 1),
        ("Clear rats from the cellar", 8, 15, 80, 200, 2),
        ("Deliver an urgent message", 10, 20, 100, 250, 2),
        ("Find a lost pet", 12, 18, 120, 280, 2),
        ("Escort a merchant caravan", 12, 25, 120, 300, 3),
        ("Investigate strange noises", 15, 30, 150, 400, 4),
        ("Guard a village festival", 20, 35, 180, 450, 3),
        ("Hunt wild boars in the forest", 20, 40, 200, 500, 5),
        ("Rescue trapped miners", 25, 45, 220, 550, 4),
        ("Explore ancient ruins", 25, 50, 250, 600, 6),
        ("Defeat goblin raiders", 30, 60, 300, 700, 7),
        
        # Medium adventures (45-180 minutes)  
        ("Search for lost treasure", 45, 90, 400, 800, 6),
        ("Retrieve stolen artifacts", 50, 100, 450, 900, 8),
        ("Investigate haunted manor", 60, 120, 500, 1000, 9),
        ("Slay a dangerous beast", 70, 140, 600, 1200, 9),
        ("Defend against orc siege", 80, 160, 700, 1400, 10),
        ("Venture into dragon's lair", 90, 180, 800, 1600, 10),
        ("Infiltrate enemy fortress", 100, 180, 900, 1700, 11),
        
        # Long adventures (2-8 hours)
        ("Journey to distant lands", 120, 240, 1000, 2000, 12),
        ("Seal an ancient evil", 150, 300, 1200, 2400, 13),
        ("Navigate the Shadowlands", 180, 360, 1400, 2800, 14),
        ("Save the kingdom", 200, 400, 1600, 3200, 15),
        ("Quest for the Holy Grail", 240, 420, 1800, 3600, 16),
        
        # Epic adventures (6-24 hours)
        ("Explore the Underdark", 360, 600, 2000, 4000, 17),
        ("Cross the Elemental Planes", 420, 720, 2200, 4400, 18),
        ("Challenge the Gods", 480, 960, 2500, 5000, 20),
        ("Conquer the Nine Hells", 600, 1200, 3000, 6000, 22),
        ("Reforge the World", 720, 1440, 3500, 7000, 25),
        
        # Legendary adventures (1-7 days)
        ("Transcend mortal limits", 1440, 2880, 5000, 10000, 30),
        ("Become one with eternity", 2160, 4320, 7000, 14000, 35),
        ("Reshape reality itself", 2880, 5760, 10000, 20000, 40),
        ("Achieve ultimate ascension", 4320, 10080, 15000, 30000, 50),
    ]
    
    @commands.command(aliases=["adv"])
    @has_character()
    async def adventure(self, ctx: commands.Context, duration: int = None):
        """Adventures are automatic! No manual start needed."""
        await ctx.send(
            "🤖 **Adventures are automatic!**\n\n"
            "✅ Just stay **online** (green status) and adventures will start automatically\n"
            "✅ Use `!autoplay status` to check the auto-game system\n"
            "✅ Use `!profile` to see your progress\n\n"
            "No manual adventure commands needed!"
        )
        return
        # Check if already on adventure
        active = self.db.get_active_adventure(ctx.author.id)
        if active:
            finish_time = datetime.fromisoformat(active['finish_at'].replace('Z', '+00:00'))
            remaining = (finish_time - datetime.now()).total_seconds()
            if remaining > 0:
                mins, secs = divmod(int(remaining), 60)
                await ctx.send(f"❌ You're already on an adventure! Completes in {mins}m {secs}s")
                return
                
        # Get character data for power calculation
        char_data = self.db.get_character(ctx.author.id)
        char_level = char_data['level']
        
        # Show available adventures if no duration specified
        if duration is None:
            embed = self.embed(
                "🗺️ Available Adventures",
                "Choose an adventure duration (in minutes):"
            )
            
            # Group adventures by duration category
            short_adventures = []
            medium_adventures = []
            long_adventures = []
            epic_adventures = []
            legendary_adventures = []
            
            for i, (name, min_dur, max_dur, min_reward, max_reward, difficulty) in enumerate(self.ADVENTURES):
                if difficulty <= char_level + 5:  # Can do adventures up to 5 levels above
                    risk = "🟢 Easy" if difficulty <= char_level - 2 else "🟡 Medium" if difficulty <= char_level + 1 else "🔴 Hard"
                    
                    # Format duration nicely
                    if max_dur < 60:
                        duration_str = f"{min_dur}-{max_dur}min"
                    elif max_dur < 1440:
                        duration_str = f"{min_dur//60}-{max_dur//60}h"
                    else:
                        duration_str = f"{min_dur//1440}-{max_dur//1440}d"
                    
                    adventure_text = f"**{duration_str}**: {name}\n├ Reward: {min_reward:,}-{max_reward:,} gold | {risk}"
                    
                    if max_dur <= 60:
                        short_adventures.append(adventure_text)
                    elif max_dur <= 180:
                        medium_adventures.append(adventure_text)
                    elif max_dur <= 480:
                        long_adventures.append(adventure_text)
                    elif max_dur <= 1440:
                        epic_adventures.append(adventure_text)
                    else:
                        legendary_adventures.append(adventure_text)
            
            # Add categories with adventures
            if short_adventures:
                embed.add_field(
                    name="⚡ Short Adventures (5min - 1h)",
                    value="\n\n".join(short_adventures[:5]),  # Show first 5
                    inline=False
                )
            if medium_adventures:
                embed.add_field(
                    name="⏳ Medium Adventures (45min - 3h)",
                    value="\n\n".join(medium_adventures[:4]),  # Show first 4
                    inline=False
                )
            if long_adventures:
                embed.add_field(
                    name="🏔️ Long Adventures (2h - 8h)",
                    value="\n\n".join(long_adventures[:3]),  # Show first 3
                    inline=False
                )
            if epic_adventures:
                embed.add_field(
                    name="🌟 Epic Adventures (6h - 24h)",
                    value="\n\n".join(epic_adventures[:3]),  # Show first 3
                    inline=False
                )
            if legendary_adventures and char_level >= 25:  # Only show to high level players
                embed.add_field(
                    name="🏆 Legendary Adventures (1d - 7d)",
                    value="\n\n".join(legendary_adventures[:2]),  # Show first 2
                    inline=False
                )
            
            # Add usage instructions if any adventures are available
            if any([short_adventures, medium_adventures, long_adventures, epic_adventures, legendary_adventures]):
                embed.add_field(
                    name="🎮 Usage",
                    value=f"Use `!adventure <minutes>` to start\nExamples: `!adventure 15` (15 min), `!adventure 120` (2 hours), `!adventure 1440` (1 day)",
                    inline=False
                )
            else:
                embed.description = "No adventures available for your level!"
                
            await ctx.send(embed=embed)
            return
            
        # Validate duration
        if not 5 <= duration <= 10080:  # 5 minutes to 7 days
            await ctx.send("❌ Adventure duration must be between 5 minutes and 7 days (10080 minutes)!")
            return
            
        # Find suitable adventure
        suitable_adventures = [
            adv for adv in self.ADVENTURES 
            if adv[1] <= duration <= adv[2] and adv[5] <= char_level + 2
        ]
        
        if not suitable_adventures:
            await ctx.send("❌ No adventures available for that duration at your level!")
            return
            
        # Select random adventure
        adventure = random.choice(suitable_adventures)
        name, min_dur, max_dur, min_reward, max_reward, difficulty = adventure
        
        # Calculate success chance based on character power
        equipment_bonus = self.calculate_adventure_power(ctx.author.id)
        base_chance = 60  # Base 60% success
        level_bonus = max(0, char_level - difficulty) * 5  # +5% per level above difficulty
        equipment_chance = min(20, equipment_bonus // 10)  # Up to +20% from equipment
        luck_bonus = (char_data['luck'] - 1.0) * 10  # Luck modifier
        
        success_chance = min(95, base_chance + level_bonus + equipment_chance + luck_bonus)
        
        # Start adventure
        finish_time = datetime.now() + timedelta(minutes=duration)
        success = self.db.start_adventure(ctx.author.id, name, difficulty, duration * 60)
        
        if not success:
            await ctx.send("❌ Failed to start adventure!")
            return
            
        embed = self.embed(
            "🗺️ Adventure Started!",
            f"You embark on: **{name}**"
        )
        embed.add_field(name="⏱️ Duration", value=f"{duration} minutes", inline=True)
        embed.add_field(name="🎯 Difficulty", value=f"Level {difficulty}", inline=True) 
        embed.add_field(name="📊 Success Chance", value=f"{success_chance:.1f}%", inline=True)
        embed.add_field(name="💰 Potential Reward", value=f"{min_reward}-{max_reward} gold", inline=True)
        embed.add_field(name="🏁 Completes", value=f"<t:{int(finish_time.timestamp())}:R>", inline=True)
        
        embed.set_footer(text="Use !status to check progress, or !cancel to abort")
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def status(self, ctx: commands.Context):
        """Check your adventure status"""
        active = self.db.get_active_adventure(ctx.author.id)
        if not active:
            await ctx.send(
                "❌ **You're not on an adventure!**\n\n"
                "🤖 Adventures are **automatic** - just stay **online** (green status)\n"
                "✅ Use `!autoplay status` to check the auto-game system\n"
                "✅ Use `!profile` to see your progress"
            )
            return
            
        finish_time = datetime.fromisoformat(active['finish_at'].replace('Z', '+00:00'))
        remaining = (finish_time - datetime.now()).total_seconds()
        
        if remaining <= 0:
            # Adventure completed, process results
            await self.complete_adventure(ctx, active)
            return
            
        # Show progress
        total_duration = (finish_time - datetime.fromisoformat(active['started_at'].replace('Z', '+00:00'))).total_seconds()
        progress = max(0, (total_duration - remaining) / total_duration * 100)
        
        mins, secs = divmod(int(remaining), 60)
        hours, mins = divmod(mins, 60)
        
        time_str = f"{hours}h {mins}m {secs}s" if hours > 0 else f"{mins}m {secs}s"
        
        embed = self.embed(
            "🗺️ Adventure in Progress",
            f"**{active['adventure_name']}**"
        )
        embed.add_field(name="⏱️ Time Remaining", value=time_str, inline=True)
        embed.add_field(name="📊 Progress", value=f"{progress:.1f}%", inline=True)
        embed.add_field(name="🎯 Difficulty", value=f"Level {active['difficulty']}", inline=True)
        
        # Progress bar
        filled = int(progress / 10)
        bar = "🟩" * filled + "⬜" * (10 - filled)
        embed.add_field(name="Progress Bar", value=bar, inline=False)
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def cancel(self, ctx: commands.Context):
        """Cancel your current adventure"""
        active = self.db.get_active_adventure(ctx.author.id)
        if not active:
            await ctx.send("❌ You're not on an adventure!")
            return
            
        if not await ctx.confirm("Cancel your current adventure? You won't get any rewards."):
            await ctx.send("Adventure continues.")
            return
            
        # Cancel adventure
        self.db.complete_adventure(active['id'], False)
        
        embed = self.embed(
            "🚫 Adventure Cancelled",
            f"You abandoned: **{active['adventure_name']}**"
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def complete(self, ctx: commands.Context):
        """Manually complete your adventure (if time is up)"""
        active = self.db.get_active_adventure(ctx.author.id)
        if not active:
            await ctx.send("❌ You're not on an adventure!")
            return
            
        finish_time = datetime.fromisoformat(active['finish_at'].replace('Z', '+00:00'))
        remaining = (finish_time - datetime.now()).total_seconds()
        
        if remaining > 0:
            mins, secs = divmod(int(remaining), 60)
            await ctx.send(f"❌ Adventure not complete yet! {mins}m {secs}s remaining.")
            return
            
        await self.complete_adventure(ctx, active)
        
    async def complete_adventure(self, ctx: commands.Context, adventure_data: dict):
        """Process adventure completion"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Calculate success
        equipment_bonus = self.calculate_adventure_power(ctx.author.id)
        base_chance = 60
        level_bonus = max(0, char_data['level'] - adventure_data['difficulty']) * 5
        equipment_chance = min(20, equipment_bonus // 10)
        luck_bonus = (char_data['luck'] - 1.0) * 10
        
        success_chance = min(95, base_chance + level_bonus + equipment_chance + luck_bonus)
        success = random.random() < (success_chance / 100)
        
        # Mark as complete
        self.db.complete_adventure(adventure_data['id'], success)
        
        # Get adventure details
        adventure_info = None
        for adv in self.ADVENTURES:
            if adv[0] == adventure_data['adventure_name']:
                adventure_info = adv
                break
                
        if not adventure_info:
            await ctx.send("❌ Adventure data corrupted!")
            return
            
        name, min_dur, max_dur, min_reward, max_reward, difficulty = adventure_info
        
        embed = self.embed(
            "🏁 Adventure Complete!",
            f"**{adventure_data['adventure_name']}**"
        )
        
        if success:
            # Calculate base rewards
            gold_reward = random.randint(min_reward, max_reward)
            xp_reward = difficulty * 10 + random.randint(5, 15)
            
            # Bonus for higher difficulty
            difficulty_bonus = max(0, difficulty - char_data['level']) * 0.1
            gold_reward = int(gold_reward * (1 + difficulty_bonus))
            
            # Apply race multipliers
            from cogs.race import RaceCog
            race_multipliers = RaceCog.get_race_multipliers(ctx.author.id)
            
            # Apply divine blessing bonuses
            from cogs.religion import ReligionCog
            religion_cog = self.bot.get_cog('ReligionCog')
            if religion_cog:
                blessing_bonuses = religion_cog.get_active_blessings(ctx.author.id)
                # Apply blessing multipliers
                race_multipliers['xp_gain'] *= blessing_bonuses['xp_mult']
                race_multipliers['gold_find'] *= blessing_bonuses['gold_mult']
                
                # Check for guaranteed adventure success blessing
                if blessing_bonuses['adventure_success']:
                    # Consume the blessing (one-time use)
                    self.db.execute(
                        "DELETE FROM divine_blessings WHERE user_id = ? AND effect = 'adventure_success'",
                        (ctx.author.id,)
                    )
                    self.db.commit()
            
            # Apply final multipliers
            gold_reward = int(gold_reward * race_multipliers['gold_find'])
            xp_reward = int(xp_reward * race_multipliers['xp_gain'])
            
            # Give rewards
            new_money = char_data['money'] + gold_reward
            
            self.db.update_character(
                ctx.author.id, 
                money=new_money,
                xp=char_data['xp'] + xp_reward,
                completed=char_data['completed'] + 1
            )
            
            embed.color = discord.Color.green()
            embed.add_field(name="✅ Result", value="**SUCCESS!**", inline=True)
            embed.add_field(name="💰 Gold Earned", value=f"{gold_reward:,}", inline=True)
            embed.add_field(name="⭐ XP Gained", value=f"{xp_reward}", inline=True)
            
            # Chance for item reward (10% + difficulty bonus)
            item_chance = 0.1 + (difficulty * 0.02)
            if random.random() < item_chance:
                # Generate item reward
                min_stat = max(4, difficulty + 1)  # Minimum 4 stats, difficulty-appropriate
                max_stat = min(50, difficulty + 8)
                
                item = ItemGenerator.generate_item(
                    ctx.author.id,
                    min_stat=min_stat,
                    max_stat=max_stat
                )
                
                item_id = self.db.create_item(
                    ctx.author.id, item.name, item.type.value,
                    item.value, item.damage, item.armor, item.hand.value
                )
                
                embed.add_field(
                    name="🎁 Bonus Item!",
                    value=f"**{item.name}**\n{item.damage}⚔️ {item.armor}🛡️",
                    inline=False
                )
                
        else:
            # Failure
            embed.color = discord.Color.red()
            embed.add_field(name="❌ Result", value="**FAILED!**", inline=True)
            embed.add_field(name="💰 Gold Earned", value="0", inline=True)
            embed.add_field(name="⭐ XP Gained", value="0", inline=True)
            
            # Small consolation XP
            consolation_xp = random.randint(1, 5)
            self.db.update_character(ctx.author.id, xp=char_data['xp'] + consolation_xp)
            embed.add_field(name="🎗️ Consolation", value=f"{consolation_xp} XP", inline=False)
            
        # Log transaction
        if success:
            self.db.log_transaction(
                None, ctx.author.id, gold_reward, "adventure_reward",
                {"adventure": adventure_data['adventure_name'], "difficulty": difficulty}
            )
            
        await ctx.send(embed=embed)
        
    def calculate_adventure_power(self, user_id: int) -> int:
        """Calculate adventure power from equipment"""
        items = self.db.get_equipped_items(user_id)
        return sum(item['damage'] + item['armor'] for item in items)
        
    @commands.command()
    @has_character()
    async def adventures(self, ctx: commands.Context):
        """View your adventure history"""
        # Get completed adventures
        history = self.db.fetchall(
            """SELECT * FROM adventures 
               WHERE user_id = ? AND status != 'active' 
               ORDER BY started_at DESC LIMIT 10""",
            (ctx.author.id,)
        )
        
        char_data = self.db.get_character(ctx.author.id)
        
        embed = self.embed(
            "📜 Adventure History",
            f"Total completed: **{char_data['completed']}**"
        )
        
        if not history:
            embed.add_field(
                name="No Adventures Yet",
                value="Stay **online** (green status) and adventures will start automatically!",
                inline=False
            )
        else:
            history_text = []
            for adv in history:
                status = "✅" if adv['status'] == 'completed' else "❌"
                date = datetime.fromisoformat(adv['started_at'].replace('Z', '+00:00')).strftime('%m/%d')
                history_text.append(f"{status} **{adv['adventure_name']}** ({date})")
                
            embed.add_field(
                name="Recent Adventures",
                value="\n".join(history_text),
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdventureCog(bot))