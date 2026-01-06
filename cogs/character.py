"""Character management cog - creation, stats, evolution"""
import discord
from discord.ext import commands
from typing import Optional
import random
import asyncio
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.character import Character, CharacterClass, Race, ClassEvolution
from classes.items import ItemGenerator, ItemType

class CharacterCog(DiscordRPGCog):
    """Character creation and management commands"""
    
    @commands.command(aliases=["new", "register", "start"])
    @commands.cooldown(1, 3600, commands.BucketType.user)  # 1 hour cooldown
    async def create(self, ctx: commands.Context, *, name: str = None):
        """Create a new character and start playing DiscordRPG"""
        # Check if user already has character
        if self.db.get_character(ctx.author.id):
            await ctx.send("❌ You already have a character! Use `!profile` to view it.")
            return
            
        # Get character name
        if not name:
            await ctx.send("What shall your character's name be? (3-20 characters)")
            
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
                
            try:
                msg = await self.bot.wait_for('message', timeout=30.0, check=check)
                name = msg.content
            except asyncio.TimeoutError:
                await ctx.send("❌ Character creation timed out.")
                return
                
        # Validate name
        if not (3 <= len(name) <= 20):
            await ctx.send("❌ Character name must be between 3 and 20 characters!")
            return
            
        if not name.replace(" ", "").isalnum():
            await ctx.send("❌ Character name can only contain letters, numbers, and spaces!")
            return
            
        # Create character
        success = self.db.create_character(ctx.author.id, name)
        if not success:
            await ctx.send("❌ Failed to create character. Please try again.")
            return
            
        # Create starter items
        sword = ItemGenerator.generate_item(
            ctx.author.id,
            min_stat=3,
            max_stat=3,
            item_type=ItemType.SWORD
        )
        sword.name = "Starter Sword"
        sword_id = self.db.create_item(
            ctx.author.id, sword.name, sword.type.value,
            sword.value, sword.damage, sword.armor, sword.hand.value,
            sword.health_bonus, sword.speed_bonus, sword.luck_bonus,
            sword.crit_bonus, sword.magic_bonus, sword.slot_type
        )
        self.db.equip_item(sword_id, ctx.author.id)
        
        shield = ItemGenerator.generate_item(
            ctx.author.id,
            min_stat=3,
            max_stat=3,
            item_type=ItemType.SHIELD
        )
        shield.name = "Starter Shield"
        shield_id = self.db.create_item(
            ctx.author.id, shield.name, shield.type.value,
            shield.value, shield.damage, shield.armor, shield.hand.value,
            shield.health_bonus, shield.speed_bonus, shield.luck_bonus,
            shield.crit_bonus, shield.magic_bonus, shield.slot_type
        )
        self.db.equip_item(shield_id, ctx.author.id)
        
        # Send success message
        embed = self.embed(
            "✨ Character Created!",
            f"Welcome to DiscordRPG, **{name}**!\n\n"
            f"You start as a **Novice** with:\n"
            f"• 100 gold\n"
            f"• Starter Sword (3 damage)\n"
            f"• Starter Shield (3 armor)\n\n"
            f"Use `!help` to see available commands!"
        )
        embed.set_footer(text="Begin your adventure now!")
        await ctx.send(embed=embed)
        
    @commands.command(aliases=["p", "stats", "char"])
    async def profile(self, ctx: commands.Context, user: Optional[discord.User] = None):
        """View your character profile"""
        user = user or ctx.author
        
        # Get character data
        char_data = self.db.get_character(user.id)
        if not char_data:
            if user == ctx.author:
                await ctx.send("❌ You don't have a character! Use `!create` to make one.")
            else:
                await ctx.send(f"❌ {user.name} doesn't have a character!")
            return
            
        # Get equipped items
        items = self.db.get_equipped_items(user.id)
        total_damage = sum(item['damage'] for item in items)
        total_armor = sum(item['armor'] for item in items)
        
        # Calculate armor bonuses
        total_health_bonus = sum(item.get('health_bonus', 0) for item in items)
        total_speed_bonus = sum(item.get('speed_bonus', 0) for item in items)
        total_luck_bonus = sum(item.get('luck_bonus', 0.0) for item in items)
        total_crit_bonus = sum(item.get('crit_bonus', 0.0) for item in items)
        total_magic_bonus = sum(item.get('magic_bonus', 0) for item in items)
        
        # Create character object for calculations
        char = Character(user.id, char_data['name'])
        char.level = char_data['level']
        char.char_class = CharacterClass(char_data['class'])
        char.race = Race(char_data['race'])
        char.luck = char_data['luck']
        
        stats = char.total_stats
        
        # Build profile embed
        embed = self.embed(f"{char_data['name']}'s Profile")
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Basic info
        embed.add_field(
            name="📊 Basic Info",
            value=f"**Class:** {char_data['class']}\n"
                  f"**Race:** {char_data['race']}\n"
                  f"**Level:** {char_data['level']}\n"
                  f"**XP:** {char_data['xp']}/{char.xp_required}",
            inline=True
        )
        
        # Resources
        embed.add_field(
            name="💰 Resources",
            value=f"**Gold:** {char_data['money']:,}\n"
                  f"**Luck:** {char_data['luck']:.2f}\n"
                  f"**Favor:** {char_data['favor'] or 0}",
            inline=True
        )
        
        # Calculate true total power (matching combat system and leaderboards)
        true_total_power = (stats['attack'] + stats['defense'] + total_damage + total_armor + 
                           total_health_bonus + total_speed_bonus + 
                           int(total_luck_bonus * 100) + int(total_crit_bonus * 100) + total_magic_bonus)
        
        # Combat stats
        embed.add_field(
            name="⚔️ Combat Stats",
            value=f"**Attack:** {stats['attack']} (+{total_damage})\n"
                  f"**Defense:** {stats['defense']} (+{total_armor})\n"
                  f"**Magic:** {stats['magic']} (+{total_magic_bonus})\n"
                  f"**Total Power:** {true_total_power}",
            inline=True
        )
        
        # Armor bonuses (only show if player has armor equipped)
        if total_health_bonus > 0 or total_speed_bonus > 0 or total_luck_bonus > 0 or total_crit_bonus > 0:
            armor_bonuses = []
            if total_health_bonus > 0:
                armor_bonuses.append(f"**Health:** +{total_health_bonus}")
            if total_speed_bonus > 0:
                armor_bonuses.append(f"**Speed:** +{total_speed_bonus}")
            if total_luck_bonus > 0:
                armor_bonuses.append(f"**Luck:** +{total_luck_bonus:.3f}")
            if total_crit_bonus > 0:
                armor_bonuses.append(f"**Crit:** +{total_crit_bonus:.1%}")
            
            if armor_bonuses:
                embed.add_field(
                    name="🛡️ Armor Bonuses",
                    value="\n".join(armor_bonuses),
                    inline=True
                )
        
        # PvP stats
        embed.add_field(
            name="🏆 PvP Record",
            value=f"**Wins:** {char_data['pvpwins']}\n"
                  f"**Losses:** {char_data['pvplosses']}\n"
                  f"**Win Rate:** {char_data['pvpwins'] / max(1, char_data['pvpwins'] + char_data['pvplosses']) * 100:.1f}%",
            inline=True
        )
        
        # Social
        social_info = []
        if char_data['marriage']:
            social_info.append(f"💑 Married")
        if char_data['guild']:
            guild = self.db.get_guild(char_data['guild'])
            if guild:
                social_info.append(f"🏰 Guild: {guild['name']}")
        if char_data['god']:
            social_info.append(f"🙏 Following: {char_data['god']}")
            
        if social_info:
            embed.add_field(
                name="👥 Social",
                value="\n".join(social_info),
                inline=True
            )
            
        # Active divine blessings
        from cogs.religion import ReligionCog
        religion_cog = self.bot.get_cog('ReligionCog')
        if religion_cog:
            blessing_bonuses = religion_cog.get_active_blessings(user.id)
            active_blessings = self.db.fetchall(
                "SELECT * FROM divine_blessings WHERE user_id = ? AND expires_at > ?",
                (user.id, datetime.now())
            )
            
            if active_blessings:
                blessing_text = []
                for blessing in active_blessings[:3]:  # Show max 3 blessings
                    time_left = datetime.fromisoformat(blessing['expires_at']) - datetime.now()
                    minutes_left = max(0, int(time_left.total_seconds() // 60))
                    blessing_text.append(f"✨ {blessing['blessing_name']} ({minutes_left}m)")
                
                embed.add_field(
                    name="🙏 Divine Blessings",
                    value="\n".join(blessing_text) if blessing_text else "None active",
                    inline=True
                )
            
        # Progress
        embed.add_field(
            name="📈 Progress",
            value=f"**Adventures:** {char_data['completed']}\n"
                  f"**Deaths:** {char_data['deaths']}\n"
                  f"**Raid Stats:** {char_data['raidstats']}",
            inline=True
        )
        
        if char_data['description']:
            embed.add_field(
                name="📝 Description",
                value=char_data['description'][:1024],
                inline=False
            )
            
        embed.color = discord.Color(char_data['colour'] or 0x000000)
        # Remove broken image - just use avatar thumbnail
            
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def evolve(self, ctx: commands.Context):
        """Evolve your class (available at levels 5, 10, 15, 20, 25, 30)"""
        char_data = self.db.get_character(ctx.author.id)
        
        char = Character(ctx.author.id, char_data['name'])
        char.level = char_data['level']
        char.char_class = CharacterClass(char_data['class'])
        
        # Check if player meets level requirement AND has evolution options
        options = char.get_evolution_options()
        
        # Determine minimum level needed based on current class tier
        min_level_needed = 5  # Default first evolution (Novice -> Tier 1)
        
        # Tier 1 classes (Level 5 -> 10 for evolution)
        tier_1_classes = ["Warrior", "Thief", "Mage", "Ranger", "Raider", "Ritualist", "Paragon"]
        # Tier 2 classes (Level 10 -> 15 for evolution)  
        tier_2_classes = ["Swordsman", "Knight", "Rogue", "Assassin", "Wizard", "Warlock", "Hunter", "Tracker", "Viking", "Chieftain", "Mystic", "Shaman", "Champion"]
        # Tier 3 classes (Level 15 -> 20 for evolution)
        tier_3_classes = ["Warlord", "Paladin", "Bandit", "Shadow", "Sorcerer", "Necromancer", "Bowmaster", "Beastmaster", "Ravager", "Conqueror", "Oracle", "Sage", "Hero"]
        # Tier 4 classes (Level 20 -> 25 for evolution)
        tier_4_classes = ["Berserker", "Nightblade", "Archmage", "Marksman", "Warchief", "Prophet", "Legend"]
        # Tier 5 classes (Level 25 -> 30 for evolution)
        tier_5_classes = ["Eternal"]
        
        if char.char_class.value in tier_1_classes:
            min_level_needed = 10
        elif char.char_class.value in tier_2_classes:
            min_level_needed = 15
        elif char.char_class.value in tier_3_classes:
            min_level_needed = 20
        elif char.char_class.value in tier_4_classes:
            min_level_needed = 25
        elif char.char_class.value in tier_5_classes:
            min_level_needed = 30
        
        if char.level < min_level_needed:
            await ctx.send(f"❌ You need to be level {min_level_needed} or higher to evolve from **{char.char_class.value}**!")
            return
            
        if not options:
            await ctx.send("❌ No evolution options available for your class at this time.")
            return
            
        # Check for premium class
        if CharacterClass.PARAGON in options:
            # Check if user has premium
            is_premium = False  # TODO: Implement premium check
            if not is_premium:
                options.remove(CharacterClass.PARAGON)
                
        if not options:
            await ctx.send("❌ No evolution options available.")
            return
            
        # Show options with warning for convergence
        description = "Choose your class evolution:\n\n" + "\n".join([f"`{i+1}` - **{opt.value}**" for i, opt in enumerate(options)])
        
        # Add warning if evolving to Eternal (convergence point)
        if any(opt == CharacterClass.ETERNAL for opt in options):
            description += "\n\n⚠️ **Warning**: Evolving to Eternal means leaving behind your traditional class path. All paths converge to Eternal, leading ultimately to Immortal."
        
        embed = self.embed("🌟 Class Evolution", description)
        embed.set_footer(text="Type the number of your choice within 30 seconds")
        await ctx.send(embed=embed)
        
        # Wait for choice
        def check(m):
            return (m.author == ctx.author and m.channel == ctx.channel and 
                   m.content.isdigit() and 1 <= int(m.content) <= len(options))
                   
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            choice = int(msg.content) - 1
            new_class = options[choice]
        except asyncio.TimeoutError:
            await ctx.send("❌ Evolution timed out.")
            return
            
        # Store old class for message
        old_class_name = char.char_class.value
        
        # Update class
        self.db.update_character(ctx.author.id, **{"class": new_class.value})
        
        # Add debug logging
        import logging
        logger = logging.getLogger('DiscordRPG.Evolve')
        logger.info(f"Evolution executed for user {ctx.author.id} ({ctx.author.name}): {old_class_name} -> {new_class.value}")
        
        embed = self.success_embed(
            f"You have evolved from **{old_class_name}** to **{new_class.value}**!\n\n"
            f"Your new class bonuses are now active."
        )
        await ctx.send(embed=embed)
        logger.info(f"Evolution message sent for user {ctx.author.id}")
        
    @commands.command()
    @has_character()
    async def changerace(self, ctx: commands.Context):
        """Change your race (costs 1 reset point)"""
        char_data = self.db.get_character(ctx.author.id)
        
        if char_data['reset_points'] <= 0:
            await ctx.send("❌ You don't have any reset points left!")
            return
            
        # Show race options
        races = list(Race)
        embed = self.embed(
            "🧬 Change Race",
            "Choose your new race:\n\n" +
            "\n".join([f"`{i+1}` - **{race.value}**" for i, race in enumerate(races)])
        )
        embed.set_footer(text=f"This will cost 1 reset point (you have {char_data['reset_points']})")
        await ctx.send(embed=embed)
        
        # Wait for choice
        def check(m):
            return (m.author == ctx.author and m.channel == ctx.channel and 
                   m.content.isdigit() and 1 <= int(m.content) <= len(races))
                   
        try:
            msg = await self.bot.wait_for('message', timeout=30.0, check=check)
            choice = int(msg.content) - 1
            new_race = races[choice]
        except asyncio.TimeoutError:
            await ctx.send("❌ Race change timed out.")
            return
            
        # Confirm
        if not await ctx.confirm(f"Change your race to **{new_race.value}**? This will cost 1 reset point."):
            await ctx.send("Race change cancelled.")
            return
            
        # Update race and deduct reset point
        self.db.update_character(
            ctx.author.id, 
            race=new_race.value,
            reset_points=char_data['reset_points'] - 1
        )
        
        embed = self.success_embed(
            f"Your race has been changed to **{new_race.value}**!\n"
            f"Reset points remaining: {char_data['reset_points'] - 1}"
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def description(self, ctx: commands.Context, *, desc: str = None):
        """Set your character description"""
        if not desc:
            await ctx.send("❌ Please provide a description!")
            return
            
        if len(desc) > 200:
            await ctx.send("❌ Description must be 200 characters or less!")
            return
            
        self.db.update_character(ctx.author.id, description=desc)
        await ctx.send("✅ Character description updated!")
        
    @commands.command(aliases=["classstats", "classinfo"])
    @has_character()
    async def classbonuses(self, ctx: commands.Context, *, class_name: str = None):
        """View your current class bonuses or bonuses for a specific class"""
        char_data = self.db.get_character(ctx.author.id)
        
        if class_name:
            # Try to find the class by name
            target_class = None
            for cls in CharacterClass:
                if cls.value.lower() == class_name.lower():
                    target_class = cls
                    break
            
            if not target_class:
                await ctx.send(f"❌ Class '{class_name}' not found! Use `!classes` to see all available classes.")
                return
                
            display_class = target_class
            display_level = char_data['level']  # Use player's level for calculations
        else:
            # Show current class bonuses
            display_class = CharacterClass(char_data['class'])
            display_level = char_data['level']
        
        # Calculate bonuses
        from classes.character import ClassStats
        bonuses = ClassStats.get_class_bonuses(display_class, display_level)
        
        # Determine tier
        tier = 0
        if display_level >= 30:
            tier = 6
        elif display_level >= 25:
            tier = 5
        elif display_level >= 20:
            tier = 4
        elif display_level >= 15:
            tier = 3
        elif display_level >= 10:
            tier = 2
        elif display_level >= 5:
            tier = 1
        
        embed = self.embed(
            f"📊 {display_class.value} Class Bonuses",
            f"**Tier {tier}** bonuses at level {display_level}"
        )
        
        # Combat multipliers
        combat_bonuses = []
        if bonuses["attack_mult"] != 1.0:
            combat_bonuses.append(f"**Attack:** {bonuses['attack_mult']:.1f}x ({(bonuses['attack_mult']-1)*100:+.0f}%)")
        if bonuses["defense_mult"] != 1.0:
            combat_bonuses.append(f"**Defense:** {bonuses['defense_mult']:.1f}x ({(bonuses['defense_mult']-1)*100:+.0f}%)")
        if bonuses["magic_mult"] != 1.0:
            combat_bonuses.append(f"**Magic:** {bonuses['magic_mult']:.1f}x ({(bonuses['magic_mult']-1)*100:+.0f}%)")
        if bonuses["speed_mult"] != 1.0:
            combat_bonuses.append(f"**Speed:** {bonuses['speed_mult']:.1f}x ({(bonuses['speed_mult']-1)*100:+.0f}%)")
        
        if combat_bonuses:
            embed.add_field(
                name="⚔️ Combat Multipliers",
                value="\n".join(combat_bonuses),
                inline=True
            )
        
        # Special abilities
        special_abilities = []
        if bonuses["steal_chance"] > 0:
            special_abilities.append(f"**Steal Chance:** {bonuses['steal_chance']*100:.0f}%")
        if bonuses["crit_chance"] > 0.05:  # Base is 5%
            special_abilities.append(f"**Crit Chance:** {bonuses['crit_chance']*100:.1f}%")
        if bonuses["dodge_chance"] > 0.05:  # Base is 5%
            special_abilities.append(f"**Dodge Chance:** {bonuses['dodge_chance']*100:.1f}%")
        if bonuses["lifesteal"] > 0:
            special_abilities.append(f"**Lifesteal:** {bonuses['lifesteal']*100:.0f}%")
        
        if special_abilities:
            embed.add_field(
                name="✨ Special Abilities",
                value="\n".join(special_abilities),
                inline=True
            )
        
        # Other bonuses
        other_bonuses = []
        if bonuses["luck_mult"] != 1.0:
            other_bonuses.append(f"**Luck:** {bonuses['luck_mult']:.2f}x ({(bonuses['luck_mult']-1)*100:+.1f}%)")
        if bonuses["raid_mult"] != 1.0:
            other_bonuses.append(f"**Raid Power:** {bonuses['raid_mult']:.1f}x ({(bonuses['raid_mult']-1)*100:+.0f}%)")
        if bonuses["favor_mult"] != 1.0:
            other_bonuses.append(f"**Favor Gain:** {bonuses['favor_mult']:.2f}x ({(bonuses['favor_mult']-1)*100:+.1f}%)")
        
        if other_bonuses:
            embed.add_field(
                name="🎯 Other Bonuses",
                value="\n".join(other_bonuses),
                inline=True
            )
        
        # Class line information
        class_lines = {
            "Warrior": "🛡️ Tank/Defense specialist",
            "Thief": "🗡️ DPS with utility abilities", 
            "Mage": "🔮 High magic damage dealer",
            "Ranger": "🏹 Balanced with luck bonuses",
            "Raider": "⚔️ Raid combat specialist",
            "Ritualist": "🙏 Religion and support focused",
            "Paragon": "👑 Premium all-rounder"
        }
        
        for line, desc in class_lines.items():
            if line.lower() in display_class.value.lower():
                embed.add_field(
                    name="📋 Class Line",
                    value=desc,
                    inline=False
                )
                break
        
        # Evolution hint
        if tier == 0:
            embed.add_field(
                name="📈 Next Evolution",
                value="Reach level 5 to evolve from Novice!",
                inline=False
            )
        elif tier < 6:
            next_level = [5, 10, 15, 20, 25, 30][tier]
            embed.add_field(
                name="📈 Next Evolution",
                value=f"Reach level {next_level} for the next tier!",
                inline=False
            )
        
        embed.set_footer(text="Use !classbonuses <class name> to see other class bonuses")
        await ctx.send(embed=embed)

    @commands.command()
    async def classes(self, ctx: commands.Context):
        """View all classes and evolution paths"""
        embed = self.embed("📋 Class System", "Class evolution paths and requirements")
        
        # Base tier (Novice -> Level 5)
        embed.add_field(
            name="🌱 **Starting Class**",
            value="**Novice** *(Level 1)*\nEveryone starts here",
            inline=False
        )
        
        # Tier 1 (Level 5)
        tier1_classes = "**Warrior** - Melee combat specialist\n**Thief** - Stealth and agility\n**Mage** - Magical arts\n**Ranger** - Nature and archery\n**Raider** - Aggressive combat\n**Ritualist** - Mystical practices"
        embed.add_field(
            name="⚔️ **Tier 1** *(Level 5)*",
            value=tier1_classes,
            inline=True
        )
        
        # Tier 2 (Level 10) 
        tier2_classes = "**Swordsman, Knight** (from Warrior)\n**Rogue, Assassin** (from Thief)\n**Wizard, Warlock** (from Mage)\n**Hunter, Tracker** (from Ranger)\n**Viking, Chieftain** (from Raider)\n**Mystic, Shaman** (from Ritualist)"
        embed.add_field(
            name="🛡️ **Tier 2** *(Level 10)*",
            value=tier2_classes,
            inline=True
        )
        
        embed.add_field(
            name="🏆 **Higher Tiers**",
            value="**Tier 3** *(Level 15)*: Warlord, Paladin, Bandit, Shadow...\n**Tier 4** *(Level 20)*: Berserker, Nightblade, Archmage...\n**Tier 5** *(Level 25)*: Eternal *(All paths converge)*\n**Tier 6** *(Level 30)*: Immortal *(Final evolution)*",
            inline=False
        )
        
        embed.add_field(
            name="📈 **How to Evolve**",
            value="• Use `!evolve` at levels **5, 10, 15, 20, 25, 30**\n• Choose from available paths for your class\n• Each class provides different stat bonuses\n• Evolution is permanent!",
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.command()
    @has_character()
    async def background(self, ctx: commands.Context, *, url: str = None):
        """Set your profile background image"""
        if not url:
            await ctx.send("❌ Please provide an image URL!")
            return
            
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            await ctx.send("❌ Please provide a valid image URL!")
            return
            
        self.db.update_character(ctx.author.id, background=url)
        await ctx.send("✅ Profile background updated!")
        
    @commands.command()
    @has_character()
    async def color(self, ctx: commands.Context, color: str = None):
        """Set your profile embed color (hex code)"""
        if not color:
            await ctx.send("❌ Please provide a hex color code (e.g., #FF6B6B)!")
            return
            
        # Parse color
        if color.startswith('#'):
            color = color[1:]
            
        try:
            color_int = int(color, 16)
            if not (0 <= color_int <= 0xFFFFFF):
                raise ValueError
        except ValueError:
            await ctx.send("❌ Invalid color code! Use hex format like #FF6B6B")
            return
            
        self.db.update_character(ctx.author.id, colour=color_int)
        
        embed = discord.Embed(
            title="✅ Color Updated",
            description=f"Your profile color has been set to #{color.upper()}",
            color=discord.Color(color_int)
        )
        await ctx.send(embed=embed)
        
    @commands.command()
    async def online(self, ctx: commands.Context):
        """Show online players and their status"""
        all_chars = self.db.fetchall("SELECT user_id, name, level FROM profile ORDER BY level DESC")
        
        online_players = []
        offline_players = []
        
        for char in all_chars:
            user = self.bot.get_user(char['user_id'])
            if user:
                # Check status in all guilds
                is_online = False
                for guild in self.bot.guilds:
                    member = guild.get_member(user.id)
                    if member:
                        if member.status == discord.Status.online:
                            is_online = True
                            online_players.append((char, "🟢 Online"))
                        elif member.status == discord.Status.idle:
                            offline_players.append((char, "🟡 Idle (No Progress)"))
                        elif member.status == discord.Status.dnd:
                            offline_players.append((char, "🔴 DND (No Progress)"))
                        else:
                            offline_players.append((char, "⚫ Offline (No Progress)"))
                        break
                        
        embed = self.embed("👥 Player Status", "Only **ONLINE** (🟢) players progress!")
        
        # Online players
        if online_players:
            online_text = []
            for char, status in online_players[:10]:  # Show max 10
                online_text.append(f"{status} **{char['name']}** (Lv.{char['level']})")
            embed.add_field(
                name=f"🎮 Active Players ({len(online_players)})",
                value="\n".join(online_text),
                inline=False
            )
            
        # Offline/inactive
        if offline_players:
            offline_text = []
            for char, status in offline_players[:10]:  # Show max 10
                offline_text.append(f"{status} {char['name']} (Lv.{char['level']})")
            embed.add_field(
                name=f"💤 Inactive Players ({len(offline_players)})",
                value="\n".join(offline_text),
                inline=False
            )
            
        embed.set_footer(text="Set your status to Online to participate!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CharacterCog(bot))