"""Inventory and equipment management"""
import discord
from discord.ext import commands
from typing import Optional
import math

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character

class PaginationView(discord.ui.View):
    """Pagination view for inventory and market"""
    
    def __init__(self, *, timeout=300):
        super().__init__(timeout=timeout)
        self.current_page = 1
        self.total_pages = 1
        self.user_id = None
        self.command_type = None  # 'inventory' or 'market'
        self.cog = None
        
    def set_data(self, user_id, current_page, total_pages, command_type, cog):
        self.user_id = user_id
        self.current_page = current_page
        self.total_pages = total_pages
        self.command_type = command_type
        self.cog = cog
        self.update_buttons()
        
    def update_buttons(self):
        # Update button states
        self.previous_button.disabled = (self.current_page <= 1)
        self.next_button.disabled = (self.current_page >= self.total_pages)
        
    @discord.ui.button(label='◀️ Previous', style=discord.ButtonStyle.secondary, custom_id='prev')
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use someone else's pagination buttons!", ephemeral=True)
            return
            
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_page(interaction)
    
    @discord.ui.button(label='▶️ Next', style=discord.ButtonStyle.secondary, custom_id='next')
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can't use someone else's pagination buttons!", ephemeral=True)
            return
            
        if self.current_page < self.total_pages:
            self.current_page += 1
            await self.update_page(interaction)
    
    async def update_page(self, interaction):
        """Update the embed with new page data"""
        if self.command_type == 'inventory':
            embed = await self.cog.get_inventory_embed(self.user_id, self.current_page)
        elif self.command_type == 'market':
            embed = await self.cog.get_market_embed(self.current_page)
        
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def on_timeout(self):
        """Disable buttons when view times out"""
        for item in self.children:
            item.disabled = True
        # Note: The message won't auto-edit on timeout in this basic implementation

from classes.items import ItemGenerator, ItemType, ItemRarity, CrateSystem

class InventoryCog(DiscordRPGCog):
    """Inventory, equipment, and item commands"""
    
    async def get_inventory_embed(self, user_id: int, page: int = 1):
        """Generate inventory embed for given page"""
        items = self.db.get_user_items(user_id)
        
        if not items:
            embed = self.embed("📦 Inventory", "Your inventory is empty!")
            
            # Check for crates even if inventory is empty
            char_data = self.db.get_character(user_id)
            crate_info = []
            if char_data['crates_common'] > 0:
                crate_info.append(f"📦 Common: {char_data['crates_common']}")
            if char_data['crates_uncommon'] > 0:
                crate_info.append(f"📦 Uncommon: {char_data['crates_uncommon']}")
            if char_data['crates_rare'] > 0:
                crate_info.append(f"📦 Rare: {char_data['crates_rare']}")
            if char_data['crates_magic'] > 0:
                crate_info.append(f"✨ Magic: {char_data['crates_magic']}")
            if char_data['crates_legendary'] > 0:
                crate_info.append(f"🌟 Legendary: {char_data['crates_legendary']}")
            if char_data['crates_mystery'] > 0:
                crate_info.append(f"❓ Mystery: {char_data['crates_mystery']}")
                
            if crate_info:
                embed.add_field(
                    name="📦 Crates",
                    value=" • ".join(crate_info) + "\nUse `!crate <type>` to open",
                    inline=False
                )
                
            return embed
            
        # Paginate items (10 per page)
        items_per_page = 10
        total_pages = math.ceil(len(items) / items_per_page)
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]
        
        embed = self.embed(
            f"📦 Inventory (Page {page}/{total_pages})",
            f"Showing items {start_idx + 1}-{min(end_idx, len(items))} of {len(items)}"
        )
        
        for item in page_items:
            equipped_text = "🟢 **EQUIPPED**" if item['equipped'] else ""
            
            # Show different stats for armor vs weapons
            if item.get('slot_type') in ['head', 'chest', 'legs', 'hands', 'feet']:
                # Armor piece - show armor bonuses
                armor_stats = []
                if item['armor'] > 0:
                    armor_stats.append(f"{item['armor']}🛡️")
                if item.get('health_bonus', 0) > 0:
                    armor_stats.append(f"{item['health_bonus']}❤️")
                if item.get('speed_bonus', 0) > 0:
                    armor_stats.append(f"{item['speed_bonus']}💨")
                if item.get('luck_bonus', 0) > 0:
                    armor_stats.append(f"{item['luck_bonus']:.2f}🍀")
                if item.get('crit_bonus', 0) > 0:
                    armor_stats.append(f"{item['crit_bonus']:.1%}💥")
                if item.get('magic_bonus', 0) > 0:
                    armor_stats.append(f"{item['magic_bonus']}✨")
                stats = " ".join(armor_stats) or "No bonuses"
            else:
                # Weapon - show damage and armor
                stats = f"{item['damage']}⚔️ {item['armor']}🛡️"
            
            value_text = f"💰 {item['value']:,}" if item['value'] > 0 else ""
            # Determine slot type based on item type if not specified
            if item.get('slot_type'):
                slot_type = item['slot_type'].title()
            elif item['type'] in ['Helmet']:
                slot_type = 'Head'
            elif item['type'] in ['Chestplate']:
                slot_type = 'Chest'
            elif item['type'] in ['Leggings']:
                slot_type = 'Legs'
            elif item['type'] in ['Gauntlets']:
                slot_type = 'Hands'
            elif item['type'] in ['Boots']:
                slot_type = 'Feet'
            elif item['type'] in ['Shield']:
                slot_type = 'Shield'
            else:
                slot_type = 'Weapon'
            
            embed.add_field(
                name=f"[{item['id']}] {item['name']} {equipped_text}",
                value=f"`{item['type']}` ({slot_type}) • {stats} • {value_text}",
                inline=False
            )
            
        # Add crate information
        char_data = self.db.get_character(user_id)
        crate_info = []
        if char_data['crates_common'] > 0:
            crate_info.append(f"📦 Common: {char_data['crates_common']}")
        if char_data['crates_uncommon'] > 0:
            crate_info.append(f"📦 Uncommon: {char_data['crates_uncommon']}")
        if char_data['crates_rare'] > 0:
            crate_info.append(f"📦 Rare: {char_data['crates_rare']}")
        if char_data['crates_magic'] > 0:
            crate_info.append(f"✨ Magic: {char_data['crates_magic']}")
        if char_data['crates_legendary'] > 0:
            crate_info.append(f"🌟 Legendary: {char_data['crates_legendary']}")
        if char_data['crates_mystery'] > 0:
            crate_info.append(f"❓ Mystery: {char_data['crates_mystery']}")
            
        if crate_info:
            embed.add_field(
                name="📦 Crates",
                value=" • ".join(crate_info) + "\nUse `!crate <type>` to open",
                inline=False
            )
            
        return embed
    
    @commands.command(aliases=["inv", "items"])
    @has_character()
    async def inventory(self, ctx: commands.Context, page: int = 1):
        """View your inventory"""
        items = self.db.get_user_items(ctx.author.id)
        embed = await self.get_inventory_embed(ctx.author.id, page)
        
        # Check if pagination is needed
        if items and len(items) > 10:
            items_per_page = 10
            total_pages = math.ceil(len(items) / items_per_page)
            
            # Create pagination view
            view = PaginationView()
            view.set_data(ctx.author.id, page, total_pages, 'inventory', self)
            
            await ctx.send(embed=embed, view=view)
        else:
            # No pagination needed
            await ctx.send(embed=embed)
        
    @commands.command(aliases=["equipped"])
    @has_character()
    async def equipment(self, ctx: commands.Context):
        """View your equipped items"""
        items = self.db.get_equipped_items(ctx.author.id)
        
        embed = self.embed("⚔️ Equipment", "Your currently equipped items:")
        
        if not items:
            embed.description = "No items equipped. Use `!equip <item_id>` to equip items."
        else:
            total_damage = sum(item['damage'] for item in items)
            total_armor = sum(item['armor'] for item in items)
            
            # Calculate armor bonuses
            total_health_bonus = sum(item.get('health_bonus', 0) for item in items)
            total_speed_bonus = sum(item.get('speed_bonus', 0) for item in items)
            total_luck_bonus = sum(item.get('luck_bonus', 0.0) for item in items)
            total_crit_bonus = sum(item.get('crit_bonus', 0.0) for item in items)
            total_magic_bonus = sum(item.get('magic_bonus', 0) for item in items)
            total_value = sum(item['value'] for item in items)
            
            equipment_text = []
            for item in items:
                stats = f"{item['damage']}⚔️ {item['armor']}🛡️"
                equipment_text.append(f"**{item['name']}** - `{item['type']}` ({stats})")
                
            embed.add_field(
                name="📋 Equipped Items",
                value="\n".join(equipment_text),
                inline=False
            )
            
            embed.add_field(name="⚔️ Total Damage", value=total_damage, inline=True)
            embed.add_field(name="🛡️ Total Armor", value=total_armor, inline=True)
            embed.add_field(name="💰 Total Value", value=f"{total_value:,}", inline=True)
            
            # Show armor bonuses if any
            if any([total_health_bonus, total_speed_bonus, total_luck_bonus, total_crit_bonus, total_magic_bonus]):
                bonus_stats = []
                if total_health_bonus > 0:
                    bonus_stats.append(f"❤️ Health: +{total_health_bonus}")
                if total_speed_bonus > 0:
                    bonus_stats.append(f"💨 Speed: +{total_speed_bonus}")
                if total_luck_bonus > 0:
                    bonus_stats.append(f"🍀 Luck: +{total_luck_bonus:.3f}")
                if total_crit_bonus > 0:
                    bonus_stats.append(f"💥 Crit: +{total_crit_bonus:.1%}")
                if total_magic_bonus > 0:
                    bonus_stats.append(f"✨ Magic: +{total_magic_bonus}")
                
                if bonus_stats:
                    embed.add_field(
                        name="🛡️ Armor Bonuses",
                        value="\n".join(bonus_stats),
                        inline=False
                    )
            
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["e"])
    @has_character()
    async def equip(self, ctx: commands.Context, item_id: int):
        """Equip an item by ID"""
        # Get the item
        item = self.db.get_item_by_id(item_id)
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
            
        if item['equipped']:
            await ctx.send("❌ This item is already equipped!")
            return
            
        # Check equipment conflicts
        equipped_items = self.db.get_equipped_items(ctx.author.id)
        
        # Simple equipment logic
        hand = item['hand']
        item_type = item['type']
        slot_type = item.get('slot_type') or 'weapon'
        
        # Define weapon types that conflict with each other
        weapon_types = ['Sword', 'Axe', 'Hammer', 'Mace', 'Dagger', 'Knife', 'Spear', 'Wand', 'Staff', 'Bow', 'Crossbow', 'Greatsword', 'Halberd', 'Katana', 'Scythe']
        armor_slots = ['head', 'chest', 'legs', 'hands', 'feet']
        
        # Check for conflicts
        conflicts = []
        for eq_item in equipped_items:
            eq_slot_type = eq_item.get('slot_type') or 'weapon'
            
            # Armor slot conflicts - only one item per armor slot
            if slot_type in armor_slots and eq_slot_type == slot_type:
                conflicts.append(eq_item)
            # Shield conflicts - only one shield allowed
            elif item_type == 'Shield' and eq_item['type'] == 'Shield':
                conflicts.append(eq_item)
            # Weapon/Shield conflicts - handle hand requirements
            elif slot_type == 'weapon' and eq_slot_type == 'weapon':
                # Two-handed weapons conflict with all other weapons and shields
                if hand == 'both' or eq_item['hand'] == 'both':
                    conflicts.append(eq_item)
                # Specific hand conflicts (including shields)
                elif hand in ['left', 'right'] and eq_item['hand'] == hand:
                    conflicts.append(eq_item)
                # Weapon type conflicts - only one primary weapon allowed
                elif item_type in weapon_types and eq_item['type'] in weapon_types:
                    conflicts.append(eq_item)
                # "Any" hand conflicts when both hands full
                elif hand == 'any' and eq_item['hand'] in ['left', 'right', 'any']:
                    if len([x for x in equipped_items if (x.get('slot_type') or 'weapon') == 'weapon' and x['hand'] in ['left', 'right', 'any']]) >= 2:
                        conflicts.append(eq_item)
                    
        # Unequip conflicting items
        for conflict in conflicts:
            self.db.unequip_item(conflict['id'], ctx.author.id)
            
        # Equip the new item
        success = self.db.equip_item(item_id, ctx.author.id)
        
        if success:
            embed = self.success_embed(f"Equipped **{item['name']}**!")
            if conflicts:
                unequipped = [c['name'] for c in conflicts]
                embed.add_field(
                    name="Unequipped",
                    value="\n".join(unequipped),
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to equip item!")
            
    @commands.command(aliases=["unequip", "u"])
    @has_character()
    async def remove(self, ctx: commands.Context, item_id: int):
        """Unequip an item by ID"""
        item = self.db.get_item_by_id(item_id)
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
            
        if not item['equipped']:
            await ctx.send("❌ This item is not equipped!")
            return
            
        success = self.db.unequip_item(item_id, ctx.author.id)
        
        if success:
            embed = self.success_embed(f"Unequipped **{item['name']}**!")
            await ctx.send(embed=embed)
        else:
            await ctx.send("❌ Failed to unequip item!")
            
    @commands.command(aliases=["iteminfo"])
    @has_character()
    async def item(self, ctx: commands.Context, item_id: int):
        """View detailed information about an item"""
        item = self.db.get_item_by_id(item_id)
        if not item:
            await ctx.send("❌ Item not found!")
            return
            
        # Get item rarity based on all stats
        total_stats = (item['damage'] + item['armor'] + 
                      item.get('health_bonus', 0) + item.get('speed_bonus', 0) + 
                      int(item.get('luck_bonus', 0) * 100) + int(item.get('crit_bonus', 0) * 100) + 
                      item.get('magic_bonus', 0))
        if total_stats >= 50:
            rarity = "Divine"
            color = 0xFFD700
        elif total_stats >= 45:
            rarity = "Mythic"
            color = 0xFF6347
        elif total_stats >= 40:
            rarity = "Legendary"
            color = 0xFF4500
        elif total_stats >= 30:
            rarity = "Magic"
            color = 0x9932CC
        elif total_stats >= 20:
            rarity = "Rare"
            color = 0x0000FF
        elif total_stats >= 10:
            rarity = "Uncommon"
            color = 0x32CD32
        else:
            rarity = "Common"
            color = 0x808080
            
        embed = discord.Embed(
            title=f"{item['name']}",
            color=discord.Color(color)
        )
        
        embed.add_field(name="Type", value=item['type'], inline=True)
        embed.add_field(name="Rarity", value=rarity, inline=True)
        embed.add_field(name="Slot", value=(item.get('slot_type') or 'weapon').title(), inline=True)
        
        # Basic stats
        embed.add_field(name="⚔️ Damage", value=item['damage'], inline=True)
        embed.add_field(name="🛡️ Armor", value=item['armor'], inline=True)
        embed.add_field(name="💰 Value", value=f"{item['value']:,}", inline=True)
        
        # Armor bonuses (only show if they exist)
        armor_bonuses = []
        if item.get('health_bonus', 0) > 0:
            armor_bonuses.append(f"❤️ Health: +{item['health_bonus']}")
        if item.get('speed_bonus', 0) > 0:
            armor_bonuses.append(f"💨 Speed: +{item['speed_bonus']}")
        if item.get('luck_bonus', 0) > 0:
            armor_bonuses.append(f"🍀 Luck: +{item['luck_bonus']:.3f}")
        if item.get('crit_bonus', 0) > 0:
            armor_bonuses.append(f"💥 Crit: +{item['crit_bonus']:.1%}")
        if item.get('magic_bonus', 0) > 0:
            armor_bonuses.append(f"✨ Magic: +{item['magic_bonus']}")
        
        if armor_bonuses:
            embed.add_field(
                name="🛡️ Armor Bonuses", 
                value="\n".join(armor_bonuses), 
                inline=False
            )
        
        embed.add_field(name="Status", value="🟢 Equipped" if item['equipped'] else "⚪ Not Equipped", inline=True)
        
        if item['owner'] != ctx.author.id:
            owner = ctx.bot.get_user(item['owner'])
            embed.add_field(name="Owner", value=owner.mention if owner else f"User {item['owner']}", inline=True)
        else:
            embed.add_field(name="Item ID", value=f"`{item['id']}`", inline=True)
            
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def sell(self, ctx: commands.Context, item_id: int):
        """Sell an item to the merchant"""
        item = self.db.get_item_by_id(item_id)
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
            
        if item['equipped']:
            await ctx.send("❌ Cannot sell equipped items! Unequip it first.")
            return
            
        # Calculate sell price (base value or stat-based)
        sell_price = max(item['value'] // 4, (item['damage'] + item['armor']) * 10)
        
        if not await ctx.confirm(f"Sell **{item['name']}** for **{sell_price:,}** gold?"):
            await ctx.send("Sale cancelled.")
            return
            
        # Remove item and give gold
        self.db.delete_item(item_id)
        char_data = self.db.get_character(ctx.author.id)
        new_money = char_data['money'] + sell_price
        self.db.update_character(ctx.author.id, money=new_money)
        
        # Log transaction
        self.db.log_transaction(
            ctx.author.id, None, sell_price, "item_sale",
            {"item": item['name'], "item_id": item_id}
        )
        
        embed = self.success_embed(
            f"Sold **{item['name']}** for **{sell_price:,}** gold!\n"
            f"You now have **{new_money:,}** gold."
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def give(self, ctx: commands.Context, user: discord.User, item_id: int):
        """Give an item to another user"""
        if user.bot or user == ctx.author:
            await ctx.send("❌ Cannot give items to bots or yourself!")
            return
            
        # Check if recipient has character
        recipient_data = self.db.get_character(user.id)
        if not recipient_data:
            await ctx.send("❌ The recipient doesn't have a character!")
            return
            
        item = self.db.get_item_by_id(item_id)
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
            
        if item['equipped']:
            await ctx.send("❌ Cannot give equipped items! Unequip it first.")
            return
            
        if not await ctx.confirm(f"Give **{item['name']}** to {user.mention}?"):
            await ctx.send("Transfer cancelled.")
            return
            
        # Transfer ownership
        self.db.execute(
            "UPDATE inventory SET owner = ? WHERE id = ?",
            (user.id, item_id)
        )
        self.db.commit()
        
        # Log transaction
        self.db.log_transaction(
            ctx.author.id, user.id, 0, "item_transfer",
            {"item": item['name'], "item_id": item_id}
        )
        
        embed = self.success_embed(
            f"Gave **{item['name']}** to {user.mention}!"
        )
        await ctx.send(embed=embed)
        
        # Notify recipient
        try:
            dm_embed = self.embed(
                "🎁 Item Received",
                f"{ctx.author.mention} gave you **{item['name']}**!\n"
                f"Check your inventory with `!inventory`"
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass
            
    @commands.command(aliases=["open"])
    @has_character()
    async def crate(self, ctx: commands.Context, crate_type: str):
        """Open a crate (common, uncommon, rare, magic, legendary, mystery)"""
        char_data = self.db.get_character(ctx.author.id)
        
        crate_map = {
            "common": ("crates_common", "Common Crate"),
            "uncommon": ("crates_uncommon", "Uncommon Crate"),  
            "rare": ("crates_rare", "Rare Crate"),
            "magic": ("crates_magic", "Magic Crate"),
            "legendary": ("crates_legendary", "Legendary Crate"),
            "mystery": ("crates_mystery", "Mystery Crate")
        }
        
        if crate_type.lower() not in crate_map:
            await ctx.send("❌ Invalid crate type! Options: common, uncommon, rare, magic, legendary, mystery")
            return
            
        crate_field, crate_name = crate_map[crate_type.lower()]
        crate_count = char_data[crate_field]
        
        if crate_count <= 0:
            await ctx.send(f"❌ You don't have any {crate_name}s!")
            return
            
        # Open crate
        reward_type, item, money = CrateSystem.open_crate(crate_type.lower(), ctx.author.id)
        
        # Deduct crate
        self.db.update_character(ctx.author.id, **{crate_field: crate_count - 1})
        
        embed = self.embed(f"📦 {crate_name} Opened!")
        
        if reward_type == "money":
            # Give money
            new_money = char_data['money'] + money
            self.db.update_character(ctx.author.id, money=new_money)
            
            embed.add_field(name="💰 Money Reward", value=f"{money:,} gold", inline=False)
            embed.color = discord.Color.gold()
            
        else:  # item
            # Create item in database
            item_id = self.db.create_item(
                ctx.author.id, item.name, item.type.value,
                item.value, item.damage, item.armor, item.hand.value,
                item.health_bonus, item.speed_bonus, item.luck_bonus,
                item.crit_bonus, item.magic_bonus, item.slot_type
            )
            
            total_stats = item.damage + item.armor
            rarity_colors = {
                "Common": 0x808080,
                "Uncommon": 0x32CD32, 
                "Rare": 0x0000FF,
                "Magic": 0x9932CC,
                "Legendary": 0xFF4500,
                "Mythic": 0xFF6347,
                "Divine": 0xFFD700
            }
            
            embed.add_field(
                name="⚔️ Item Reward", 
                value=f"**{item.name}**\n`{item.type.value}` • {item.damage}⚔️ {item.armor}🛡️",
                inline=False
            )
            embed.color = discord.Color(rarity_colors.get(item.rarity.value.title(), 0x808080))
            
        # Log crate history
        self.db.execute(
            "INSERT INTO crate_history (user_id, crate_type, item_name, item_stats) VALUES (?, ?, ?, ?)",
            (ctx.author.id, crate_type, 
             item.name if item else "Gold", 
             item.stat_total if item else money)
        )
        self.db.commit()
        
        embed.set_footer(text=f"Remaining {crate_name}s: {crate_count - 1}")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(InventoryCog(bot))