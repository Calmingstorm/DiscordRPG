"""SQLite database connection and helper functions"""
import sqlite3
import asyncio
import os
import json
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class Database:
    """SQLite database connection manager"""
    
    def __init__(self, db_path: str = "./discordrpg.db"):
        self.db_path = db_path
        self._connection = None
        
    def get_connection(self) -> sqlite3.Connection:
        """Get or create database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            # Enable foreign keys
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
        
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            
    def init_database(self):
        """Initialize database with schema"""
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema = f.read()
            conn = self.get_connection()
            conn.executescript(schema)
            conn.commit()
            
            # Run migrations
            self._run_migrations(conn)
            
            print("Database initialized successfully")
        else:
            print(f"Schema file not found at {schema_path}")
            
    def _run_migrations(self, conn):
        """Run database migrations"""
        try:
            # Check if alignment column exists, if not add it
            cursor = conn.execute("PRAGMA table_info(profile)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'alignment' not in columns:
                conn.execute("ALTER TABLE profile ADD COLUMN alignment TEXT DEFAULT 'neutral'")
                conn.commit()
                print("Added alignment column to profile table")

            # Check for inventory bonus stats
            cursor = conn.execute("PRAGMA table_info(inventory)")
            inv_columns = [row[1] for row in cursor.fetchall()]
            
            inventory_updates = [
                ('health_bonus', 'INTEGER DEFAULT 0'),
                ('speed_bonus', 'INTEGER DEFAULT 0'),
                ('luck_bonus', 'REAL DEFAULT 0.0'),
                ('crit_bonus', 'REAL DEFAULT 0.0'),
                ('magic_bonus', 'INTEGER DEFAULT 0'),
                ('slot_type', 'TEXT')
            ]
            
            for col_name, col_def in inventory_updates:
                if col_name not in inv_columns:
                    conn.execute(f"ALTER TABLE inventory ADD COLUMN {col_name} {col_def}")
                    print(f"Added {col_name} column to inventory table")
            
            conn.commit()

            # Create epic_adventures table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS epic_adventures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
                    adventure_type TEXT,
                    adventure_name TEXT,
                    difficulty INTEGER,
                    started_at TEXT,
                    finish_at TEXT,
                    base_xp_reward INTEGER,
                    base_gold_reward INTEGER,
                    item_quality_min INTEGER,
                    item_quality_max INTEGER,
                    status TEXT DEFAULT 'active'
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_epic_adventures_user ON epic_adventures(user_id, status)")
            conn.commit()
            
            # Fix NULL slot_type values - infer from item type
            conn.execute("""
                UPDATE inventory SET slot_type = 'weapon' 
                WHERE slot_type IS NULL AND type IN 
                ('Sword', 'Axe', 'Hammer', 'Mace', 'Dagger', 'Knife', 'Spear', 
                 'Wand', 'Staff', 'Bow', 'Crossbow', 'Greatsword', 'Halberd', 'Katana', 'Scythe')
            """)
            conn.execute("UPDATE inventory SET slot_type = 'shield' WHERE slot_type IS NULL AND type = 'Shield'")
            conn.execute("UPDATE inventory SET slot_type = 'head' WHERE slot_type IS NULL AND type = 'Helmet'")
            conn.execute("UPDATE inventory SET slot_type = 'chest' WHERE slot_type IS NULL AND type = 'Chestplate'")
            conn.execute("UPDATE inventory SET slot_type = 'legs' WHERE slot_type IS NULL AND type = 'Leggings'")
            conn.execute("UPDATE inventory SET slot_type = 'hands' WHERE slot_type IS NULL AND type = 'Gauntlets'")
            conn.execute("UPDATE inventory SET slot_type = 'feet' WHERE slot_type IS NULL AND type = 'Boots'")
            conn.commit()
                
        except Exception as e:
            print(f"Migration error: {e}")
            
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query"""
        conn = self.get_connection()
        return conn.execute(query, params)
        
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
        
    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
        
    def commit(self):
        """Commit current transaction"""
        conn = self.get_connection()
        conn.commit()
        
    def row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert sqlite3.Row to dictionary"""
        if row is None:
            return None
        return dict(row)

    # Character operations
    def create_character(self, user_id: int, name: str) -> bool:
        """Create a new character"""
        try:
            self.execute(
                """INSERT INTO profile (user_id, name, money, xp, level, last_date) 
                   VALUES (?, ?, 100, 0, 1, date('now'))""",
                (user_id, name)
            )
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def get_character(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get character data"""
        row = self.fetchone(
            "SELECT * FROM profile WHERE user_id = ?",
            (user_id,)
        )
        return self.row_to_dict(row) if row else None
        
    def get_profile(self, user_id: int):
        """Get profile as character object for race system compatibility"""
        from classes.character import Character
        data = self.get_character(user_id)
        if not data:
            return None
        
        # Create character object from database data
        char = Character(user_id, data.get('name', 'Unknown'))
        char.level = data.get('level', 1)
        char.xp = data.get('xp', 0)
        char.money = data.get('money', 100)
        char.race = data.get('race', 'Human')
        
        return char
        
    def update_profile(self, user_id: int, **kwargs) -> bool:
        """Update profile fields (alias for update_character)"""
        return self.update_character(user_id, **kwargs)
        
    def update_character(self, user_id: int, **kwargs) -> bool:
        """Update character fields"""
        if not kwargs:
            return False
            
        # If XP is being updated, recalculate level
        if 'xp' in kwargs and 'level' not in kwargs:
            new_level = min(50, 1 + int((kwargs['xp'] / 100) ** 0.5))
            kwargs['level'] = new_level
            
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        query = f"UPDATE profile SET {set_clause} WHERE user_id = ?"
        
        self.execute(query, (*kwargs.values(), user_id))
        self.commit()
        return True
        
    # Item operations
    def create_item(self, owner_id: int, name: str, item_type: str,
                   value: int, damage: int, armor: int, hand: str,
                   health_bonus: int = 0, speed_bonus: int = 0, 
                   luck_bonus: float = 0.0, crit_bonus: float = 0.0, 
                   magic_bonus: int = 0, slot_type: str = None) -> int:
        """Create a new item and return its ID"""
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
        """Get all items owned by a user"""
        rows = self.fetchall(
            "SELECT * FROM inventory WHERE owner = ? ORDER BY equipped DESC, (damage + armor) DESC",
            (user_id,)
        )
        return [self.row_to_dict(row) for row in rows]
        
    def get_equipped_items(self, user_id: int) -> List[Dict[str, Any]]:
        """Get equipped items for a user"""
        rows = self.fetchall(
            "SELECT * FROM inventory WHERE owner = ? AND equipped = 1",
            (user_id,)
        )
        return [self.row_to_dict(row) for row in rows]
        
    def equip_item(self, item_id: int, user_id: int) -> bool:
        """Equip an item"""
        cursor = self.execute(
            "UPDATE inventory SET equipped = 1 WHERE id = ? AND owner = ?",
            (item_id, user_id)
        )
        self.commit()
        return cursor.rowcount > 0
        
    def unequip_item(self, item_id: int, user_id: int) -> bool:
        """Unequip an item"""
        cursor = self.execute(
            "UPDATE inventory SET equipped = 0 WHERE id = ? AND owner = ?",
            (item_id, user_id)
        )
        self.commit()
        return cursor.rowcount > 0
        
    def delete_item(self, item_id: int) -> bool:
        """Delete an item"""
        cursor = self.execute(
            "DELETE FROM inventory WHERE id = ?",
            (item_id,)
        )
        self.commit()
        return cursor.rowcount > 0
        
    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get item by ID"""
        row = self.fetchone(
            "SELECT * FROM inventory WHERE id = ?",
            (item_id,)
        )
        return self.row_to_dict(row) if row else None

    def get_equipped_slots(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get all equipped items by slot"""
        rows = self.fetchall(
            """SELECT es.slot, i.* FROM equipped_slots es
               JOIN inventory i ON es.item_id = i.id
               WHERE es.user_id = ?""",
            (user_id,)
        )
        equipped_slots = {}
        for row in rows:
            # Convert sqlite3.Row to dict to safely access values
            row_dict = self.row_to_dict(row)
            slot = row_dict['slot']
            equipped_slots[slot] = row_dict
        return equipped_slots

    def equip_item_to_slot(self, item_id: int, user_id: int, slot: str) -> bool:
        """Equip an item to a specific slot"""
        try:
            # First, unequip any item currently in this slot
            self.execute(
                "DELETE FROM equipped_slots WHERE user_id = ? AND slot = ?",
                (user_id, slot)
            )
            
            # Then equip the new item
            self.execute(
                """INSERT INTO equipped_slots (user_id, slot, item_id)
                   VALUES (?, ?, ?)""",
                (user_id, slot, item_id)
            )
            
            # Update legacy equipped flag
            self.execute(
                "UPDATE inventory SET equipped = 1 WHERE id = ?",
                (item_id,)
            )
            
            self.commit()
            return True
        except Exception:
            return False

    def unequip_item_from_slot(self, user_id: int, slot: str) -> bool:
        """Unequip an item from a specific slot"""
        try:
            # Get the item ID first
            row = self.fetchone(
                "SELECT item_id FROM equipped_slots WHERE user_id = ? AND slot = ?",
                (user_id, slot)
            )
            
            if row:
                # Convert sqlite3.Row to dict to safely access values
                row_dict = self.row_to_dict(row)
                item_id = row_dict['item_id']
                
                # Remove from equipped_slots
                self.execute(
                    "DELETE FROM equipped_slots WHERE user_id = ? AND slot = ?",
                    (user_id, slot)
                )
                
                # Update legacy equipped flag
                self.execute(
                    "UPDATE inventory SET equipped = 0 WHERE id = ?",
                    (item_id,)
                )
                
                self.commit()
                return True
            return False
        except Exception:
            return False
        
    # Guild operations
    def create_guild(self, name: str, owner_id: int) -> Optional[int]:
        """Create a new guild"""
        try:
            # Create guild
            cursor = self.execute(
                """INSERT INTO guild (name, owner, balance)
                   VALUES (?, ?, 0)""",
                (name, owner_id)
            )
            guild_id = cursor.lastrowid
            
            # Add owner as member
            self.execute(
                """INSERT INTO guild_members (guild_id, user_id, rank)
                   VALUES (?, ?, 'Leader')""",
                (guild_id, owner_id)
            )
            
            # Update user's guild
            self.execute(
                "UPDATE profile SET guild = ? WHERE user_id = ?",
                (guild_id, owner_id)
            )
            
            self.commit()
            return guild_id
        except sqlite3.IntegrityError:
            return None
            
    def get_guild(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Get guild data"""
        row = self.fetchone(
            "SELECT * FROM guild WHERE id = ?",
            (guild_id,)
        )
        return self.row_to_dict(row) if row else None
        
    def get_guild_members(self, guild_id: int) -> List[Dict[str, Any]]:
        """Get all members of a guild"""
        rows = self.fetchall(
            """SELECT p.*, gm.rank FROM profile p 
               JOIN guild_members gm ON p.user_id = gm.user_id
               WHERE gm.guild_id = ?""",
            (guild_id,)
        )
        return [self.row_to_dict(row) for row in rows]
        
    # Market operations
    def list_item_on_market(self, item_id: int, price: int) -> bool:
        """List an item on the market"""
        try:
            self.execute(
                "INSERT INTO market (item_id, price) VALUES (?, ?)",
                (item_id, price)
            )
            self.commit()
            return True
        except sqlite3.IntegrityError:
            return False
            
    def get_market_items(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get items from market"""
        rows = self.fetchall(
            """SELECT m.*, i.* FROM market m
               JOIN inventory i ON m.item_id = i.id
               ORDER BY m.listed_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        return [self.row_to_dict(row) for row in rows]
        
    def buy_market_item(self, item_id: int, buyer_id: int) -> bool:
        """Buy an item from the market"""
        try:
            # Start transaction
            conn = self.get_connection()
            
            # Get item and market info
            market_item = self.fetchone(
                """SELECT m.price, i.owner FROM market m
                   JOIN inventory i ON m.item_id = i.id
                   WHERE m.item_id = ?""",
                (item_id,)
            )
            if not market_item:
                return False
                
            # Convert sqlite3.Row to dict to safely access values
            market_dict = self.row_to_dict(market_item)
            price = market_dict['price']
            seller_id = market_dict['owner']
            
            # Check buyer has enough money
            buyer_money_row = self.fetchone(
                "SELECT money FROM profile WHERE user_id = ?",
                (buyer_id,)
            )
            buyer_money = self.row_to_dict(buyer_money_row)['money']
            
            if buyer_money < price:
                return False
                
            # Transfer money
            self.execute(
                "UPDATE profile SET money = money - ? WHERE user_id = ?",
                (price, buyer_id)
            )
            self.execute(
                "UPDATE profile SET money = money + ? WHERE user_id = ?",
                (price, seller_id)
            )
            
            # Transfer item ownership
            self.execute(
                "UPDATE inventory SET owner = ?, equipped = 0 WHERE id = ?",
                (buyer_id, item_id)
            )
            
            # Remove from market
            self.execute(
                "DELETE FROM market WHERE item_id = ?",
                (item_id,)
            )
            
            self.commit()
            return True
        except Exception:
            return False
            
    # Adventure operations
    def start_adventure(self, user_id: int, adventure_name: str, 
                       difficulty: int, duration_seconds: int) -> bool:
        """Start an adventure"""
        try:
            # Calculate finish time
            finish_time = datetime.now().timestamp() + duration_seconds
            
            self.execute(
                """INSERT INTO adventures (user_id, adventure_name, difficulty, finish_at)
                   VALUES (?, ?, ?, datetime(?, 'unixepoch'))""",
                (user_id, adventure_name, difficulty, finish_time)
            )
            
            self.execute(
                "UPDATE profile SET last_adventure = datetime('now') WHERE user_id = ?",
                (user_id,)
            )
            
            self.commit()
            return True
        except Exception:
            return False
            
    def get_active_adventure(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active adventure"""
        row = self.fetchone(
            """SELECT * FROM adventures 
               WHERE user_id = ? AND status = 'active'
               ORDER BY started_at DESC LIMIT 1""",
            (user_id,)
        )
        return self.row_to_dict(row) if row else None
        
    def complete_adventure(self, adventure_id: int, success: bool) -> bool:
        """Mark adventure as completed"""
        status = 'completed' if success else 'failed'
        cursor = self.execute(
            "UPDATE adventures SET status = ? WHERE id = ?",
            (status, adventure_id)
        )
        self.commit()
        return cursor.rowcount > 0
        
    # Cooldown operations
    def get_cooldowns(self, user_id: int) -> Dict[str, Optional[str]]:
        """Get all cooldowns for a user"""
        row = self.fetchone(
            "SELECT * FROM cooldowns WHERE user_id = ?",
            (user_id,)
        )
        if row:
            return self.row_to_dict(row)
        else:
            # Create cooldown entry if doesn't exist
            self.execute(
                "INSERT OR IGNORE INTO cooldowns (user_id) VALUES (?)",
                (user_id,)
            )
            self.commit()
            return {}
            
    def set_cooldown(self, user_id: int, cooldown_type: str) -> bool:
        """Set a cooldown timestamp"""
        # Validate cooldown_type to prevent SQL injection
        valid_cooldown_types = {
            'daily', 'adventure', 'battle', 'prayer', 'sacrifice', 
            'blessing', 'raid', 'gambling', 'shop'
        }
        if cooldown_type not in valid_cooldown_types:
            return False
            
        # Ensure cooldown entry exists
        self.execute(
            "INSERT OR IGNORE INTO cooldowns (user_id) VALUES (?)",
            (user_id,)
        )
        
        query = f"UPDATE cooldowns SET {cooldown_type} = datetime('now') WHERE user_id = ?"
        self.execute(query, (user_id,))
        self.commit()
        return True
        
    # Transaction logging
    def log_transaction(self, from_user: Optional[int], to_user: Optional[int],
                       amount: int, subject: str, info: Dict[str, Any]) -> bool:
        """Log a transaction"""
        self.execute(
            """INSERT INTO transactions (from_user, to_user, amount, subject, info)
               VALUES (?, ?, ?, ?, ?)""",
            (from_user, to_user, amount, subject, json.dumps(info))
        )
        self.commit()
        return True
        
    # Leaderboard operations
    def get_leaderboard(self, category: str = "level", limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard data"""
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
            f"""SELECT user_id, name, level, xp, money, pvpwins, pvplosses, completed
                FROM profile 
                ORDER BY {order_by} 
                LIMIT ?""",
            (limit,)
        )
        return [self.row_to_dict(row) for row in rows]