#!/usr/bin/env python3
"""DiscordRPG Bot Setup Script"""

import os
import sqlite3
import shutil
from pathlib import Path

def setup_environment():
    """Create .env file from example if it doesn't exist"""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            shutil.copy('.env.example', '.env')
            print("✅ Created .env file from example")
            print("📝 Please edit .env with your Discord bot token and OpenAI API key")
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("ℹ️ .env file already exists")
    return True

def setup_database():
    """Initialize the database with schema"""
    if os.path.exists('discordrpg.db'):
        print("ℹ️ Database already exists")
        return True
    
    try:
        # Create database and load schema
        conn = sqlite3.connect('discordrpg.db')
        
        # Read and execute schema
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        conn.executescript(schema)
        conn.commit()
        conn.close()
        
        print("✅ Database created and initialized")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = [
        'discord.py',
        'python-dotenv',
        'openai',  # Optional but recommended
    ]
    
    package_map = {
        'python-dotenv': 'dotenv',
        'discord.py': 'discord'
    }
    
    missing_packages = []
    
    for package in required_packages:
        import_name = package_map.get(package, package.replace('-', '_').replace('.py', ''))
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def main():
    """Main setup routine"""
    print("🎮 DiscordRPG Bot Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('bot.py'):
        print("❌ Please run this script from the DiscordRPG directory")
        return
    
    # Setup steps
    steps = [
        ("Checking dependencies", check_dependencies),
        ("Setting up environment", setup_environment),
        ("Initializing database", setup_database),
    ]
    
    success = True
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            success = False
            break
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Edit .env with your Discord bot token")
        print("2. Optionally add OpenAI API key for AI features")
        print("3. Run: python3 start.py")
        print("\n🔗 Bot invite link: https://discord.com/developers/applications")
    else:
        print("❌ Setup failed. Please resolve the issues above.")

if __name__ == "__main__":
    main()