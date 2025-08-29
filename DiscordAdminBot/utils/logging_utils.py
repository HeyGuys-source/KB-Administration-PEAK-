import discord
from datetime import datetime
from typing import Optional
import logging

class ModerationLogger:
    def __init__(self, bot):
        self.bot = bot
    
    async def log_action(self, guild: discord.Guild, action_type: str, moderator: discord.Member, 
                        target: Optional[discord.Member] = None, reason: Optional[str] = None, 
                        details: Optional[str] = None, color: int = 0x2F3136):
        """Log moderation action to database and mod log channel"""
        
        # Log to database
        await self.bot.db.log_action(
            guild.id, action_type, moderator.id, 
            target.id if target else None, reason, details
        )
        
        # Log to mod log channel if configured
        mod_log_channel_id = await self.bot.db.get_mod_log_channel(guild.id)
        if mod_log_channel_id:
            channel = guild.get_channel(mod_log_channel_id)
            if channel and isinstance(channel, discord.TextChannel):
                embed = self.create_log_embed(action_type, moderator, target, reason, details, color)
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    logging.warning(f"Cannot send to mod log channel in {guild.name}")
                except Exception as e:
                    logging.error(f"Error sending to mod log: {e}")
    
    def create_log_embed(self, action_type: str, moderator: discord.Member, 
                        target: Optional[discord.Member] = None, reason: Optional[str] = None, 
                        details: Optional[str] = None, color: int = 0x2F3136) -> discord.Embed:
        """Create embed for moderation log"""
        
        embed = discord.Embed(
            title=f"🔨 {action_type.title()}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Moderator",
            value=f"{moderator.mention} ({moderator})",
            inline=True
        )
        
        if target:
            embed.add_field(
                name="Target",
                value=f"{target.mention} ({target})",
                inline=True
            )
        
        if reason:
            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )
        
        if details:
            embed.add_field(
                name="Details",
                value=details,
                inline=False
            )
        
        embed.set_footer(text=f"Action ID: {datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        
        return embed
    
    async def create_success_embed(self, title: str, description: str, color: int = 0x00FF00) -> discord.Embed:
        """Create success embed"""
        embed = discord.Embed(
            title=f"✅ {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        return embed
    
    async def create_error_embed(self, title: str, description: str, color: int = 0xFF0000) -> discord.Embed:
        """Create error embed"""
        embed = discord.Embed(
            title=f"❌ {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        return embed
    
    async def create_warning_embed(self, title: str, description: str, color: int = 0xFFFF00) -> discord.Embed:
        """Create warning embed"""
        embed = discord.Embed(
            title=f"⚠️ {title}",
            description=description,
            color=color,
            timestamp=datetime.utcnow()
        )
        return embed
