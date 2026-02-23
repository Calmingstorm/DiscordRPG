"""
Season Reset Script for DiscordRPG (MariaDB)
Wipes all player data while preserving user registrations.
Creates a mysqldump backup before resetting.
"""
import os
import subprocess
import gzip
import shutil
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'discordrpg')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'discordrpg')


def create_backup():
    """Create a mysqldump backup before reset"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"pre_season_reset_{timestamp}.sql")

    env = os.environ.copy()
    env['MYSQL_PWD'] = DB_PASS

    result = subprocess.run(
        ['mysqldump', '-h', DB_HOST, '-u', DB_USER,
         '--single-transaction', '--routines', '--triggers', DB_NAME],
        capture_output=True, timeout=120, env=env
    )

    if result.returncode != 0:
        print(f"Backup FAILED: {result.stderr.decode()}")
        return None

    with open(backup_path, 'wb') as f:
        f.write(result.stdout)

    compressed_path = backup_path + ".gz"
    with open(backup_path, 'rb') as f_in:
        with gzip.open(compressed_path, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(backup_path)

    size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
    print(f"Backup created: {compressed_path} ({size_mb:.2f} MB)")
    return compressed_path


def main():
    import pymysql

    # Backup first
    backup_path = create_backup()
    if not backup_path:
        print("Aborting: backup failed.")
        return

    conn = pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASS,
        database=DB_NAME, charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor, autocommit=False
    )
    cursor = conn.cursor()

    # Count players before reset
    cursor.execute("SELECT COUNT(*) AS cnt FROM profile")
    player_count = cursor.fetchone()['cnt']
    print(f"Resetting {player_count} players...")

    # 1. Reset all profile stats to defaults (keep identity & preferences)
    cursor.execute("""
        UPDATE profile SET
            money = 0,
            xp = 0,
            level = 1,
            `class` = 'Novice',
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
            ascension_respec_used = 0,
            previous_class = NULL
    """)
    print(f"  Reset {cursor.rowcount} profile stats")

    # 2. Wipe tables in FK-safe order (children before parents)
    # Disable FK checks temporarily for clean wipe
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    tables_to_wipe = [
        'equipped_slots',
        'market',
        'trade_offers',
        'quest_chapters',
        'quest_history',
        'personal_quests',
        'divine_blessings',
        'event_participation',
        'crate_history',
        'penalties',
        'cooldowns',
        'transactions',
        'battle_logs',
        'raid_bosses',
        'epic_adventures',
        'adventures',
        'inventory',
        'marriages',
        'children',
        'tournaments',
        'pets',
        'guild_members',
    ]

    for table in tables_to_wipe:
        try:
            cursor.execute(f"DELETE FROM `{table}`")
            print(f"  Wiped {table}: {cursor.rowcount} rows")
        except Exception as e:
            print(f"  Skipped {table}: {e}")

    # 3. Reset guilds and alliances (order matters: alliance refs guild)
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

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

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
