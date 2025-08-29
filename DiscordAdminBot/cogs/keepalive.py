import discord
from discord.ext import commands, tasks
import asyncio
import logging
import time
from datetime import datetime

class KeepAlive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_activity = time.time()
        self.keepalive_task.start()
        logging.info("KeepAlive system initialized")
    
    def cog_unload(self):
        """Clean up when cog is unloaded"""
        self.keepalive_task.cancel()
        logging.info("KeepAlive system stopped")
    
    @tasks.loop(seconds=20)
    async def keepalive_task(self):
        """Internal keepalive task that runs every 20 seconds"""
        try:
            # Perform internal operations to maintain activity
            
            # 1. Check bot status and update last activity
            self.last_activity = time.time()
            
            # 2. Silently check guild count (internal operation)
            guild_count = len(self.bot.guilds)
            
            # 3. Check database connection (if available)
            if hasattr(self.bot, 'db') and self.bot.db:
                try:
                    # Simple database ping to keep connection alive
                    await self.bot.db.db.execute("SELECT 1")
                except:
                    pass  # Silent fail, just for keepalive
            
            # 4. Update bot's internal cache by checking user count
            total_members = sum(guild.member_count for guild in self.bot.guilds if guild.member_count)
            
            # 5. Refresh bot's presence status (internal operation)
            current_time = datetime.now().strftime("%H:%M")
            await self.bot.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=f"for /help | {guild_count} servers | {current_time}"
                )
            )
            
            # Log keepalive (only in debug mode to avoid spam)
            logging.debug(f"KeepAlive: Active | Guilds: {guild_count} | Members: {total_members}")
            
        except Exception as e:
            # Silent error handling - don't spam logs with keepalive errors
            logging.debug(f"KeepAlive error (non-critical): {e}")
    
    @keepalive_task.before_loop
    async def before_keepalive(self):
        """Wait for bot to be ready before starting keepalive"""
        await self.bot.wait_until_ready()
        logging.info("KeepAlive task started - monitoring every 20 seconds")
    
    @keepalive_task.after_loop
    async def after_keepalive(self):
        """Cleanup after keepalive loop ends"""
        if self.keepalive_task.is_being_cancelled():
            logging.info("KeepAlive task cancelled")
    
    @commands.command(name="keepalive_status", hidden=True)
    @commands.is_owner()
    async def keepalive_status(self, ctx):
        """Check keepalive status (owner only)"""
        uptime = time.time() - self.last_activity
        status = "🟢 Active" if self.keepalive_task.is_running() else "🔴 Inactive"
        
        embed = discord.Embed(
            title="🔄 KeepAlive Status",
            color=0x00FF00 if self.keepalive_task.is_running() else 0xFF0000,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Status", 
            value=status, 
            inline=True
        )
        
        embed.add_field(
            name="Last Activity", 
            value=f"{uptime:.1f} seconds ago", 
            inline=True
        )
        
        embed.add_field(
            name="Next Check", 
            value="< 20 seconds", 
            inline=True
        )
        
        embed.add_field(
            name="Guilds Monitored", 
            value=f"{len(self.bot.guilds)}", 
            inline=True
        )
        
        embed.set_footer(text="Internal KeepAlive System")
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Reset activity timer when bot becomes ready"""
        self.last_activity = time.time()
        logging.info("Bot ready - KeepAlive system active")
    
    @commands.Cog.listener()  
    async def on_guild_join(self, guild):
        """Update activity when joining new guilds"""
        self.last_activity = time.time()
        logging.info(f"Joined guild: {guild.name} - KeepAlive updated")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Update activity when leaving guilds"""
        self.last_activity = time.time()
        logging.info(f"Left guild: {guild.name} - KeepAlive updated")


async def setup(bot):
    await bot.add_cog(KeepAlive(bot))