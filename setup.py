#!/usr/bin/env python3
"""DiscordRPG Bot Setup Script"""

import os
import shutil
import subprocess
import sys


def check_python_version():
    """Ensure Python 3.8+"""
    if sys.version_info < (3, 8):
        print("Python 3.8 or higher is required.")
        return False
    print(f"Python {sys.version_info.major}.{sys.version_info.minor} - OK")
    return True


def check_dependencies():
    """Check if required Python packages are installed"""
    required = {
        'discord': 'discord.py',
        'dotenv': 'python-dotenv',
        'pymysql': 'pymysql',
    }
    optional = {
        'openai': 'openai',
        'httpx': 'httpx',
    }

    missing = []
    for import_name, package_name in required.items():
        try:
            __import__(import_name)
        except ImportError:
            missing.append(package_name)

    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False

    for import_name, package_name in optional.items():
        try:
            __import__(import_name)
        except ImportError:
            print(f"  Optional package not installed: {package_name} (needed for AI features)")

    print("All required packages installed - OK")
    return True


def setup_environment():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("Created .env from .env.example")
            print("  >> Edit .env with your Discord bot token and database credentials")
        else:
            print(".env.example not found")
            return False
    else:
        print(".env already exists - OK")
    return True


def check_database():
    """Test MariaDB/MySQL connection using .env credentials"""
    try:
        from dotenv import load_dotenv
        load_dotenv()

        import pymysql
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'discordrpg')
        password = os.getenv('DB_PASS', '')
        database = os.getenv('DB_NAME', 'discordrpg')

        if password == 'your_database_password_here' or not password:
            print("  >> Database credentials not configured yet. Edit .env first.")
            print("  >> See INSTALL.md for MariaDB setup instructions.")
            return True  # Not a fatal error during setup

        conn = pymysql.connect(host=host, user=user, password=password, database=database)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s", (database,))
        table_count = cursor.fetchone()[0]

        if table_count == 0:
            print(f"Database '{database}' is empty. Initializing schema...")
            with open('schema.sql', 'r') as f:
                schema = f.read()
            for stmt in schema.split(';'):
                stmt = stmt.strip()
                if stmt and not stmt.startswith('--'):
                    cursor.execute(stmt)
            conn.commit()
            print(f"Schema initialized ({database})")
        else:
            print(f"Database '{database}' has {table_count} tables - OK")

        conn.close()
        return True

    except ImportError:
        print("pymysql not installed yet. Install dependencies first.")
        return True  # Not fatal, they'll install deps
    except Exception as e:
        print(f"Database check failed: {e}")
        print("  >> Make sure MariaDB/MySQL is running and credentials are correct.")
        return False


def main():
    print("DiscordRPG Bot Setup")
    print("=" * 40)

    if not os.path.exists('bot.py'):
        print("Please run this script from the DiscordRPG directory.")
        return

    steps = [
        ("Checking Python version", check_python_version),
        ("Checking dependencies", check_dependencies),
        ("Setting up environment", setup_environment),
        ("Checking database", check_database),
    ]

    success = True
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            success = False
            break

    print("\n" + "=" * 40)
    if success:
        print("Setup complete!")
        print("\nNext steps:")
        print("  1. Edit .env with your Discord bot token and DB credentials")
        print("  2. Optionally add an OpenAI API key for AI features")
        print("  3. Run: python3 start.py")
    else:
        print("Setup failed. Resolve the issues above and try again.")


if __name__ == "__main__":
    main()
