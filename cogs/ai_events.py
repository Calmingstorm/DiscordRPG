"""AI Dynamic Event Generation - Unique events powered by OpenAI"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from classes.items import ItemGenerator, ItemType, ItemRarity

# Import OpenAI safely
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger('DiscordRPG.AIEvents')

class AIEventsCog(DiscordRPGCog):
    """Dynamic AI-generated events with rewards and boss fights - runs parallel to existing systems"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.openai_client = None
        self.active_events = {}
        self.openai_enabled = False
        self._initialize_openai()
        
    def _initialize_openai(self):
        """Initialize OpenAI client if available and configured"""
        if not OPENAI_AVAILABLE:
            logger.info("OpenAI package not available. AI events will not run.")
            return
            
        # Load configuration from environment
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check if OpenAI integration is enabled
        self.openai_enabled = os.getenv('OPENAI_ENABLED', 'false').lower() in ['true', '1', 'yes', 'on']
        
        if not self.openai_enabled:
            logger.info("OpenAI integration is disabled - AI events will not run")
            logger.info("Set OPENAI_ENABLED=true in .env to enable AI events")
            return
            
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            self.openai_enabled = False
            return
            
        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI client initialized for AI events")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_enabled = False

    async def cog_load(self):
        """Start AI events if OpenAI is enabled"""
        if self.openai_enabled and not self.ai_event_generator.is_running():
            self.ai_event_generator.start()
            logger.info("🎲 AI Event Generator started")
        else:
            logger.info("🎲 AI Event Generator disabled - OpenAI not available")
            
    async def cog_unload(self):
        """Stop the AI event generator"""
        if self.ai_event_generator.is_running():
            self.ai_event_generator.cancel()
            logger.info("🎲 AI Event Generator stopped")

    def is_user_online(self, user: discord.User) -> bool:
        """Check if user is online (green status) in any guild"""
        for guild in self.bot.guilds:
            member = guild.get_member(user.id)
            if member and member.status == discord.Status.online:
                return True
        return False

    async def get_online_players(self, min_level: int = 1, max_players: int = 20) -> List[Dict]:
        """Get online players eligible for events"""
        online_players = []
        
        # Get all character IDs
        all_chars = self.db.fetchall("SELECT user_id, name, level FROM profile WHERE level >= ?", (min_level,))
        
        for char in all_chars:
            user = self.bot.get_user(char['user_id'])
            if user and self.is_user_online(user):
                # Check if not in adventure or epic adventure
                active_adventure = self.db.fetchone(
                    "SELECT id FROM adventures WHERE user_id = ? AND status = 'active'",
                    (char['user_id'],)
                )
                active_epic = self.db.fetchone(
                    "SELECT id FROM epic_adventures WHERE user_id = ? AND status = 'active'",
                    (char['user_id'],)
                )
                
                # Players can participate in AI events even if on adventures (parallel system)
                online_players.append({
                    'user_id': char['user_id'],
                    'name': char['name'],
                    'level': char['level'],
                    'user': user
                })
                
                if len(online_players) >= max_players:
                    break
                    
        return online_players

    async def generate_ai_content(self, event_type: str, participants: List[Dict]) -> Dict:
        """Generate AI event content or fallback to templates"""
        if not self.openai_client or not self.openai_enabled:
            return self._get_fallback_event(event_type, participants)
            
        try:
            # Build context
            participant_info = []
            for p in participants[:5]:  # Limit context size
                participant_info.append(f"- {p['name']} (Level {p['level']})")
            
            participant_text = "\n".join(participant_info)
            if len(participants) > 5:
                participant_text += f"\n- ...and {len(participants)-5} more adventurers"
            
            # Event-specific prompts
            system_prompts = {
                'treasure': "You are creating a treasure discovery event for a Discord RPG. Create a short (2-3 sentences) fantasy scenario where adventurers discover treasure. Include the event title and description. Be family-friendly, exciting, and fantasy-themed.",
                'mini_boss': "You are creating a mini boss fight for a Discord RPG. Create a fantasy boss with a name, short description, and a few taunting phrases. Keep it family-friendly, exciting, and under 200 words total.",
                'world_event': "You are creating a server-wide crisis event for a Discord RPG. Create a short fantasy scenario that threatens everyone and requires group cooperation. Keep it family-friendly and under 150 words.",
                'mystery': "You are creating a unique mystery event for a Discord RPG. Create something unusual and magical that adventurers might encounter. Keep it family-friendly, intriguing, and under 150 words."
            }
            
            user_prompt = f"""Create a {event_type} event for these participants:
{participant_text}

IMPORTANT: Return ONLY valid JSON in this exact format:
{{
  "title": "Short event title (under 40 chars)",
  "description": "Event description in 2-3 sentences",
  "special": "Any special dialogue or mechanics",
  "rewards_flavor": "How rewards should be described",
  "item_names": ["Name1", "Name2", "Name3", "Name4", "Name5"]
}}

Requirements:
- Fantasy themed, family-friendly
- Item names should match the event theme
- Keep title under 40 characters
- No code blocks, just raw JSON"""

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompts.get(event_type, system_prompts['treasure'])},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=300,
                    temperature=0.8
                )
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"AI Response: {content[:200]}...")  # Log first 200 chars for debugging
            
            # Try to parse JSON, fallback to text parsing
            try:
                # First try direct JSON parsing
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Direct JSON parsing failed: {e}")
                # Try to extract JSON from code blocks
                try:
                    # Look for JSON within ```json blocks
                    if '```json' in content:
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        json_content = content[json_start:json_end].strip()
                        return json.loads(json_content)
                    
                    # Try to find JSON-like content
                    if '{' in content and '}' in content:
                        start = content.find('{')
                        end = content.rfind('}') + 1
                        json_content = content[start:end]
                        
                        # Fix common JSON issues
                        # Fix unquoted keys
                        json_content = json_content.replace('title:', '"title":').replace('description:', '"description":')
                        json_content = json_content.replace('special:', '"special":').replace('rewards_flavor:', '"rewards_flavor":')
                        json_content = json_content.replace('item_names:', '"item_names":')
                        
                        # Fix trailing commas
                        json_content = json_content.replace(',}', '}').replace(',]', ']')
                        
                        # Fix single quotes
                        json_content = json_content.replace("'", '"')
                        
                        logger.info(f"Cleaned JSON: {json_content}")
                        return json.loads(json_content)
                        
                except:
                    pass
                
                # Final fallback: extract content manually
                lines = content.split('\n')
                title = lines[0].replace('"', '').replace('Title:', '').replace('title:', '').strip()
                if title.startswith('{'):
                    title = title[1:].strip()
                
                description = ' '.join(lines[1:3]).replace('"', '').replace('Description:', '').strip()
                
                return {
                    "title": title[:40] if title and len(title) > 5 else f"Mysterious {event_type.title()}",
                    "description": description if description and len(description) > 10 else f"A {event_type} event has begun!",
                    "special": "",
                    "rewards_flavor": "treasure",
                    "item_names": ["Mysterious Artifact", "Unknown Relic", "Strange Weapon", "Mystical Item", "Enchanted Gear"]
                }
                
        except Exception as e:
            logger.warning(f"AI generation failed: {e}")
            return self._get_fallback_event(event_type, participants)

    def _get_fallback_event(self, event_type: str, participants: List[Dict]) -> Dict:
        """Fallback event templates when AI is unavailable"""
        fallback_events = {
            'treasure': [
                {"title": "🏺 Ancient Ruins Discovered", "description": "Crumbling ruins have emerged from the mists, containing forgotten treasures waiting to be claimed!", "special": "", "rewards_flavor": "ancient relics", "item_names": ["Ruined Blade", "Ancient Circlet", "Forgotten Shield", "Dusty Grimoire", "Stone Gauntlets"]},
                {"title": "💰 Merchant Caravan Attack", "description": "Bandits have attacked a merchant caravan! Brave adventurers can claim the scattered treasure.", "special": "", "rewards_flavor": "merchant goods", "item_names": ["Trader's Blade", "Silk Cloak", "Merchant's Staff", "Caravan Shield", "Golden Dagger"]},
                {"title": "🌟 Fallen Star Fragment", "description": "A star has fallen from the heavens, leaving behind magical crystals and celestial treasures!", "special": "", "rewards_flavor": "celestial artifacts", "item_names": ["Starfall Sword", "Cosmic Shield", "Celestial Robes", "Meteor Hammer", "Stardust Wand"]}
            ],
            'mini_boss': [
                {"title": "⚔️ The Iron Golem Awakens", "description": "An ancient iron golem has stirred to life, challenging any who dare approach its domain!", "special": "'INTRUDERS WILL BE CRUSHED!' - Iron Golem", "rewards_flavor": "metallic treasures", "item_names": ["Iron-Forged Blade", "Golem's Gauntlets", "Molten Core Shield", "Construct Hammer", "Steel-Heart Armor"]},
                {"title": "🐉 Wyrmling's Fury", "description": "A young dragon demands tribute from passing adventurers. Will you pay... or fight?", "special": "'Your gold or your life, mortals!' - Young Dragon", "rewards_flavor": "draconic hoard", "item_names": ["Wyrmling Claw", "Dragonscale Vest", "Flame-Touched Sword", "Dragon's Tooth Dagger", "Scale-Mail Boots"]},
                {"title": "👻 Spectral Guardian", "description": "The ghost of a fallen knight blocks the path, seeking worthy opponents to test their mettle.", "special": "'Face me, if you dare!' - Spectral Knight", "rewards_flavor": "spectral weapons", "item_names": ["Ghostly Blade", "Phantom Armor", "Soul-Touched Shield", "Ethereal Helm", "Wraith Cloak"]}
            ],
            'world_event': [
                {"title": "🌪️ Chaos Storms Brewing", "description": "Dark magic swirls across the realm, threatening all in its path! Unite to dispel the growing darkness.", "special": "", "rewards_flavor": "storm-touched items", "item_names": ["Stormcaller Staff", "Thunder Cloak", "Lightning Blade", "Wind-Walker Boots", "Storm Crown"]},
                {"title": "👑 The King's Call", "description": "The royal herald announces a grand tournament! All skilled adventurers are called to prove their worth.", "special": "", "rewards_flavor": "royal rewards", "item_names": ["Royal Blade", "Crown Guard Shield", "Noble's Cloak", "Ceremonial Mace", "Regent's Gauntlets"]},
                {"title": "🔮 Magical Convergence", "description": "The ley lines are surging with power! Magical energies offer great rewards to those brave enough to harness them.", "special": "", "rewards_flavor": "enchanted items", "item_names": ["Ley-Line Staff", "Mana-Woven Robes", "Arcane Focus", "Mystic Circlet", "Power Crystal Blade"]}
            ],
            'mystery': [
                {"title": "❓ The Wandering Portal", "description": "A mysterious portal has appeared, leading to unknown realms. What lies beyond?", "special": "", "rewards_flavor": "otherworldly items", "item_names": ["Voidwalker Blade", "Dimensional Cloak", "Portal-Touched Staff", "Planar Shield", "Reality Ripper"]},
                {"title": "🎭 The Enigmatic Stranger", "description": "A hooded figure offers cryptic challenges and mysterious rewards to worthy adventurers.", "special": "", "rewards_flavor": "mysterious gifts", "item_names": ["Stranger's Gift", "Enigma Blade", "Riddle-Wrapped Cloak", "Mystery Box Shield", "Cryptic Wand"]},
                {"title": "📜 Ancient Prophecy", "description": "An old prophecy stirs, foretelling great rewards for those who can decipher its meaning.", "special": "", "rewards_flavor": "prophetic items", "item_names": ["Prophet's Blade", "Seer's Circlet", "Oracle Staff", "Vision Shield", "Fate-Bound Armor"]}
            ]
        }
        
        return random.choice(fallback_events.get(event_type, fallback_events['treasure']))

    def create_item_in_db(self, item) -> int:
        """Helper to create items with all stats in database"""
        return self.db.create_item(
            item.owner_id, item.name, item.type.value,
            item.value, item.damage, item.armor, item.hand.value,
            item.health_bonus, item.speed_bonus, item.luck_bonus,
            item.crit_bonus, item.magic_bonus, item.slot_type
        )

    async def execute_treasure_event(self, event_data: Dict, participants: List[Dict]) -> Dict:
        """Execute treasure event with random rewards"""
        rewards = []
        
        # Determine number of winners (30-60% of participants)
        num_winners = max(1, int(len(participants) * random.uniform(0.3, 0.6)))
        winners = random.sample(participants, min(num_winners, len(participants)))
        
        for winner in winners:
            # Generate rewards based on level
            level = winner['level']
            
            # Base XP and gold
            base_xp = random.randint(50 * level, 100 * level)
            base_gold = random.randint(100 * level, 300 * level)
            
            # Get race multipliers
            from cogs.race import RaceCog
            race_multipliers = RaceCog.get_race_multipliers(winner['user_id'])
            
            # Get divine blessing bonuses
            from cogs.religion import ReligionCog
            religion_cog = self.bot.get_cog('ReligionCog')
            if religion_cog:
                blessing_bonuses = religion_cog.get_active_blessings(winner['user_id'])
                race_multipliers['xp_gain'] *= blessing_bonuses['xp_mult']
                race_multipliers['gold_find'] *= blessing_bonuses['gold_mult']
            
            # Apply multipliers
            final_xp = int(base_xp * race_multipliers['xp_gain'])
            final_gold = int(base_gold * race_multipliers['gold_find'])
            
            # Chance for item (30% chance - same as regular battles)
            item_found = None
            if random.random() < 0.3:
                # Small chance (5%) for exceptional treasure items
                if random.random() < 0.05:
                    # Exceptional items - comparable to low-tier epic adventure rewards
                    min_quality = max(8, level + 3)   # Higher quality
                    max_quality = min(25, level + 12) # Cap at reasonable level, max 25 stats
                    item_found = ItemGenerator.generate_random_equipment(
                        winner['user_id'], min_quality, max_quality
                    )
                else:
                    # Regular quality - same as autoplay battles
                    min_quality = max(4, level + 1)  # Minimum 4 stats, level-appropriate
                    max_quality = level + 6          # Same range as adventure rewards
                    item_found = ItemGenerator.generate_random_equipment(
                        winner['user_id'], min_quality, max_quality
                    )
                
                # Use AI-generated item names
                if 'item_names' in event_data and event_data['item_names']:
                    item_found.name = random.choice(event_data['item_names'])
                else:
                    # Fallback to generic name
                    item_found.name = f"Treasure {item_found.name}"
                
                self.create_item_in_db(item_found)
            
            # Update character
            char_data = self.db.get_character(winner['user_id'])
            new_xp = char_data['xp'] + final_xp
            new_gold = char_data['money'] + final_gold
            new_level = min(50, 1 + int((new_xp / 100) ** 0.5))
            
            self.db.update_character(
                winner['user_id'],
                xp=new_xp,
                money=new_gold,
                level=new_level
            )
            
            rewards.append({
                'user_id': winner['user_id'],
                'name': winner['name'],
                'xp': final_xp,
                'gold': final_gold,
                'item': item_found.name if item_found else None,
                'leveled_up': new_level > char_data['level']
            })
        
        return {
            'type': 'treasure',
            'event_data': event_data,
            'participants': participants,
            'winners': rewards
        }

    async def execute_mini_boss_event(self, event_data: Dict, participants: List[Dict]) -> Dict:
        """Execute mini boss fight event"""
        # Create a virtual boss based on participant levels
        avg_level = sum(p['level'] for p in participants) / len(participants)
        boss_power = int(avg_level * len(participants) * 1.2)  # Boss is 20% stronger than group
        
        # Calculate group power
        group_power = 0
        for participant in participants:
            char_data = self.db.get_character(participant['user_id'])
            
            # Basic power calculation (simplified from combat.py)
            base_power = char_data['level'] * 5
            
            # Get equipped items for bonus power
            equipped_items = self.db.fetchall(
                "SELECT damage, armor, health_bonus, magic_bonus FROM inventory WHERE owner = ? AND equipped = 1",
                (participant['user_id'],)
            )
            
            equipment_power = 0
            for item in equipped_items:
                equipment_power += (item.get('damage', 0) + item.get('armor', 0) + 
                                  item.get('health_bonus', 0) + item.get('magic_bonus', 0))
            
            participant_power = base_power + equipment_power
            group_power += participant_power
        
        # Determine battle outcome
        success_chance = min(0.9, group_power / boss_power)  # Cap at 90%
        success = random.random() < success_chance
        
        # Distribute rewards
        rewards = []
        for participant in participants:
            if success:
                # Victory rewards (higher)
                base_xp = random.randint(100 * participant['level'], 200 * participant['level'])
                base_gold = random.randint(200 * participant['level'], 500 * participant['level'])
                item_chance = 0.6  # 60% chance for item
            else:
                # Defeat rewards (consolation)
                base_xp = random.randint(30 * participant['level'], 60 * participant['level'])
                base_gold = random.randint(50 * participant['level'], 150 * participant['level'])
                item_chance = 0.2  # 20% chance for item
            
            # Apply multipliers (same as treasure event)
            from cogs.race import RaceCog
            race_multipliers = RaceCog.get_race_multipliers(participant['user_id'])
            
            from cogs.religion import ReligionCog
            religion_cog = self.bot.get_cog('ReligionCog')
            if religion_cog:
                blessing_bonuses = religion_cog.get_active_blessings(participant['user_id'])
                race_multipliers['xp_gain'] *= blessing_bonuses['xp_mult']
                race_multipliers['gold_find'] *= blessing_bonuses['gold_mult']
            
            final_xp = int(base_xp * race_multipliers['xp_gain'])
            final_gold = int(base_gold * race_multipliers['gold_find'])
            
            # Generate item if won
            item_found = None
            if random.random() < item_chance:
                # Small chance (10%) for legendary boss items on victory
                if success and random.random() < 0.1:
                    # Legendary boss items - comparable to mid-tier epic adventures
                    min_quality = max(10, participant['level'] + 4)  # Higher quality
                    max_quality = min(30, participant['level'] + 15) # Cap at 30 stats
                    item_found = ItemGenerator.generate_random_equipment(
                        participant['user_id'], min_quality, max_quality
                    )
                elif success:
                    # Victory items - slightly better than regular battles
                    min_quality = max(4, participant['level'] + 2)  # Same as battle winners
                    max_quality = participant['level'] + 8           # Same as battle winners
                    item_found = ItemGenerator.generate_random_equipment(
                        participant['user_id'], min_quality, max_quality
                    )
                else:
                    # Defeat items - lower quality
                    min_quality = max(3, participant['level'])       # Same as battle losers
                    max_quality = participant['level'] + 4           # Same as battle losers
                    item_found = ItemGenerator.generate_random_equipment(
                        participant['user_id'], min_quality, max_quality
                    )
                
                # Use AI-generated item names
                if 'item_names' in event_data and event_data['item_names']:
                    item_found.name = random.choice(event_data['item_names'])
                else:
                    # Fallback to generic name
                    item_found.name = f"Boss {item_found.name}"
                
                self.create_item_in_db(item_found)
            
            # Update character
            char_data = self.db.get_character(participant['user_id'])
            new_xp = char_data['xp'] + final_xp
            new_gold = char_data['money'] + final_gold
            new_level = min(50, 1 + int((new_xp / 100) ** 0.5))
            
            self.db.update_character(
                participant['user_id'],
                xp=new_xp,
                money=new_gold,
                level=new_level
            )
            
            rewards.append({
                'user_id': participant['user_id'],
                'name': participant['name'],
                'xp': final_xp,
                'gold': final_gold,
                'item': item_found.name if item_found else None,
                'leveled_up': new_level > char_data['level']
            })
        
        return {
            'type': 'mini_boss',
            'event_data': event_data,
            'participants': participants,
            'success': success,
            'boss_power': boss_power,
            'group_power': group_power,
            'rewards': rewards
        }

    async def send_event_embed(self, event_result: Dict):
        """Send event embed to game channel"""
        # Find main channel
        channel = None
        for guild in self.bot.guilds:
            for chan in guild.text_channels:
                if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                    channel = chan
                    break
            if channel:
                break
        
        if not channel:
            return
        
        event_type = event_result['type']
        event_data = event_result['event_data']
        
        if event_type == 'treasure':
            await self._send_treasure_embed(channel, event_result)
        elif event_type == 'mini_boss':
            await self._send_boss_embed(channel, event_result)

    async def _send_treasure_embed(self, channel, event_result):
        """Send treasure event embed"""
        event_data = event_result['event_data']
        winners = event_result['winners']
        
        embed = self.embed(
            f"🎲 {event_data['title']}",
            event_data['description']
        )
        
        # Add participants
        participant_list = [p['name'] for p in event_result['participants']]
        embed.add_field(
            name="⚔️ Adventurers",
            value=', '.join(participant_list) if len(participant_list) <= 10 else f"{', '.join(participant_list[:10])}, +{len(participant_list)-10} more",
            inline=False
        )
        
        # Add winners and rewards
        winner_text = []
        for winner in winners[:8]:  # Limit display
            reward_parts = [f"**{winner['xp']:,} XP**", f"**{winner['gold']:,} gold**"]
            if winner['item']:
                reward_parts.append(f"*{winner['item']}*")
            if winner['leveled_up']:
                reward_parts.append("🎉 **LEVEL UP!**")
            
            winner_text.append(f"• **{winner['name']}**: {', '.join(reward_parts)}")
        
        if len(winners) > 8:
            winner_text.append(f"• *...and {len(winners)-8} more winners!*")
        
        embed.add_field(
            name=f"🏆 Treasure Found! ({len(winners)} winners)",
            value='\n'.join(winner_text) if winner_text else "No treasure found this time...",
            inline=False
        )
        
        embed.color = discord.Color.gold()
        embed.set_footer(text=f"AI Event • {len(event_result['participants'])} participants")
        
        await channel.send(embed=embed)

    async def _send_boss_embed(self, channel, event_result):
        """Send boss fight embed with progressive updates"""
        event_data = event_result['event_data']
        
        # Initial embed
        embed = self.embed(
            f"🎲 {event_data['title']}",
            event_data['description']
        )
        
        # Add participants
        participant_list = [p['name'] for p in event_result['participants']]
        embed.add_field(
            name="⚔️ Battle Party",
            value=', '.join(participant_list) if len(participant_list) <= 10 else f"{', '.join(participant_list[:10])}, +{len(participant_list)-10} more",
            inline=False
        )
        
        # Add boss taunt if available
        if event_data.get('special'):
            embed.add_field(
                name="👹 Boss Taunt",
                value=f"*\"{event_data['special']}\"*",
                inline=False
            )
        
        embed.add_field(
            name="⚔️ Battle Status",
            value="⏳ **The battle begins!**",
            inline=False
        )
        
        embed.color = discord.Color.red()
        embed.set_footer(text=f"AI Boss Fight • {len(event_result['participants'])} vs 1")
        
        # Send initial embed
        message = await channel.send(embed=embed)
        
        # Wait and update with result
        await asyncio.sleep(3)
        
        # Update with battle result
        if event_result['success']:
            status_text = "🎉 **VICTORY!** The heroes have triumphed!"
            embed.color = discord.Color.green()
        else:
            status_text = "💀 **DEFEAT!** The boss proves too powerful..."
            embed.color = discord.Color.dark_red()
        
        embed.set_field_at(
            2,  # Battle Status field
            name="⚔️ Battle Result",
            value=status_text,
            inline=False
        )
        
        # Add rewards
        rewards_text = []
        for reward in event_result['rewards'][:8]:  # Limit display
            reward_parts = [f"**{reward['xp']:,} XP**", f"**{reward['gold']:,} gold**"]
            if reward['item']:
                reward_parts.append(f"*{reward['item']}*")
            if reward['leveled_up']:
                reward_parts.append("🎉 **LEVEL UP!**")
            
            rewards_text.append(f"• **{reward['name']}**: {', '.join(reward_parts)}")
        
        if len(event_result['rewards']) > 8:
            rewards_text.append(f"• *...and {len(event_result['rewards'])-8} more heroes!*")
        
        embed.add_field(
            name="🏆 Battle Rewards",
            value='\n'.join(rewards_text) if rewards_text else "The battle yields no rewards...",
            inline=False
        )
        
        await message.edit(embed=embed)

    @tasks.loop(minutes=15)  # Fixed 15-minute interval (between existing 10-20 min suggestion)
    async def ai_event_generator(self):
        """Main AI event generation loop"""
        try:
            if not self.openai_enabled:
                return
            
            # Random additional delay (0-5 minutes) to avoid exact timing
            await asyncio.sleep(random.randint(0, 300))
            
            # Get online players
            min_level = random.choice([1, 1, 1, 5, 10])  # Favor low-level inclusive events
            online_players = await self.get_online_players(min_level=min_level, max_players=20)
            
            if len(online_players) < 2:  # Need at least 2 players
                logger.info("Not enough players online for AI event")
                return
            
            # Select event type (weighted)
            event_types = ['treasure'] * 4 + ['mini_boss'] * 3 + ['world_event'] * 2 + ['mystery'] * 1
            event_type = random.choice(event_types)
            
            # Limit participants based on event type
            if event_type == 'treasure':
                max_participants = random.randint(3, 12)
            elif event_type == 'mini_boss':
                max_participants = random.randint(3, 8)
            elif event_type == 'world_event':
                max_participants = min(15, len(online_players))  # Up to 15 for world events
            else:  # mystery
                max_participants = random.randint(2, 6)
            
            participants = random.sample(online_players, min(max_participants, len(online_players)))
            
            # Generate AI content
            event_data = await self.generate_ai_content(event_type, participants)
            
            # Execute event
            if event_type == 'treasure':
                event_result = await self.execute_treasure_event(event_data, participants)
            elif event_type == 'mini_boss':
                event_result = await self.execute_mini_boss_event(event_data, participants)
            else:
                # For world_event and mystery, use treasure mechanics for now
                event_result = await self.execute_treasure_event(event_data, participants)
            
            # Send results
            await self.send_event_embed(event_result)
            
            # Log event
            logger.info(f"AI Event executed: {event_type} with {len(participants)} participants")
            
        except Exception as e:
            logger.error(f"Error in AI event generation: {e}")

    @ai_event_generator.before_loop
    async def before_ai_event_generator(self):
        """Wait for bot to be ready and add initial delay"""
        await self.bot.wait_until_ready()
        # Random initial delay (1-5 minutes) to avoid conflicts with startup
        initial_delay = random.randint(60, 300)
        logger.info(f"🎲 AI Events will start in {initial_delay//60} minutes {initial_delay%60} seconds")
        await asyncio.sleep(initial_delay)

    @commands.command()
    async def aieventsstatus(self, ctx: commands.Context):
        """Check AI events system status (Admin only)"""
        if not await self.is_admin(ctx.author.id):
            await ctx.send("❌ This command is admin-only.")
            return
            
        embed = self.embed("🎲 AI Events System Status", "Current status of dynamic AI events")
        
        embed.add_field(
            name="🔧 Configuration",
            value=f"**OpenAI Available**: {'✅' if OPENAI_AVAILABLE else '❌'}\n"
                  f"**OpenAI Enabled**: {'✅' if self.openai_enabled else '❌'}\n"
                  f"**Event Loop Running**: {'✅' if self.ai_event_generator.is_running() else '❌'}",
            inline=False
        )
        
        if self.ai_event_generator.is_running():
            embed.add_field(
                name="⏱️ Next Event",
                value=f"Next AI event in approximately **{15 - (datetime.now().minute % 15)} minutes**",
                inline=False
            )
        else:
            embed.add_field(
                name="⚠️ Status",
                value="AI Events are **disabled**. Check OpenAI configuration in .env file.",
                inline=False
            )
        
        embed.add_field(
            name="📊 Info",
            value="AI Events run **parallel** to all existing systems\n"
                  "Events occur every **15 minutes** with random delays\n"
                  "Includes: Treasure hunts, mini bosses, world events",
            inline=False
        )
        
        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AIEventsCog(bot))