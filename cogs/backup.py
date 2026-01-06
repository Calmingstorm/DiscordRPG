"""Database backup and management system"""
import discord
from discord.ext import commands, tasks
import shutil
import os
import gzip
import json
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog

# Set up logging
logger = logging.getLogger('DiscordRPG.backup')

class BackupCog(DiscordRPGCog):
    """Database backup and management commands"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "discordrpg.db")
        
        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Backup settings
        self.max_backups = 30  # Keep 30 days of backups
        self.max_hourly_backups = 24  # Keep 24 hourly backups
        
    async def cog_load(self):
        """Start backup tasks when cog loads"""
        if not self.daily_backup.is_running():
            self.daily_backup.start()
        if not self.hourly_backup.is_running():
            self.hourly_backup.start()
        if not self.cleanup_old_backups.is_running():
            self.cleanup_old_backups.start()
    
    async def cog_unload(self):
        """Stop backup tasks when cog unloads"""
        if self.daily_backup.is_running():
            self.daily_backup.stop()
        if self.hourly_backup.is_running():
            self.hourly_backup.stop()
        if self.cleanup_old_backups.is_running():
            self.cleanup_old_backups.stop()
    
    def create_backup(self, backup_type: str = "manual") -> tuple[bool, str]:
        """Create a database backup
        
        Args:
            backup_type: Type of backup (daily, hourly, manual)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            if not os.path.exists(self.db_path):
                return False, "Database file not found"
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"discordrpg_backup_{backup_type}_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Compress the backup to save space
            compressed_path = backup_path + ".gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            os.remove(backup_path)
            
            # Get file size for reporting
            file_size = os.path.getsize(compressed_path)
            size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Database backup created: {compressed_path} ({size_mb:.2f} MB)")
            return True, f"Backup created successfully: {backup_filename}.gz ({size_mb:.2f} MB)"
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, f"Backup failed: {str(e)}"
    
    def restore_backup(self, backup_filename: str) -> tuple[bool, str]:
        """Restore database from backup
        
        Args:
            backup_filename: Name of backup file to restore
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Validate filename to prevent path traversal attacks
            if not backup_filename or '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
                return False, "Invalid backup filename"
            
            # Ensure filename has expected extension
            if not backup_filename.endswith('.db.gz'):
                return False, "Invalid backup file format"
            
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Verify the resolved path is still within backup directory
            if not os.path.abspath(backup_path).startswith(os.path.abspath(self.backup_dir)):
                return False, "Invalid backup file path"
            
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_filename}"
            
            # Create backup of current database before restoring
            current_backup_success, current_backup_msg = self.create_backup("pre_restore")
            if not current_backup_success:
                return False, f"Failed to backup current database: {current_backup_msg}"
            
            # Decompress backup file
            temp_db_path = backup_path.replace('.gz', '')
            with gzip.open(backup_path, 'rb') as f_in:
                with open(temp_db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Replace current database with backup
            shutil.copy2(temp_db_path, self.db_path)
            
            # Clean up temporary file
            os.remove(temp_db_path)
            
            logger.info(f"Database restored from backup: {backup_filename}")
            return True, f"Database successfully restored from {backup_filename}"
            
        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False, f"Restore failed: {str(e)}"
    
    def get_backup_list(self) -> list[dict]:
        """Get list of available backups with metadata"""
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.db.gz') and 'discordrpg_backup' in filename:
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    
                    # Parse backup info from filename
                    parts = filename.replace('.db.gz', '').split('_')
                    backup_type = parts[2] if len(parts) > 2 else "unknown"
                    timestamp_str = parts[3] if len(parts) > 3 else "unknown"
                    
                    try:
                        created_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    except ValueError:
                        created_date = datetime.fromtimestamp(stat.st_mtime)
                    
                    backups.append({
                        'filename': filename,
                        'type': backup_type,
                        'created': created_date,
                        'size_mb': stat.st_size / (1024 * 1024),
                        'age_hours': (datetime.now() - created_date).total_seconds() / 3600
                    })
                    
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
            
        return backups
    
    def cleanup_old_backups_sync(self) -> tuple[int, int]:
        """Clean up old backup files
        
        Returns:
            tuple: (daily_removed, hourly_removed)
        """
        backups = self.get_backup_list()
        daily_removed = 0
        hourly_removed = 0
        
        try:
            # Separate backups by type
            daily_backups = [b for b in backups if b['type'] == 'daily']
            hourly_backups = [b for b in backups if b['type'] == 'hourly']
            
            # Remove old daily backups (keep only the most recent ones)
            if len(daily_backups) > self.max_backups:
                old_dailies = daily_backups[self.max_backups:]
                for backup in old_dailies:
                    file_path = os.path.join(self.backup_dir, backup['filename'])
                    os.remove(file_path)
                    daily_removed += 1
                    logger.info(f"Removed old daily backup: {backup['filename']}")
            
            # Remove old hourly backups
            if len(hourly_backups) > self.max_hourly_backups:
                old_hourlies = hourly_backups[self.max_hourly_backups:]
                for backup in old_hourlies:
                    file_path = os.path.join(self.backup_dir, backup['filename'])
                    os.remove(file_path)
                    hourly_removed += 1
                    logger.info(f"Removed old hourly backup: {backup['filename']}")
                    
            # Also remove any backups older than 31 days regardless of count
            cutoff_date = datetime.now() - timedelta(days=31)
            for backup in backups:
                if backup['created'] < cutoff_date and backup['type'] in ['daily', 'hourly']:
                    file_path = os.path.join(self.backup_dir, backup['filename'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Removed expired backup: {backup['filename']}")
                        
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
            
        return daily_removed, hourly_removed
    
    @tasks.loop(hours=24)  # Run daily at the same time
    async def daily_backup(self):
        """Create daily database backup"""
        try:
            success, message = self.create_backup("daily")
            if success:
                logger.info(f"Daily backup completed: {message}")
            else:
                logger.error(f"Daily backup failed: {message}")
                
                # Try to notify admins about backup failure
                channel = await self.get_game_channel()
                if channel:
                    await channel.send(f"⚠️ **Database Backup Failed**: {message}")
                    
        except Exception as e:
            logger.error(f"Daily backup task error: {e}")
    
    @tasks.loop(hours=3)  # Run every 3 hours
    async def hourly_backup(self):
        """Create periodic database backup"""
        try:
            success, message = self.create_backup("hourly")
            if success:
                logger.info(f"Hourly backup completed: {message}")
            else:
                logger.error(f"Hourly backup failed: {message}")
                
        except Exception as e:
            logger.error(f"Hourly backup task error: {e}")
    
    @tasks.loop(hours=6)  # Run every 6 hours
    async def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            daily_removed, hourly_removed = self.cleanup_old_backups_sync()
            if daily_removed > 0 or hourly_removed > 0:
                logger.info(f"Backup cleanup: removed {daily_removed} daily, {hourly_removed} hourly backups")
                
        except Exception as e:
            logger.error(f"Backup cleanup task error: {e}")
    
    @daily_backup.before_loop
    async def before_daily_backup(self):
        """Wait for bot to be ready before starting daily backup"""
        await self.bot.wait_until_ready()
        # Wait until 3 AM for daily backups
        now = datetime.now()
        target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
        
        wait_seconds = (target_time - now).total_seconds()
        logger.info(f"Daily backup scheduled for {target_time} (in {wait_seconds/3600:.1f} hours)")
        await asyncio.sleep(wait_seconds)
    
    @hourly_backup.before_loop
    async def before_hourly_backup(self):
        """Wait for bot to be ready before starting hourly backup"""
        await self.bot.wait_until_ready()
        # Start hourly backups after a 10 minute delay
        await asyncio.sleep(600)
    
    @cleanup_old_backups.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup"""
        await self.bot.wait_until_ready()
        # Start cleanup after 30 minutes
        await asyncio.sleep(1800)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        """Create a manual database backup (Admin only)"""
        embed = self.embed("🔄 Creating Backup", "Creating manual database backup...")
        msg = await ctx.send(embed=embed)
        
        success, message = self.create_backup("manual")
        
        if success:
            embed = self.embed("✅ Backup Complete", message)
            embed.color = discord.Color.green()
        else:
            embed = self.embed("❌ Backup Failed", message)
            embed.color = discord.Color.red()
            
        await msg.edit(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backups(self, ctx: commands.Context):
        """List available database backups (Admin only)"""
        backups = self.get_backup_list()
        
        if not backups:
            embed = self.embed("📁 No Backups", "No backup files found.")
            await ctx.send(embed=embed)
            return
        
        embed = self.embed("📁 Available Backups", f"Found {len(backups)} backup files")
        
        # Show most recent 10 backups
        recent_backups = backups[:10]
        backup_text = []
        
        for backup in recent_backups:
            age_str = f"{backup['age_hours']:.1f}h ago" if backup['age_hours'] < 48 else f"{backup['age_hours']/24:.1f}d ago"
            backup_text.append(
                f"**{backup['type'].title()}** - {backup['created'].strftime('%Y-%m-%d %H:%M')}\n"
                f"Size: {backup['size_mb']:.1f}MB | Age: {age_str}\n"
                f"`{backup['filename']}`"
            )
        
        embed.add_field(
            name="Recent Backups",
            value="\n\n".join(backup_text),
            inline=False
        )
        
        if len(backups) > 10:
            embed.add_field(
                name="📊 Summary",
                value=f"Showing 10 of {len(backups)} backups\nTotal size: {sum(b['size_mb'] for b in backups):.1f}MB",
                inline=False
            )
        
        embed.set_footer(text="Use !restore <filename> to restore a backup")
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx: commands.Context, backup_filename: str):
        """Restore database from backup (Admin only) - USE WITH CAUTION"""
        # Double confirmation for safety
        if not await ctx.confirm(
            f"⚠️ **WARNING**: This will replace the current database with the backup.\n"
            f"All current progress since the backup will be **PERMANENTLY LOST**!\n\n"
            f"Restore from: `{backup_filename}`?"
        ):
            await ctx.send("Database restore cancelled.")
            return
        
        # Final confirmation
        if not await ctx.confirm(
            "🚨 **FINAL WARNING**: Are you absolutely sure you want to restore?\n"
            "This action cannot be undone!"
        ):
            await ctx.send("Database restore cancelled.")
            return
        
        embed = self.embed("🔄 Restoring Database", f"Restoring from backup: {backup_filename}")
        embed.color = discord.Color.orange()
        msg = await ctx.send(embed=embed)
        
        success, message = self.restore_backup(backup_filename)
        
        if success:
            embed = self.embed("✅ Restore Complete", message)
            embed.color = discord.Color.green()
            embed.add_field(
                name="⚠️ Important",
                value="Bot restart recommended to refresh database connections.",
                inline=False
            )
        else:
            embed = self.embed("❌ Restore Failed", message)
            embed.color = discord.Color.red()
            
        await msg.edit(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup_status(self, ctx: commands.Context):
        """Show backup system status (Admin only)"""
        backups = self.get_backup_list()
        
        # Count backups by type
        daily_count = len([b for b in backups if b['type'] == 'daily'])
        hourly_count = len([b for b in backups if b['type'] == 'hourly'])
        manual_count = len([b for b in backups if b['type'] == 'manual'])
        
        # Get next backup times
        next_daily = "Unknown"
        next_hourly = "Unknown"
        
        if self.daily_backup.next_iteration:
            next_daily = self.daily_backup.next_iteration.strftime('%Y-%m-%d %H:%M')
        
        if self.hourly_backup.next_iteration:
            next_hourly = self.hourly_backup.next_iteration.strftime('%Y-%m-%d %H:%M')
        
        embed = self.embed("📊 Backup System Status", "Database backup system information")
        
        embed.add_field(
            name="📁 Backup Counts",
            value=f"**Daily:** {daily_count}/{self.max_backups}\n"
                  f"**Hourly:** {hourly_count}/{self.max_hourly_backups}\n"
                  f"**Manual:** {manual_count}",
            inline=True
        )
        
        embed.add_field(
            name="⏰ Next Scheduled",
            value=f"**Daily:** {next_daily}\n**Hourly:** {next_hourly}",
            inline=True
        )
        
        embed.add_field(
            name="💾 Storage",
            value=f"**Total backups:** {len(backups)}\n"
                  f"**Total size:** {sum(b['size_mb'] for b in backups):.1f}MB\n"
                  f"**Location:** `{os.path.basename(self.backup_dir)}/`",
            inline=True
        )
        
        # Task status
        status_text = []
        status_text.append(f"Daily backup: {'✅ Running' if self.daily_backup.is_running() else '❌ Stopped'}")
        status_text.append(f"Hourly backup: {'✅ Running' if self.hourly_backup.is_running() else '❌ Stopped'}")
        status_text.append(f"Auto cleanup: {'✅ Running' if self.cleanup_old_backups.is_running() else '❌ Stopped'}")
        
        embed.add_field(
            name="🔧 Task Status",
            value="\n".join(status_text),
            inline=False
        )
        
        # Most recent backup
        if backups:
            latest = backups[0]
            age_hours = latest['age_hours']
            age_str = f"{age_hours:.1f}h ago" if age_hours < 48 else f"{age_hours/24:.1f}d ago"
            
            embed.add_field(
                name="🕐 Latest Backup",
                value=f"**{latest['type'].title()}** backup created {age_str}\n`{latest['filename']}`",
                inline=False
            )
        
        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BackupCog(bot))