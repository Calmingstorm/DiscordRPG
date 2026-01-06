"""Economy system - market, trading, shops"""
import discord
from discord.ext import commands
import math
import asyncio
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemGenerator, ItemRarity

class EconomyCog(DiscordRPGCog):
    """Economy and trading commands"""
    
    async def get_market_embed(self, page: int = 1):
        """Generate market embed for given page"""
        items_per_page = 10
        offset = (page - 1) * items_per_page
        items = self.db.get_market_items(100, offset)  # Get more items to calculate total pages
        
        if not items:
            embed = self.embed("🏪 Global Market", "No items for sale!")
            return embed
            
        # Calculate total pages
        total_items = len(self.db.get_market_items(1000, 0))  # Get total count
        total_pages = math.ceil(total_items / items_per_page)
        page = max(1, min(page, total_pages))
        
        # Get items for this page
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx] if start_idx < len(items) else []
        
        embed = self.embed(
            f"🏪 Global Market (Page {page}/{total_pages})",
            "Use `!buy <item_id>` to purchase items"
        )
        
        for item in page_items:
            stats = self.format_item_stats(item)
            try:
                owner = self.bot.get_user(item['owner'])
                owner_name = owner.display_name if owner else f"User{item['owner']}"
            except:
                owner_name = f"User{item['owner']}"
            
            # Add slot type for armor
            slot_type = item['slot_type'] if item['slot_type'] else 'weapon'
            slot_info = f" ({slot_type.title()})" if item['slot_type'] else ""
            
            embed.add_field(
                name=f"[{item['item_id']}] {item['name']} - {item['price']:,}💰",
                value=f"`{item['type']}{slot_info}` • {stats} • Seller: {owner_name}",
                inline=False
            )
            
        return embed
    
    def format_item_stats(self, item) -> str:
        """Format item stats including all bonuses"""
        stats = []
        
        # Helper function to safely get values from both dict and sqlite3.Row objects
        def get_val(key, default=0):
            try:
                return item[key] if item[key] is not None else default
            except (KeyError, TypeError):
                return default
        
        # Basic stats
        if get_val('damage', 0) > 0:
            stats.append(f"{item['damage']}⚔️")
        if get_val('armor', 0) > 0:
            stats.append(f"{item['armor']}🛡️")
            
        # Armor bonus stats
        if get_val('health_bonus', 0) > 0:
            stats.append(f"{item['health_bonus']}❤️")
        if get_val('speed_bonus', 0) > 0:
            stats.append(f"{item['speed_bonus']}💨")
        if get_val('luck_bonus', 0.0) > 0:
            stats.append(f"{item['luck_bonus']:.1f}🍀")
        if get_val('crit_bonus', 0.0) > 0:
            stats.append(f"{item['crit_bonus']:.1f}💥")
        if get_val('magic_bonus', 0) > 0:
            stats.append(f"{item['magic_bonus']}✨")
            
        return " ".join(stats) if stats else "0⚔️ 0🛡️"
    
    @commands.command()
    @has_character()
    async def market(self, ctx: commands.Context, page: int = 1):
        """Browse the global marketplace"""
        # Get total count to check if pagination is needed
        all_items = self.db.get_market_items(1000, 0)
        embed = await self.get_market_embed(page)
        
        # Check if pagination is needed
        if len(all_items) > 10:
            items_per_page = 10
            total_pages = math.ceil(len(all_items) / items_per_page)
            
            # Import PaginationView from inventory.py
            from cogs.inventory import PaginationView
            
            # Create pagination view
            view = PaginationView()
            view.set_data(ctx.author.id, page, total_pages, 'market', self)
            
            await ctx.send(embed=embed, view=view)
        else:
            # No pagination needed
            await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def offer(self, ctx: commands.Context, item_id: int, price: int):
        """List an item on the market"""
        if price <= 0:
            await ctx.send("❌ Price must be positive!")
            return
            
        if price > 10000000:  # 10M gold limit
            await ctx.send("❌ Maximum price is 10,000,000 gold!")
            return
            
        # Check item ownership
        item = self.db.get_item_by_id(item_id)
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
            
        if item['equipped']:
            await ctx.send("❌ Cannot sell equipped items! Unequip first.")
            return
            
        # Check if already on market
        existing = self.db.fetchone(
            "SELECT * FROM market WHERE item_id = ?",
            (item_id,)
        )
        if existing:
            await ctx.send("❌ Item is already on the market!")
            return
            
        # Calculate market tax (5%)
        tax = int(price * 0.05)
        char_data = self.db.get_character(ctx.author.id)
        
        if char_data['money'] < tax:
            await ctx.send(f"❌ You need {tax:,} gold to pay the listing fee!")
            return
            
        if not await ctx.confirm(
            f"List **{item['name']}** for **{price:,}** gold?\n"
            f"Listing fee: {tax:,} gold (5%)"
        ):
            await ctx.send("Listing cancelled.")
            return
            
        # List item
        success = self.db.list_item_on_market(item_id, price)
        if success:
            # Deduct listing fee
            self.db.update_character(ctx.author.id, money=char_data['money'] - tax)
            
            # Log transaction
            self.db.log_transaction(
                ctx.author.id, None, tax, "market_fee",
                {"item": item['name'], "price": price}
            )
            
            embed = self.success_embed(
                f"Listed **{item['name']}** on the market for **{price:,}** gold!\n"
                f"Listing fee: {tax:,} gold"
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to list item!")
            
    @commands.command()
    @has_character() 
    async def buy(self, ctx: commands.Context, item_id: int):
        """Buy an item from the market"""
        # Get market item
        market_item = self.db.fetchone(
            """SELECT m.*, i.* FROM market m
               JOIN inventory i ON m.item_id = i.id
               WHERE i.id = ?""",
            (item_id,)
        )
        
        if not market_item:
            await ctx.send("❌ Item not found on market!")
            return
            
        if market_item['owner'] == ctx.author.id:
            await ctx.send("❌ Cannot buy your own item!")
            return
            
        char_data = self.db.get_character(ctx.author.id)
        price = market_item['price']
        
        if char_data['money'] < price:
            await ctx.send(f"❌ You need {price:,} gold but only have {char_data['money']:,}!")
            return
            
        if not await ctx.confirm(
            f"Buy **{market_item['name']}** for **{price:,}** gold?\n"
            f"{self.format_item_stats(market_item)}"
        ):
            await ctx.send("Purchase cancelled.")
            return
            
        # Process purchase
        success = self.db.buy_market_item(item_id, ctx.author.id)
        
        if success:
            embed = self.success_embed(
                f"Purchased **{market_item['name']}** for **{price:,}** gold!"
            )
            slot_type = market_item['slot_type'] if market_item['slot_type'] else 'weapon'
            slot_info = f" ({slot_type.title()})" if market_item['slot_type'] else ""
            embed.add_field(
                name="Item Stats",
                value=f"`{market_item['type']}{slot_info}` • {self.format_item_stats(market_item)}",
                inline=False
            )
            await ctx.send(embed=embed)
            
            # Notify seller
            seller = ctx.bot.get_user(market_item['owner'])
            if seller:
                try:
                    seller_embed = self.embed(
                        "💰 Item Sold!",
                        f"Your **{market_item['name']}** sold for **{price:,}** gold!\n"
                        f"Buyer: {ctx.author.mention}"
                    )
                    await seller.send(embed=seller_embed)
                except discord.Forbidden:
                    pass
        else:
            await ctx.send("❌ Failed to purchase item! It may have been sold already.")
            
    @commands.command()
    @has_character()
    async def withdraw(self, ctx: commands.Context, item_id: int):
        """Remove your item from the market"""
        # Check if item is on market and owned by user
        market_item = self.db.fetchone(
            """SELECT m.*, i.* FROM market m
               JOIN inventory i ON m.item_id = i.id
               WHERE i.id = ? AND i.owner = ?""",
            (item_id, ctx.author.id)
        )
        
        if not market_item:
            await ctx.send("❌ Item not found on market or not owned by you!")
            return
            
        # Remove from market
        self.db.execute("DELETE FROM market WHERE item_id = ?", (item_id,))
        self.db.commit()
        
        embed = self.success_embed(
            f"Removed **{market_item['name']}** from the market."
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def shop(self, ctx: commands.Context):
        """Visit the item shop"""
        embed = self.embed("🏪 Item Shop", "Welcome to the shop!")
        
        # Daily shop items (generated daily)
        import hashlib
        today = ctx.bot.user.created_at.strftime('%Y%m%d')  # Use bot creation date as seed
        seed = int(hashlib.md5(today.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        shop_items = []
        for i in range(3):  # 3 daily items
            rarity_weights = [(ItemRarity.COMMON, 50), (ItemRarity.UNCOMMON, 30), 
                             (ItemRarity.RARE, 15), (ItemRarity.MAGIC, 5)]
            
            rarity = random.choices([r[0] for r in rarity_weights], 
                                   weights=[r[1] for r in rarity_weights])[0]
            
            stat_ranges = {
                ItemRarity.COMMON: (1, 9),
                ItemRarity.UNCOMMON: (10, 19),
                ItemRarity.RARE: (20, 29),
                ItemRarity.MAGIC: (30, 39),
            }
            
            min_stat, max_stat = stat_ranges[rarity]
            item = ItemGenerator.generate_item(0, min_stat, max_stat)
            
            # Price based on stats and rarity
            base_price = (item.damage + item.armor) * 100
            rarity_mult = {
                ItemRarity.COMMON: 1.0,
                ItemRarity.UNCOMMON: 1.5,
                ItemRarity.RARE: 2.5,
                ItemRarity.MAGIC: 4.0
            }
            price = int(base_price * rarity_mult[rarity])
            
            shop_items.append((item, price, i))
            
        # Reset random seed
        random.seed()
        
        for item, price, idx in shop_items:
            # Create a dict-like representation for format_item_stats
            item_dict = {
                'damage': item.damage,
                'armor': item.armor,
                'health_bonus': getattr(item, 'health_bonus', 0),
                'speed_bonus': getattr(item, 'speed_bonus', 0),
                'luck_bonus': getattr(item, 'luck_bonus', 0.0),
                'crit_bonus': getattr(item, 'crit_bonus', 0.0),
                'magic_bonus': getattr(item, 'magic_bonus', 0),
                'slot_type': getattr(item, 'slot_type', None)
            }
            stats = self.format_item_stats(item_dict)
            slot_info = f" ({item_dict['slot_type'].title()})" if item_dict['slot_type'] else ""
            
            embed.add_field(
                name=f"[{idx}] {item.name} - {price:,}💰",
                value=f"`{item.type.value}{slot_info}` • {stats}",
                inline=False
            )
            
        embed.add_field(
            name="💡 How to Buy",
            value="Use `!buyshop <number>` to purchase\nExample: `!buyshop 0`",
            inline=False
        )
        embed.set_footer(text="Shop refreshes daily!")
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def buyshop(self, ctx: commands.Context, item_number: int):
        """Buy an item from the shop"""
        if not 0 <= item_number <= 2:
            await ctx.send("❌ Invalid item number! Use 0, 1, or 2.")
            return
            
        # Regenerate daily shop (same logic as shop command)
        import hashlib
        today = ctx.bot.user.created_at.strftime('%Y%m%d')
        seed = int(hashlib.md5(today.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        shop_items = []
        for i in range(3):
            rarity_weights = [(ItemRarity.COMMON, 50), (ItemRarity.UNCOMMON, 30),
                             (ItemRarity.RARE, 15), (ItemRarity.MAGIC, 5)]
            
            rarity = random.choices([r[0] for r in rarity_weights],
                                   weights=[r[1] for r in rarity_weights])[0]
            
            stat_ranges = {
                ItemRarity.COMMON: (1, 9),
                ItemRarity.UNCOMMON: (10, 19), 
                ItemRarity.RARE: (20, 29),
                ItemRarity.MAGIC: (30, 39),
            }
            
            min_stat, max_stat = stat_ranges[rarity]
            item = ItemGenerator.generate_item(ctx.author.id, min_stat, max_stat)
            
            base_price = (item.damage + item.armor) * 100
            rarity_mult = {
                ItemRarity.COMMON: 1.0,
                ItemRarity.UNCOMMON: 1.5,
                ItemRarity.RARE: 2.5,
                ItemRarity.MAGIC: 4.0
            }
            price = int(base_price * rarity_mult[rarity])
            
            shop_items.append((item, price))
            
        random.seed()
        
        item, price = shop_items[item_number]
        char_data = self.db.get_character(ctx.author.id)
        
        if char_data['money'] < price:
            await ctx.send(f"❌ You need {price:,} gold but only have {char_data['money']:,}!")
            return
            
        if not await ctx.confirm(f"Buy **{item.name}** for **{price:,}** gold?"):
            await ctx.send("Purchase cancelled.")
            return
            
        # Create item and deduct money
        item_id = self.db.create_item(
            ctx.author.id, item.name, item.type.value,
            item.value, item.damage, item.armor, item.hand.value,
            item.health_bonus, item.speed_bonus, item.luck_bonus, 
            item.crit_bonus, item.magic_bonus, item.slot_type
        )
        
        self.db.update_character(ctx.author.id, money=char_data['money'] - price)
        
        # Log transaction
        self.db.log_transaction(
            ctx.author.id, None, price, "shop_purchase",
            {"item": item.name}
        )
        
        embed = self.success_embed(
            f"Purchased **{item.name}** for **{price:,}** gold!"
        )
        
        # Create dict for format_item_stats
        item_dict = {
            'damage': item.damage,
            'armor': item.armor,
            'health_bonus': getattr(item, 'health_bonus', 0),
            'speed_bonus': getattr(item, 'speed_bonus', 0),
            'luck_bonus': getattr(item, 'luck_bonus', 0.0),
            'crit_bonus': getattr(item, 'crit_bonus', 0.0),
            'magic_bonus': getattr(item, 'magic_bonus', 0),
            'slot_type': getattr(item, 'slot_type', None)
        }
        slot_info = f" ({item_dict['slot_type'].title()})" if item_dict['slot_type'] else ""
        
        embed.add_field(
            name="Item Stats",
            value=f"`{item.type.value}{slot_info}` • {self.format_item_stats(item_dict)}",
            inline=False
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def trade(self, ctx: commands.Context, user: discord.User, my_item: int, their_item: int):
        """Propose a direct item trade"""
        if user.bot or user == ctx.author:
            await ctx.send("❌ Cannot trade with bots or yourself!")
            return
            
        # Check if both users have characters
        other_char = self.db.get_character(user.id)
        if not other_char:
            await ctx.send("❌ The other user doesn't have a character!")
            return
            
        # Check item ownership
        my_item_data = self.db.get_item_by_id(my_item)
        their_item_data = self.db.get_item_by_id(their_item)
        
        if not my_item_data or my_item_data['owner'] != ctx.author.id:
            await ctx.send("❌ You don't own the item you're offering!")
            return
            
        if not their_item_data or their_item_data['owner'] != user.id:
            await ctx.send("❌ They don't own the item you're requesting!")
            return
            
        if my_item_data['equipped'] or their_item_data['equipped']:
            await ctx.send("❌ Cannot trade equipped items!")
            return
            
        # Send trade proposal
        embed = self.embed(
            "🤝 Trade Proposal",
            f"{user.mention}, {ctx.author.mention} wants to trade with you!"
        )
        
        embed.add_field(
            name=f"{ctx.author.display_name} offers:",
            value=f"**{my_item_data['name']}**\n{self.format_item_stats(my_item_data)}",
            inline=True
        )
        
        embed.add_field(
            name=f"{user.display_name} gives:",
            value=f"**{their_item_data['name']}**\n{self.format_item_stats(their_item_data)}",
            inline=True
        )
        
        embed.add_field(name="React", value="✅ to accept, ❌ to decline", inline=False)
        
        trade_msg = await ctx.send(embed=embed)
        await trade_msg.add_reaction("✅")
        await trade_msg.add_reaction("❌")
        
        def check(reaction, react_user):
            return (react_user == user and 
                   str(reaction.emoji) in ["✅", "❌"] and 
                   reaction.message.id == trade_msg.id)
        
        try:
            reaction, react_user = await ctx.bot.wait_for('reaction_add', timeout=120.0, check=check)
            if str(reaction.emoji) == "❌":
                await ctx.send(f"{user.mention} declined the trade.")
                return
        except asyncio.TimeoutError:
            await ctx.send("Trade proposal timed out.")
            return
            
        await trade_msg.delete()
        
        # Execute trade
        self.db.execute("UPDATE inventory SET owner = ? WHERE id = ?", (user.id, my_item))
        self.db.execute("UPDATE inventory SET owner = ? WHERE id = ?", (ctx.author.id, their_item))
        self.db.commit()
        
        # Log transactions
        self.db.log_transaction(
            ctx.author.id, user.id, 0, "item_trade",
            {"given": my_item_data['name'], "received": their_item_data['name']}
        )
        
        embed = self.success_embed(
            f"Trade completed!\n"
            f"{ctx.author.mention} traded **{my_item_data['name']}** for **{their_item_data['name']}**"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))