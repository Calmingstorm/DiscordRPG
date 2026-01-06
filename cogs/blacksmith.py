"""Blacksmith system - Dismantle, Reforge, and Upgrade items"""
import discord
from discord.ext import commands
from typing import Optional, List, Dict, Any
import random

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemRarity, ItemGenerator, ItemType


class BlacksmithCog(DiscordRPGCog):
    """Blacksmith commands for salvaging, reforging, and upgrading items"""
    
    # Material costs for operations
    REROLL_COSTS = {
        'scrap': 3,   # Common/Uncommon items
        'dust': 3,    # Rare/Magic items
        'essence': 2  # Legendary+ items
    }
    
    # Upgrade costs by level range
    UPGRADE_COSTS = {
        (1, 3): {'scrap': 1, 'dust': 1, 'essence': 1},
        (4, 6): {'scrap': 2, 'dust': 2, 'essence': 1},
        (7, 9): {'scrap': 3, 'dust': 3, 'essence': 2},
        (10, 10): {'scrap': 5, 'dust': 5, 'essence': 3}
    }
    
    # Upgrade success rates by level
    UPGRADE_SUCCESS_RATES = {
        (1, 3): 1.0,   # 100%
        (4, 6): 0.7,   # 70%
        (7, 9): 0.4,   # 40%
        (10, 10): 0.1  # 10%
    }
    
    # Rarity colors for embeds
    RARITY_COLORS = {
        ItemRarity.COMMON: 0x808080,
        ItemRarity.UNCOMMON: 0x32CD32,
        ItemRarity.RARE: 0x0000FF,
        ItemRarity.MAGIC: 0x9932CC,
        ItemRarity.LEGENDARY: 0xFF4500,
        ItemRarity.MYTHIC: 0xFF6347,
        ItemRarity.DIVINE: 0xFFD700
    }
    
    def _get_item_rarity(self, item: Dict[str, Any]) -> ItemRarity:
        """Calculate rarity from item dict"""
        total = (item['damage'] + item['armor'] + 
                 item.get('health_bonus', 0) + item.get('speed_bonus', 0) +
                 int(item.get('luck_bonus', 0) * 100) + int(item.get('crit_bonus', 0) * 100) +
                 item.get('magic_bonus', 0))
        
        if total >= 50:
            return ItemRarity.DIVINE
        elif total >= 45:
            return ItemRarity.MYTHIC
        elif total >= 40:
            return ItemRarity.LEGENDARY
        elif total >= 30:
            return ItemRarity.MAGIC
        elif total >= 20:
            return ItemRarity.RARE
        elif total >= 10:
            return ItemRarity.UNCOMMON
        else:
            return ItemRarity.COMMON
    
    def _get_dismantle_yield(self, rarity: ItemRarity) -> tuple[str, int]:
        """Get material type and amount for dismantling"""
        material_type = ItemRarity.get_material_tier(rarity)
        
        if material_type == 'essence':
            # Legendary+ gives 1 essence
            return ('essence', 1)
        else:
            # Common/Uncommon/Rare/Magic give 1-3 of their material
            return (material_type, random.randint(1, 3))
    
    def _get_upgrade_cost(self, target_level: int, material_type: str) -> int:
        """Get material cost for upgrading to target level"""
        for (min_lvl, max_lvl), costs in self.UPGRADE_COSTS.items():
            if min_lvl <= target_level <= max_lvl:
                return costs[material_type]
        return 1
    
    def _get_upgrade_success_rate(self, target_level: int) -> float:
        """Get success rate for upgrading to target level"""
        for (min_lvl, max_lvl), rate in self.UPGRADE_SUCCESS_RATES.items():
            if min_lvl <= target_level <= max_lvl:
                return rate
        return 1.0
    
    @commands.command(aliases=['smith', 'forge'])
    @has_character()
    async def blacksmith(self, ctx: commands.Context):
        """View your blacksmith materials and available options"""
        char_data = self.db.get_character(ctx.author.id)
        
        embed = self.embed(
            "⚒️ The Blacksmith",
            "Welcome, adventurer! I can help you improve your gear."
        )
        
        # Material wallet
        scrap = char_data.get('material_scrap', 0)
        dust = char_data.get('material_dust', 0)
        essence = char_data.get('material_essence', 0)
        
        embed.add_field(
            name="📦 Your Materials",
            value=(
                f"🔩 **Scrap Metal:** {scrap:,}\n"
                f"✨ **Magic Dust:** {dust:,}\n"
                f"💜 **Void Essence:** {essence:,}"
            ),
            inline=False
        )
        
        # Services
        embed.add_field(
            name="🔨 Services",
            value=(
                "**`!dismantle <item_id>`** - Salvage items for materials\n"
                "**`!dismantle all <rarity>`** - Bulk salvage by rarity\n"
                "**`!reforge <item_id>`** - Reroll item stats (keeps rarity)\n"
                "**`!upgrade <item_id>`** - Enhance item (+5% stats per level)"
            ),
            inline=False
        )
        
        # Material sources
        embed.add_field(
            name="📋 Material Sources",
            value=(
                "🔩 Scrap Metal → Common/Uncommon items\n"
                "✨ Magic Dust → Rare/Magic items\n"
                "💜 Void Essence → Legendary/Mythic/Divine items"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @has_character()
    async def dismantle(self, ctx: commands.Context, target: str, rarity_filter: str = None):
        """Dismantle items for materials. Usage: !dismantle <item_id> or !dismantle all <rarity>"""
        
        if target.lower() == 'all':
            await self._dismantle_bulk(ctx, rarity_filter)
        else:
            try:
                item_id = int(target)
                await self._dismantle_single(ctx, item_id)
            except ValueError:
                await ctx.send("❌ Invalid item ID! Use `!dismantle <item_id>` or `!dismantle all <rarity>`")
    
    async def _dismantle_single(self, ctx: commands.Context, item_id: int):
        """Dismantle a single item"""
        item = self.db.get_item_by_id(item_id)
        
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
        
        if item['equipped']:
            await ctx.send("❌ Cannot dismantle equipped items! Unequip it first.")
            return
        
        # Calculate yield
        rarity = self._get_item_rarity(item)
        material_type, amount = self._get_dismantle_yield(rarity)
        
        # Confirm
        material_names = {'scrap': '🔩 Scrap Metal', 'dust': '✨ Magic Dust', 'essence': '💜 Void Essence'}
        if not await ctx.confirm(
            f"Dismantle **{item['name']}** ({rarity.value.title()})?\n"
            f"You will receive: **{amount}x {material_names[material_type]}**"
        ):
            await ctx.send("Dismantling cancelled.")
            return
        
        # Delete item
        self.db.delete_item(item_id)
        
        # Add materials
        char_data = self.db.get_character(ctx.author.id)
        material_col = f'material_{material_type}'
        new_amount = char_data.get(material_col, 0) + amount
        self.db.update_character(ctx.author.id, **{material_col: new_amount})
        
        embed = self.success_embed(
            f"Dismantled **{item['name']}**!\n"
            f"Received: **{amount}x {material_names[material_type]}**\n"
            f"Total {material_names[material_type]}: **{new_amount:,}**"
        )
        await ctx.send(embed=embed)
    
    async def _dismantle_bulk(self, ctx: commands.Context, rarity_filter: str):
        """Dismantle all items of a specific rarity"""
        if not rarity_filter:
            await ctx.send("❌ Please specify a rarity! Example: `!dismantle all common`")
            return
        
        # Validate rarity
        rarity_map = {
            'common': ItemRarity.COMMON,
            'uncommon': ItemRarity.UNCOMMON,
            'rare': ItemRarity.RARE,
            'magic': ItemRarity.MAGIC,
            'legendary': ItemRarity.LEGENDARY,
            'mythic': ItemRarity.MYTHIC,
            'divine': ItemRarity.DIVINE
        }
        
        if rarity_filter.lower() not in rarity_map:
            await ctx.send(f"❌ Invalid rarity! Options: {', '.join(rarity_map.keys())}")
            return
        
        target_rarity = rarity_map[rarity_filter.lower()]
        
        # Get all user items of this rarity (excluding equipped)
        all_items = self.db.get_user_items(ctx.author.id)
        matching_items = [
            item for item in all_items 
            if not item['equipped'] and self._get_item_rarity(item) == target_rarity
        ]
        
        if not matching_items:
            await ctx.send(f"❌ No unequipped {target_rarity.value.title()} items to dismantle!")
            return
        
        # Calculate total yield
        material_type = ItemRarity.get_material_tier(target_rarity)
        total_yield = sum(self._get_dismantle_yield(target_rarity)[1] for _ in matching_items)
        
        # Show items to be dismantled
        item_list = "\n".join([f"• [{item['id']}] {item['name']}" for item in matching_items[:10]])
        if len(matching_items) > 10:
            item_list += f"\n... and {len(matching_items) - 10} more"
        
        material_names = {'scrap': '🔩 Scrap Metal', 'dust': '✨ Magic Dust', 'essence': '💜 Void Essence'}
        
        if not await ctx.confirm(
            f"Dismantle **{len(matching_items)}** {target_rarity.value.title()} items?\n\n"
            f"{item_list}\n\n"
            f"Expected yield: **~{total_yield}x {material_names[material_type]}**"
        ):
            await ctx.send("Bulk dismantling cancelled.")
            return
        
        # Process all items
        actual_yield = 0
        for item in matching_items:
            self.db.delete_item(item['id'])
            _, amount = self._get_dismantle_yield(target_rarity)
            actual_yield += amount
        
        # Add materials
        char_data = self.db.get_character(ctx.author.id)
        material_col = f'material_{material_type}'
        new_amount = char_data.get(material_col, 0) + actual_yield
        self.db.update_character(ctx.author.id, **{material_col: new_amount})
        
        embed = self.success_embed(
            f"Dismantled **{len(matching_items)}** {target_rarity.value.title()} items!\n"
            f"Received: **{actual_yield}x {material_names[material_type]}**\n"
            f"Total {material_names[material_type]}: **{new_amount:,}**"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    @has_character()
    async def reforge(self, ctx: commands.Context, item_id: int):
        """Reroll an item's stats while keeping its rarity tier"""
        item = self.db.get_item_by_id(item_id)
        
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
        
        # Get rarity and material type
        rarity = self._get_item_rarity(item)
        material_type = ItemRarity.get_material_tier(rarity)
        cost = self.REROLL_COSTS[material_type]
        
        # Check materials
        char_data = self.db.get_character(ctx.author.id)
        material_col = f'material_{material_type}'
        current_materials = char_data.get(material_col, 0)
        
        if current_materials < cost:
            material_names = {'scrap': 'Scrap Metal', 'dust': 'Magic Dust', 'essence': 'Void Essence'}
            await ctx.send(
                f"❌ Not enough materials! Need **{cost}x {material_names[material_type]}** "
                f"(you have {current_materials})"
            )
            return
        
        # Calculate current stats
        current_total = (item['damage'] + item['armor'] + 
                        item.get('health_bonus', 0) + item.get('speed_bonus', 0) +
                        int(item.get('luck_bonus', 0) * 100) + int(item.get('crit_bonus', 0) * 100) +
                        item.get('magic_bonus', 0))
        
        min_stat, max_stat = ItemRarity.get_stat_range(rarity)
        
        # Show preview
        material_names = {'scrap': '🔩 Scrap Metal', 'dust': '✨ Magic Dust', 'essence': '💜 Void Essence'}
        upgrade_display = f" +{item.get('upgrade_level', 0)}" if item.get('upgrade_level', 0) > 0 else ""
        
        embed = discord.Embed(
            title=f"⚒️ Reforge: {item['name']}{upgrade_display}",
            color=self.RARITY_COLORS.get(rarity, 0x808080)
        )
        
        # Current stats
        current_stats = f"⚔️ Damage: {item['damage']}\n🛡️ Armor: {item['armor']}"
        if item.get('health_bonus', 0) > 0:
            current_stats += f"\n❤️ Health: +{item['health_bonus']}"
        if item.get('speed_bonus', 0) > 0:
            current_stats += f"\n💨 Speed: +{item['speed_bonus']}"
        if item.get('luck_bonus', 0) > 0:
            current_stats += f"\n🍀 Luck: +{item['luck_bonus']:.2f}"
        if item.get('crit_bonus', 0) > 0:
            current_stats += f"\n💥 Crit: +{item['crit_bonus']:.1%}"
        if item.get('magic_bonus', 0) > 0:
            current_stats += f"\n✨ Magic: +{item['magic_bonus']}"
        
        embed.add_field(
            name=f"📊 Current Stats ({current_total} pts)",
            value=current_stats,
            inline=True
        )
        
        embed.add_field(
            name="🎲 Potential Outcome",
            value=(
                f"**Range:** {min_stat} - {max_stat} pts\n"
                f"**Tier:** {rarity.value.title()} (locked)\n"
                f"Stats will be redistributed based on item type."
            ),
            inline=True
        )
        
        embed.add_field(
            name="💳 Cost",
            value=f"{cost}x {material_names[material_type]}",
            inline=False
        )
        
        embed.set_footer(text="Note: Upgrade level (+X) is preserved during reforge")
        
        await ctx.send(embed=embed)
        
        if not await ctx.confirm("Proceed with reforge?"):
            await ctx.send("Reforge cancelled.")
            return
        
        # Deduct materials
        self.db.update_character(ctx.author.id, **{material_col: current_materials - cost})
        
        # Create Item object for reroll
        item_type = ItemType(item['type'])
        from classes.items import Item, ItemHand
        item_obj = Item(
            item_id=item['id'],
            owner_id=item['owner'],
            name=item['name'],
            item_type=item_type,
            value=item['value'],
            damage=item['damage'],
            armor=item['armor'],
            hand=ItemHand(item['hand']) if item['hand'] else ItemHand.ANY,
            equipped=item['equipped'],
            health_bonus=item.get('health_bonus', 0),
            speed_bonus=item.get('speed_bonus', 0),
            luck_bonus=item.get('luck_bonus', 0),
            crit_bonus=item.get('crit_bonus', 0),
            magic_bonus=item.get('magic_bonus', 0),
            slot_type=item.get('slot_type'),
            upgrade_level=item.get('upgrade_level', 0)
        )
        
        # Reroll stats
        new_stats = ItemGenerator.reroll_item(item_obj)
        
        # Update item in database
        self.db.execute(
            """UPDATE inventory SET 
               name = ?, damage = ?, armor = ?, value = ?,
               health_bonus = ?, speed_bonus = ?, luck_bonus = ?,
               crit_bonus = ?, magic_bonus = ?
               WHERE id = ?""",
            (new_stats['name'], new_stats['damage'], new_stats['armor'], new_stats['value'],
             new_stats['health_bonus'], new_stats['speed_bonus'], new_stats['luck_bonus'],
             new_stats['crit_bonus'], new_stats['magic_bonus'], item_id)
        )
        self.db.commit()
        
        # Calculate new total
        new_total = (new_stats['damage'] + new_stats['armor'] + 
                    new_stats['health_bonus'] + new_stats['speed_bonus'] +
                    int(new_stats['luck_bonus'] * 100) + int(new_stats['crit_bonus'] * 100) +
                    new_stats['magic_bonus'])
        
        # Result embed
        result_embed = discord.Embed(
            title="⚒️ Reforge Complete!",
            color=self.RARITY_COLORS.get(rarity, 0x808080)
        )
        
        result_embed.add_field(
            name=f"🔄 {item['name']} → {new_stats['name']}",
            value=f"Stat Total: {current_total} → **{new_total}**",
            inline=False
        )
        
        new_stats_display = f"⚔️ Damage: {new_stats['damage']}\n🛡️ Armor: {new_stats['armor']}"
        if new_stats['health_bonus'] > 0:
            new_stats_display += f"\n❤️ Health: +{new_stats['health_bonus']}"
        if new_stats['speed_bonus'] > 0:
            new_stats_display += f"\n💨 Speed: +{new_stats['speed_bonus']}"
        if new_stats['luck_bonus'] > 0:
            new_stats_display += f"\n🍀 Luck: +{new_stats['luck_bonus']:.2f}"
        if new_stats['crit_bonus'] > 0:
            new_stats_display += f"\n💥 Crit: +{new_stats['crit_bonus']:.1%}"
        if new_stats['magic_bonus'] > 0:
            new_stats_display += f"\n✨ Magic: +{new_stats['magic_bonus']}"
        
        result_embed.add_field(name="📊 New Stats", value=new_stats_display, inline=False)
        
        diff = new_total - current_total
        if diff > 0:
            result_embed.set_footer(text=f"📈 +{diff} stat points! Great roll!")
        elif diff < 0:
            result_embed.set_footer(text=f"📉 {diff} stat points. Better luck next time!")
        else:
            result_embed.set_footer(text="📊 Same total, different distribution.")
        
        await ctx.send(embed=result_embed)
    
    @commands.command(aliases=['enhance'])
    @has_character()
    async def upgrade(self, ctx: commands.Context, item_id: int):
        """Upgrade an item to increase its stats by 5% per level"""
        item = self.db.get_item_by_id(item_id)
        
        if not item or item['owner'] != ctx.author.id:
            await ctx.send("❌ Item not found or you don't own it!")
            return
        
        current_level = item.get('upgrade_level', 0)
        
        if current_level >= 10:
            await ctx.send("❌ This item is already at maximum upgrade level (+10)!")
            return
        
        target_level = current_level + 1
        
        # Get rarity and material requirements
        rarity = self._get_item_rarity(item)
        material_type = ItemRarity.get_material_tier(rarity)
        cost = self._get_upgrade_cost(target_level, material_type)
        success_rate = self._get_upgrade_success_rate(target_level)
        
        # Check materials
        char_data = self.db.get_character(ctx.author.id)
        material_col = f'material_{material_type}'
        current_materials = char_data.get(material_col, 0)
        
        if current_materials < cost:
            material_names = {'scrap': 'Scrap Metal', 'dust': 'Magic Dust', 'essence': 'Void Essence'}
            await ctx.send(
                f"❌ Not enough materials! Need **{cost}x {material_names[material_type]}** "
                f"(you have {current_materials})"
            )
            return
        
        # Calculate current effective stats
        multiplier = 1.0 + (0.05 * current_level)
        new_multiplier = 1.0 + (0.05 * target_level)
        
        effective_damage = int(item['damage'] * multiplier)
        effective_armor = int(item['armor'] * multiplier)
        new_effective_damage = int(item['damage'] * new_multiplier)
        new_effective_armor = int(item['armor'] * new_multiplier)
        
        # Show upgrade preview
        material_names = {'scrap': '🔩 Scrap Metal', 'dust': '✨ Magic Dust', 'essence': '💜 Void Essence'}
        level_display = f"+{current_level}" if current_level > 0 else ""
        
        embed = discord.Embed(
            title=f"⬆️ Upgrade: {item['name']} {level_display}",
            color=self.RARITY_COLORS.get(rarity, 0x808080)
        )
        
        embed.add_field(
            name="📊 Current → After Upgrade",
            value=(
                f"**Level:** +{current_level} → **+{target_level}**\n"
                f"**Bonus:** {int(multiplier * 100 - 100)}% → **{int(new_multiplier * 100 - 100)}%**\n"
                f"⚔️ Damage: {effective_damage} → **{new_effective_damage}**\n"
                f"🛡️ Armor: {effective_armor} → **{new_effective_armor}**"
            ),
            inline=False
        )
        
        # Risk warning for higher levels
        if success_rate < 1.0:
            risk_text = f"⚠️ **{int(success_rate * 100)}% Success Rate**\n"
            if target_level >= 7:
                risk_text += "Failure: Item downgrades by 1 level\n"
            else:
                risk_text += "Failure: Materials lost, item unchanged\n"
            if target_level == 10:
                risk_text += "⚠️ **DANGER: Failure resets item to +0!**"
            embed.add_field(name="⚠️ Risk", value=risk_text, inline=False)
        
        embed.add_field(
            name="💳 Cost",
            value=f"{cost}x {material_names[material_type]}",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
        if not await ctx.confirm(f"Attempt upgrade to +{target_level}?"):
            await ctx.send("Upgrade cancelled.")
            return
        
        # Deduct materials
        self.db.update_character(ctx.author.id, **{material_col: current_materials - cost})
        
        # Roll for success
        success = random.random() < success_rate
        
        if success:
            # Update upgrade level
            self.db.execute(
                "UPDATE inventory SET upgrade_level = ? WHERE id = ?",
                (target_level, item_id)
            )
            self.db.commit()
            
            result_embed = discord.Embed(
                title="✨ Upgrade Successful!",
                description=(
                    f"**{item['name']}** is now **+{target_level}**!\n\n"
                    f"⚔️ Effective Damage: {new_effective_damage}\n"
                    f"🛡️ Effective Armor: {new_effective_armor}"
                ),
                color=discord.Color.green()
            )
            await ctx.send(embed=result_embed)
        else:
            # Handle failure
            if target_level == 10:
                # Reset to +0
                self.db.execute(
                    "UPDATE inventory SET upgrade_level = 0 WHERE id = ?",
                    (item_id,)
                )
                self.db.commit()
                
                result_embed = discord.Embed(
                    title="💥 Upgrade Failed!",
                    description=(
                        f"The upgrade failed catastrophically!\n"
                        f"**{item['name']}** has been reset to **+0**."
                    ),
                    color=discord.Color.red()
                )
            elif target_level >= 7:
                # Downgrade by 1 level
                new_level = current_level - 1
                self.db.execute(
                    "UPDATE inventory SET upgrade_level = ? WHERE id = ?",
                    (max(0, new_level), item_id)
                )
                self.db.commit()
                
                result_embed = discord.Embed(
                    title="💔 Upgrade Failed!",
                    description=(
                        f"The upgrade failed!\n"
                        f"**{item['name']}** dropped to **+{max(0, new_level)}**."
                    ),
                    color=discord.Color.orange()
                )
            else:
                # Just lose materials
                result_embed = discord.Embed(
                    title="❌ Upgrade Failed!",
                    description=(
                        f"The upgrade failed.\n"
                        f"Materials were consumed, but **{item['name']}** remains at +{current_level}."
                    ),
                    color=discord.Color.orange()
                )
            
            await ctx.send(embed=result_embed)
    
    @commands.command()
    @has_character()
    async def materials(self, ctx: commands.Context):
        """Quick view of your blacksmith materials"""
        char_data = self.db.get_character(ctx.author.id)
        
        scrap = char_data.get('material_scrap', 0)
        dust = char_data.get('material_dust', 0)
        essence = char_data.get('material_essence', 0)
        
        embed = self.embed(
            "📦 Materials",
            f"🔩 **Scrap Metal:** {scrap:,}\n"
            f"✨ **Magic Dust:** {dust:,}\n"
            f"💜 **Void Essence:** {essence:,}"
        )
        
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BlacksmithCog(bot))
