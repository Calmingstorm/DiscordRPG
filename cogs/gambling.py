"""Gambling and casino games"""
import discord
from discord.ext import commands
import random
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character

# 5 minute cooldown for all gambling commands
GAMBLING_COOLDOWN = 300


class GamblingCog(DiscordRPGCog):
    """Casino games and gambling"""

    async def update_quest_progress(self, user_id: int, objective_type: str, amount: int = 1):
        """Helper to update personal quest progress"""
        try:
            quest_cog = self.bot.get_cog('PersonalQuestsCog')
            if quest_cog:
                await quest_cog.check_and_update_progress(user_id, objective_type, amount)
        except Exception as e:
            pass  # Silently ignore quest tracking errors

    @commands.command(aliases=["cf", "flip"])
    @has_character()
    @commands.cooldown(1, GAMBLING_COOLDOWN, commands.BucketType.user)
    async def coinflip(self, ctx: commands.Context, amount: int, choice: str):
        """Flip a coin (heads/tails or h/t) - 5 min cooldown"""
        char_data = self.db.get_character(ctx.author.id)

        if amount <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Bet amount must be positive!")
            return

        if amount > char_data['money']:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ You only have {char_data['money']:,} gold!")
            return

        # Parse choice
        choice = choice.lower()
        if choice in ['h', 'heads']:
            player_choice = 'heads'
        elif choice in ['t', 'tails']:
            player_choice = 'tails'
        else:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Choose 'heads'/'h' or 'tails'/'t'!")
            return

        # Pure 50/50
        result = random.choice(['heads', 'tails'])
        won = result == player_choice

        # Update money
        if won:
            winnings = amount
            new_money = char_data['money'] + winnings
            result_text = f"**You win {winnings:,} gold!**"
            color = discord.Color.green()
            await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
        else:
            new_money = char_data['money'] - amount
            result_text = f"**You lose {amount:,} gold!**"
            color = discord.Color.red()
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)

        self.db.update_character(ctx.author.id, money=new_money)

        # Log transaction
        self.db.log_transaction(
            ctx.author.id if not won else None,
            None if not won else ctx.author.id,
            amount,
            "coinflip",
            {"choice": player_choice, "result": result, "won": won}
        )

        embed = discord.Embed(
            title="🪙 Coinflip",
            description=f"The coin lands on **{result}**!\n{result_text}",
            color=color
        )

        embed.add_field(name="Your Choice", value=player_choice.title(), inline=True)
        embed.add_field(name="Result", value=result.title(), inline=True)
        embed.add_field(name="New Balance", value=f"{new_money:,} gold", inline=True)

        await ctx.send(embed=embed)

    @commands.command(aliases=["slot", "spin"])
    @has_character()
    @commands.cooldown(1, GAMBLING_COOLDOWN, commands.BucketType.user)
    async def slots(self, ctx: commands.Context, amount: int):
        """Play the slot machine - 5 min cooldown"""
        char_data = self.db.get_character(ctx.author.id)

        if amount <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Bet amount must be positive!")
            return

        if amount > char_data['money']:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ You only have {char_data['money']:,} gold!")
            return

        # Fixed slot weights - no luck influence
        symbols = ["🍒", "🍋", "🍊", "🔔", "⭐", "💎"]
        weights = [30, 25, 20, 15, 8, 2]

        # Spin reels
        reel1 = random.choices(symbols, weights=weights)[0]
        reel2 = random.choices(symbols, weights=weights)[0]
        reel3 = random.choices(symbols, weights=weights)[0]

        result = [reel1, reel2, reel3]

        # Calculate winnings
        multiplier = 0

        if reel1 == reel2 == reel3:  # Three of a kind
            symbol_multipliers = {
                "🍒": 2,
                "🍋": 3,
                "🍊": 4,
                "🔔": 5,
                "⭐": 10,
                "💎": 20
            }
            multiplier = symbol_multipliers[reel1]
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:  # Two of a kind
            multiplier = 1
        else:  # No match
            multiplier = 0

        # Apply winnings/losses
        if multiplier > 0:
            winnings = amount * multiplier
            new_money = char_data['money'] + winnings - amount
            result_text = f"**You win {winnings:,} gold!** ({multiplier}x multiplier)"
            color = discord.Color.green()
            net_gain = winnings - amount
            if net_gain > 0:
                await self.update_quest_progress(ctx.author.id, 'gold_earn', net_gain)
        else:
            new_money = char_data['money'] - amount
            result_text = f"**You lose {amount:,} gold!**"
            color = discord.Color.red()
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)

        self.db.update_character(ctx.author.id, money=new_money)

        # Create spinning animation
        embed = self.embed("🎰 Slot Machine", "Spinning...")
        msg = await ctx.send(embed=embed)

        await asyncio.sleep(1)

        # Show result
        embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{' | '.join(result)}\n\n{result_text}",
            color=color
        )

        embed.add_field(name="Bet", value=f"{amount:,} gold", inline=True)
        embed.add_field(name="Multiplier", value=f"{multiplier}x", inline=True)
        embed.add_field(name="Balance", value=f"{new_money:,} gold", inline=True)

        # Show payout table on loss
        if multiplier == 0:
            embed.add_field(
                name="💰 Payouts",
                value="🍒🍒🍒 = 2x\n🍋🍋🍋 = 3x\n🍊🍊🍊 = 4x\n🔔🔔🔔 = 5x\n⭐⭐⭐ = 10x\n💎💎💎 = 20x",
                inline=False
            )

        await msg.edit(embed=embed)

    @commands.command(aliases=["bj"])
    @has_character()
    @commands.cooldown(1, GAMBLING_COOLDOWN, commands.BucketType.user)
    async def blackjack(self, ctx: commands.Context, amount: int):
        """Play blackjack against the house - 5 min cooldown"""
        char_data = self.db.get_character(ctx.author.id)

        if amount <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Bet amount must be positive!")
            return

        if amount > char_data['money']:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ You only have {char_data['money']:,} gold!")
            return

        # Create deck
        deck = []
        suits = ["♠", "♥", "♦", "♣"]
        values = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]

        for suit in suits:
            for value in values:
                deck.append(f"{value}{suit}")

        random.shuffle(deck)

        # Deal initial cards
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        def card_value(card):
            value = card[:-1]
            if value in ["J", "Q", "K"]:
                return 10
            elif value == "A":
                return 11
            else:
                return int(value)

        def hand_value(hand):
            total = sum(card_value(card) for card in hand)
            aces = sum(1 for card in hand if card[:-1] == "A")

            while total > 21 and aces > 0:
                total -= 10
                aces -= 1

            return total

        def format_hand(hand, hide_dealer=False):
            if hide_dealer:
                return f"{hand[0]} ??  (? + ?)"
            else:
                cards = " ".join(hand)
                value = hand_value(hand)
                return f"{cards}  ({value})"

        # Check for blackjacks
        player_bj = hand_value(player_hand) == 21
        dealer_bj = hand_value(dealer_hand) == 21

        if player_bj and dealer_bj:
            embed = self.embed("🃏 Blackjack - Push", "Both have blackjack!")
            embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
            embed.add_field(name="Dealer Hand", value=format_hand(dealer_hand), inline=False)
            await ctx.send(embed=embed)
            return
        elif player_bj:
            winnings = int(amount * 1.5)
            new_money = char_data['money'] + winnings
            self.db.update_character(ctx.author.id, money=new_money)
            await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)

            embed = self.embed("🃏 Blackjack!", f"You win {winnings:,} gold!")
            embed.color = discord.Color.gold()
            embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
            embed.add_field(name="Dealer Hand", value=format_hand(dealer_hand), inline=False)
            await ctx.send(embed=embed)
            return
        elif dealer_bj:
            new_money = char_data['money'] - amount
            self.db.update_character(ctx.author.id, money=new_money)
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)

            embed = self.embed("🃏 Dealer Blackjack", f"You lose {amount:,} gold!")
            embed.color = discord.Color.red()
            embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
            embed.add_field(name="Dealer Hand", value=format_hand(dealer_hand), inline=False)
            await ctx.send(embed=embed)
            return

        # Player turn
        while hand_value(player_hand) < 21:
            embed = self.embed("🃏 Blackjack", "Your turn!")
            embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
            embed.add_field(name="Dealer Hand", value=format_hand(dealer_hand, hide_dealer=True), inline=False)
            embed.add_field(name="Actions", value="🇭 Hit | 🇸 Stand", inline=False)

            msg = await ctx.send(embed=embed)
            await msg.add_reaction("🇭")
            await msg.add_reaction("🇸")

            def check(reaction, user):
                return (user == ctx.author and
                       str(reaction.emoji) in ["🇭", "🇸"] and
                       reaction.message.id == msg.id)

            try:
                reaction, user = await ctx.bot.wait_for('reaction_add', timeout=30.0, check=check)
                action = str(reaction.emoji)
            except asyncio.TimeoutError:
                action = "🇸"

            await msg.delete()

            if action == "🇭":
                player_hand.append(deck.pop())
            else:
                break

        player_value = hand_value(player_hand)

        # Check for bust
        if player_value > 21:
            new_money = char_data['money'] - amount
            self.db.update_character(ctx.author.id, money=new_money)
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)

            embed = self.embed("🃏 Bust!", f"You lose {amount:,} gold!")
            embed.color = discord.Color.red()
            embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
            await ctx.send(embed=embed)
            return

        # Dealer turn
        while hand_value(dealer_hand) < 17:
            dealer_hand.append(deck.pop())

        dealer_value = hand_value(dealer_hand)

        # Determine winner
        if dealer_value > 21:
            winnings = amount
            new_money = char_data['money'] + winnings
            result = f"Dealer busts! You win {winnings:,} gold!"
            color = discord.Color.green()
            await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
        elif player_value > dealer_value:
            winnings = amount
            new_money = char_data['money'] + winnings
            result = f"You win {winnings:,} gold!"
            color = discord.Color.green()
            await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
        elif dealer_value > player_value:
            new_money = char_data['money'] - amount
            result = f"Dealer wins! You lose {amount:,} gold!"
            color = discord.Color.red()
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)
        else:
            new_money = char_data['money']
            result = "Push! No money exchanged."
            color = discord.Color.blue()

        self.db.update_character(ctx.author.id, money=new_money)

        embed = discord.Embed(title="🃏 Blackjack Results", description=result, color=color)
        embed.add_field(name="Your Hand", value=format_hand(player_hand), inline=False)
        embed.add_field(name="Dealer Hand", value=format_hand(dealer_hand), inline=False)
        embed.add_field(name="New Balance", value=f"{new_money:,} gold", inline=True)

        await ctx.send(embed=embed)

    @commands.command(aliases=["dice", "roll"])
    @has_character()
    @commands.cooldown(1, GAMBLING_COOLDOWN, commands.BucketType.user)
    async def diceroll(self, ctx: commands.Context, amount: int):
        """Roll dice - win if you roll higher than the house - 5 min cooldown"""
        char_data = self.db.get_character(ctx.author.id)

        if amount <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Bet amount must be positive!")
            return

        if amount > char_data['money']:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ You only have {char_data['money']:,} gold!")
            return

        # Pure dice rolls - no luck influence
        player_roll = random.randint(1, 100)
        house_roll = random.randint(1, 100)

        # Determine result
        if player_roll > house_roll:
            difference = player_roll - house_roll
            if difference >= 50:
                multiplier = 2.0
            elif difference >= 30:
                multiplier = 1.5
            elif difference >= 10:
                multiplier = 1.2
            else:
                multiplier = 1.0

            winnings = int(amount * multiplier)
            new_money = char_data['money'] + winnings
            result = f"**You win {winnings:,} gold!** ({multiplier}x)"
            color = discord.Color.green()
            await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
        elif house_roll > player_roll:
            new_money = char_data['money'] - amount
            result = f"**You lose {amount:,} gold!**"
            color = discord.Color.red()
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)
        else:
            new_money = char_data['money']
            result = "**It's a tie! No money lost.**"
            color = discord.Color.blue()

        self.db.update_character(ctx.author.id, money=new_money)

        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=result,
            color=color
        )

        embed.add_field(name="Your Roll", value=f"🎲 {player_roll}", inline=True)
        embed.add_field(name="House Roll", value=f"🏠 {house_roll}", inline=True)
        embed.add_field(name="Balance", value=f"{new_money:,} gold", inline=True)

        if player_roll <= house_roll:
            embed.add_field(
                name="💡 Tip",
                value="Win by 10+ for 1.2x\nWin by 30+ for 1.5x\nWin by 50+ for 2x",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command()
    @has_character()
    @commands.cooldown(1, GAMBLING_COOLDOWN, commands.BucketType.user)
    async def gamble(self, ctx: commands.Context, amount: int):
        """Simple high-risk gambling - 40% chance to double your money - 5 min cooldown"""
        char_data = self.db.get_character(ctx.author.id)

        if amount <= 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Bet amount must be positive!")
            return

        if amount > char_data['money']:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ You only have {char_data['money']:,} gold!")
            return

        # Fixed 40% chance - no luck influence
        final_chance = 40.0

        won = random.randint(1, 100) <= final_chance

        if won:
            winnings = amount * 2
            new_money = char_data['money'] + winnings
            result_text = f"🎉 **JACKPOT!** You win {winnings:,} gold!"
            color = discord.Color.gold()

            if amount >= 5000:
                xp_bonus = random.randint(10, 25)
                self.db.update_character(
                    ctx.author.id,
                    money=new_money,
                    xp=char_data['xp'] + xp_bonus
                )
                result_text += f"\n✨ Bonus: +{xp_bonus} XP!"
                await self.update_quest_progress(ctx.author.id, 'xp_gain', xp_bonus)
                await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
            else:
                self.db.update_character(ctx.author.id, money=new_money)
                await self.update_quest_progress(ctx.author.id, 'gold_earn', winnings)
        else:
            new_money = char_data['money'] - amount
            result_text = f"💸 **You lose {amount:,} gold!**"
            color = discord.Color.red()
            self.db.update_character(ctx.author.id, money=new_money)
            await self.update_quest_progress(ctx.author.id, 'gold_spend', amount)

        # Log transaction
        self.db.log_transaction(
            ctx.author.id if not won else None,
            None if not won else ctx.author.id,
            amount,
            "gambling",
            {"won": won, "chance": final_chance}
        )

        embed = discord.Embed(
            title="🎰 High Stakes Gambling",
            description=result_text,
            color=color
        )

        embed.add_field(name="💰 Bet", value=f"{amount:,} gold", inline=True)
        embed.add_field(name="🎯 Win Chance", value=f"{final_chance:.0f}%", inline=True)
        embed.add_field(name="💳 Balance", value=f"{new_money:,} gold", inline=True)

        if not won:
            embed.add_field(
                name="💡 Tip",
                value="Try other games: `!coinflip`, `!slots`, `!blackjack`, `!diceroll`",
                inline=False
            )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))
