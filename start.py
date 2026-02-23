#!/usr/bin/env python3
"""
Startup script for the DiscordRPG bot
Handles database initialization and bot startup
"""
import os
import sys

def main():
    """Main startup function"""
    print("🎮 DiscordRPG Discord Bot")
    print("=" * 30)
    
    # Check for required files
    if not os.path.exists('.env'):
        print("❌ Error: .env file not found!")
        print("Make sure you have a .env file with DISCORD_TOKEN set")
        return
        
    # Import and run bot
    try:
        from bot import DiscordRPGBot
        print("🚀 Starting bot...")
        bot = DiscordRPGBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()