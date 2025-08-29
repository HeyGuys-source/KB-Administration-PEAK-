import discord
from discord.ext import commands
from functools import wraps
import logging

def has_admin_permissions():
    """Decorator to check if user has administrator or manage server permissions"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Bot owner always has permissions
        if interaction.user.id == interaction.client.owner_id:
            return True
        
        # Check if user has administrator permission
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Check if user has manage guild permission
        if interaction.user.guild_permissions.manage_guild:
            return True
        
        return False
    
    return discord.app_commands.check(predicate)

def has_moderation_permissions():
    """Decorator to check if user has moderation permissions"""
    def predicate(interaction: discord.Interaction) -> bool:
        # Bot owner always has permissions
        if interaction.user.id == interaction.client.owner_id:
            return True
        
        # Check for various moderation permissions
        perms = interaction.user.guild_permissions
        return any([
            perms.administrator,
            perms.manage_guild,
            perms.manage_messages,
            perms.kick_members,
            perms.ban_members,
            perms.manage_roles
        ])
    
    return discord.app_commands.check(predicate)

async def check_bot_permissions(interaction: discord.Interaction, *permissions) -> bool:
    """Check if bot has required permissions"""
    bot_member = interaction.guild.me
    bot_perms = bot_member.guild_permissions
    
    missing_perms = []
    for perm in permissions:
        if not getattr(bot_perms, perm, False):
            missing_perms.append(perm.replace('_', ' ').title())
    
    if missing_perms:
        await interaction.response.send_message(
            f"❌ I'm missing the following permissions: {', '.join(missing_perms)}",
            ephemeral=True
        )
        return False
    
    return True

async def check_hierarchy(interaction: discord.Interaction, target_member: discord.Member) -> bool:
    """Check if the command user and bot can act on the target member"""
    if not target_member:
        return True
    
    # Check if target is the guild owner
    if target_member.id == interaction.guild.owner_id:
        await interaction.response.send_message(
            "❌ I cannot perform actions on the server owner.",
            ephemeral=True
        )
        return False
    
    # Check if target is the command user
    if target_member.id == interaction.user.id:
        await interaction.response.send_message(
            "❌ You cannot perform this action on yourself.",
            ephemeral=True
        )
        return False
    
    # Check if target is the bot
    if target_member.id == interaction.client.user.id:
        await interaction.response.send_message(
            "❌ I cannot perform actions on myself.",
            ephemeral=True
        )
        return False
    
    # Check user hierarchy
    if target_member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message(
            "❌ You cannot perform this action on someone with an equal or higher role.",
            ephemeral=True
        )
        return False
    
    # Check bot hierarchy
    if target_member.top_role >= interaction.guild.me.top_role:
        await interaction.response.send_message(
            "❌ I cannot perform this action on someone with an equal or higher role than me.",
            ephemeral=True
        )
        return False
    
    return True

def convert_duration(duration_str: str) -> int:
    """Convert duration string to seconds"""
    duration_str = duration_str.lower().strip()
    
    # Parse duration (e.g., "10m", "1h", "2d")
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    if duration_str[-1] in multipliers:
        try:
            number = int(duration_str[:-1])
            unit = duration_str[-1]
            return number * multipliers[unit]
        except ValueError:
            return 0
    else:
        try:
            return int(duration_str)  # Assume seconds if no unit
        except ValueError:
            return 0

def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration"""
    units = [
        ('week', 604800),
        ('day', 86400),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1)
    ]
    
    result = []
    for unit_name, unit_seconds in units:
        if seconds >= unit_seconds:
            count = seconds // unit_seconds
            seconds %= unit_seconds
            if count == 1:
                result.append(f"{count} {unit_name}")
            else:
                result.append(f"{count} {unit_name}s")
    
    if not result:
        return "0 seconds"
    
    if len(result) == 1:
        return result[0]
    elif len(result) == 2:
        return f"{result[0]} and {result[1]}"
    else:
        return f"{', '.join(result[:-1])}, and {result[-1]}"
