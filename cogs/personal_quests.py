"""Personal Quest Lines - AI-generated multi-chapter quests unique to each player"""
import discord
from discord.ext import commands, tasks
import random
import asyncio
import json
import os
import math
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import logging

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog, has_character
from utils.scaling import calculate_quest_chapter_xp, get_level_bonus

# Import OpenAI safely
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger('DiscordRPG.PersonalQuests')


class PersonalQuestsCog(DiscordRPGCog):
    """AI-generated personal quest lines with multi-chapter narratives"""

    # Objective types that can be tracked
    OBJECTIVE_TYPES = {
        'adventures': 'Complete {target} adventures',
        'pvp_wins': 'Win {target} PvP battles',
        'gold_earn': 'Earn {target} gold',
        'gold_spend': 'Spend {target} gold',
        'level_reach': 'Reach level {target}',
        'xp_gain': 'Gain {target} XP',
        'items_acquire': 'Acquire {target} new items',
        'items_sell': 'Sell {target} items',
        'prayers': 'Pray {target} times',
        'raids': 'Participate in {target} raids',
        'crates_open': 'Open {target} crates',
        'epic_adventures': 'Complete {target} epic adventures',
        'battles_total': 'Fight in {target} battles (win or lose)',
    }

    # Quest themes based on class archetypes
    CLASS_THEMES = {
        'Warrior': ['honor', 'strength', 'battle', 'protection', 'valor'],
        'Thief': ['shadows', 'cunning', 'treasure', 'stealth', 'deception'],
        'Mage': ['arcane', 'knowledge', 'power', 'mystery', 'elements'],
        'Ranger': ['nature', 'hunt', 'wilderness', 'beasts', 'survival'],
        'Raider': ['conquest', 'glory', 'plunder', 'dominance', 'legacy'],
        'Ritualist': ['spirits', 'prophecy', 'fate', 'visions', 'cosmic'],
        'Paladin': ['justice', 'divine', 'crusade', 'redemption', 'light'],
        'Assassin': ['silence', 'precision', 'contracts', 'vengeance', 'shadows'],
        'Necromancer': ['death', 'undeath', 'souls', 'forbidden', 'darkness'],
    }

    # Race flavor themes
    RACE_THEMES = {
        'Human': ['ambition', 'legacy', 'unity'],
        'Elf': ['ancient', 'ethereal', 'timeless'],
        'Dwarf': ['forge', 'ancestors', 'mountain'],
        'Orc': ['blood', 'war', 'tribe'],
        'Halfling': ['luck', 'adventure', 'home'],
        'Gnome': ['invention', 'curiosity', 'trickery'],
        'Dragonborn': ['draconic', 'heritage', 'flame'],
        'Tiefling': ['infernal', 'redemption', 'defiance'],
        'Undead': ['eternal', 'curse', 'memory'],
        'Demon': ['chaos', 'power', 'corruption'],
    }

    def __init__(self, bot):
        super().__init__(bot)
        self.openai_client = None
        self.openai_enabled = False
        self._initialize_openai()

    def _initialize_openai(self):
        """Initialize OpenAI client if available"""
        if not OPENAI_AVAILABLE:
            logger.info("OpenAI package not available. Personal quests will use templates.")
            return

        from dotenv import load_dotenv
        load_dotenv()

        self.openai_enabled = os.getenv('OPENAI_ENABLED', 'false').lower() in ['true', '1', 'yes', 'on']

        if not self.openai_enabled:
            logger.info("OpenAI disabled - personal quests will use templates")
            return

        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found")
            self.openai_enabled = False
            return

        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("OpenAI initialized for Personal Quests")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.openai_enabled = False

    async def cog_load(self):
        """Start quest systems when cog loads"""
        if not self.quest_generator.is_running():
            self.quest_generator.start()
            logger.info("Personal Quest Generator started")
        if not self.quest_progress_checker.is_running():
            self.quest_progress_checker.start()
            logger.info("Quest Progress Checker started")

    async def cog_unload(self):
        """Stop quest systems"""
        if self.quest_generator.is_running():
            self.quest_generator.cancel()
        if self.quest_progress_checker.is_running():
            self.quest_progress_checker.cancel()

    def is_user_online(self, user_id: int) -> bool:
        """Check if user is online"""
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member and member.status == discord.Status.online:
                return True
        return False

    def get_class_archetype(self, char_class: str) -> str:
        """Map specific class to archetype for theming"""
        class_map = {
            # Warrior path
            'Novice': 'Warrior', 'Warrior': 'Warrior', 'Swordsman': 'Warrior',
            'Knight': 'Warrior', 'Warlord': 'Warrior', 'Berserker': 'Warrior',
            'Paladin': 'Paladin', 'Warlord Supreme': 'Warrior',
            # Thief path
            'Thief': 'Thief', 'Rogue': 'Thief', 'Bandit': 'Thief',
            'Shadow': 'Assassin', 'Assassin': 'Assassin', 'Nightblade': 'Assassin',
            'Shadowlord': 'Assassin',
            # Mage path
            'Mage': 'Mage', 'Wizard': 'Mage', 'Sorcerer': 'Mage',
            'Warlock': 'Mage', 'Archmage': 'Mage', 'Archsorcerer': 'Mage',
            'Necromancer': 'Necromancer',
            # Ranger path
            'Ranger': 'Ranger', 'Hunter': 'Ranger', 'Tracker': 'Ranger',
            'Bowmaster': 'Ranger', 'Beastmaster': 'Ranger', 'Marksman': 'Ranger',
            'Grandmaster Archer': 'Ranger', 'Time Hunter': 'Ranger',
            # Raider path
            'Raider': 'Raider', 'Viking': 'Raider', 'Chieftain': 'Raider',
            'Ravager': 'Raider', 'Conqueror': 'Raider', 'Warchief': 'Raider',
            'Khan': 'Raider', 'Worldbreaker': 'Raider',
            # Ritualist path
            'Ritualist': 'Ritualist', 'Mystic': 'Ritualist', 'Shaman': 'Ritualist',
            'Oracle': 'Ritualist', 'Sage': 'Ritualist', 'Prophet': 'Ritualist',
            'Divine Oracle': 'Ritualist', 'Cosmic Sage': 'Ritualist',
            # Apex classes
            'God Emperor': 'Warrior', 'Void Walker': 'Assassin',
            'Reality Weaver': 'Mage', 'Universal Sovereign': 'Ritualist',
        }
        return class_map.get(char_class, 'Warrior')

    async def generate_quest_content(self, char_data: Dict, quest_history: List) -> Dict:
        """Generate AI quest content or use templates"""
        char_class = char_data.get('class', 'Novice')
        char_race = char_data.get('race', 'Human')
        char_level = char_data.get('level', 1)
        char_name = char_data.get('name', 'Adventurer')

        archetype = self.get_class_archetype(char_class)
        class_themes = self.CLASS_THEMES.get(archetype, ['adventure', 'glory'])
        race_themes = self.RACE_THEMES.get(char_race, ['destiny'])

        # Determine quest difficulty/length based on level
        if char_level < 10:
            total_chapters = 3
            difficulty = 'novice'
        elif char_level < 25:
            total_chapters = 4
            difficulty = 'journeyman'
        elif char_level < 50:
            total_chapters = 4
            difficulty = 'expert'
        elif char_level < 100:
            total_chapters = 5
            difficulty = 'master'
        else:
            total_chapters = 5
            difficulty = 'legendary'

        if not self.openai_client or not self.openai_enabled:
            return self._generate_template_quest(char_data, archetype, total_chapters, difficulty)

        try:
            # Build context from quest history
            history_context = ""
            if quest_history:
                completed_titles = [q['quest_title'] for q in quest_history[-5:]]
                history_context = f"Previously completed quests: {', '.join(completed_titles)}. Generate something fresh and different."

            system_prompt = f"""You are a master storyteller creating personalized quest lines for a Discord RPG.

CHARACTER INFO:
- Name: {char_name}
- Class: {char_class} (archetype: {archetype})
- Race: {char_race}
- Level: {char_level}
- Difficulty tier: {difficulty}

QUEST REQUIREMENTS:
- Create a {total_chapters}-chapter personal quest line
- Theme should blend class themes ({', '.join(class_themes)}) with race themes ({', '.join(race_themes)})
- Each chapter should have a compelling mini-story that advances the overall narrative
- The quest should feel personal to this character's journey
- Avoid generic "kill X monsters" framing - make objectives feel story-driven
{history_context}

IMPORTANT: Return ONLY valid JSON matching this exact structure:
{{
  "quest_title": "Epic quest title (max 50 chars)",
  "quest_theme": "One-word theme like 'redemption' or 'vengeance'",
  "opening_narrative": "2-3 sentences setting up the quest's premise",
  "chapters": [
    {{
      "chapter_title": "Chapter title (max 40 chars)",
      "narrative": "2-3 sentences describing this chapter's story beat",
      "objective_flavor": "Story-flavored description of what the player must do"
    }}
  ],
  "completion_teaser": "One sentence hinting at the grand finale"
}}

Generate exactly {total_chapters} chapters. Be creative, dramatic, and make it feel epic!"""

            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Create a personal quest for {char_name} the {char_race} {char_class}."}
                    ],
                    max_tokens=800,
                    temperature=0.85,
                    response_format={"type": "json_object"}
                )
            )

            content = response.choices[0].message.content.strip()
            quest_data = json.loads(content)
            quest_data['total_chapters'] = total_chapters
            quest_data['difficulty'] = difficulty
            return quest_data

        except Exception as e:
            logger.warning(f"AI quest generation failed: {e}")
            return self._generate_template_quest(char_data, archetype, total_chapters, difficulty)

    def _generate_template_quest(self, char_data: Dict, archetype: str, total_chapters: int, difficulty: str) -> Dict:
        """Generate template-based quest when AI unavailable"""
        char_name = char_data.get('name', 'Adventurer')
        char_class = char_data.get('class', 'Novice')
        char_race = char_data.get('race', 'Human')

        # Template quests by archetype
        templates = {
            'Warrior': {
                'titles': [
                    "The {race}'s Trial of Steel",
                    "Blade of the Fallen Legion",
                    "The Warlord's Challenge",
                    "Honor Among Warriors"
                ],
                'themes': ['honor', 'strength', 'valor'],
                'opening': "Ancient warrior spirits have sensed your growing power, {name}. They call you to prove your worth through trials of combat and courage."
            },
            'Thief': {
                'titles': [
                    "Shadows of the {race} Syndicate",
                    "The Impossible Heist",
                    "Whispers in the Dark",
                    "The Phantom's Legacy"
                ],
                'themes': ['cunning', 'shadows', 'treasure'],
                'opening': "A mysterious contact has reached out, {name}. There's a job that requires your particular talents - one that could make you legendary among thieves."
            },
            'Mage': {
                'titles': [
                    "The Arcane Convergence",
                    "Secrets of the {race} Grimoire",
                    "The Forbidden Ritual",
                    "Echoes of Ancient Magic"
                ],
                'themes': ['arcane', 'knowledge', 'power'],
                'opening': "The ley lines pulse with unusual energy, {name}. Ancient magical forces stir, and you alone possess the talent to uncover their secrets."
            },
            'Ranger': {
                'titles': [
                    "Hunt of the {race} Stalker",
                    "The Primal Call",
                    "Whispers of the Wild",
                    "The Beast Within"
                ],
                'themes': ['nature', 'hunt', 'survival'],
                'opening': "The wilderness calls to you, {name}. A great hunt awaits - one that will test every skill you've honed in the wild."
            },
            'Raider': {
                'titles': [
                    "Conquest of the {race} Horde",
                    "The Warchief's Ambition",
                    "Blood and Glory",
                    "The Plunderer's Path"
                ],
                'themes': ['conquest', 'glory', 'dominance'],
                'opening': "The drums of war beat in your blood, {name}. A great conquest awaits those bold enough to seize it."
            },
            'Ritualist': {
                'titles': [
                    "Visions of the {race} Seer",
                    "The Cosmic Tapestry",
                    "Whispers of Fate",
                    "The Spirit Walker's Journey"
                ],
                'themes': ['prophecy', 'spirits', 'fate'],
                'opening': "The spirits speak your name, {name}. A prophecy unfolds, and you stand at its center."
            },
            'Assassin': {
                'titles': [
                    "The {race}'s Mark",
                    "Contract of Shadows",
                    "The Silent Blade",
                    "Vengeance in Darkness"
                ],
                'themes': ['silence', 'vengeance', 'precision'],
                'opening': "A contract has come to you, {name}. Not just any contract - one that will cement your legend among the silent brotherhood."
            },
            'Necromancer': {
                'titles': [
                    "The {race} Death Knight's Rise",
                    "Whispers from Beyond",
                    "The Bone Throne",
                    "Echoes of the Damned"
                ],
                'themes': ['death', 'undeath', 'forbidden'],
                'opening': "The boundary between life and death grows thin, {name}. Power awaits those willing to reach into the darkness."
            },
            'Paladin': {
                'titles': [
                    "The {race} Crusader's Oath",
                    "Light Against Shadow",
                    "The Sacred Quest",
                    "Redemption's Call"
                ],
                'themes': ['justice', 'light', 'redemption'],
                'opening': "A divine vision has been granted to you, {name}. Evil stirs in the land, and you have been chosen to stand against it."
            },
        }

        template = templates.get(archetype, templates['Warrior'])
        title = random.choice(template['titles']).format(race=char_race)
        theme = random.choice(template['themes'])
        opening = template['opening'].format(name=char_name)

        # Generate chapter templates
        chapter_templates = [
            {"title": "The Call", "narrative": "Your journey begins with an unexpected summons.", "objective_flavor": "Prove your readiness"},
            {"title": "First Steps", "narrative": "The path ahead becomes clearer as you take action.", "objective_flavor": "Begin your quest in earnest"},
            {"title": "Rising Challenges", "narrative": "Obstacles mount, but so does your determination.", "objective_flavor": "Overcome the growing difficulties"},
            {"title": "The Revelation", "narrative": "A crucial truth is revealed that changes everything.", "objective_flavor": "Uncover the hidden truth"},
            {"title": "The Final Trial", "narrative": "Everything has led to this moment.", "objective_flavor": "Face your ultimate challenge"},
        ]

        chapters = chapter_templates[:total_chapters]

        return {
            'quest_title': title,
            'quest_theme': theme,
            'opening_narrative': opening,
            'chapters': chapters,
            'completion_teaser': "Your legend grows with each step...",
            'total_chapters': total_chapters,
            'difficulty': difficulty
        }

    def generate_chapter_objective(self, chapter_num: int, total_chapters: int,
                                   char_level: int, difficulty: str) -> Dict:
        """Generate appropriate objective for a chapter"""
        # Scale targets based on difficulty and chapter
        difficulty_mult = {
            'novice': 0.5,
            'journeyman': 1.0,
            'expert': 1.5,
            'master': 2.0,
            'legendary': 3.0
        }.get(difficulty, 1.0)

        chapter_mult = 1 + (chapter_num - 1) * 0.3  # Later chapters are harder

        # Base targets that scale with level
        base_targets = {
            'adventures': max(2, int(3 * chapter_mult * difficulty_mult)),
            'pvp_wins': max(1, int(2 * chapter_mult * difficulty_mult)),
            'gold_earn': max(500, int(1000 * char_level * 0.5 * chapter_mult * difficulty_mult)),
            'gold_spend': max(200, int(500 * char_level * 0.3 * chapter_mult * difficulty_mult)),
            'xp_gain': max(200, int(500 * char_level * 0.4 * chapter_mult * difficulty_mult)),
            'items_acquire': max(1, int(2 * chapter_mult * difficulty_mult)),
            'items_sell': max(1, int(3 * chapter_mult * difficulty_mult)),
            'prayers': max(1, int(2 * chapter_mult * difficulty_mult)),
            'raids': max(1, int(1 * chapter_mult * difficulty_mult)),
            'crates_open': max(1, int(2 * chapter_mult * difficulty_mult)),
            'battles_total': max(2, int(3 * chapter_mult * difficulty_mult)),
        }

        # Add epic adventures only for higher level players
        if char_level >= 10:
            base_targets['epic_adventures'] = max(1, int(1 * chapter_mult * difficulty_mult * 0.5))

        # Add level_reach only for final chapters of lower level players
        if chapter_num == total_chapters and char_level < 50:
            base_targets['level_reach'] = char_level + int(3 * difficulty_mult)

        # Weight objective selection based on chapter position
        if chapter_num == 1:
            # First chapter: easier objectives
            weights = {
                'adventures': 30, 'pvp_wins': 15, 'gold_earn': 20,
                'xp_gain': 20, 'prayers': 10, 'battles_total': 5
            }
        elif chapter_num == total_chapters:
            # Final chapter: challenging objectives
            weights = {
                'adventures': 15, 'pvp_wins': 20, 'gold_earn': 15,
                'raids': 15, 'epic_adventures': 15 if char_level >= 10 else 0,
                'level_reach': 10 if char_level < 50 else 0, 'battles_total': 10
            }
        else:
            # Middle chapters: balanced
            weights = {
                'adventures': 20, 'pvp_wins': 15, 'gold_earn': 15,
                'gold_spend': 10, 'xp_gain': 10, 'items_acquire': 10,
                'items_sell': 5, 'prayers': 5, 'crates_open': 5, 'battles_total': 5
            }

        # Filter to only objectives we have targets for
        valid_weights = {k: v for k, v in weights.items() if k in base_targets and v > 0}

        # Select objective type
        objective_type = random.choices(
            list(valid_weights.keys()),
            weights=list(valid_weights.values()),
            k=1
        )[0]

        target = base_targets[objective_type]
        description = self.OBJECTIVE_TYPES[objective_type].format(target=target)

        return {
            'type': objective_type,
            'target': target,
            'description': description
        }

    def calculate_chapter_rewards(self, chapter_num: int, total_chapters: int,
                                  char_level: int, difficulty: str) -> Dict:
        """Calculate rewards for completing a chapter using new scaling system"""
        difficulty_mult = {
            'novice': 0.7,
            'journeyman': 1.0,
            'expert': 1.3,
            'master': 1.6,
            'legendary': 2.0
        }.get(difficulty, 1.0)

        # Calculate XP using new scaling system
        base_xp = calculate_quest_chapter_xp(
            player_level=char_level,
            chapter_number=chapter_num,
            total_chapters=total_chapters,
            race_xp_bonus=1.0,
            blessing_xp_mult=1.0
        )

        # Apply difficulty multiplier
        base_xp = int(base_xp * difficulty_mult)

        # Gold calculation with level bonus
        chapter_mult = 1 + (chapter_num - 1) * 0.25
        if chapter_num == total_chapters:
            chapter_mult *= 1.5
        base_gold = int((250 + get_level_bonus(char_level, 100)) * chapter_mult * difficulty_mult)

        # Determine crate reward (higher chance on later chapters)
        crate = None
        crate_roll = random.random()
        if chapter_num == total_chapters:
            # Final chapter: guaranteed good crate
            if crate_roll < 0.3:
                crate = 'legendary'
            elif crate_roll < 0.7:
                crate = 'magic'
            else:
                crate = 'rare'
        elif chapter_num >= total_chapters - 1:
            # Second to last: good chance
            if crate_roll < 0.4:
                crate = 'magic' if random.random() < 0.3 else 'rare'
            elif crate_roll < 0.7:
                crate = 'uncommon'
        else:
            # Earlier chapters: smaller chance
            if crate_roll < 0.25:
                crate = 'uncommon' if random.random() < 0.5 else 'common'

        return {
            'xp': base_xp,
            'gold': base_gold,
            'crate': crate
        }

    async def create_quest_for_player(self, user_id: int) -> Optional[int]:
        """Create a new quest for a player"""
        char_data = self.db.get_character(user_id)
        if not char_data:
            return None

        # Check if player already has an active quest
        existing = self.db.fetchone(
            "SELECT id FROM personal_quests WHERE user_id = ? AND status = 'active'",
            (user_id,)
        )
        if existing:
            return None

        # Get quest history for context
        history = self.db.fetchall(
            "SELECT quest_title, quest_theme FROM quest_history WHERE user_id = ? ORDER BY completed_at DESC LIMIT 5",
            (user_id,)
        )
        quest_history = [self.db.row_to_dict(h) for h in history]

        # Generate quest content
        quest_content = await self.generate_quest_content(char_data, quest_history)

        # Create quest in database
        cursor = self.db.execute(
            """INSERT INTO personal_quests
               (user_id, quest_title, quest_theme, quest_context, total_chapters)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, quest_content['quest_title'], quest_content['quest_theme'],
             json.dumps(quest_content), quest_content['total_chapters'])
        )
        quest_id = cursor.lastrowid

        # Create chapters
        for i, chapter in enumerate(quest_content['chapters'], 1):
            objective = self.generate_chapter_objective(
                i, quest_content['total_chapters'],
                char_data['level'], quest_content['difficulty']
            )
            rewards = self.calculate_chapter_rewards(
                i, quest_content['total_chapters'],
                char_data['level'], quest_content['difficulty']
            )

            status = 'active' if i == 1 else 'locked'
            started_at = datetime.now().isoformat() if i == 1 else None

            self.db.execute(
                """INSERT INTO quest_chapters
                   (quest_id, chapter_number, chapter_title, chapter_narrative,
                    objective_type, objective_target, objective_description,
                    rewards_xp, rewards_gold, rewards_crate, status, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (quest_id, i, chapter['chapter_title'], chapter['narrative'],
                 objective['type'], objective['target'], objective['description'],
                 rewards['xp'], rewards['gold'], rewards['crate'], status, started_at)
            )

        self.db.commit()
        logger.info(f"Created quest '{quest_content['quest_title']}' for user {user_id}")
        return quest_id

    async def check_and_update_progress(self, user_id: int, objective_type: str, amount: int = 1):
        """Update quest progress for a specific objective type"""
        # Get active quest and chapter
        active_chapter = self.db.fetchone(
            """SELECT qc.*, pq.quest_title, pq.total_chapters
               FROM quest_chapters qc
               JOIN personal_quests pq ON qc.quest_id = pq.id
               WHERE pq.user_id = ? AND pq.status = 'active' AND qc.status = 'active'""",
            (user_id,)
        )

        if not active_chapter:
            return

        chapter = self.db.row_to_dict(active_chapter)

        # Special handling for level_reach: check current level directly
        if chapter['objective_type'] == 'level_reach':
            char_data = self.db.get_character(user_id)
            current_level = char_data['level']
            if current_level != chapter['objective_progress']:
                self.db.execute(
                    "UPDATE quest_chapters SET objective_progress = ? WHERE id = ?",
                    (current_level, chapter['id'])
                )
                self.db.commit()
            if current_level >= chapter['objective_target']:
                await self.complete_chapter(user_id, chapter)
            return

        # Check if objective type matches
        if chapter['objective_type'] != objective_type:
            return

        # Update progress
        new_progress = chapter['objective_progress'] + amount
        self.db.execute(
            "UPDATE quest_chapters SET objective_progress = ? WHERE id = ?",
            (new_progress, chapter['id'])
        )
        self.db.commit()

        # Check if chapter is complete
        if new_progress >= chapter['objective_target']:
            await self.complete_chapter(user_id, chapter)

    async def complete_chapter(self, user_id: int, chapter: Dict):
        """Complete a chapter and potentially the quest"""
        try:
            quest_id = chapter['quest_id']
            chapter_num = chapter['chapter_number']
            total_chapters = chapter['total_chapters']

            # Mark chapter complete
            self.db.execute(
                "UPDATE quest_chapters SET status = 'completed', completed_at = ? WHERE id = ?",
                (datetime.now().isoformat(), chapter['id'])
            )

            # Award rewards
            char_data = self.db.get_character(user_id)
            new_xp = char_data['xp'] + chapter['rewards_xp']
            new_gold = char_data['money'] + chapter['rewards_gold']
            new_level = min(999, 1 + int((new_xp / 100) ** 0.5))

            update_data = {'xp': new_xp, 'money': new_gold, 'level': new_level}

            # Award crate if any
            if chapter['rewards_crate']:
                crate_field = f"crates_{chapter['rewards_crate']}"
                current_crates = char_data.get(crate_field, 0)
                update_data[crate_field] = current_crates + 1

            self.db.update_character(user_id, **update_data)

            # Check if quest is complete
            if chapter_num >= total_chapters:
                await self.complete_quest(user_id, quest_id)
            else:
                # Unlock next chapter
                self.db.execute(
                    """UPDATE quest_chapters
                       SET status = 'active', started_at = ?
                       WHERE quest_id = ? AND chapter_number = ?""",
                    (datetime.now().isoformat(), quest_id, chapter_num + 1)
                )
                self.db.execute(
                    "UPDATE personal_quests SET current_chapter = ? WHERE id = ?",
                    (chapter_num + 1, quest_id)
                )

            self.db.commit()
        except Exception as e:
            logger.error(f"Error completing chapter {chapter.get('chapter_number')} for user {user_id}: {e}")

    async def complete_quest(self, user_id: int, quest_id: int):
        """Complete an entire quest"""
        quest = self.db.fetchone(
            "SELECT * FROM personal_quests WHERE id = ?",
            (quest_id,)
        )
        quest_data = self.db.row_to_dict(quest)

        # Calculate total rewards earned
        chapters = self.db.fetchall(
            "SELECT rewards_xp, rewards_gold FROM quest_chapters WHERE quest_id = ?",
            (quest_id,)
        )
        total_xp = sum(self.db.row_to_dict(c)['rewards_xp'] for c in chapters)
        total_gold = sum(self.db.row_to_dict(c)['rewards_gold'] for c in chapters)

        # Generate completion narrative if AI available
        completion_narrative = "Your legend grows as another chapter of your story comes to a close."
        if self.openai_client and self.openai_enabled:
            try:
                char_data = self.db.get_character(user_id)
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "Write a brief (2-3 sentences) epic conclusion for a completed quest. Be dramatic and celebratory."},
                            {"role": "user", "content": f"{char_data['name']} the {char_data['race']} {char_data['class']} has completed the quest '{quest_data['quest_title']}' with theme '{quest_data['quest_theme']}'."}
                        ],
                        max_tokens=100,
                        temperature=0.8
                    )
                )
                completion_narrative = response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Failed to generate completion narrative: {e}")

        # Remove old completed quests for this user to avoid UNIQUE(user_id, status) violation
        # (quest data is preserved in quest_history)
        self.db.execute(
            "DELETE FROM personal_quests WHERE user_id = ? AND status = 'completed'",
            (user_id,)
        )

        # Mark quest complete
        self.db.execute(
            "UPDATE personal_quests SET status = 'completed', completed_at = ? WHERE id = ?",
            (datetime.now().isoformat(), quest_id)
        )

        # Add to history
        self.db.execute(
            """INSERT INTO quest_history
               (user_id, quest_title, quest_theme, chapters_completed,
                total_xp_earned, total_gold_earned, completion_narrative)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, quest_data['quest_title'], quest_data['quest_theme'],
             quest_data['total_chapters'], total_xp, total_gold, completion_narrative)
        )

        self.db.commit()
        logger.info(f"Quest '{quest_data['quest_title']}' completed by user {user_id}")

    async def send_chapter_complete_notification(self, user_id: int, chapter: Dict, quest_complete: bool):
        """Send notification when chapter/quest completes"""
        user = self.bot.get_user(user_id)
        if not user:
            return

        # Find game channel
        channel = None
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                for chan in guild.text_channels:
                    if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                        channel = chan
                        break
                if channel:
                    break

        if not channel:
            return

        if quest_complete:
            embed = discord.Embed(
                title="Quest Complete!",
                description=f"**{chapter['quest_title']}**\n\n{user.mention} has completed their personal quest!",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Final Chapter Complete",
                value=f"**{chapter['chapter_title']}**\n{chapter['chapter_narrative']}",
                inline=False
            )
        else:
            embed = discord.Embed(
                title="Chapter Complete!",
                description=f"**{chapter['quest_title']}** - Chapter {chapter['chapter_number']}",
                color=discord.Color.green()
            )
            embed.add_field(
                name=f"{chapter['chapter_title']}",
                value=chapter['chapter_narrative'],
                inline=False
            )

        # Add rewards
        rewards_text = f"**{chapter['rewards_xp']:,} XP** | **{chapter['rewards_gold']:,} Gold**"
        if chapter['rewards_crate']:
            rewards_text += f" | **1x {chapter['rewards_crate'].title()} Crate**"
        embed.add_field(name="Rewards", value=rewards_text, inline=False)

        embed.set_footer(text=f"Personal Quest System | Use !quest to view progress")

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send quest notification: {e}")

    async def send_quest_start_notification(self, user_id: int, quest_id: int):
        """Send notification when a new quest starts"""
        user = self.bot.get_user(user_id)
        if not user:
            return

        quest = self.db.fetchone("SELECT * FROM personal_quests WHERE id = ?", (quest_id,))
        quest_data = self.db.row_to_dict(quest)
        quest_context = json.loads(quest_data['quest_context'])

        first_chapter = self.db.fetchone(
            "SELECT * FROM quest_chapters WHERE quest_id = ? AND chapter_number = 1",
            (quest_id,)
        )
        chapter_data = self.db.row_to_dict(first_chapter)

        # Find game channel
        channel = None
        for guild in self.bot.guilds:
            member = guild.get_member(user_id)
            if member:
                for chan in guild.text_channels:
                    if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                        channel = chan
                        break
                if channel:
                    break

        if not channel:
            return

        embed = discord.Embed(
            title=f"New Personal Quest for {user.display_name}!",
            description=f"**{quest_data['quest_title']}**\n\n{quest_context.get('opening_narrative', 'A new adventure awaits...')}",
            color=discord.Color.purple()
        )
        embed.add_field(
            name=f"Chapter 1: {chapter_data['chapter_title']}",
            value=chapter_data['chapter_narrative'],
            inline=False
        )
        embed.add_field(
            name="Objective",
            value=chapter_data['objective_description'],
            inline=False
        )
        embed.set_footer(text=f"Use !quest to track progress")

        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send quest start notification: {e}")

    # ========== BACKGROUND TASKS ==========

    async def get_game_channel(self):
        """Find the game channel for notifications"""
        for guild in self.bot.guilds:
            for chan in guild.text_channels:
                if chan.name.lower() in ['discordrpg', 'rpg', 'game', 'bot']:
                    return chan
        return None

    @tasks.loop(minutes=25)  # Separate from AI events (15 min) and autoplay
    async def quest_generator(self):
        """Generate new quests for eligible players"""
        try:
            # Add random delay to avoid exact timing
            await asyncio.sleep(random.randint(0, 180))

            # Get online players without active quests
            eligible = self.db.fetchall(
                """SELECT p.user_id, p.level, p.name FROM profile p
                   LEFT JOIN personal_quests pq ON p.user_id = pq.user_id AND pq.status = 'active'
                   WHERE pq.id IS NULL AND p.level >= 3""",
                ()
            )

            if not eligible:
                return

            # Filter to online players
            online_eligible = []
            for row in eligible:
                player = self.db.row_to_dict(row)
                if self.is_user_online(player['user_id']):
                    online_eligible.append(player)

            if not online_eligible:
                return

            # Select 15-20 players to give quests
            num_quests = min(len(online_eligible), random.randint(15, 20))
            selected = random.sample(online_eligible, num_quests)

            # Find game channel for bulk notification
            channel = await self.get_game_channel()
            if not channel:
                return

            # Send initial "generating" embed
            embed = discord.Embed(
                title="📜 Generating Personal Quests...",
                description=f"Creating unique quests for {len(selected)} adventurers...",
                color=discord.Color.purple()
            )
            embed.add_field(name="Progress", value="⏳ Starting...", inline=False)
            msg = await channel.send(embed=embed)

            # Generate quests and track results
            quest_assignments = []
            for i, player in enumerate(selected):
                quest_id = await self.create_quest_for_player(player['user_id'])
                if quest_id:
                    # Get quest title
                    quest = self.db.fetchone("SELECT quest_title FROM personal_quests WHERE id = ?", (quest_id,))
                    quest_data = self.db.row_to_dict(quest)
                    quest_assignments.append({
                        'name': player['name'],
                        'title': quest_data['quest_title']
                    })

                    # Update embed with progress
                    progress_text = f"Generated {len(quest_assignments)}/{len(selected)} quests..."
                    embed = discord.Embed(
                        title="📜 Generating Personal Quests...",
                        description=f"Creating unique quests for {len(selected)} adventurers...",
                        color=discord.Color.purple()
                    )
                    embed.add_field(name="Progress", value=f"⏳ {progress_text}", inline=False)

                    # Show last few assignments
                    if quest_assignments:
                        recent = quest_assignments[-5:]  # Show last 5
                        preview = "\n".join([f"• **{q['name']}** → *{q['title']}*" for q in recent])
                        if len(quest_assignments) > 5:
                            preview = f"...\n{preview}"
                        embed.add_field(name="Recent", value=preview, inline=False)

                    try:
                        await msg.edit(embed=embed)
                    except Exception:
                        pass  # Ignore edit failures

                await asyncio.sleep(1)  # Small delay between generations

            # Final embed with all assignments
            if quest_assignments:
                embed = discord.Embed(
                    title="📜 New Personal Quests Assigned!",
                    description=f"**{len(quest_assignments)}** adventurers have embarked on personal quests!",
                    color=discord.Color.gold()
                )

                # Split into chunks if too many
                quest_lines = [f"• **{q['name']}** → *{q['title']}*" for q in quest_assignments]

                # Discord field limit is 1024 chars, so chunk if needed
                chunk = []
                chunk_len = 0
                field_num = 1

                for line in quest_lines:
                    if chunk_len + len(line) + 1 > 1000:  # Leave buffer
                        embed.add_field(
                            name=f"Quests{f' (Part {field_num})' if field_num > 1 else ''}",
                            value="\n".join(chunk),
                            inline=False
                        )
                        chunk = []
                        chunk_len = 0
                        field_num += 1
                    chunk.append(line)
                    chunk_len += len(line) + 1

                if chunk:
                    embed.add_field(
                        name=f"Quests{f' (Part {field_num})' if field_num > 1 else ''}",
                        value="\n".join(chunk),
                        inline=False
                    )

                embed.set_footer(text="Use !quest to view your quest details and objectives!")

                try:
                    await msg.edit(embed=embed)
                except Exception:
                    # If edit fails, send new message
                    await channel.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in quest generator: {e}")

    @quest_generator.before_loop
    async def before_quest_generator(self):
        """Wait for bot to be ready"""
        await self.bot.wait_until_ready()
        # Initial delay to avoid startup conflicts
        initial_delay = random.randint(120, 300)
        logger.info(f"Quest Generator will start in {initial_delay//60}m {initial_delay%60}s")
        await asyncio.sleep(initial_delay)

    @tasks.loop(minutes=2)  # Check progress frequently
    async def quest_progress_checker(self):
        """Periodically check for completed objectives (backup for event hooks)"""
        try:
            # This is a safety net - most progress updates happen via hooks
            # But this catches any edge cases
            active_chapters = self.db.fetchall(
                """SELECT qc.*, pq.user_id, pq.total_chapters
                   FROM quest_chapters qc
                   JOIN personal_quests pq ON qc.quest_id = pq.id
                   WHERE pq.status = 'active' AND qc.status = 'active'
                   AND qc.objective_progress >= qc.objective_target""",
                ()
            )

            for chapter_row in active_chapters:
                chapter = self.db.row_to_dict(chapter_row)
                await self.complete_chapter(chapter['user_id'], chapter)

        except Exception as e:
            logger.error(f"Error in progress checker: {e}")

    @quest_progress_checker.before_loop
    async def before_progress_checker(self):
        """Wait for bot to be ready"""
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)  # Short delay

    # ========== COMMANDS ==========

    @commands.command(aliases=['q', 'questlog', 'myquest'])
    @has_character()
    async def quest(self, ctx: commands.Context):
        """View your current personal quest progress"""
        quest = self.db.fetchone(
            "SELECT * FROM personal_quests WHERE user_id = ? AND status = 'active'",
            (ctx.author.id,)
        )

        if not quest:
            embed = self.embed(
                "No Active Quest",
                "You don't have an active personal quest.\n\n"
                "New quests are assigned automatically to online players.\n"
                "Stay online and keep adventuring!"
            )
            embed.color = discord.Color.greyple()
            await ctx.send(embed=embed)
            return

        # Auto-fix: detect stuck quests where all chapters are complete but quest is still active
        quest_data_check = self.db.row_to_dict(quest)
        incomplete_chapters = self.db.fetchone(
            "SELECT COUNT(*) as count FROM quest_chapters WHERE quest_id = ? AND status != 'completed'",
            (quest_data_check['id'],)
        )
        if incomplete_chapters and self.db.row_to_dict(incomplete_chapters)['count'] == 0:
            # All chapters done but quest stuck as active - complete it now
            logger.info(f"Auto-fixing stuck quest {quest_data_check['id']} for user {ctx.author.id}")
            await self.complete_quest(ctx.author.id, quest_data_check['id'])
            embed = self.embed(
                "Quest Complete!",
                f"**{quest_data_check['quest_title']}** has been completed!\n\n"
                "A new quest will be assigned automatically."
            )
            embed.color = discord.Color.gold()
            await ctx.send(embed=embed)
            return

        quest_data = self.db.row_to_dict(quest)
        quest_context = json.loads(quest_data['quest_context']) if quest_data['quest_context'] else {}

        # Auto-check level_reach objectives when viewing quest
        active_ch = self.db.fetchone(
            """SELECT qc.*, pq.total_chapters FROM quest_chapters qc
               JOIN personal_quests pq ON qc.quest_id = pq.id
               WHERE qc.quest_id = ? AND qc.status = 'active'""",
            (quest_data['id'],)
        )
        if active_ch:
            ch_data = self.db.row_to_dict(active_ch)
            if ch_data['objective_type'] == 'level_reach':
                await self.check_and_update_progress(ctx.author.id, 'level_reach')
                # Re-check if quest was completed by the level check
                quest_recheck = self.db.fetchone(
                    "SELECT * FROM personal_quests WHERE id = ? AND status = 'active'",
                    (quest_data['id'],)
                )
                if not quest_recheck:
                    embed = self.embed(
                        "Quest Complete!",
                        f"**{quest_data['quest_title']}** has been completed!\n\n"
                        "A new quest will be assigned automatically."
                    )
                    embed.color = discord.Color.gold()
                    await ctx.send(embed=embed)
                    return

        # Get chapters
        chapters = self.db.fetchall(
            "SELECT * FROM quest_chapters WHERE quest_id = ? ORDER BY chapter_number",
            (quest_data['id'],)
        )

        embed = discord.Embed(
            title=f"📜 {quest_data['quest_title']}",
            description=quest_context.get('opening_narrative', 'Your personal quest awaits...'),
            color=discord.Color.purple()
        )

        # Track total rewards earned
        total_xp_earned = 0
        total_gold_earned = 0
        crates_earned = []

        # Show chapter progress
        for chapter_row in chapters:
            chapter = self.db.row_to_dict(chapter_row)

            if chapter['status'] == 'completed':
                status_icon = "✅"
                # Show rewards earned
                rewards_parts = [f"+{chapter['rewards_xp']:,} XP", f"+{chapter['rewards_gold']:,} Gold"]
                if chapter['rewards_crate']:
                    rewards_parts.append(f"+{chapter['rewards_crate'].title()} Crate")
                    crates_earned.append(chapter['rewards_crate'])
                progress_text = f"Complete! ({', '.join(rewards_parts)})"
                total_xp_earned += chapter['rewards_xp']
                total_gold_earned += chapter['rewards_gold']
            elif chapter['status'] == 'active':
                status_icon = "🔶"
                progress = chapter['objective_progress']
                target = chapter['objective_target']
                progress_pct = min(100, int((progress / target) * 100))
                bar_filled = int(progress_pct / 10)
                bar_empty = 10 - bar_filled
                progress_bar = "█" * bar_filled + "░" * bar_empty
                progress_text = f"{progress_bar} {progress}/{target}\n*{chapter['objective_description']}*"
            else:
                status_icon = "🔒"
                progress_text = "Locked"

            embed.add_field(
                name=f"{status_icon} Ch.{chapter['chapter_number']}: {chapter['chapter_title']}",
                value=progress_text,
                inline=False
            )

        # Show current chapter rewards preview
        active_chapter = next((self.db.row_to_dict(c) for c in chapters if self.db.row_to_dict(c)['status'] == 'active'), None)
        if active_chapter:
            rewards_text = f"{active_chapter['rewards_xp']:,} XP | {active_chapter['rewards_gold']:,} Gold"
            if active_chapter['rewards_crate']:
                rewards_text += f" | {active_chapter['rewards_crate'].title()} Crate"
            embed.add_field(name="🎁 Chapter Reward", value=rewards_text, inline=True)

        # Show total earned so far
        if total_xp_earned > 0 or total_gold_earned > 0:
            earned_text = f"{total_xp_earned:,} XP | {total_gold_earned:,} Gold"
            if crates_earned:
                earned_text += f" | {len(crates_earned)} Crate(s)"
            embed.add_field(name="💰 Earned So Far", value=earned_text, inline=True)

        embed.set_footer(text=f"Chapter {quest_data['current_chapter']}/{quest_data['total_chapters']} | Theme: {quest_data['quest_theme'].title()}")

        await ctx.send(embed=embed)

    @commands.command()
    @has_character()
    async def questhistory(self, ctx: commands.Context):
        """View your completed quest history"""
        history = self.db.fetchall(
            """SELECT * FROM quest_history
               WHERE user_id = ?
               ORDER BY completed_at DESC LIMIT 10""",
            (ctx.author.id,)
        )

        if not history:
            embed = self.embed(
                "Quest History",
                "You haven't completed any personal quests yet.\n"
                "Complete your active quest to build your legend!"
            )
            embed.color = discord.Color.greyple()
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="Your Quest History",
            description="Tales of your completed adventures",
            color=discord.Color.gold()
        )

        for quest_row in history:
            quest = self.db.row_to_dict(quest_row)
            completed_date = quest['completed_at'][:10] if quest['completed_at'] else 'Unknown'

            embed.add_field(
                name=f" {quest['quest_title']}",
                value=f"*{quest['quest_theme'].title()}* | {quest['chapters_completed']} chapters\n"
                      f"Rewards: {quest['total_xp_earned']:,} XP, {quest['total_gold_earned']:,} Gold\n"
                      f"Completed: {completed_date}",
                inline=False
            )

        total_quests = len(history)
        embed.set_footer(text=f"Showing {total_quests} completed quest(s)")

        await ctx.send(embed=embed)

    @commands.command()
    @has_character()
    async def abandonquest(self, ctx: commands.Context):
        """Abandon your current quest (no rewards, 1 hour cooldown for new quest)"""
        quest = self.db.fetchone(
            "SELECT * FROM personal_quests WHERE user_id = ? AND status = 'active'",
            (ctx.author.id,)
        )

        if not quest:
            await ctx.send(" You don't have an active quest to abandon.")
            return

        quest_data = self.db.row_to_dict(quest)

        # Confirm abandonment
        embed = self.embed(
            "Abandon Quest?",
            f"Are you sure you want to abandon **{quest_data['quest_title']}**?\n\n"
            f" You will lose all progress\n"
            f" No rewards will be given\n"
            f" You must wait before receiving a new quest"
        )
        embed.color = discord.Color.orange()

        msg = await ctx.send(embed=embed)
        await msg.add_reaction('')
        await msg.add_reaction('')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['', ''] and reaction.message.id == msg.id

        try:
            reaction, _ = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == '':
                # Abandon the quest
                self.db.execute(
                    "UPDATE personal_quests SET status = 'abandoned' WHERE id = ?",
                    (quest_data['id'],)
                )
                self.db.commit()

                await ctx.send(f" You have abandoned **{quest_data['quest_title']}**. A new quest may find you soon...")
            else:
                await ctx.send(" Quest abandonment cancelled. Your adventure continues!")

        except asyncio.TimeoutError:
            await ctx.send(" Abandonment cancelled (timed out).")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def queststatus(self, ctx: commands.Context):
        """Check personal quest system status (Admin only)"""

        embed = self.embed(" Personal Quest System Status", "")

        embed.add_field(
            name=" Configuration",
            value=f"**OpenAI Available**: {'Yes' if OPENAI_AVAILABLE else 'No'}\n"
                  f"**OpenAI Enabled**: {'Yes' if self.openai_enabled else 'No'}\n"
                  f"**Quest Generator Running**: {'Yes' if self.quest_generator.is_running() else 'No'}\n"
                  f"**Progress Checker Running**: {'Yes' if self.quest_progress_checker.is_running() else 'No'}",
            inline=False
        )

        # Stats
        active_quests = self.db.fetchone("SELECT COUNT(*) as count FROM personal_quests WHERE status = 'active'", ())
        completed_quests = self.db.fetchone("SELECT COUNT(*) as count FROM quest_history", ())

        embed.add_field(
            name=" Statistics",
            value=f"**Active Quests**: {self.db.row_to_dict(active_quests)['count']}\n"
                  f"**Completed Quests**: {self.db.row_to_dict(completed_quests)['count']}",
            inline=False
        )

        embed.add_field(
            name=" Info",
            value="Quest Generator: Every **25 minutes** (+ random delay)\n"
                  "Progress Checker: Every **2 minutes**\n"
                  "Minimum Level: **3**",
            inline=False
        )

        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(PersonalQuestsCog(bot))
