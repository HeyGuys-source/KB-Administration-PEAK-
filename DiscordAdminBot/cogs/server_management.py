import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_admin_permissions, check_bot_permissions, check_hierarchy, convert_duration
from utils.logging_utils import ModerationLogger
from datetime import datetime

class ServerManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = ModerationLogger(bot)
    
    @app_commands.command(name="slowmode", description="Set slowmode for a channel")
    @app_commands.describe(
        channel="The channel to set slowmode for",
        duration="Slowmode duration in seconds (0 to disable)"
    )
    @has_admin_permissions()
    async def slowmode(self, interaction: discord.Interaction, channel: discord.TextChannel, duration: int):
        if not await check_bot_permissions(interaction, "manage_channels"):
            return
        
        if duration < 0 or duration > 21600:  # Discord max is 6 hours
            await interaction.response.send_message("❌ Duration must be between 0 and 21600 seconds (6 hours).", ephemeral=True)
            return
        
        try:
            await channel.edit(slowmode_delay=duration)
            
            if duration == 0:
                action_text = "disabled"
                details = f"Slowmode disabled in {channel.mention}"
            else:
                action_text = f"set to {duration} seconds"
                details = f"Slowmode set to {duration}s in {channel.mention}"
            
            await self.logger.log_action(
                interaction.guild, "Slowmode", interaction.user,
                details=details,
                color=0x2F3136
            )
            
            embed = await self.logger.create_success_embed(
                "Slowmode Updated",
                f"Slowmode {action_text} for {channel.mention}"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to modify this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="nick", description="Change a user's nickname")
    @app_commands.describe(
        user="The user to change nickname for",
        nickname="The new nickname (leave empty to reset)"
    )
    @has_admin_permissions()
    async def nick(self, interaction: discord.Interaction, user: discord.Member, nickname: str = None):
        if not await check_bot_permissions(interaction, "manage_nicknames"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        old_nick = user.display_name
        
        try:
            await user.edit(nick=nickname)
            
            action_text = f"changed to '{nickname}'" if nickname else "reset"
            
            await self.logger.log_action(
                interaction.guild, "Nickname Change", interaction.user, user,
                details=f"Old: {old_nick} → New: {nickname or user.name}",
                color=0x2F3136
            )
            
            embed = await self.logger.create_success_embed(
                "Nickname Updated",
                f"**{old_nick}**'s nickname has been {action_text}"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change this user's nickname.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="resetnick", description="Reset a user's nickname")
    @app_commands.describe(user="The user to reset nickname for")
    @has_admin_permissions()
    async def resetnick(self, interaction: discord.Interaction, user: discord.Member):
        if not await check_bot_permissions(interaction, "manage_nicknames"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        old_nick = user.display_name
        
        try:
            await user.edit(nick=None)
            
            await self.logger.log_action(
                interaction.guild, "Nickname Reset", interaction.user, user,
                details=f"Reset from: {old_nick}",
                color=0x2F3136
            )
            
            embed = await self.logger.create_success_embed(
                "Nickname Reset",
                f"**{old_nick}**'s nickname has been reset to **{user.name}**"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to change this user's nickname.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="move", description="Move a user to a voice channel")
    @app_commands.describe(
        user="The user to move",
        channel="The voice channel to move them to"
    )
    @has_admin_permissions()
    async def move(self, interaction: discord.Interaction, user: discord.Member, channel: discord.VoiceChannel):
        if not await check_bot_permissions(interaction, "move_members"):
            return
        
        if not user.voice:
            await interaction.response.send_message("❌ This user is not in a voice channel.", ephemeral=True)
            return
        
        try:
            old_channel = user.voice.channel
            await user.move_to(channel)
            
            await self.logger.log_action(
                interaction.guild, "Voice Move", interaction.user, user,
                details=f"From: {old_channel.name} → To: {channel.name}",
                color=0x2F3136
            )
            
            embed = await self.logger.create_success_embed(
                "User Moved",
                f"**{user}** moved from **{old_channel.name}** to **{channel.name}**"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to move this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="roleadd", description="Add a role to a user")
    @app_commands.describe(
        user="The user to add the role to",
        role="The role to add"
    )
    @has_admin_permissions()
    async def roleadd(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        # Check role hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot add a role that is equal to or higher than my highest role.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot add a role that is equal to or higher than your highest role.", ephemeral=True)
            return
        
        if role in user.roles:
            await interaction.response.send_message(f"❌ **{user}** already has the **{role.name}** role.", ephemeral=True)
            return
        
        try:
            await user.add_roles(role)
            
            await self.logger.log_action(
                interaction.guild, "Role Added", interaction.user, user,
                details=f"Role: {role.name}",
                color=0x00FF00
            )
            
            embed = await self.logger.create_success_embed(
                "Role Added",
                f"Added **{role.name}** role to **{user}**"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="roleremove", description="Remove a role from a user")
    @app_commands.describe(
        user="The user to remove the role from",
        role="The role to remove"
    )
    @has_admin_permissions()
    async def roleremove(self, interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        # Check role hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot remove a role that is equal to or higher than my highest role.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot remove a role that is equal to or higher than your highest role.", ephemeral=True)
            return
        
        if role not in user.roles:
            await interaction.response.send_message(f"❌ **{user}** doesn't have the **{role.name}** role.", ephemeral=True)
            return
        
        try:
            await user.remove_roles(role)
            
            await self.logger.log_action(
                interaction.guild, "Role Removed", interaction.user, user,
                details=f"Role: {role.name}",
                color=0xFF8000
            )
            
            embed = await self.logger.create_success_embed(
                "Role Removed",
                f"Removed **{role.name}** role from **{user}**"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to manage this role.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="roleall", description="Give a role to all members in the server")
    @app_commands.describe(role="The role to give to everyone")
    @has_admin_permissions()
    async def roleall(self, interaction: discord.Interaction, role: discord.Role):
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        # Check role hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot manage a role that is equal to or higher than my highest role.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot manage a role that is equal to or higher than your highest role.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        members_to_add = [member for member in interaction.guild.members if role not in member.roles and not member.bot]
        
        if not members_to_add:
            await interaction.followup.send("❌ All members already have this role or there are no members to add it to.")
            return
        
        success_count = 0
        failed_count = 0
        
        for member in members_to_add:
            try:
                await member.add_roles(role)
                success_count += 1
            except:
                failed_count += 1
        
        await self.logger.log_action(
            interaction.guild, "Mass Role Add", interaction.user,
            details=f"Role: {role.name}\nSuccessful: {success_count}\nFailed: {failed_count}",
            color=0x00FF00
        )
        
        embed = await self.logger.create_success_embed(
            "Mass Role Assignment",
            f"Added **{role.name}** to {success_count} members" + 
            (f"\nFailed to add to {failed_count} members" if failed_count > 0 else "")
        )
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="removeroleall", description="Remove a role from all members in the server")
    @app_commands.describe(role="The role to remove from everyone")
    @has_admin_permissions()
    async def removeroleall(self, interaction: discord.Interaction, role: discord.Role):
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        # Check role hierarchy
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("❌ I cannot manage a role that is equal to or higher than my highest role.", ephemeral=True)
            return
        
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ You cannot manage a role that is equal to or higher than your highest role.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        members_to_remove = [member for member in interaction.guild.members if role in member.roles]
        
        if not members_to_remove:
            await interaction.followup.send("❌ No members have this role.")
            return
        
        success_count = 0
        failed_count = 0
        
        for member in members_to_remove:
            try:
                await member.remove_roles(role)
                success_count += 1
            except:
                failed_count += 1
        
        await self.logger.log_action(
            interaction.guild, "Mass Role Remove", interaction.user,
            details=f"Role: {role.name}\nSuccessful: {success_count}\nFailed: {failed_count}",
            color=0xFF8000
        )
        
        embed = await self.logger.create_success_embed(
            "Mass Role Removal",
            f"Removed **{role.name}** from {success_count} members" + 
            (f"\nFailed to remove from {failed_count} members" if failed_count > 0 else "")
        )
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="lock", description="Lock a channel (disable messaging)")
    @app_commands.describe(channel="The channel to lock")
    @has_admin_permissions()
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await check_bot_permissions(interaction, "manage_channels"):
            return
        
        try:
            # Get @everyone role
            everyone_role = interaction.guild.default_role
            
            # Remove send messages permission
            await channel.set_permissions(everyone_role, send_messages=False)
            
            await self.logger.log_action(
                interaction.guild, "Channel Lock", interaction.user,
                details=f"Channel: {channel.mention}",
                color=0xFF0000
            )
            
            embed = await self.logger.create_success_embed(
                "Channel Locked",
                f"🔒 {channel.mention} has been locked"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to lock this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="unlock", description="Unlock a channel (enable messaging)")
    @app_commands.describe(channel="The channel to unlock")
    @has_admin_permissions()
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await check_bot_permissions(interaction, "manage_channels"):
            return
        
        try:
            # Get @everyone role
            everyone_role = interaction.guild.default_role
            
            # Reset send messages permission (None = inherit)
            await channel.set_permissions(everyone_role, send_messages=None)
            
            await self.logger.log_action(
                interaction.guild, "Channel Unlock", interaction.user,
                details=f"Channel: {channel.mention}",
                color=0x00FF00
            )
            
            embed = await self.logger.create_success_embed(
                "Channel Unlocked",
                f"🔓 {channel.mention} has been unlocked"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unlock this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="servermute", description="Server-mute a user across all voice channels")
    @app_commands.describe(user="The user to server-mute")
    @has_admin_permissions()
    async def servermute(self, interaction: discord.Interaction, user: discord.Member):
        if not await check_bot_permissions(interaction, "mute_members"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        if not user.voice:
            await interaction.response.send_message("❌ This user is not in a voice channel.", ephemeral=True)
            return
        
        try:
            await user.edit(mute=True)
            
            await self.logger.log_action(
                interaction.guild, "Server Mute", interaction.user, user,
                details=f"Voice channel: {user.voice.channel.name}",
                color=0xFF8000
            )
            
            embed = await self.logger.create_success_embed(
                "User Server-Muted",
                f"**{user}** has been server-muted in voice channels"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ServerManagement(bot))
