-- SQLite Database Schema for Full IdleRPG

-- Users/Profile table
CREATE TABLE IF NOT EXISTS profile (
    user_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    money INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    class TEXT DEFAULT 'Novice',
    race TEXT DEFAULT 'Human',
    health INTEGER DEFAULT 100,
    speed INTEGER DEFAULT 10,
    pvpwins INTEGER DEFAULT 0,
    pvplosses INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    kills INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,
    god TEXT,
    favor INTEGER DEFAULT 0,
    luck REAL DEFAULT 1.0,
    marriage INTEGER,
    guild INTEGER,
    background TEXT DEFAULT 'https://i.imgur.com/default.png',
    description TEXT,
    colour INTEGER DEFAULT 0,
    donations INTEGER DEFAULT 0,
    raidstats INTEGER DEFAULT 0,
    atkmultiply REAL DEFAULT 1.0,
    defmultiply REAL DEFAULT 1.0,
    crates_common INTEGER DEFAULT 0,
    crates_uncommon INTEGER DEFAULT 0,
    crates_rare INTEGER DEFAULT 0,
    crates_magic INTEGER DEFAULT 0,
    crates_legendary INTEGER DEFAULT 0,
    crates_mystery INTEGER DEFAULT 0,
    material_scrap INTEGER DEFAULT 0,
    material_dust INTEGER DEFAULT 0,
    material_essence INTEGER DEFAULT 0,
    last_date TEXT,
    streak INTEGER DEFAULT 0,
    vote_ban INTEGER DEFAULT 0,
    has_character INTEGER DEFAULT 1,
    reset_points INTEGER DEFAULT 2,
    last_adventure TEXT,
    adventure_alert INTEGER DEFAULT 1,
    alignment TEXT DEFAULT 'neutral',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items/Inventory table
CREATE TABLE IF NOT EXISTS inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    value INTEGER DEFAULT 0,
    type TEXT NOT NULL CHECK(type IN ('Sword', 'Shield', 'Axe', 'Bow', 'Spear', 'Wand', 'Dagger', 'Knife', 'Hammer', 'Staff', 'Mace', 'Crossbow', 'Greatsword', 'Halberd', 'Katana', 'Scythe', 'Helmet', 'Chestplate', 'Leggings', 'Gauntlets', 'Boots')),
    damage INTEGER DEFAULT 0,
    armor INTEGER DEFAULT 0,
    health_bonus INTEGER DEFAULT 0,
    speed_bonus INTEGER DEFAULT 0,
    luck_bonus REAL DEFAULT 0.0,
    crit_bonus REAL DEFAULT 0.0,
    magic_bonus INTEGER DEFAULT 0,
    slot_type TEXT,
    upgrade_level INTEGER DEFAULT 0,
    hand TEXT CHECK(hand IN ('left', 'right', 'both', 'any')),
    equipped INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guilds table
CREATE TABLE IF NOT EXISTS guild (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    owner INTEGER REFERENCES profile(user_id),
    balance INTEGER DEFAULT 0,
    memberlimit INTEGER DEFAULT 50,
    wins INTEGER DEFAULT 0,
    loses INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    privacy INTEGER DEFAULT 1,
    color INTEGER,
    upgrade INTEGER DEFAULT 0,
    alliance INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild members
CREATE TABLE IF NOT EXISTS guild_members (
    guild_id INTEGER REFERENCES guild(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    rank TEXT DEFAULT 'Member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id, user_id)
);

-- Alliances table
CREATE TABLE IF NOT EXISTS alliance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    icon TEXT,
    owner INTEGER REFERENCES guild(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cities table
CREATE TABLE IF NOT EXISTS cities (
    name TEXT PRIMARY KEY,
    owner INTEGER REFERENCES alliance(id),
    level INTEGER DEFAULT 1,
    buildings_thief INTEGER DEFAULT 0,
    buildings_raid INTEGER DEFAULT 0,
    buildings_trade INTEGER DEFAULT 0,
    buildings_adventure INTEGER DEFAULT 0
);

-- Market/Trading
CREATE TABLE IF NOT EXISTS market (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    price INTEGER NOT NULL,
    listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading offers
CREATE TABLE IF NOT EXISTS trade_offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    to_user INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES inventory(id) ON DELETE CASCADE,
    price INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- Marriages
CREATE TABLE IF NOT EXISTS marriages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1 INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    user2 INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    married_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    lovescore INTEGER DEFAULT 0,
    UNIQUE(user1, user2)
);

-- Children
CREATE TABLE IF NOT EXISTS children (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    parent1 INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    parent2 INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    age INTEGER DEFAULT 0,
    gender TEXT,
    born_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Adventures/Quests
CREATE TABLE IF NOT EXISTS adventures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    adventure_name TEXT,
    difficulty INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finish_at TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- Tournament data
CREATE TABLE IF NOT EXISTS tournaments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_by INTEGER REFERENCES profile(user_id),
    prize_money INTEGER DEFAULT 0,
    participants TEXT, -- JSON array
    winner INTEGER,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    status TEXT DEFAULT 'pending'
);

-- Battle logs
CREATE TABLE IF NOT EXISTS battle_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attacker INTEGER REFERENCES profile(user_id),
    defender INTEGER REFERENCES profile(user_id),
    winner INTEGER,
    battle_type TEXT,
    damage_dealt INTEGER,
    damage_taken INTEGER,
    money_stolen INTEGER,
    fought_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Raid bosses
CREATE TABLE IF NOT EXISTS raid_bosses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    hp INTEGER NOT NULL,
    max_hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    active INTEGER DEFAULT 1,
    participants TEXT, -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pet data (for Rangers)
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner INTEGER REFERENCES profile(user_id) ON DELETE CASCADE UNIQUE,
    name TEXT NOT NULL,
    hunger INTEGER DEFAULT 100,
    thirst INTEGER DEFAULT 100,
    love INTEGER DEFAULT 0,
    joy INTEGER DEFAULT 100,
    last_fed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_watered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cooldowns
CREATE TABLE IF NOT EXISTS cooldowns (
    user_id INTEGER PRIMARY KEY REFERENCES profile(user_id) ON DELETE CASCADE,
    daily TIMESTAMP,
    vote TIMESTAMP,
    adventure TIMESTAMP,
    pray TIMESTAMP,
    sacrifice TIMESTAMP,
    steal TIMESTAMP,
    hunt TIMESTAMP
);

-- Transaction logs
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user INTEGER,
    to_user INTEGER,
    amount INTEGER,
    subject TEXT,
    info TEXT, -- JSON data
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Server settings
CREATE TABLE IF NOT EXISTS server_settings (
    guild_id INTEGER PRIMARY KEY,
    prefix TEXT DEFAULT '!',
    language TEXT DEFAULT 'en_US',
    currency_emoji TEXT,
    welcome_channel INTEGER,
    game_channel INTEGER
);

-- User settings
CREATE TABLE IF NOT EXISTS user_settings (
    user_id INTEGER PRIMARY KEY REFERENCES profile(user_id) ON DELETE CASCADE,
    language TEXT DEFAULT 'en_US',
    notifications INTEGER DEFAULT 1,
    dm_notifications INTEGER DEFAULT 0,
    mention_notifications INTEGER DEFAULT 1
);

-- Gods
CREATE TABLE IF NOT EXISTS gods (
    name TEXT PRIMARY KEY,
    description TEXT,
    luck_bonus REAL DEFAULT 1.0,
    sacrifice_multiplier REAL DEFAULT 1.0,
    top_followers TEXT -- JSON array
);

-- Insert default gods
INSERT OR IGNORE INTO gods (name, description, luck_bonus, sacrifice_multiplier) VALUES
    ('Chaos', 'God of randomness and disorder', 1.2, 0.8),
    ('Order', 'God of structure and planning', 0.9, 1.1),
    ('War', 'God of combat and conflict', 1.0, 1.0),
    ('Nature', 'God of life and growth', 1.1, 0.9),
    ('Death', 'God of endings and rebirth', 0.8, 1.3);

-- Crate history
CREATE TABLE IF NOT EXISTS crate_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    crate_type TEXT,
    item_name TEXT,
    item_stats INTEGER,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Event participation
CREATE TABLE IF NOT EXISTS event_participation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    event_type TEXT,
    event_data TEXT, -- JSON
    participated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Penalties table for tracking IdleRPG penalties
CREATE TABLE IF NOT EXISTS penalties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    penalty_type TEXT NOT NULL,
    penalty_seconds INTEGER NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Divine blessings table for temporary player buffs
CREATE TABLE IF NOT EXISTS divine_blessings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES profile(user_id) ON DELETE CASCADE,
    effect TEXT NOT NULL,
    value REAL NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    blessing_name TEXT NOT NULL,
    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Epic/Legendary Adventures table
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
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_inventory_owner ON inventory(owner);
CREATE INDEX IF NOT EXISTS idx_inventory_equipped ON inventory(owner, equipped);
CREATE INDEX IF NOT EXISTS idx_market_price ON market(price);
CREATE INDEX IF NOT EXISTS idx_adventures_user ON adventures(user_id, status);
CREATE INDEX IF NOT EXISTS idx_epic_adventures_user ON epic_adventures(user_id, status);
CREATE INDEX IF NOT EXISTS idx_battle_logs_users ON battle_logs(attacker, defender);
CREATE INDEX IF NOT EXISTS idx_transactions_users ON transactions(from_user, to_user);
CREATE INDEX IF NOT EXISTS idx_cooldowns_user ON cooldowns(user_id);
CREATE INDEX IF NOT EXISTS idx_penalties_user ON penalties(user_id);
CREATE INDEX IF NOT EXISTS idx_divine_blessings_user ON divine_blessings(user_id, expires_at);