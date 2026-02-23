"""MariaDB database connection and helper functions"""
import pymysql
import pymysql.cursors
import re
import os
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime


class Database:
    """MariaDB database connection manager"""

    def __init__(self, db_path: str = None):
        # db_path kept for signature compat but ignored
        self.host = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'discordrpg')
        self.password = os.getenv('DB_PASS', '')
        self.database = os.getenv('DB_NAME', 'discordrpg')
        self._connection = None

    # --- SQL translation layer ---
    @staticmethod
    def _translate_sql(query: str) -> str:
        """Translate SQLite-flavored SQL to MariaDB"""
        # Parameter placeholders: ? → %s
        query = query.replace('?', '%s')
        # INSERT OR IGNORE → INSERT IGNORE
        query = re.sub(r'INSERT\s+OR\s+IGNORE', 'INSERT IGNORE', query, flags=re.IGNORECASE)
        # INSERT OR REPLACE → REPLACE
        query = re.sub(r'INSERT\s+OR\s+REPLACE', 'REPLACE', query, flags=re.IGNORECASE)
        # datetime('now', '-N day(s)') → DATE_SUB(NOW(), INTERVAL N DAY)
        query = re.sub(
            r"datetime\s*\(\s*'now'\s*,\s*'-(\d+)\s+days?'\s*\)",
            r'DATE_SUB(NOW(), INTERVAL \1 DAY)',
            query, flags=re.IGNORECASE
        )
        # datetime('now') → NOW()
        query = re.sub(r"datetime\s*\(\s*'now'\s*\)", 'NOW()', query, flags=re.IGNORECASE)
        # date('now') → CURDATE()
        query = re.sub(r"date\s*\(\s*'now'\s*\)", 'CURDATE()', query, flags=re.IGNORECASE)
        # datetime(%s, 'unixepoch') → FROM_UNIXTIME(%s)
        query = re.sub(
            r"datetime\s*\(\s*%s\s*,\s*'unixepoch'\s*\)",
            'FROM_UNIXTIME(%s)',
            query, flags=re.IGNORECASE
        )
        return query

    # --- Connection management ---
    def get_connection(self) -> pymysql.Connection:
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        else:
            self._connection.ping(reconnect=True)
        return self._connection

    def close(self):
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None

    def init_database(self):
        """Run migrations (schema already exists in MariaDB)"""
        conn = self.get_connection()
        self._run_migrations(conn)
        print("Database initialized successfully")

    def _run_migrations(self, conn):
        """Run database migrations"""
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'profile'",
                (self.database,)
            )
            columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

            if 'alignment' not in columns:
                cursor.execute("ALTER TABLE profile ADD COLUMN alignment VARCHAR(32) DEFAULT 'neutral'")
                conn.commit()
                print("Added alignment column to profile table")

            if 'ascension_respec_used' not in columns:
                cursor.execute("ALTER TABLE profile ADD COLUMN ascension_respec_used TINYINT(1) DEFAULT 0")
                conn.commit()
                print("Added ascension_respec_used column to profile table")

            if 'previous_class' not in columns:
                cursor.execute("ALTER TABLE profile ADD COLUMN previous_class VARCHAR(64)")
                conn.commit()
                print("Added previous_class column to profile table")

            if 'sell_confirmation' not in columns:
                cursor.execute("ALTER TABLE profile ADD COLUMN sell_confirmation TINYINT(1) DEFAULT 1")
                conn.commit()
                print("Added sell_confirmation column to profile table")

            self._migrate_legacy_equipment(conn)

        except Exception as e:
            print(f"Migration error: {e}")

    def _migrate_legacy_equipment(self, conn):
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT i.id, i.owner, i.slot_type, i.name, i.damage + i.armor as power
                FROM inventory i
                LEFT JOIN equipped_slots es ON i.id = es.item_id
                WHERE i.equipped = 1 AND es.item_id IS NULL AND i.slot_type IS NOT NULL
                ORDER BY i.owner, i.slot_type, (i.damage + i.armor) DESC
            ''')
            legacy_items = cursor.fetchall()

            if not legacy_items:
                return

            print(f"Migrating {len(legacy_items)} legacy equipped items...")

            from collections import defaultdict
            user_slots = defaultdict(list)
            for item in legacy_items:
                user_slots[(item['owner'], item['slot_type'])].append(
                    (item['id'], item['name'], item['power'])
                )

            fixed_conflicts = 0
            migrated_items = 0

            for (owner, slot_type), items in user_slots.items():
                if len(items) > 1:
                    items.sort(key=lambda x: x[2], reverse=True)
                    best_item = items[0]
                    for item_id, name, power in items[1:]:
                        cursor.execute("UPDATE inventory SET equipped = 0 WHERE id = %s", (item_id,))
                        fixed_conflicts += 1
                    item_id, name, power = best_item
                    cursor.execute(
                        "REPLACE INTO equipped_slots (user_id, slot, item_id) VALUES (%s, %s, %s)",
                        (owner, slot_type, item_id)
                    )
                    migrated_items += 1
                else:
                    item_id, name, power = items[0]
                    cursor.execute(
                        "REPLACE INTO equipped_slots (user_id, slot, item_id) VALUES (%s, %s, %s)",
                        (owner, slot_type, item_id)
                    )
                    migrated_items += 1

            conn.commit()
            print(f"Equipment migration complete: {migrated_items} items migrated, {fixed_conflicts} conflicts resolved")

        except Exception as e:
            print(f"Equipment migration error: {e}")

    # --- Core query methods ---
    def execute(self, query: str, params: tuple = ()) -> pymysql.cursors.DictCursor:
        query = self._translate_sql(query)
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def commit(self):
        conn = self.get_connection()
        conn.commit()

    def row_to_dict(self, row) -> Optional[Dict[str, Any]]:
        """Convert row to dict — DictCursor already returns dicts"""
        if row is None:
            return None
        return dict(row)

    # --- Character operations ---
    def create_character(self, user_id: int, name: str) -> bool:
        try:
            self.execute(
                """INSERT INTO profile (user_id, name, money, xp, level, last_date)
                   VALUES (?, ?, 100, 0, 1, CURDATE())""",
                (user_id, name)
            )
            self.commit()
            return True
        except pymysql.err.IntegrityError:
            return False

    def get_character(self, user_id: int) -> Optional[Dict[str, Any]]:
        row = self.fetchone("SELECT * FROM profile WHERE user_id = ?", (user_id,))
        return self.row_to_dict(row) if row else None

    def get_profile(self, user_id: int):
        from classes.character import Character
        data = self.get_character(user_id)
        if not data:
            return None
        char = Character(user_id, data.get('name', 'Unknown'))
        char.level = data.get('level', 1)
        char.xp = data.get('xp', 0)
        char.money = data.get('money', 100)
        char.race = data.get('race', 'Human')
        char.luck = data.get('luck', 1.0)
        return char

    def update_profile(self, user_id: int, **kwargs) -> bool:
        return self.update_character(user_id, **kwargs)

    PROFILE_COLUMNS = {
        'name', 'money', 'xp', 'level', 'class', 'race', 'pvpwins', 'pvplosses',
        'deaths', 'kills', 'completed', 'god', 'favor', 'luck', 'marriage', 'guild',
        'background', 'description', 'colour', 'donations', 'raidstats',
        'atkmultiply', 'defmultiply', 'crates_common', 'crates_uncommon',
        'crates_rare', 'crates_magic', 'crates_legendary', 'crates_mystery',
        'last_date', 'streak', 'vote_ban', 'has_character', 'reset_points',
        'last_adventure', 'adventure_alert', 'alignment',
        'epic_adventures_completed', 'legendary_adventures_completed',
        'last_epic_adventure', 'ascension_respec_used', 'previous_class',
        'sell_confirmation',
    }

    def update_character(self, user_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        # Validate column names to prevent SQL injection
        invalid = set(kwargs.keys()) - self.PROFILE_COLUMNS
        if invalid:
            raise ValueError(f"Invalid profile columns: {invalid}")
        if 'xp' in kwargs and 'level' not in kwargs:
            new_level = min(999, 1 + int((kwargs['xp'] / 100) ** 0.5))
            kwargs['level'] = new_level
        set_clause = ", ".join([f"`{k}` = %s" for k in kwargs.keys()])
        query = f"UPDATE profile SET {set_clause} WHERE user_id = %s"
        self._execute_raw(query, (*kwargs.values(), user_id))
        self.commit()
        return True

    def _execute_raw(self, query: str, params: tuple = ()):
        """Execute without SQL translation (already MariaDB-native)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor

    # --- Item operations ---
    def create_item(self, owner_id: int, name: str, item_type: str,
                    value: int, damage: int, armor: int, hand: str,
                    health_bonus: int = 0, speed_bonus: int = 0,
                    luck_bonus: float = 0.0, crit_bonus: float = 0.0,
                    magic_bonus: int = 0, slot_type: str = None) -> int:
        cursor = self.execute(
            """INSERT INTO inventory (owner, name, value, type, damage, armor, hand,
                                     health_bonus, speed_bonus, luck_bonus, crit_bonus,
                                     magic_bonus, slot_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (owner_id, name, value, item_type, damage, armor, hand,
             health_bonus, speed_bonus, luck_bonus, crit_bonus, magic_bonus, slot_type)
        )
        self.commit()
        return cursor.lastrowid

    def get_user_items(self, user_id: int) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            "SELECT * FROM inventory WHERE owner = ? ORDER BY equipped DESC, (damage + armor) DESC",
            (user_id,)
        )
        return [self.row_to_dict(row) for row in rows]

    def get_equipped_items(self, user_id: int) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            "SELECT * FROM inventory WHERE owner = ? AND equipped = 1",
            (user_id,)
        )
        return [self.row_to_dict(row) for row in rows]

    def equip_item(self, item_id: int, user_id: int) -> bool:
        cursor = self.execute(
            "UPDATE inventory SET equipped = 1 WHERE id = ? AND owner = ?",
            (item_id, user_id)
        )
        self.commit()
        return cursor.rowcount > 0

    def unequip_item(self, item_id: int, user_id: int) -> bool:
        cursor = self.execute(
            "UPDATE inventory SET equipped = 0 WHERE id = ? AND owner = ?",
            (item_id, user_id)
        )
        self.commit()
        return cursor.rowcount > 0

    def delete_item(self, item_id: int) -> bool:
        cursor = self.execute("DELETE FROM inventory WHERE id = ?", (item_id,))
        self.commit()
        return cursor.rowcount > 0

    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        row = self.fetchone("SELECT * FROM inventory WHERE id = ?", (item_id,))
        return self.row_to_dict(row) if row else None

    def get_equipped_slots(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        rows = self.fetchall(
            """SELECT es.slot, i.* FROM equipped_slots es
               JOIN inventory i ON es.item_id = i.id
               WHERE es.user_id = ?""",
            (user_id,)
        )
        equipped_slots = {}
        for row in rows:
            row_dict = self.row_to_dict(row)
            slot = row_dict['slot']
            equipped_slots[slot] = row_dict
        return equipped_slots

    def equip_item_to_slot(self, item_id: int, user_id: int, slot: str) -> bool:
        try:
            self.execute("DELETE FROM equipped_slots WHERE user_id = ? AND slot = ?", (user_id, slot))
            self.execute(
                "INSERT INTO equipped_slots (user_id, slot, item_id) VALUES (?, ?, ?)",
                (user_id, slot, item_id)
            )
            self.execute("UPDATE inventory SET equipped = 1 WHERE id = ?", (item_id,))
            self.commit()
            return True
        except Exception:
            self.get_connection().rollback()
            return False

    def unequip_item_from_slot(self, user_id: int, slot: str) -> bool:
        try:
            row = self.fetchone(
                "SELECT item_id FROM equipped_slots WHERE user_id = ? AND slot = ?",
                (user_id, slot)
            )
            if row:
                row_dict = self.row_to_dict(row)
                item_id = row_dict['item_id']
                self.execute("DELETE FROM equipped_slots WHERE user_id = ? AND slot = ?", (user_id, slot))
                self.execute("UPDATE inventory SET equipped = 0 WHERE id = ?", (item_id,))
                self.commit()
                return True
            return False
        except Exception:
            self.get_connection().rollback()
            return False

    # --- Guild operations ---
    def create_guild(self, name: str, owner_id: int) -> Optional[int]:
        try:
            cursor = self.execute(
                "INSERT INTO guild (name, owner, balance) VALUES (?, ?, 0)",
                (name, owner_id)
            )
            guild_id = cursor.lastrowid
            self.execute(
                "INSERT INTO guild_members (guild_id, user_id, `rank`) VALUES (?, ?, 'Leader')",
                (guild_id, owner_id)
            )
            self.execute("UPDATE profile SET guild = ? WHERE user_id = ?", (guild_id, owner_id))
            self.commit()
            return guild_id
        except pymysql.err.IntegrityError:
            return None

    def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        row = self.fetchone("SELECT * FROM guild WHERE id = ?", (guild_id,))
        return self.row_to_dict(row) if row else None

    def get_guild_members(self, guild_id: int) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            """SELECT p.*, gm.`rank` FROM profile p
               JOIN guild_members gm ON p.user_id = gm.user_id
               WHERE gm.guild_id = ?""",
            (guild_id,)
        )
        return [self.row_to_dict(row) for row in rows]

    # --- Market operations ---
    def list_item_on_market(self, item_id: int, price: int) -> bool:
        try:
            self.execute("INSERT INTO market (item_id, price) VALUES (?, ?)", (item_id, price))
            self.commit()
            return True
        except pymysql.err.IntegrityError:
            return False

    def get_market_items(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        rows = self.fetchall(
            """SELECT m.*, i.* FROM market m
               JOIN inventory i ON m.item_id = i.id
               ORDER BY m.listed_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        return [self.row_to_dict(row) for row in rows]

    def buy_market_item(self, item_id: int, buyer_id: int) -> bool:
        try:
            market_item = self.fetchone(
                """SELECT m.price, i.owner FROM market m
                   JOIN inventory i ON m.item_id = i.id
                   WHERE m.item_id = ?""",
                (item_id,)
            )
            if not market_item:
                return False
            market_dict = self.row_to_dict(market_item)
            price = market_dict['price']
            seller_id = market_dict['owner']

            # Atomic money deduction — WHERE clause ensures sufficient funds
            cursor = self.execute(
                "UPDATE profile SET money = money - ? WHERE user_id = ? AND money >= ?",
                (price, buyer_id, price)
            )
            if cursor.rowcount == 0:
                return False  # Insufficient funds

            self.execute("UPDATE profile SET money = money + ? WHERE user_id = ?", (price, seller_id))
            self.execute("UPDATE inventory SET owner = ?, equipped = 0 WHERE id = ?", (buyer_id, item_id))
            self.execute("DELETE FROM market WHERE item_id = ?", (item_id,))
            self.commit()
            return True
        except Exception:
            self.get_connection().rollback()
            return False

    # --- Adventure operations ---
    def start_adventure(self, user_id: int, adventure_name: str,
                        difficulty: int, duration_seconds: int) -> bool:
        try:
            finish_time = datetime.now().timestamp() + duration_seconds
            self._execute_raw(
                """INSERT INTO adventures (user_id, adventure_name, difficulty, finish_at)
                   VALUES (%s, %s, %s, FROM_UNIXTIME(%s))""",
                (user_id, adventure_name, difficulty, finish_time)
            )
            self._execute_raw("UPDATE profile SET last_adventure = NOW() WHERE user_id = %s", (user_id,))
            self.commit()
            return True
        except Exception:
            self.get_connection().rollback()
            return False

    def get_active_adventure(self, user_id: int) -> Optional[Dict[str, Any]]:
        row = self.fetchone(
            """SELECT * FROM adventures
               WHERE user_id = ? AND status = 'active'
               ORDER BY started_at DESC LIMIT 1""",
            (user_id,)
        )
        return self.row_to_dict(row) if row else None

    def complete_adventure(self, adventure_id: int, success: bool) -> bool:
        status = 'completed' if success else 'failed'
        cursor = self.execute("UPDATE adventures SET status = ? WHERE id = ?", (status, adventure_id))
        self.commit()
        return cursor.rowcount > 0

    # --- Cooldown operations ---
    def get_cooldowns(self, user_id: int) -> Dict[str, Any]:
        row = self.fetchone("SELECT * FROM cooldowns WHERE user_id = ?", (user_id,))
        if row:
            return self.row_to_dict(row)
        else:
            self.execute("INSERT IGNORE INTO cooldowns (user_id) VALUES (%s)", (user_id,))
            self.commit()
            return {}

    def set_cooldown(self, user_id: int, cooldown_type: str) -> bool:
        valid_cooldown_types = {
            'daily', 'vote', 'adventure', 'pray', 'sacrifice',
            'steal', 'hunt'
        }
        if cooldown_type not in valid_cooldown_types:
            return False
        self.execute("INSERT IGNORE INTO cooldowns (user_id) VALUES (%s)", (user_id,))
        self._execute_raw(
            f"UPDATE cooldowns SET `{cooldown_type}` = NOW() WHERE user_id = %s",
            (user_id,)
        )
        self.commit()
        return True

    # --- Transaction logging ---
    def log_transaction(self, from_user: Optional[int], to_user: Optional[int],
                        amount: int, subject: str, info: Dict[str, Any]) -> bool:
        self.execute(
            """INSERT INTO transactions (from_user, to_user, amount, subject, info)
               VALUES (?, ?, ?, ?, ?)""",
            (from_user, to_user, amount, subject, json.dumps(info))
        )
        self.commit()
        return True

    # --- Leaderboard ---
    def get_leaderboard(self, category: str = "level", limit: int = 10) -> List[Dict[str, Any]]:
        valid_categories = {
            "level": "level DESC, xp DESC",
            "money": "money DESC",
            "pvp": "pvpwins DESC",
            "completed": "completed DESC"
        }
        if category not in valid_categories:
            category = "level"
        order_by = valid_categories[category]
        rows = self.fetchall(
            f"SELECT user_id, name, level, xp, money, pvpwins, pvplosses, completed "
            f"FROM profile ORDER BY {order_by} LIMIT %s",
            (limit,)
        )
        return [self.row_to_dict(row) for row in rows]
