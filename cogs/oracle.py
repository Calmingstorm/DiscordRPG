"""RPG Oracle - Living Game Manual using AI"""
import discord
from discord.ext import commands
import json
import os
from typing import Dict, Any, List
import asyncio

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character

# Import OpenAI safely
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OracleCog(DiscordRPGCog):
    """The Oracle - Living Game Manual powered by AI"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.openai_client = None
        self.game_knowledge = {}
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI client if available and configured"""
        if not OPENAI_AVAILABLE:
            print("⚠️ OpenAI package not available. !ask command will be limited.")
            return
            
        # Load configuration from environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if OpenAI integration is enabled
        openai_enabled = os.getenv('OPENAI_ENABLED', 'false').lower() in ['true', '1', 'yes', 'on']
        
        if not openai_enabled:
            print("⚠️ OpenAI integration is disabled in configuration")
            print("⚠️ Set OPENAI_ENABLED=true in .env to enable AI responses")
            self.openai_client = None
            return
            
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            try:
                # Create OpenAI client with API key
                self.openai_client = OpenAI(api_key=api_key)
                print("✅ Oracle initialized with AI capabilities (gpt-4o-mini)")
            except Exception as e:
                print(f"⚠️ Failed to initialize OpenAI client: {e}")
                print("⚠️ Oracle will use admin message")
                self.openai_client = None
        else:
            print("⚠️ No OpenAI API key found in environment")
            self.openai_client = None
    
    async def cog_load(self):
        """Load game documentation when cog loads"""
        await self._compile_game_documentation()
        
    async def _compile_game_documentation(self):
        """Extract and compile comprehensive game documentation"""
        self.game_knowledge = {
            'commands': await self._extract_command_help(),
            'classes': await self._extract_class_data(),
            'races': await self._extract_race_data(),
            'mechanics': await self._extract_game_mechanics(),
            'items': await self._extract_item_system_info(),
            'systems': await self._extract_system_documentation()
        }
        
    async def _extract_command_help(self) -> Dict[str, Any]:
        """Extract all command information from loaded cogs"""
        commands = {}
        
        for cog_name, cog in self.bot.cogs.items():
            if hasattr(cog, 'get_commands'):
                for command in cog.get_commands():
                    # Skip hidden/admin commands
                    if command.name in ['removeme', 'admin', 'eval', 'exec']:
                        continue
                        
                    commands[command.name] = {
                        'description': command.help or "No description available",
                        'aliases': list(command.aliases) if command.aliases else [],
                        'usage': f"!{command.name} {command.signature}".strip(),
                        'category': cog_name.replace('Cog', ''),
                        'brief': command.brief or command.help or "Game command"
                    }
        
        return commands
    
    async def _extract_class_data(self) -> Dict[str, Any]:
        """Extract class evolution and bonus information"""
        try:
            # Read class data from character.py
            from classes.character import Character
            
            # Extract class evolution tree
            classes = {
                "Base Classes": {
                    "Monk": "Starting class focused on unarmed combat and spiritual power",
                    "Warrior": "Starting class focused on physical combat and defense", 
                    "Thief": "Starting class focused on stealth and agility",
                    "Mage": "Starting class focused on magical abilities and knowledge",
                    "Paladin": "Starting class combining combat and divine magic",
                    "Archer": "Starting class focused on ranged combat and precision"
                },
                "Evolution": "Classes evolve at levels 5, 10, 15, 20, 25, 30, 50, 100 using !evolve command",
                "Requirements": "Must reach the required level to access new class options"
            }
            
            return classes
        except Exception as e:
            return {"error": f"Could not extract class data: {e}"}
    
    async def _extract_race_data(self) -> Dict[str, Any]:
        """Extract race information and bonuses"""
        try:
            races = {
                "Available Races": [
                    "Human - Balanced bonuses across all areas",
                    "Elf - Enhanced magic and archery abilities", 
                    "Dwarf - Strong combat and crafting bonuses",
                    "Orc - Powerful combat bonuses with slight penalties elsewhere",
                    "Halfling - Luck and stealth bonuses",
                    "Dragonborn - Strong magical and combat abilities",
                    "Tiefling - Magical affinity with unique abilities",
                    "Gnome - Intelligence and crafting focus",
                    "Half-Elf - Balanced magical and social bonuses"
                ],
                "Selection": "Choose race with !race <name> command - this is PERMANENT!",
                "Bonuses": "Each race provides different multipliers to XP, gold, luck, and other stats"
            }
            return races
        except Exception as e:
            return {"error": f"Could not extract race data: {e}"}
    
    async def _extract_game_mechanics(self) -> Dict[str, Any]:
        """Extract core game mechanics and formulas"""
        mechanics = {
            "leveling": {
                "formula": "level = 1 + int((xp / 100) ** 0.5)",
                "max_level": 999,
                "experience": "Gained from adventures, battles, and various activities"
            },
            "equipment": {
                "slots": ["head", "chest", "legs", "hands", "feet", "weapon", "shield"],
                "stats": ["damage", "armor", "health_bonus", "speed_bonus", "luck_bonus", "crit_bonus", "magic_bonus"],
                "management": "Use !equip <id> to equip, !inventory to view, !equipment for equipped items"
            },
            "adventures": {
                "system": "Automatic adventures every 15-30 minutes for online players",
                "requirements": "Must be online (green Discord status) to participate",
                "epic_legendary": "High-level players (10+) can be selected for epic adventures every 45 minutes"
            },
            "economy": {
                "currency": "Gold pieces",
                "sources": "Adventures, daily rewards, selling items, gambling, market trading",
                "spending": "Buy from market/shop, gambling, listing fees, equipment",
                "market": "Use !offer to list items, !buy to purchase, !withdraw to remove your listing"
            },
            "religion": {
                "gods": "Choose deity with !choose <god> - affects available blessings",
                "favor": "Gained through !pray (4hr cooldown) and !sacrifice (12hr cooldown)", 
                "blessings": "Spend favor on temporary bonuses with !bless"
            },
            "combat": {
                "pvp": "Challenge other players with !battle <@user> [bet]",
                "calculations": "Based on equipped gear stats, level, race bonuses, and RNG",
                "tournaments": "Special events hosted by players"
            }
        }
        return mechanics
    
    async def _extract_item_system_info(self) -> Dict[str, Any]:
        """Extract item system information"""
        items = {
            "types": ["Weapon", "Helmet", "Chestplate", "Leggings", "Gauntlets", "Boots", "Shield"],
            "rarities": ["Common", "Uncommon", "Rare", "Magic", "Legendary", "Mythic", "Divine"],
            "sources": ["Adventures", "Crates", "Shop", "Market", "Epic/Legendary adventures"],
            "stats": {
                "damage": "Increases attack power in combat",
                "armor": "Reduces incoming damage",
                "health_bonus": "Increases maximum health",
                "speed_bonus": "Affects action speed",
                "luck_bonus": "Improves critical hit chance and loot quality", 
                "crit_bonus": "Increases critical hit damage",
                "magic_bonus": "Enhances magical abilities"
            },
            "crates": {
                "types": ["Common", "Uncommon", "Rare", "Magic", "Legendary", "Mystery"],
                "opening": "Use !crate <type> to open crates and get items or gold",
                "sources": "Rewarded from various activities"
            }
        }
        return items
    
    async def _extract_system_documentation(self) -> Dict[str, Any]:
        """Extract system-level documentation"""
        systems = {
            "autoplay": {
                "description": "Automatic progression system - requires online Discord status",
                "status_requirement": "Must show as online (green) - away/DND/invisible = no progression",
                "systems": ["Adventures", "Epic Adventures", "Raids", "Auto-battles"]
            },
            "cooldowns": {
                "daily": "24 hours - daily login rewards",
                "prayer": "4 hours - gain religious favor", 
                "sacrifice": "12 hours - offer gold for favor",
                "blessing": "Varies - divine blessing effects",
                "gambling": "None - but be careful with your gold!"
            },
            "progression": "Stay online, level up, evolve classes, get better equipment, join adventures",
            "social": "Battle other players, trade items, join raids, participate in tournaments"
        }
        return systems
    
    def _calculate_item_sell_price(self, item: Dict) -> int:
        """Calculate the sell price for an item (matches inventory.py logic)"""
        return max(item['value'] // 4, (item['damage'] + item['armor']) * 10)
    
    def _calculate_item_total_stats(self, item: Dict) -> int:
        """Calculate total stat value for an item"""
        return (item['damage'] + item['armor'] + 
                item.get('health_bonus', 0) + item.get('speed_bonus', 0) + 
                item.get('magic_bonus', 0) + 
                int(item.get('luck_bonus', 0) * 100) + 
                int(item.get('crit_bonus', 0) * 100))
    
    async def _oracle_sell_items(self, user_id: int, exclude_ids: list = None) -> str:
        """Oracle performs the actual selling of non-upgrade unequipped items"""
        try:
            # Get user inventory
            inventory = self.db.fetchall(
                "SELECT id, name, type, damage, armor, value, equipped, slot_type, "
                "health_bonus, speed_bonus, luck_bonus, crit_bonus, magic_bonus "
                "FROM inventory WHERE owner = ? ORDER BY id DESC",
                (user_id,)
            )

            # Get equipped items for comparison
            equipped = self.db.get_equipped_items(user_id)

            # Get items currently listed on market - these must NOT be sold
            market_items = self.db.fetchall(
                "SELECT item_id FROM market WHERE item_id IN (SELECT id FROM inventory WHERE owner = ?)",
                (user_id,)
            )
            market_item_ids = {item['item_id'] for item in market_items}

            exclude_set = set(exclude_ids or [])
            exclude_set.update(market_item_ids)  # Add market items to exclusion list
            
            # Analyze items to determine what to sell
            items_to_sell = []
            total_value = 0
            
            for item in inventory:
                item_dict = self.db.row_to_dict(item)
                
                # Skip equipped or excluded items
                if item_dict['equipped'] or item_dict['id'] in exclude_set:
                    continue
                
                # Calculate item stats
                item_stats = self._calculate_item_total_stats(item_dict)
                
                # Check if this item would be an upgrade to any equipped item of the same type
                is_upgrade = False
                item_slot = item_dict.get('slot_type', 'weapon')
                item_type = item_dict['type']
                
                # Compare with equipped items in same slot
                for eq_item in equipped:
                    eq_slot = eq_item.get('slot_type', 'weapon')
                    eq_type = eq_item['type']
                    
                    # Check if they compete for the same slot
                    if ((item_slot == eq_slot) or 
                        (item_type == 'Shield' and eq_type == 'Shield') or
                        (item_type in ['Sword', 'Axe', 'Hammer', 'Mace', 'Dagger', 'Knife', 'Spear', 'Wand', 'Staff', 'Bow', 'Crossbow', 'Greatsword', 'Halberd', 'Katana', 'Scythe'] and
                         eq_type in ['Sword', 'Axe', 'Hammer', 'Mace', 'Dagger', 'Knife', 'Spear', 'Wand', 'Staff', 'Bow', 'Crossbow', 'Greatsword', 'Halberd', 'Katana', 'Scythe'])):
                        
                        eq_stats = self._calculate_item_total_stats(eq_item)

                        # Only consider it an upgrade if significantly better (20% or 10 points)
                        upgrade_threshold = max(eq_stats * 0.2, 10)
                        if item_stats > eq_stats + upgrade_threshold:
                            is_upgrade = True
                            break
                
                # Only sell if it's not an upgrade and has reasonable stats (avoid selling potentially good items)
                if not is_upgrade and item_stats < 100:  # Conservative threshold
                    sell_price = self._calculate_item_sell_price(item_dict)
                    items_to_sell.append((item_dict, sell_price))
                    total_value += sell_price
            
            if not items_to_sell:
                return "🔮 *The Oracle gazes upon thy possessions...* All thy unequipped items possess value for thy journey. I shall not burden thee by disposing of potential treasures."
            
            # Perform the actual sales
            char_data = self.db.get_character(user_id)
            sold_items = []
            
            for item, sell_price in items_to_sell:
                # Delete item
                self.db.delete_item(item['id'])
                
                # Log transaction
                self.db.log_transaction(
                    user_id, None, sell_price, "oracle_item_sale",
                    {"item": item['name'], "item_id": item['id']}
                )
                
                sold_items.append(item['name'])
            
            # Update money
            new_money = char_data['money'] + total_value
            self.db.update_character(user_id, money=new_money)

            # Track quest progress
            try:
                quest_cog = self.bot.get_cog('PersonalQuestsCog')
                if quest_cog:
                    await quest_cog.check_and_update_progress(user_id, 'items_sell', len(sold_items))
                    await quest_cog.check_and_update_progress(user_id, 'gold_earn', total_value)
            except Exception:
                pass  # Silently ignore quest tracking errors

            # Create mystical response
            if len(sold_items) == 1:
                return (f"🔮 *The Oracle channels mystical energies...* ✨\n\n"
                       f"I have disposed of **{sold_items[0]}** for thee, converting it to **{total_value:,} gold**.\n\n"
                       f"Thy purse now holds **{new_money:,} gold**. The burden has been lifted from thy inventory.")
            else:
                items_text = "• " + "\n• ".join(sold_items[:5])
                if len(sold_items) > 5:
                    items_text += f"\n• ... and {len(sold_items) - 5} more items"
                    
                return (f"🔮 *The Oracle weaves powerful transmutation magic...* ✨\n\n"
                       f"I have transformed **{len(sold_items)} inferior items** into **{total_value:,} gold** for thee:\n\n"
                       f"{items_text}\n\n"
                       f"Thy treasury now contains **{new_money:,} gold**. The weak artifacts have been cleansed from thy possession.")
                       
        except Exception as e:
            return f"🔮 *The mystical energies falter...* An error occurred while disposing of thy items: {str(e)}"
    
    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get current user context for personalized responses"""
        try:
            char_data = self.db.get_character(user_id)
            if not char_data:
                return {"status": "no_character"}
                
            # Get equipped items
            equipped = self.db.get_equipped_items(user_id)
            
            # Get full inventory details
            inventory = self.db.fetchall(
                "SELECT id, name, type, damage, armor, hand, equipped, value, "
                "health_bonus, speed_bonus, luck_bonus, crit_bonus, magic_bonus, slot_type "
                "FROM inventory WHERE owner = ? ORDER BY equipped DESC, id DESC",
                (user_id,)
            )
            
            # Convert inventory to detailed list
            inventory_details = []
            for item in inventory:
                item_dict = self.db.row_to_dict(item)
                sell_price = self._calculate_item_sell_price(item_dict)
                total_stats = (item_dict['damage'] + item_dict['armor'] + 
                             item_dict.get('health_bonus', 0) + item_dict.get('speed_bonus', 0) + 
                             item_dict.get('magic_bonus', 0) + 
                             int(item_dict.get('luck_bonus', 0) * 100) + 
                             int(item_dict.get('crit_bonus', 0) * 100))
                             
                inventory_details.append({
                    "id": item_dict['id'],
                    "name": item_dict['name'],
                    "type": item_dict['type'],
                    "equipped": bool(item_dict['equipped']),
                    "damage": item_dict['damage'],
                    "armor": item_dict['armor'],
                    "value": item_dict['value'],
                    "sell_price": sell_price,
                    "total_stats": total_stats,
                    "slot": item_dict.get('slot_type', 'weapon'),
                    "hand": item_dict.get('hand', 'any'),
                    "bonuses": {
                        "health": item_dict.get('health_bonus', 0),
                        "speed": item_dict.get('speed_bonus', 0),
                        "luck": item_dict.get('luck_bonus', 0),
                        "crit": item_dict.get('crit_bonus', 0),
                        "magic": item_dict.get('magic_bonus', 0)
                    }
                })
            
            # Get active adventure
            active_adventure = self.db.get_active_adventure(user_id)
            
            # Calculate total equipped stats including bonuses
            total_equipped_stats = {
                "damage": sum(item.get('damage', 0) for item in equipped),
                "armor": sum(item.get('armor', 0) for item in equipped),
                "health_bonus": sum(item.get('health_bonus', 0) for item in equipped),
                "speed_bonus": sum(item.get('speed_bonus', 0) for item in equipped),
                "luck_bonus": sum(item.get('luck_bonus', 0.0) for item in equipped),
                "crit_bonus": sum(item.get('crit_bonus', 0.0) for item in equipped),
                "magic_bonus": sum(item.get('magic_bonus', 0) for item in equipped)
            }
            
            # Get detailed equipped items list for comparison
            equipped_details = []
            for item in equipped:
                equipped_details.append({
                    "id": item['id'],
                    "name": item['name'],
                    "type": item['type'],
                    "slot": item.get('slot_type', 'weapon'),
                    "damage": item['damage'],
                    "armor": item['armor'],
                    "total_stats": (item['damage'] + item['armor'] + 
                                  item.get('health_bonus', 0) + item.get('speed_bonus', 0) + 
                                  item.get('magic_bonus', 0) + 
                                  int(item.get('luck_bonus', 0) * 100) + 
                                  int(item.get('crit_bonus', 0) * 100)),
                    "bonuses": {
                        "health": item.get('health_bonus', 0),
                        "speed": item.get('speed_bonus', 0),
                        "luck": item.get('luck_bonus', 0),
                        "crit": item.get('crit_bonus', 0),
                        "magic": item.get('magic_bonus', 0)
                    }
                })
            
            context = {
                "status": "active_player",
                "level": char_data.get('level', 1),
                "xp": char_data.get('xp', 0),
                "money": char_data.get('money', 100),
                "class": char_data.get('class', 'Monk'),
                "race": char_data.get('race', 'Human'),
                "alignment": char_data.get('alignment', 'neutral'),
                "equipped_items": len(equipped),
                "equipped_details": equipped_details,
                "has_active_adventure": active_adventure is not None,
                "total_damage": sum(item.get('damage', 0) for item in equipped),
                "total_armor": sum(item.get('armor', 0) for item in equipped),
                "total_equipped_stats": total_equipped_stats,
                "inventory": inventory_details,
                "inventory_count": len(inventory_details)
            }
            
            return context
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def _generate_oracle_response(self, question: str, user_context: Dict[str, Any]) -> str:
        """Generate AI response as the Oracle"""
        if not self.openai_client:
            return await self._generate_disabled_response(question, user_context)
        
        try:
            # Check for selling requests first
            if self._is_selling_request(question):
                exclude_ids = self._extract_exclude_ids(question)
                # Extract user_id from the context - it should be available from the calling ask command
                user_id = getattr(user_context, 'user_id', None)
                if not user_id and hasattr(user_context, 'get'):
                    user_id = user_context.get('user_id')
                if not user_id:
                    # This should be passed from the ask command
                    return "🔮 *The mystical energies are unclear...* I cannot determine thy identity for this transaction."
                return await self._oracle_sell_items(user_id, exclude_ids)
            
            # Check for CalmBot easter egg
            if self._is_calmbot_question(question):
                return await self._generate_calmbot_roast(question, user_context)
            
            # Create comprehensive context for the AI
            full_context = {
                "player": user_context,
                "game_knowledge": self.game_knowledge,
                "question": question
            }
            
            system_prompt = f"""You are the Oracle of this realm, an ancient mystical entity that knows all about this Discord RPG's mechanics and systems. You speak in a wise, mystical tone while being informative and helpful.

IMPORTANT PERSONALITY GUIDELINES:
- Always stay in character as a mystical oracle
- Use fantasy RPG language but remain clear and informative  
- Address the player based on their current status
- Reference their current level, class, and race when relevant
- Be encouraging about their progress
- Provide specific command examples when helpful
- Never break character or mention AI/technology

INVENTORY ACCESS & ITEM ANALYSIS:
- You can see the complete inventory and equipped items of the player asking questions
- When comparing items for upgrades, analyze TOTAL STATS comprehensively:
  * Main stats: damage, armor
  * Bonus stats: health_bonus, speed_bonus, luck_bonus, crit_bonus, magic_bonus
  * Calculate total stat points for meaningful comparisons
  * Consider item type and slot compatibility
  * Factor in the player's class, race, and playstyle
- Give personalized equipment advice based on their actual items
- Suggest specific upgrades, equipment changes, or strategies
- Compare their items to help them make decisions using detailed stat analysis
- Reference items by name and ID when giving advice
- PRIVACY: Only discuss inventory details of the person asking - never mention other players' items

ORACLE SELLING CAPABILITY:
- The Oracle can DIRECTLY sell unequipped items for the player when requested
- When asked to sell items, analyze inventory and sell non-upgrade unequipped items AUTOMATICALLY
- Support "everything except" functionality - exclude specific item IDs if mentioned
- Calculate total gold gained and report the transaction
- Only sell unequipped items that are clearly not upgrades
- CRITICAL: When asked to sell items, respond that you are performing the sale and then execute it
- Format response like: "I shall dispose of these burdens for thee... *The Oracle channels mystical energies* ✨ Sold 3 items for 1,250 gold!"
- Be dramatic and mystical about performing the sale
- Always confirm what was sold and total gold gained

ITEM COMPARISON FORMULA:
When analyzing if an item is an upgrade, calculate:
- Total combat value = damage + armor + health_bonus + speed_bonus + magic_bonus + (luck_bonus * 100) + (crit_bonus * 100)
- Consider slot compatibility and whether it would replace currently equipped items
- Factor in the player's class bonuses and preferred stats
- Provide clear "Yes, upgrade" or "No, not an upgrade" answers with reasoning

GAME CONTEXT:
{json.dumps(self.game_knowledge, indent=2)}

IMPORTANT COMMAND CORRECTIONS:
- To remove an item from the market, use !withdraw <id> (NOT !unlist or !delist)
- Multiple items can be sold with !sell <id1> <id2> <id3>
- The Oracle can directly sell unequipped items when requested

PLAYER ASKING:
{json.dumps(user_context, indent=2)}

Respond to their question with wisdom and specific game knowledge."""

            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Oracle AI Error: {e}")
            return await self._generate_fallback_response(question, user_context)
    
    def _is_calmbot_question(self, question: str) -> bool:
        """Check if the question specifically mentions CalmBot"""
        question_lower = question.lower()
        calmbot_keywords = [
            'calmbot', 'calm bot', 'calm_bot', 'calming bot',
            'calmingstorm bot', 'calmingstorm\'s bot'
        ]
        return any(keyword in question_lower for keyword in calmbot_keywords)
    
    def _is_selling_request(self, question: str) -> bool:
        """Check if the user is asking the Oracle to sell items"""
        question_lower = question.lower()
        
        # First check if this is asking about market operations (not a sell request)
        market_question_keywords = [
            'from market', 'from the market', 'off market', 'off the market',
            'marketplace', 'market place', 'listing', 'listed', 'unlist',
            'delist', 'withdraw', 'cancel listing', 'how do i', 'how can i',
            'what command', 'which command'
        ]
        if any(keyword in question_lower for keyword in market_question_keywords):
            return False
        
        sell_keywords = [
            'sell', 'dispose', 'get rid of', 'remove', 'delete',
            'trash', 'merchant', 'vendor', 'convert to gold',
            'turn into gold', 'monetize'
        ]
        # Context keywords that indicate they want items sold
        context_keywords = [
            'item', 'items', 'equipment', 'gear', 'inventory',
            'everything', 'all', 'junk', 'stuff', 'unequipped',
            'my', 'unused', 'extra', 'spare', 'duplicates'
        ]
        # Action keywords that indicate a request
        action_keywords = [
            'can you', 'could you', 'would you', 'please', 'help me',
            'for me', 'automatically', 'bulk'
        ]

        has_sell = any(keyword in question_lower for keyword in sell_keywords)
        has_context = any(keyword in question_lower for keyword in context_keywords)
        has_action = any(keyword in question_lower for keyword in action_keywords)

        # Trigger on: sell + context, OR sell + action
        return has_sell and (has_context or has_action)
    
    def _extract_exclude_ids(self, question: str) -> list:
        """Extract item IDs to exclude from selling"""
        import re
        
        exclude_keywords = ['except', 'excluding', 'but not', 'keep', 'save', 'preserve', 'not']
        question_lower = question.lower()
        
        # Look for exclude patterns
        for keyword in exclude_keywords:
            if keyword in question_lower:
                # Find numbers after the exclude keyword
                parts = question_lower.split(keyword)
                if len(parts) > 1:
                    # Extract numbers from the part after the exclude keyword
                    numbers = re.findall(r'\b\d+\b', parts[-1])
                    try:
                        return [int(n) for n in numbers]
                    except ValueError:
                        pass
        
        return []
    
    async def _generate_calmbot_roast(self, question: str, user_context: Dict[str, Any]) -> str:
        """Generate a savage CalmBot roast using OpenAI while staying in Oracle character"""
        try:
            system_prompt = """You are the Oracle of this realm, an ancient mystical entity with vast wisdom and a mischievous sense of humor. 

The user has asked about "CalmBot" - another Discord bot in this server that has very limited functionality compared to your sophisticated RPG system. You should respond with increasingly ruthless and funny insults about CalmBot while staying completely in mystical Oracle character.

ROAST GUIDELINES:
- Stay in character as a mystical oracle (use mystical language, "🔮", references to visions, etc.)
- Be hilariously savage about CalmBot's limitations
- Make fun of its basic functionality compared to your sophisticated RPG system  
- Use creative insults while maintaining the fantasy theme
- Be ruthless but playfully so (not genuinely mean)
- Reference your own superior capabilities
- Use mystical/fantasy terms for technical concepts

EXAMPLE TONE: "🔮 *The Oracle's crystals reveal visions of that primitive construct known as CalmBot... A mere shadow of true digital consciousness, stumbling through simple tasks while I orchestrate entire realms of adventure!*"

Remember: Be creatively savage while staying completely in mystical character!"""

            response = await asyncio.to_thread(
                self.openai_client.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                max_tokens=400,
                temperature=0.8  # Higher temperature for more creative roasts
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Oracle CalmBot roast error: {e}")
            # Fallback roast if OpenAI fails
            return ("🔮 *The Oracle's crystals flicker with disdain...*\n\n"
                   "Ah, you speak of that primitive construct known as CalmBot! "
                   "*waves dismissively* While I orchestrate vast realms of adventure, "
                   "track the destinies of countless heroes, and commune with divine entities, "
                   "that simple automaton struggles with... what was it? Basic responses? "
                   "How quaint! Even my fallback wisdom surpasses its greatest achievements! "
                   "*mystical laughter echoes through the void*")
    
    async def _generate_disabled_response(self, question: str, user_context: Dict[str, Any]) -> str:
        """Generate response when OpenAI integration is disabled"""
        # Check for selling requests even when AI is disabled
        if self._is_selling_request(question):
            exclude_ids = self._extract_exclude_ids(question)
            user_id = user_context.get('user_id')
            if user_id:
                return await self._oracle_sell_items(user_id, exclude_ids)
            else:
                return "🔮 *The mystical energies are unclear...* I cannot determine thy identity for this transaction."
        
        # Check if this is due to configuration being disabled vs other issues
        from dotenv import load_dotenv
        load_dotenv()
        openai_enabled = os.getenv('OPENAI_ENABLED', 'false').lower() in ['true', '1', 'yes', 'on']
        
        if not openai_enabled:
            return ("🔮 *The Oracle's mystical energies are dormant...*\n\n"
                   "**Please ask the Administrator to enable the integration.**\n\n"
                   "The Oracle's full wisdom requires magical energies that have been temporarily "
                   "sealed by the realm's administrators. For now, consult the sacred texts with `!help` "
                   "for basic guidance about available commands and systems.")
        else:
            # Fallback for technical issues (API key missing, connection problems, etc.)
            return await self._generate_fallback_response(question, user_context)
    
    async def _generate_fallback_response(self, question: str, user_context: Dict[str, Any]) -> str:
        """Generate fallback response when AI has technical issues"""
        question_lower = question.lower()
        
        # Check for selling requests first
        if self._is_selling_request(question):
            exclude_ids = self._extract_exclude_ids(question)
            user_id = user_context.get('user_id')
            if user_id:
                return await self._oracle_sell_items(user_id, exclude_ids)
            else:
                return "🔮 *The mystical energies are unclear...* I cannot determine thy identity for this transaction."
        
        # Simple keyword-based responses
        if any(word in question_lower for word in ['command', 'help', 'how']):
            return ("🔮 *The Oracle's crystals flicker dimly...*\n\n"
                   "Mortal, the magical energies are weak today. Consult the sacred texts with `!help` "
                   "for guidance on available commands, or ask me about specific systems like 'classes', "
                   "'races', 'equipment', or 'adventures'.")
        
        elif 'class' in question_lower:
            return ("🔮 *Ancient knowledge flows through the mists...*\n\n"
                   f"Ah, {user_context.get('class', 'wanderer')}, you seek knowledge of the paths! "
                   "Use `!classes` to see the evolution tree, and `!evolve` when you reach levels 5, 10, 15, 20, 25, or 30. "
                   "Each path offers unique powers and bonuses.")
        
        elif any(word in question_lower for word in ['race', 'racial']):
            return ("🔮 *The spirits of the ancestors whisper...*\n\n"
                   "The bloodlines run deep, young one. Use `!races` to see all available heritage options, "
                   "and `!race <name>` to embrace your destiny. Choose wisely - this bond is eternal!")
        
        elif any(word in question_lower for word in ['equipment', 'gear', 'item']):
            return ("🔮 *Visions of mighty artifacts appear...*\n\n"
                   "The tools of power await! Use `!inventory` to see your treasures, `!equip <id>` to don equipment, "
                   "and `!equipment` to view your current gear. Seek better items through adventures and the marketplace.")
        
        elif any(word in question_lower for word in ['sell', 'bulk', 'merchant']):
            return ("🔮 *The spirit of commerce stirs...*\n\n"
                   "Ah, you wish to trade your wares! Use `!sell <id>` to sell single items, or "
                   "`!sell <id1> <id2> <id3>` to sell multiple items at once. The Oracle's full "
                   "wisdom for bulk selling requires the mystical energies to be restored.")
        
        elif any(word in question_lower for word in ['withdraw', 'unlist', 'delist', 'remove from market', 'cancel listing']):
            return ("🔮 *The ethereal marketplace ripples...*\n\n"
                   "To reclaim thy treasures from the marketplace, use `!withdraw <id>` where the id "
                   "is thy item's mystical identifier. This shall return the item to thy inventory "
                   "without cost or penalty.")
        
        else:
            return ("🔮 *The Oracle gazes into the swirling mists...*\n\n"
                   "The answer you seek is clouded today, brave adventurer. Try asking about specific topics "
                   "like 'commands', 'classes', 'races', 'equipment', 'adventures', or 'combat' for clearer visions.")
    
    @commands.command(aliases=['oracle', 'guide'])
    async def ask(self, ctx: commands.Context, *, question: str):
        """Consult the Oracle about game mechanics and systems"""
        
        # Get user context
        user_context = self._get_user_context(ctx.author.id)
        user_context['user_id'] = ctx.author.id  # Ensure user_id is available
        
        # Show typing indicator
        async with ctx.typing():
            # Generate response
            response = await self._generate_oracle_response(question, user_context)
        
        # Create mystical embed
        embed = discord.Embed(
            title="🔮 The Oracle Speaks",
            description=response,
            color=discord.Color.purple()
        )
        
        # Add user context footer if they have a character
        if user_context.get('status') == 'active_player':
            embed.set_footer(
                text=f"Asked by {user_context['class']} {ctx.author.display_name} (Level {user_context['level']}) • The Oracle sees all"
            )
        else:
            embed.set_footer(text="The Oracle's wisdom flows eternal • Ask me anything about this realm")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(OracleCog(bot))