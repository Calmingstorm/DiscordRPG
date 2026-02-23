"""Database backup and management system (MariaDB version)"""
import discord
from discord.ext import commands, tasks
import subprocess
import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bot import DiscordRPGCog

logger = logging.getLogger('DiscordRPG.backup')


class BackupCog(DiscordRPGCog):
    """Database backup and management commands"""

    def __init__(self, bot):
        super().__init__(bot)
        self.backup_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.max_backups = 30
        self.max_hourly_backups = 24

    async def cog_load(self):
        if not self.daily_backup.is_running():
            self.daily_backup.start()
        if not self.hourly_backup.is_running():
            self.hourly_backup.start()
        if not self.cleanup_old_backups.is_running():
            self.cleanup_old_backups.start()

    async def cog_unload(self):
        if self.daily_backup.is_running():
            self.daily_backup.stop()
        if self.hourly_backup.is_running():
            self.hourly_backup.stop()
        if self.cleanup_old_backups.is_running():
            self.cleanup_old_backups.stop()

    def create_backup(self, backup_type: str = "manual") -> tuple:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"discordrpg_backup_{backup_type}_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)

            db_user = os.getenv('DB_USER', 'discordrpg')
            db_pass = os.getenv('DB_PASS', '')
            db_name = os.getenv('DB_NAME', 'discordrpg')
            db_host = os.getenv('DB_HOST', 'localhost')

            result = subprocess.run(
                ['mysqldump', '-h', db_host, '-u', db_user, f'-p{db_pass}',
                 '--single-transaction', '--routines', '--triggers', db_name],
                capture_output=True, timeout=120
            )

            if result.returncode != 0:
                return False, f"mysqldump failed: {result.stderr.decode()}"

            with open(backup_path, 'wb') as f:
                f.write(result.stdout)

            compressed_path = backup_path + ".gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(backup_path)

            file_size = os.path.getsize(compressed_path)
            size_mb = file_size / (1024 * 1024)

            logger.info(f"Database backup created: {compressed_path} ({size_mb:.2f} MB)")
            return True, f"Backup created successfully: {backup_filename}.gz ({size_mb:.2f} MB)"

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, f"Backup failed: {str(e)}"

    def restore_backup(self, backup_filename: str) -> tuple:
        try:
            if not backup_filename or '..' in backup_filename or '/' in backup_filename or '\\' in backup_filename:
                return False, "Invalid backup filename"
            if not backup_filename.endswith('.sql.gz'):
                return False, "Invalid backup file format (expected .sql.gz)"

            backup_path = os.path.join(self.backup_dir, backup_filename)
            if not os.path.abspath(backup_path).startswith(os.path.abspath(self.backup_dir)):
                return False, "Invalid backup file path"
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_filename}"

            current_backup_success, current_backup_msg = self.create_backup("pre_restore")
            if not current_backup_success:
                return False, f"Failed to backup current database: {current_backup_msg}"

            db_user = os.getenv('DB_USER', 'discordrpg')
            db_pass = os.getenv('DB_PASS', '')
            db_name = os.getenv('DB_NAME', 'discordrpg')
            db_host = os.getenv('DB_HOST', 'localhost')

            import gzip as gz
            with gz.open(backup_path, 'rb') as f:
                sql_data = f.read()

            result = subprocess.run(
                ['mysql', '-h', db_host, '-u', db_user, f'-p{db_pass}', db_name],
                input=sql_data, capture_output=True, timeout=120
            )

            if result.returncode != 0:
                return False, f"Restore failed: {result.stderr.decode()}"

            logger.info(f"Database restored from backup: {backup_filename}")
            return True, f"Database successfully restored from {backup_filename}"

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False, f"Restore failed: {str(e)}"

    def get_backup_list(self) -> list:
        backups = []
        try:
            for filename in os.listdir(self.backup_dir):
                if ('discordrpg_backup' in filename and
                        (filename.endswith('.sql.gz') or filename.endswith('.db.gz'))):
                    file_path = os.path.join(self.backup_dir, filename)
                    stat = os.stat(file_path)
                    parts = filename.replace('.sql.gz', '').replace('.db.gz', '').split('_')
                    backup_type = parts[2] if len(parts) > 2 else "unknown"
                    try:
                        ts = '_'.join(parts[3:5]) if len(parts) > 4 else parts[3]
                        created_date = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                    except (ValueError, IndexError):
                        created_date = datetime.fromtimestamp(stat.st_mtime)

                    backups.append({
                        'filename': filename,
                        'type': backup_type,
                        'created': created_date,
                        'size_mb': stat.st_size / (1024 * 1024),
                        'age_hours': (datetime.now() - created_date).total_seconds() / 3600
                    })
            backups.sort(key=lambda x: x['created'], reverse=True)
        except Exception as e:
            logger.error(f"Error getting backup list: {e}")
        return backups

    def cleanup_old_backups_sync(self) -> tuple:
        backups = self.get_backup_list()
        daily_removed = 0
        hourly_removed = 0
        try:
            daily_backups = [b for b in backups if b['type'] == 'daily']
            hourly_backups = [b for b in backups if b['type'] == 'hourly']
            if len(daily_backups) > self.max_backups:
                for backup in daily_backups[self.max_backups:]:
                    os.remove(os.path.join(self.backup_dir, backup['filename']))
                    daily_removed += 1
            if len(hourly_backups) > self.max_hourly_backups:
                for backup in hourly_backups[self.max_hourly_backups:]:
                    os.remove(os.path.join(self.backup_dir, backup['filename']))
                    hourly_removed += 1
            cutoff_date = datetime.now() - timedelta(days=31)
            for backup in backups:
                if backup['created'] < cutoff_date and backup['type'] in ['daily', 'hourly']:
                    file_path = os.path.join(self.backup_dir, backup['filename'])
                    if os.path.exists(file_path):
                        os.remove(file_path)
        except Exception as e:
            logger.error(f"Error during backup cleanup: {e}")
        return daily_removed, hourly_removed

    @tasks.loop(hours=24)
    async def daily_backup(self):
        try:
            success, message = self.create_backup("daily")
            if not success:
                logger.error(f"Daily backup failed: {message}")
        except Exception as e:
            logger.error(f"Daily backup task error: {e}")

    @tasks.loop(hours=3)
    async def hourly_backup(self):
        try:
            success, message = self.create_backup("hourly")
            if not success:
                logger.error(f"Hourly backup failed: {message}")
        except Exception as e:
            logger.error(f"Hourly backup task error: {e}")

    @tasks.loop(hours=6)
    async def cleanup_old_backups(self):
        try:
            self.cleanup_old_backups_sync()
        except Exception as e:
            logger.error(f"Backup cleanup task error: {e}")

    @daily_backup.before_loop
    async def before_daily_backup(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        target_time = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target_time <= now:
            target_time += timedelta(days=1)
        await asyncio.sleep((target_time - now).total_seconds())

    @hourly_backup.before_loop
    async def before_hourly_backup(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(600)

    @cleanup_old_backups.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1800)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx):
        embed = self.embed("Backup", "Creating manual database backup...")
        msg = await ctx.send(embed=embed)
        success, message = self.create_backup("manual")
        if success:
            embed = self.embed("Backup Complete", message)
            embed.color = discord.Color.green()
        else:
            embed = self.embed("Backup Failed", message)
            embed.color = discord.Color.red()
        await msg.edit(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backups(self, ctx):
        backups = self.get_backup_list()
        if not backups:
            await ctx.send(embed=self.embed("No Backups", "No backup files found."))
            return
        embed = self.embed("Available Backups", f"Found {len(backups)} backup files")
        recent = backups[:10]
        lines = []
        for b in recent:
            age = f"{b['age_hours']:.1f}h ago" if b['age_hours'] < 48 else f"{b['age_hours']/24:.1f}d ago"
            lines.append(f"**{b['type'].title()}** - {b['created'].strftime('%Y-%m-%d %H:%M')}\n"
                         f"Size: {b['size_mb']:.1f}MB | Age: {age}\n`{b['filename']}`")
        embed.add_field(name="Recent Backups", value="\n\n".join(lines), inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def restore(self, ctx, backup_filename: str):
        if not await ctx.confirm(
            f"WARNING: This will replace the current database.\n"
            f"Restore from: `{backup_filename}`?"
        ):
            await ctx.send("Restore cancelled.")
            return
        success, message = self.restore_backup(backup_filename)
        if success:
            embed = self.embed("Restore Complete", message)
            embed.color = discord.Color.green()
        else:
            embed = self.embed("Restore Failed", message)
            embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def backup_status(self, ctx):
        backups = self.get_backup_list()
        daily_count = len([b for b in backups if b['type'] == 'daily'])
        hourly_count = len([b for b in backups if b['type'] == 'hourly'])
        embed = self.embed("Backup System Status")
        embed.add_field(name="Counts",
                        value=f"Daily: {daily_count}/{self.max_backups}\nHourly: {hourly_count}/{self.max_hourly_backups}",
                        inline=True)
        embed.add_field(name="Storage",
                        value=f"Total: {len(backups)}\nSize: {sum(b['size_mb'] for b in backups):.1f}MB",
                        inline=True)
        status = []
        status.append(f"Daily: {'Running' if self.daily_backup.is_running() else 'Stopped'}")
        status.append(f"Hourly: {'Running' if self.hourly_backup.is_running() else 'Stopped'}")
        embed.add_field(name="Tasks", value="\n".join(status), inline=False)
        embed.color = discord.Color.blue()
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BackupCog(bot))
