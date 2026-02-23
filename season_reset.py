"""
Season Reset Script for DiscordRPG
Wipes all player data while preserving user registrations.
"""
import sqlite3
import shutil
from datetime import datetime

DB_PATH = '/home/calmingstorm/scripts/discordrpg/discordrpg.db'

def main():
    # Backup first
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup created: {backup_path}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Count players before reset
    cursor.execute("SELECT COUNT(*) FROM profile")
    player_count = cursor.fetchone()[0]
    print(f"Resetting {player_count} players...")

    # 1. Reset all profile stats to defaults (keep identity & preferences)
    cursor.execute("""
        UPDATE profile SET
            money = 0,
            xp = 0,
            level = 1,
            class = 'Novice',
            race = 'Human',
            pvpwins = 0,
            pvplosses = 0,
            deaths = 0,
            kills = 0,
            completed = 0,
            god = NULL,
            favor = 0,
            luck = 1.0,
            marriage = NULL,
            guild = NULL,
            raidstats = 0,
            atkmultiply = 1.0,
            defmultiply = 1.0,
            crates_common = 0,
            crates_uncommon = 0,
            crates_rare = 0,
            crates_magic = 0,
            crates_legendary = 0,
            crates_mystery = 0,
            last_date = NULL,
            streak = 0,
            last_adventure = NULL,
            epic_adventures_completed = 0,
            legendary_adventures_completed = 0,
            last_epic_adventure = NULL,
            reset_points = 2,
            ascension_respec_used = FALSE,
            previous_class = NULL
    """)
    print(f"  Reset {cursor.rowcount} profile stats")

    # 2. Wipe all game data tables
    tables_to_wipe = [
        'inventory',
        'equipped_slots',
        'epic_adventures',
        'adventures',
        'battle_logs',
        'raid_bosses',
        'market',
        'trade_offers',
        'marriages',
        'children',
        'tournaments',
        'pets',
        'cooldowns',
        'transactions',
        'crate_history',
        'event_participation',
        'penalties',
        'divine_blessings',
        'personal_quests',
        'quest_chapters',
        'quest_history',
        'guild_members',
    ]

    for table in tables_to_wipe:
        try:
            cursor.execute(f"DELETE FROM {table}")
            print(f"  Wiped {table}: {cursor.rowcount} rows")
        except Exception as e:
            print(f"  Skipped {table}: {e}")

    # 3. Reset guilds and alliances
    try:
        cursor.execute("DELETE FROM alliance")
        print(f"  Wiped alliance: {cursor.rowcount} rows")
    except Exception as e:
        print(f"  Skipped alliance: {e}")

    try:
        cursor.execute("DELETE FROM guild")
        print(f"  Wiped guild: {cursor.rowcount} rows")
    except Exception as e:
        print(f"  Skipped guild: {e}")

    conn.commit()
    conn.close()

    print(f"\nSeason reset complete!")
    print(f"  {player_count} player profiles preserved (stats reset)")
    print(f"  All game data wiped")
    print(f"  Backup at: {backup_path}")

if __name__ == '__main__':
    confirm = input("WARNING: This will wipe ALL player progress. Type 'RESET' to confirm: ")
    if confirm == 'RESET':
        main()
    else:
        print("Aborted.")
