"""Achievement commands and automatic unlock checks."""
import discord
from discord.ext import commands

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from utils.achievements import (
    achievement_points,
    all_achievements,
    evaluate_profile,
    get_achievement,
)


class AchievementsCog(DiscordRPGCog):
    """Player achievement tracking and leaderboards."""

    async def check_achievements(self, user_id: int, channel=None):
        """Evaluate and persist newly unlocked achievements for a user."""
        profile = self.db.get_character(user_id)
        if not profile:
            return []

        unlocked_keys = self.db.get_achievement_keys(user_id)
        newly_available = evaluate_profile(profile, unlocked_keys)
        saved_keys = self.db.unlock_achievements(user_id, [achievement.key for achievement in newly_available])
        newly_unlocked = [achievement for achievement in newly_available if achievement.key in saved_keys]

        if channel and newly_unlocked:
            embed = self.success_embed("Achievement unlocked")
            for achievement in newly_unlocked[:5]:
                embed.add_field(
                    name=f"{achievement.icon} {achievement.name}",
                    value=f"{achievement.description}\n+{achievement.points} achievement points",
                    inline=False,
                )
            if len(newly_unlocked) > 5:
                embed.set_footer(text=f"{len(newly_unlocked) - 5} more unlocked. Use !achievements to see the pile.")
            await channel.send(embed=embed)

        return newly_unlocked

    @commands.command(aliases=["ach", "badges"])
    @has_character()
    async def achievements(self, ctx: commands.Context, user: discord.User = None):
        """View your unlocked achievements."""
        target = user or ctx.author
        profile = self.db.get_character(target.id)
        if not profile:
            await ctx.send("❌ That user does not have a character yet.")
            return

        await self.check_achievements(target.id)
        unlocked_rows = self.db.get_user_achievements(target.id)
        unlocked_keys = [row["achievement_key"] for row in unlocked_rows]
        unlocked_set = set(unlocked_keys)
        total_points = achievement_points(unlocked_keys)
        possible_points = achievement_points(achievement.key for achievement in all_achievements())

        embed = self.embed(
            f"🏆 Achievements: {profile['name']}",
            f"**{len(unlocked_keys)}/{len(all_achievements())}** unlocked • **{total_points}/{possible_points}** points",
        )

        recent_lines = []
        for key in unlocked_keys[-10:][::-1]:
            achievement = get_achievement(key)
            if achievement:
                recent_lines.append(f"{achievement.icon} **{achievement.name}** — {achievement.description}")

        locked_count = len(all_achievements()) - len(unlocked_keys)
        next_lines = []
        for achievement in all_achievements():
            if achievement.key not in unlocked_set and not achievement.hidden:
                next_lines.append(f"{achievement.icon} **{achievement.name}** — {achievement.description}")
            if len(next_lines) >= 5:
                break

        embed.add_field(
            name="Recently unlocked",
            value="\n".join(recent_lines) if recent_lines else "Nothing yet. Grim, but fixable.",
            inline=False,
        )
        embed.add_field(
            name=f"Next targets ({locked_count} locked)",
            value="\n".join(next_lines) if next_lines else "All achievements unlocked. The saga is complete.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["achlist"])
    async def achievementlist(self, ctx: commands.Context):
        """List all available achievements."""
        by_category = {}
        for achievement in all_achievements():
            by_category.setdefault(achievement.category, []).append(achievement)

        embed = self.embed("🏆 Achievement List", f"{len(all_achievements())} achievements available")
        for category, achievements in by_category.items():
            lines = [f"{a.icon} **{a.name}** ({a.points}) — {a.description}" for a in achievements]
            embed.add_field(name=category, value="\n".join(lines), inline=False)
        await ctx.send(embed=embed)

    @commands.command(aliases=["achleaderboard", "achlb"])
    async def achievementboard(self, ctx: commands.Context):
        """View the achievement points leaderboard."""
        rows = self.db.fetchall(
            """SELECT p.user_id, p.name, COUNT(a.id) AS unlocked_count\n               FROM profile p\n               LEFT JOIN achievements a ON a.user_id = p.user_id\n               GROUP BY p.user_id, p.name\n               ORDER BY unlocked_count DESC, p.level DESC, p.xp DESC\n               LIMIT 10"""
        )
        if not rows:
            await ctx.send("❌ No leaderboard data available yet.")
            return

        lines = []
        for rank, row in enumerate(rows, 1):
            keys = self.db.get_achievement_keys(row["user_id"])
            points = achievement_points(keys)
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            lines.append(f"{medal} **{row['name']}** — {points} points ({len(keys)} unlocked)")

        embed = self.embed("🏆 Achievement Leaderboard", "The least cursed grind ledger.")
        embed.add_field(name="Rankings", value="\n".join(lines), inline=False)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AchievementsCog(bot))
