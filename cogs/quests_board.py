"""Daily and weekly objective board."""
import random
from datetime import datetime, timedelta

import discord
from discord.ext import commands

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character


DAILY_OBJECTIVES = (
    ("Claim a daily reward", "daily", 1, 150, 40),
    ("Complete adventures", "completed", 2, 250, 70),
    ("Win PvP battles", "pvpwins", 1, 300, 90),
    ("Reach a 3-day streak", "streak", 3, 200, 50),
    ("Hold 1,000 gold", "money", 1000, 150, 30),
)

WEEKLY_OBJECTIVES = (
    ("Complete 10 adventures", "completed", 10, 1200, 350),
    ("Win 5 PvP battles", "pvpwins", 5, 1500, 450),
    ("Reach level 10", "level", 10, 1000, 300),
    ("Hold 10,000 gold", "money", 10000, 1000, 250),
    ("Maintain a 7-day streak", "streak", 7, 1800, 600),
)


class QuestsBoardCog(DiscordRPGCog):
    """Rotating objective board for players who like checklists because they hate peace."""

    def cog_load(self):
        self._ensure_tables()

    def _ensure_tables(self):
        self.db.execute(
            """CREATE TABLE IF NOT EXISTS objective_claims (\n                   user_id BIGINT NOT NULL,\n                   objective_key VARCHAR(96) NOT NULL,\n                   claimed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n                   PRIMARY KEY (user_id, objective_key),\n                   CONSTRAINT objective_claims_ibfk_1\n                       FOREIGN KEY (user_id) REFERENCES profile (user_id) ON DELETE CASCADE\n               ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""
        )
        self.db.commit()

    def _objective_key(self, period: str, field: str, target: int) -> str:
        now = datetime.utcnow()
        if period == "daily":
            stamp = now.strftime("%Y%m%d")
        else:
            year, week, _ = now.isocalendar()
            stamp = f"{year}w{week:02d}"
        return f"{period}:{stamp}:{field}:{target}"

    def _progress(self, profile, field: str) -> int:
        if field == "daily":
            return 1 if profile.get("last_date") == datetime.now().strftime('%Y-%m-%d') else 0
        return int(profile.get(field) or 0)

    def _objectives(self, period: str):
        source = DAILY_OBJECTIVES if period == "daily" else WEEKLY_OBJECTIVES
        # Stable-ish rotation based on date/week without storing another cursed table.
        seed = datetime.utcnow().strftime("%Y%m%d" if period == "daily" else "%Y%W")
        rng = random.Random(seed)
        objectives = list(source)
        rng.shuffle(objectives)
        return objectives[:3]

    def _claimed_keys(self, user_id: int):
        rows = self.db.fetchall("SELECT objective_key FROM objective_claims WHERE user_id = ?", (user_id,))
        return {row["objective_key"] for row in rows}

    @commands.command(aliases=["objectives", "tasks"])
    @has_character()
    async def quests(self, ctx: commands.Context):
        """Show today's and this week's objective board."""
        profile = self.db.get_character(ctx.author.id)
        claimed = self._claimed_keys(ctx.author.id)
        embed = self.embed("📋 Objective Board", "Finish objectives, claim rewards, pretend this was your idea.")

        for period in ("daily", "weekly"):
            lines = []
            for description, field, target, xp, gold in self._objectives(period):
                key = self._objective_key(period, field, target)
                progress = min(self._progress(profile, field), target)
                done = progress >= target
                claimed_mark = "claimed" if key in claimed else "ready" if done else f"{progress}/{target}"
                lines.append(f"**{description}** — {claimed_mark} • {xp} XP / {gold} gold")
            embed.add_field(name=period.title(), value="\n".join(lines), inline=False)

        embed.set_footer(text="Use !claimquests to collect completed objective rewards.")
        await ctx.send(embed=embed)

    @commands.command(aliases=["claimobjectives", "claimtasks"])
    @has_character()
    async def claimquests(self, ctx: commands.Context):
        """Claim completed objective rewards."""
        profile = self.db.get_character(ctx.author.id)
        claimed = self._claimed_keys(ctx.author.id)
        rewards = []
        total_xp = 0
        total_gold = 0

        for period in ("daily", "weekly"):
            for description, field, target, xp, gold in self._objectives(period):
                key = self._objective_key(period, field, target)
                if key in claimed or self._progress(profile, field) < target:
                    continue
                self.db.execute(
                    "INSERT IGNORE INTO objective_claims (user_id, objective_key) VALUES (?, ?)",
                    (ctx.author.id, key),
                )
                total_xp += xp
                total_gold += gold
                rewards.append(description)

        if not rewards:
            await ctx.send("❌ No completed objectives to claim.")
            return

        new_xp = int(profile.get("xp") or 0) + total_xp
        new_level = min(999, 1 + int((new_xp / 100) ** 0.5))
        self.db.update_character(
            ctx.author.id,
            xp=new_xp,
            level=new_level,
            money=int(profile.get("money") or 0) + total_gold,
        )
        self.db.commit()

        embed = self.success_embed(
            f"Claimed **{len(rewards)}** objectives for **{total_xp} XP** and **{total_gold} gold**."
        )
        embed.add_field(name="Completed", value="\n".join(f"• {r}" for r in rewards), inline=False)
        if new_level > int(profile.get("level") or 1):
            embed.add_field(name="Level Up", value=f"Now level {new_level}.", inline=True)
        await ctx.send(embed=embed)

        achievements_cog = ctx.bot.get_cog('AchievementsCog')
        if achievements_cog:
            await achievements_cog.check_achievements(ctx.author.id, ctx.channel)


async def setup(bot):
    await bot.add_cog(QuestsBoardCog(bot))
