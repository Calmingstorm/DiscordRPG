"""Daily rewards and streak system"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import CrateSystem

class DailyCog(DiscordRPGCog):
    """Daily rewards and bonuses"""
    
    @commands.command()
    @has_character()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # Once per day
    async def daily(self, ctx: commands.Context):
        """Claim your daily reward"""
        char_data = self.db.get_character(ctx.author.id)
        
        # Check last daily claim and prevent race conditions
        last_date = char_data['last_date']
        today = datetime.now().strftime('%Y-%m-%d')
        
        if last_date == today:
            await ctx.send("❌ You've already claimed your daily reward today!")
            return
            
        # Calculate streak
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        current_streak = char_data['streak'] if last_date == yesterday else 0
        new_streak = current_streak + 1
        
        # Cap streak at 10 days for max rewards
        display_streak = min(new_streak, 10)
        
        # Base reward increases with streak
        base_gold = 100 + (display_streak * 50)  # 100-600 gold
        base_xp = 50 + (display_streak * 25)     # 50-300 XP
        
        # Random multiplier (0.8x to 1.2x)
        multiplier = random.uniform(0.8, 1.2)
        gold_reward = int(base_gold * multiplier)
        xp_reward = int(base_xp * multiplier)
        
        # Double-check and update atomically to prevent race condition
        try:
            updated_rows = self.db.execute(
                """UPDATE profile SET 
                   money = money + ?, 
                   xp = xp + ?, 
                   last_date = ?,
                   streak = ?
                   WHERE user_id = ? AND (last_date != ? OR last_date IS NULL)""",
                (gold_reward, xp_reward, today, new_streak, ctx.author.id, today)
            )
            
            if updated_rows == 0:
                await ctx.send("❌ You've already claimed your daily reward today!")
                return
                
            self.db.commit()
            
        except Exception as e:
            await ctx.send("❌ An error occurred while processing your daily reward. Please try again.")
            return
        
        embed = self.embed(
            "🌅 Daily Reward Claimed!",
            f"Day **{display_streak}** of your streak!"
        )
        
        embed.add_field(name="💰 Gold", value=f"+{gold_reward:,}", inline=True)
        embed.add_field(name="⭐ XP", value=f"+{xp_reward}", inline=True)
        embed.add_field(name="🔥 Streak", value=f"{new_streak} days", inline=True)
        
        # Bonus rewards based on streak
        bonuses = []
        
        # Crate rewards (every 3 days)
        if display_streak >= 3 and display_streak % 3 == 0:
            if display_streak <= 6:
                crate_type = "common"
                crate_field = "crates_common"
            elif display_streak <= 9:
                crate_type = "uncommon" 
                crate_field = "crates_uncommon"
            else:
                crate_type = "rare"
                crate_field = "crates_rare"
                
            current_crates = char_data[crate_field]
            self.db.update_character(ctx.author.id, **{crate_field: current_crates + 1})
            bonuses.append(f"🎁 1x {crate_type.title()} Crate")
            
        # Lucky coin (every 7 days)
        if display_streak >= 7 and display_streak % 7 == 0:
            luck_bonus = 0.1
            new_luck = char_data['luck'] + luck_bonus
            self.db.update_character(ctx.author.id, luck=new_luck)
            bonuses.append(f"🍀 +{luck_bonus} Luck")
            
        # Perfect week bonus (day 7)
        if display_streak == 7:
            bonus_gold = 1000
            self.db.update_character(ctx.author.id, money=char_data['money'] + gold_reward + bonus_gold)
            bonuses.append(f"💎 Week Bonus: +{bonus_gold:,} gold")
            
        # Perfect 10-day streak
        if display_streak == 10:
            # Magic crate
            magic_crates = char_data['crates_magic']
            self.db.update_character(ctx.author.id, crates_magic=magic_crates + 1)
            bonuses.append("✨ 1x Magic Crate")
            
        if bonuses:
            embed.add_field(
                name="🎉 Streak Bonuses",
                value="\n".join(bonuses),
                inline=False
            )
            
        # Show next milestone
        if new_streak < 10:
            next_milestone = None
            if new_streak < 3:
                next_milestone = f"Day 3: Common Crate"
            elif new_streak < 6:
                next_milestone = f"Day 6: Uncommon Crate" 
            elif new_streak < 7:
                next_milestone = f"Day 7: Week Bonus + Luck"
            elif new_streak < 9:
                next_milestone = f"Day 9: Rare Crate"
            elif new_streak < 10:
                next_milestone = f"Day 10: Magic Crate"
                
            if next_milestone:
                embed.add_field(
                    name="🎯 Next Milestone",
                    value=next_milestone,
                    inline=False
                )
        else:
            embed.add_field(
                name="👑 Streak Master",
                value="You've reached the maximum daily streak! Keep claiming for continued rewards.",
                inline=False
            )
            
        # Log transaction
        self.db.log_transaction(
            None, ctx.author.id, gold_reward, "daily_reward",
            {"streak": new_streak, "xp": xp_reward}
        )
        
        embed.set_footer(text=f"Come back tomorrow to continue your streak!")
        embed.color = discord.Color.gold()
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["streaks"])
    @has_character()
    async def streak(self, ctx: commands.Context):
        """View your current daily streak"""
        char_data = self.db.get_character(ctx.author.id)
        
        last_date = char_data['last_date']
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Check if streak is still valid
        if last_date == today:
            status = "✅ Claimed today"
            current_streak = char_data['streak']
        elif last_date == yesterday:
            status = "⏰ Ready to claim"
            current_streak = char_data['streak']
        else:
            status = "💔 Streak broken"
            current_streak = 0
            
        embed = self.embed(
            "🔥 Daily Streak",
            f"Current streak: **{current_streak}** days"
        )
        
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Last Claim", value=last_date or "Never", inline=True)
        
        # Show upcoming rewards
        display_streak = min(current_streak + 1, 10)
        next_rewards = []
        
        base_gold = 100 + (display_streak * 50)
        base_xp = 50 + (display_streak * 25)
        next_rewards.append(f"💰 {base_gold:,} gold")
        next_rewards.append(f"⭐ {base_xp} XP")
        
        # Check for bonus rewards
        if display_streak >= 3 and display_streak % 3 == 0:
            if display_streak <= 6:
                next_rewards.append("🎁 Common Crate")
            elif display_streak <= 9:
                next_rewards.append("🎁 Uncommon Crate") 
            else:
                next_rewards.append("🎁 Rare Crate")
                
        if display_streak >= 7 and display_streak % 7 == 0:
            next_rewards.append("🍀 +0.1 Luck")
            
        if display_streak == 7:
            next_rewards.append("💎 Week Bonus: +1,000 gold")
            
        if display_streak == 10:
            next_rewards.append("✨ Magic Crate")
            
        embed.add_field(
            name="Next Claim Rewards",
            value="\n".join(next_rewards),
            inline=False
        )
        
        # Streak milestones
        milestones = [
            "Day 3: First crate bonus",
            "Day 6: Uncommon crate",
            "Day 7: Perfect week + luck bonus",
            "Day 9: Rare crate",
            "Day 10: Magic crate (max streak)"
        ]
        
        embed.add_field(
            name="🎯 Streak Milestones",
            value="\n".join(milestones),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def vote(self, ctx: commands.Context):
        """Vote for the bot (placeholder for vote rewards)"""
        embed = self.embed(
            "🗳️ Vote for DiscordRPG",
            "Voting rewards coming soon!"
        )
        
        embed.add_field(
            name="How Voting Will Work",
            value="• Vote on bot listing sites\n• Get bonus crates and gold\n• Special voter-only perks\n• Support bot development",
            inline=False
        )
        
        embed.add_field(
            name="Planned Rewards",
            value="• Rare crates\n• Bonus gold multiplier\n• Exclusive titles\n• Priority support",
            inline=False
        )
        
        embed.set_footer(text="This feature is in development!")
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def leaderboard(self, ctx: commands.Context, category: str = "level"):
        """View leaderboards"""
        valid_categories = ["level", "money", "pvp", "completed"]
        
        if category.lower() not in valid_categories:
            await ctx.send(f"❌ Invalid category! Options: {', '.join(valid_categories)}")
            return
            
        # Get leaderboard data
        leaders = self.db.get_leaderboard(category.lower(), 10)
        
        if not leaders:
            await ctx.send("❌ No leaderboard data available!")
            return
            
        category_names = {
            "level": "🏆 Level Leaderboard",
            "money": "💰 Wealth Leaderboard", 
            "pvp": "⚔️ PvP Leaderboard",
            "completed": "🗺️ Adventure Leaderboard"
        }
        
        embed = self.embed(category_names[category.lower()], "Top 10 players")
        
        leaderboard_text = []
        for i, player in enumerate(leaders, 1):
            user = ctx.bot.get_user(player['user_id'])
            name = user.display_name if user else player['name']
            
            if category == "level":
                value = f"Level {player['level']} ({player['xp']:,} XP)"
            elif category == "money":
                value = f"{player['money']:,} gold"
            elif category == "pvp":
                total_fights = player['pvpwins'] + player['pvplosses']
                winrate = (player['pvpwins'] / total_fights * 100) if total_fights > 0 else 0
                value = f"{player['pvpwins']} wins ({winrate:.1f}% winrate)"
            else:  # completed
                value = f"{player['completed']} adventures"
                
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            leaderboard_text.append(f"{medal} **{name}** - {value}")
            
        embed.add_field(
            name="Rankings",
            value="\n".join(leaderboard_text),
            inline=False
        )
        
        # Show user's rank if not in top 10
        user_rank = None
        all_leaders = self.db.get_leaderboard(category.lower(), 100)
        for i, player in enumerate(all_leaders, 1):
            if player['user_id'] == ctx.author.id:
                user_rank = i
                break
                
        if user_rank and user_rank > 10:
            char_data = self.db.get_character(ctx.author.id)
            if category == "level":
                user_value = f"Level {char_data['level']}"
            elif category == "money":
                user_value = f"{char_data['money']:,} gold"
            elif category == "pvp":
                user_value = f"{char_data['pvpwins']} wins"
            else:
                user_value = f"{char_data['completed']} adventures"
                
            embed.add_field(
                name="Your Rank",
                value=f"#{user_rank} - {user_value}",
                inline=False
            )
            
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(DailyCog(bot))