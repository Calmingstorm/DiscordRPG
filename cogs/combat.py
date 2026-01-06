"""Combat system - PvP battles, tournaments, raids"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.character import Character, CharacterClass, Race

class CombatCog(DiscordRPGCog):
    """Combat and battle commands"""
    
    def __init__(self, bot):
        super().__init__(bot)
    
    @commands.command(aliases=["fight", "attack"])
    @has_character()
    @commands.cooldown(1, 300, commands.BucketType.user)  # 5 minute cooldown
    async def battle(self, ctx: commands.Context, opponent: discord.User, bet: int = 0):
        """Challenge another player to battle with optional gold wager"""
        if opponent.bot or opponent == ctx.author:
            await ctx.send("❌ Cannot battle bots or yourself!")
            return
            
        # Check if opponent has character
        opponent_data = self.db.get_character(opponent.id)
        if not opponent_data:
            await ctx.send("❌ Your opponent doesn't have a character!")
            return
            
        attacker_data = self.db.get_character(ctx.author.id)
        
        # Check betting
        if bet > 0:
            if bet > attacker_data['money'] or bet > opponent_data['money']:
                await ctx.send("❌ One of you doesn't have enough money for this bet!")
                return
                
        # Send challenge
        embed = self.embed(
            "⚔️ Battle Challenge!",
            f"{opponent.mention}, {ctx.author.mention} challenges you to battle!"
        )
        if bet > 0:
            embed.add_field(name="💰 Bet", value=f"{bet:,} gold", inline=True)
        embed.add_field(name="React", value="✅ to accept, ❌ to decline", inline=False)
        
        challenge_msg = await ctx.send(embed=embed)
        await challenge_msg.add_reaction("✅")
        await challenge_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == opponent and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == challenge_msg.id)
        
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == "❌":
                await ctx.send(f"{opponent.mention} declined the battle challenge.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Battle challenge timed out.")
            return
            
        await challenge_msg.delete()
        
        # Calculate battle stats
        attacker_stats = self.calculate_battle_power(ctx.author.id)
        defender_stats = self.calculate_battle_power(opponent.id)
        
        # Battle simulation
        winner, battle_log = self.simulate_battle(
            (ctx.author, attacker_stats),
            (opponent, defender_stats)
        )
        
        # Apply results
        if bet > 0:
            if winner == ctx.author:
                self.db.update_character(ctx.author.id, money=attacker_data['money'] + bet)
                self.db.update_character(opponent.id, money=opponent_data['money'] - bet)
            else:
                self.db.update_character(ctx.author.id, money=attacker_data['money'] - bet) 
                self.db.update_character(opponent.id, money=opponent_data['money'] + bet)
                
        # Update PvP stats
        if winner == ctx.author:
            self.db.update_character(ctx.author.id, pvpwins=attacker_data['pvpwins'] + 1)
            self.db.update_character(opponent.id, pvplosses=opponent_data['pvplosses'] + 1)
        else:
            self.db.update_character(ctx.author.id, pvplosses=attacker_data['pvplosses'] + 1)
            self.db.update_character(opponent.id, pvpwins=opponent_data['pvpwins'] + 1)
            
        # Log battle
        self.db.execute(
            """INSERT INTO battle_logs (attacker, defender, winner, battle_type, money_stolen) 
               VALUES (?, ?, ?, ?, ?)""",
            (ctx.author.id, opponent.id, winner.id, "pvp", bet)
        )
        self.db.commit()
        
        # Send results
        embed = self.embed(
            f"⚔️ Battle Results",
            f"**{winner.display_name}** wins the battle!"
        )
        
        embed.add_field(
            name="💪 Fighter Stats",
            value=f"{ctx.author.mention}: {attacker_stats} power\n{opponent.mention}: {defender_stats} power",
            inline=False
        )
        
        if bet > 0:
            embed.add_field(
                name="💰 Winnings",
                value=f"**{winner.display_name}** wins {bet:,} gold!",
                inline=True
            )
            
        embed.add_field(
            name="📊 Battle Log",
            value=battle_log,
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    # @commands.command()  # Disabled for now - can re-enable later
    @has_character()
    @commands.cooldown(1, 600, commands.BucketType.user)  # 10 minute cooldown
    async def activebattle_disabled(self, ctx: commands.Context, opponent: discord.User):
        """Interactive turn-based battle"""
        if opponent.bot or opponent == ctx.author:
            await ctx.send("❌ Cannot battle bots or yourself!")
            return
            
        opponent_data = self.db.get_character(opponent.id)
        if not opponent_data:
            await ctx.send("❌ Your opponent doesn't have a character!")
            return
            
        # Challenge acceptance (same as regular battle)
        embed = self.embed(
            "⚔️ Active Battle Challenge!",
            f"{opponent.mention}, {ctx.author.mention} challenges you to an interactive battle!"
        )
        embed.add_field(name="React", value="✅ to accept, ❌ to decline", inline=False)
        
        challenge_msg = await ctx.send(embed=embed)
        await challenge_msg.add_reaction("✅")
        await challenge_msg.add_reaction("❌")
        
        def check(reaction, user):
            return (user == opponent and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == challenge_msg.id)
        
        try:
            reaction, user = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == "❌":
                await ctx.send(f"{opponent.mention} declined the battle.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Battle challenge timed out.")
            return
            
        await challenge_msg.delete()
        
        # Initialize battle
        attacker_power = self.calculate_battle_power(ctx.author.id)
        defender_power = self.calculate_battle_power(opponent.id)
        
        attacker_hp = 100
        defender_hp = 100
        turn = 0
        battle_log = []
        
        while attacker_hp > 0 and defender_hp > 0:
            current_player = ctx.author if turn % 2 == 0 else opponent
            target = opponent if current_player == ctx.author else ctx.author
            current_hp = attacker_hp if current_player == ctx.author else defender_hp
            target_hp = defender_hp if current_player == ctx.author else attacker_hp
            
            # Show battle status
            embed = self.embed(
                f"⚔️ Active Battle - Turn {turn + 1}",
                f"{current_player.mention}'s turn!"
            )
            
            embed.add_field(
                name="💪 HP Status",
                value=f"{ctx.author.mention}: {attacker_hp}/100 HP\n{opponent.mention}: {defender_hp}/100 HP",
                inline=False
            )
            
            embed.add_field(
                name="🎮 Actions",
                value="⚔️ Attack\n🛡️ Defend\n❤️ Heal",
                inline=False
            )
            
            action_msg = await ctx.send(embed=embed)
            await action_msg.add_reaction("⚔️")
            await action_msg.add_reaction("🛡️")
            await action_msg.add_reaction("❤️")
            
            def action_check(reaction, user):
                return (user == current_player and 
                       str(reaction.emoji) in ["⚔️", "🛡️", "❤️"] and 
                       reaction.message.id == action_msg.id)
            
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30.0, check=action_check)
                action = str(reaction.emoji)
            except asyncio.TimeoutError:
                action = "⚔️"  # Default to attack
                
            await action_msg.delete()
            
            # Process action
            current_power = attacker_power if current_player == ctx.author else defender_power
            
            if action == "⚔️":  # Attack
                damage = random.randint(current_power // 2, current_power)
                if current_player == ctx.author:
                    defender_hp -= damage
                    defender_hp = max(0, defender_hp)
                else:
                    attacker_hp -= damage  
                    attacker_hp = max(0, attacker_hp)
                battle_log.append(f"{current_player.display_name} attacks for {damage} damage!")
                
            elif action == "🛡️":  # Defend
                heal = random.randint(5, 15)
                if current_player == ctx.author:
                    attacker_hp = min(100, attacker_hp + heal)
                else:
                    defender_hp = min(100, defender_hp + heal)
                battle_log.append(f"{current_player.display_name} defends and heals {heal} HP!")
                
            elif action == "❤️":  # Heal
                heal = random.randint(15, 25)
                if current_player == ctx.author:
                    attacker_hp = min(100, attacker_hp + heal)
                else:
                    defender_hp = min(100, defender_hp + heal)
                battle_log.append(f"{current_player.display_name} heals for {heal} HP!")
                
            turn += 1
            
            # Show action result
            result_embed = self.embed(
                "⚡ Action Result",
                battle_log[-1]
            )
            result_embed.add_field(
                name="💪 HP Status",
                value=f"{ctx.author.mention}: {attacker_hp}/100 HP\n{opponent.mention}: {defender_hp}/100 HP",
                inline=False
            )
            await ctx.send(embed=result_embed)
            
            await asyncio.sleep(2)
            
        # Battle ended
        winner = ctx.author if attacker_hp > 0 else opponent
        loser = opponent if winner == ctx.author else ctx.author
        
        # Update stats
        winner_data = self.db.get_character(winner.id)
        loser_data = self.db.get_character(loser.id)
        
        self.db.update_character(winner.id, pvpwins=winner_data['pvpwins'] + 1)
        self.db.update_character(loser.id, pvplosses=loser_data['pvplosses'] + 1)
        
        # Final results
        embed = self.embed(
            "🏆 Battle Complete!",
            f"**{winner.display_name}** wins the active battle!"
        )
        
        embed.add_field(
            name="📊 Battle Summary",
            value=f"Turns: {turn}\nFinal HP: {attacker_hp if winner == ctx.author else defender_hp}/100",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def tournament(self, ctx: commands.Context, prize: int = 1000):
        """Start a tournament (minimum 4 players)"""
        char_data = self.db.get_character(ctx.author.id)
        
        if prize > char_data['money']:
            await ctx.send("❌ You don't have enough money to host this tournament!")
            return
            
        if prize < 100:
            await ctx.send("❌ Minimum prize is 100 gold!")
            return
            
        # Create tournament signup
        embed = self.embed(
            "🏆 Tournament Starting!",
            f"**Prize Pool: {prize:,} gold**\n\nHosted by {ctx.author.mention}"
        )
        embed.add_field(
            name="📋 How to Join",
            value="React with 🏆 to join!\nMinimum 4 players needed.\nSignup closes in 2 minutes.",
            inline=False
        )
        
        signup_msg = await ctx.send(embed=embed)
        await signup_msg.add_reaction("🏆")
        
        # Wait for signups
        await asyncio.sleep(120)  # 2 minutes
        
        # Get participants
        signup_msg = await ctx.channel.fetch_message(signup_msg.id)
        participants = []
        
        for reaction in signup_msg.reactions:
            if str(reaction.emoji) == "🏆":
                async for user in reaction.users():
                    if not user.bot and self.db.get_character(user.id):
                        participants.append(user)
                        
        if len(participants) < 4:
            await ctx.send("❌ Not enough participants! Need at least 4 players.")
            return
            
        # Deduct prize from host
        self.db.update_character(ctx.author.id, money=char_data['money'] - prize)
        
        # Tournament bracket
        random.shuffle(participants)
        round_num = 1
        
        await ctx.send(f"🏆 Tournament begins with {len(participants)} participants!")
        
        while len(participants) > 1:
            await ctx.send(f"\n**🥊 ROUND {round_num}**")
            next_round = []
            
            for i in range(0, len(participants), 2):
                if i + 1 < len(participants):
                    p1, p2 = participants[i], participants[i + 1]
                    
                    # Quick battle
                    p1_power = self.calculate_battle_power(p1.id)
                    p2_power = self.calculate_battle_power(p2.id)
                    
                    winner, _ = self.simulate_battle((p1, p1_power), (p2, p2_power))
                    next_round.append(winner)
                    
                    await ctx.send(f"⚔️ {p1.mention} vs {p2.mention} → **{winner.mention}** wins!")
                    await asyncio.sleep(2)
                else:
                    # Bye
                    next_round.append(participants[i])
                    await ctx.send(f"🏃 {participants[i].mention} advances (bye)")
                    
            participants = next_round
            round_num += 1
            
        # Tournament winner
        champion = participants[0]
        champion_data = self.db.get_character(champion.id)
        
        # Award prize
        self.db.update_character(champion.id, money=champion_data['money'] + prize)
        
        embed = self.embed(
            "🏆 TOURNAMENT CHAMPION!",
            f"**{champion.mention}** wins the tournament!"
        )
        embed.add_field(name="💰 Prize", value=f"{prize:,} gold", inline=True)
        embed.add_field(name="🎖️ Glory", value="Tournament Victor!", inline=True)
        
        await ctx.send(embed=embed)
        
    def calculate_battle_power(self, user_id: int) -> int:
        """Calculate total battle power for a user"""
        char_data = self.db.get_character(user_id)
        items = self.db.get_equipped_items(user_id)
        
        # Base stats from character
        base_power = char_data['level'] * 5
        
        # Equipment bonuses (including new armor stats)
        equipment_power = sum(item['damage'] + item['armor'] for item in items)
        
        # Add armor bonuses to combat power
        health_bonus = sum(item.get('health_bonus', 0) for item in items)
        speed_bonus = sum(item.get('speed_bonus', 0) for item in items) 
        luck_bonus = sum(item.get('luck_bonus', 0.0) for item in items)
        crit_bonus = sum(item.get('crit_bonus', 0.0) for item in items)
        magic_bonus = sum(item.get('magic_bonus', 0) for item in items)
        
        # Add armor bonuses to total power
        equipment_power += health_bonus + speed_bonus + int(luck_bonus * 100) + int(crit_bonus * 100) + magic_bonus
        
        # Class bonuses (simplified)
        class_bonus = char_data['level'] * 2
        
        # Luck factor (with divine blessings)
        luck_modifier = char_data['luck']
        
        # Apply divine blessing bonuses
        from cogs.religion import ReligionCog
        religion_cog = self.bot.get_cog('ReligionCog')
        battle_multiplier = 1.0
        if religion_cog:
            blessing_bonuses = religion_cog.get_active_blessings(user_id)
            luck_modifier += blessing_bonuses.get('luck', 0)  # Add luck blessing
            battle_multiplier = blessing_bonuses.get('battle_mult', 1.0)  # Apply valor blessing
        
        total = int((base_power + equipment_power + class_bonus) * luck_modifier * battle_multiplier)
        return max(1, total)
        
    def simulate_battle(self, fighter1: tuple, fighter2: tuple) -> tuple:
        """Simulate a quick battle between two fighters"""
        (user1, power1), (user2, power2) = fighter1, fighter2
        
        # Add randomness
        roll1 = power1 * random.uniform(0.8, 1.2)
        roll2 = power2 * random.uniform(0.8, 1.2)
        
        # Critical hit chance
        if random.random() < 0.1:  # 10% crit
            roll1 *= 1.5
        if random.random() < 0.1:
            roll2 *= 1.5
            
        winner = user1 if roll1 > roll2 else user2
        
        battle_log = f"⚔️ {user1.display_name} ({int(roll1)}) vs {user2.display_name} ({int(roll2)})"
        
        return winner, battle_log
    
    @commands.command()
    async def battlestatus(self, ctx: commands.Context):
        """Check current battle system status"""
        embed = self.embed(
            "⚔️ Battle System Status",
            "Auto battles are handled by the AutoPlay system!"
        )
        
        embed.add_field(
            name="🤖 Auto Battle Info",
            value="Auto battles run through `!autoplay status`\nStay **online** (green status) to participate!",
            inline=False
        )
        
        embed.add_field(
            name="👤 Manual Battles Available",
            value="• `!battle @user` - Challenge specific players\n• `!battle @user 1000` - Battle with gold wager\n• `!tournament [prize]` - Multi-player tournaments",
            inline=False
        )
        
        embed.add_field(
            name="📊 Check Auto System",
            value="Use `!autoplay status` to see auto battle system status",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def battles(self, ctx: commands.Context):
        """Information about the battle system"""
        embed = self.embed(
            "⚔️ Battle System Guide",
            "Multiple battle types are available in DiscordRPG!"
        )
        
        embed.add_field(
            name="🤖 Auto Battles",
            value="• **1v1:** Quick duels\n• **3v3:** Team battles\n• **5v5:** Epic army clashes\n• **10v10:** Massive battlefields\n• Automatic selection of online players",
            inline=False
        )
        
        embed.add_field(
            name="👤 Manual Battles", 
            value="• `!battle @user` - Challenge specific players\n• `!battle @user 5000` - Battle with gold wager\n• `!tournament [prize]` - Multi-player tournaments",
            inline=False
        )
        
        embed.add_field(
            name="🏰 Raids",
            value="• Large group PvE battles\n• Fight powerful bosses together\n• Automatic every ~35 minutes\n• Use `!raids` for more info",
            inline=False
        )
        
        embed.add_field(
            name="📊 Battle Power",
            value="Your battle power comes from:\n• Character level and stats\n• Equipped weapons and armor\n• Class bonuses and abilities\n• Race bonuses and luck",
            inline=False
        )
        
        embed.add_field(
            name="💰 Battle Betting",
            value="• Add gold amount to any battle: `!battle @user 5000`\n• Both players must have enough gold\n• Winner takes the full pot (2x bet amount)\n• Loser loses their wager\n• Example: `!battle @user 1000` = winner gets 2000 gold",
            inline=False
        )
        
        embed.add_field(
            name="🎁 Battle Rewards",
            value="• XP and gold for all participants\n• Winners get bonus rewards\n• PvP win/loss stats tracking\n• Larger battles = better rewards",
            inline=False
        )
        
        embed.set_footer(text="Use !battlestatus to see current system status")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CombatCog(bot))