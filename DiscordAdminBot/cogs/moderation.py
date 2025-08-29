import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from utils.permissions import has_admin_permissions, check_bot_permissions, check_hierarchy, convert_duration, format_duration
from utils.logging_utils import ModerationLogger
import logging

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = ModerationLogger(bot)
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        user="The user to ban",
        reason="Reason for the ban"
    )
    @has_admin_permissions()
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not await check_bot_permissions(interaction, "ban_members"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        try:
            await user.ban(reason=reason)
            await self.logger.log_action(
                interaction.guild, "Ban", interaction.user, user, reason,
                color=0xFF0000
            )
            
            embed = await self.logger.create_success_embed(
                "User Banned",
                f"**{user}** has been banned.\n**Reason:** {reason}"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to ban this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="unban", description="Unban a user from the server")
    @app_commands.describe(user_id="The ID of the user to unban")
    @has_admin_permissions()
    async def unban(self, interaction: discord.Interaction, user_id: str):
        if not await check_bot_permissions(interaction, "ban_members"):
            return
        
        try:
            user_id = int(user_id)
            user = await self.bot.fetch_user(user_id)
            
            # Check if user is actually banned
            banned_users = [ban_entry.user async for ban_entry in interaction.guild.bans()]
            if user not in banned_users:
                await interaction.response.send_message("❌ This user is not banned.", ephemeral=True)
                return
            
            await interaction.guild.unban(user)
            await self.logger.log_action(
                interaction.guild, "Unban", interaction.user, user,
                color=0x00FF00
            )
            
            embed = await self.logger.create_success_embed(
                "User Unbanned",
                f"**{user}** has been unbanned."
            )
            await interaction.response.send_message(embed=embed)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid user ID provided.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ User not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        user="The user to kick",
        reason="Reason for the kick"
    )
    @has_admin_permissions()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        if not await check_bot_permissions(interaction, "kick_members"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        try:
            await user.kick(reason=reason)
            await self.logger.log_action(
                interaction.guild, "Kick", interaction.user, user, reason,
                color=0xFF8000
            )
            
            embed = await self.logger.create_success_embed(
                "User Kicked",
                f"**{user}** has been kicked.\n**Reason:** {reason}"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to kick this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="mute", description="Temporarily mute a user")
    @app_commands.describe(
        user="The user to mute",
        duration="Duration (e.g., 10m, 1h, 2d)",
        reason="Reason for the mute"
    )
    @has_admin_permissions()
    async def mute(self, interaction: discord.Interaction, user: discord.Member, 
                   duration: str, reason: str = "No reason provided"):
        
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        if not await check_hierarchy(interaction, user):
            return
        
        # Parse duration
        duration_seconds = convert_duration(duration)
        if duration_seconds <= 0:
            await interaction.response.send_message("❌ Invalid duration format. Use formats like: 10m, 1h, 2d", ephemeral=True)
            return
        
        # Get or create mute role
        mute_role_id = await self.bot.db.get_mute_role(interaction.guild.id)
        mute_role = None
        
        if mute_role_id:
            mute_role = interaction.guild.get_role(mute_role_id)
        
        if not mute_role:
            # Create mute role
            try:
                mute_role = await interaction.guild.create_role(
                    name="Muted",
                    color=discord.Color.dark_gray(),
                    reason="Auto-created mute role"
                )
                await self.bot.db.set_mute_role(interaction.guild.id, mute_role.id)
                
                # Set permissions for mute role in all channels
                for channel in interaction.guild.channels:
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await channel.set_permissions(mute_role, send_messages=False, add_reactions=False)
                        elif isinstance(channel, discord.VoiceChannel):
                            await channel.set_permissions(mute_role, speak=False)
                    except:
                        continue
                        
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to create roles.", ephemeral=True)
                return
        
        try:
            await user.add_roles(mute_role, reason=reason)
            
            # Add to database
            duration_delta = timedelta(seconds=duration_seconds)
            await self.bot.db.add_mute(interaction.guild.id, user.id, interaction.user.id, reason, duration_delta)
            
            await self.logger.log_action(
                interaction.guild, "Mute", interaction.user, user, reason,
                details=f"Duration: {format_duration(duration_seconds)}",
                color=0xFF8000
            )
            
            embed = await self.logger.create_success_embed(
                "User Muted",
                f"**{user}** has been muted for {format_duration(duration_seconds)}.\n**Reason:** {reason}"
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to mute this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="unmute", description="Remove mute from a user")
    @app_commands.describe(user="The user to unmute")
    @has_admin_permissions()
    async def unmute(self, interaction: discord.Interaction, user: discord.Member):
        if not await check_bot_permissions(interaction, "manage_roles"):
            return
        
        # Get mute role
        mute_role_id = await self.bot.db.get_mute_role(interaction.guild.id)
        if not mute_role_id:
            await interaction.response.send_message("❌ No mute role configured for this server.", ephemeral=True)
            return
        
        mute_role = interaction.guild.get_role(mute_role_id)
        if not mute_role:
            await interaction.response.send_message("❌ Mute role not found.", ephemeral=True)
            return
        
        if mute_role not in user.roles:
            await interaction.response.send_message("❌ This user is not muted.", ephemeral=True)
            return
        
        try:
            await user.remove_roles(mute_role, reason=f"Unmuted by {interaction.user}")
            await self.bot.db.remove_mute(interaction.guild.id, user.id)
            
            await self.logger.log_action(
                interaction.guild, "Unmute", interaction.user, user,
                color=0x00FF00
            )
            
            embed = await self.logger.create_success_embed(
                "User Unmuted",
                f"**{user}** has been unmuted."
            )
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to unmute this user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="warn", description="Issue a warning to a user")
    @app_commands.describe(
        user="The user to warn",
        reason="Reason for the warning"
    )
    @has_admin_permissions()
    async def warn(self, interaction: discord.Interaction, user: discord.Member, reason: str):
        if not await check_hierarchy(interaction, user):
            return
        
        # Add warning to database
        warning_id = await self.bot.db.add_warning(interaction.guild.id, user.id, interaction.user.id, reason)
        warning_count = await self.bot.db.get_warning_count(interaction.guild.id, user.id)
        
        await self.logger.log_action(
            interaction.guild, "Warning", interaction.user, user, reason,
            details=f"Warning #{warning_count} (ID: {warning_id})",
            color=0xFFFF00
        )
        
        embed = await self.logger.create_warning_embed(
            "User Warned",
            f"**{user}** has been warned.\n**Reason:** {reason}\n**Total warnings:** {warning_count}"
        )
        await interaction.response.send_message(embed=embed)
        
        # Send DM to user
        try:
            dm_embed = discord.Embed(
                title="⚠️ Warning Received",
                description=f"You have received a warning in **{interaction.guild.name}**",
                color=0xFFFF00
            )
            dm_embed.add_field(name="Reason", value=reason, inline=False)
            dm_embed.add_field(name="Total Warnings", value=str(warning_count), inline=True)
            dm_embed.add_field(name="Moderator", value=str(interaction.user), inline=True)
            
            await user.send(embed=dm_embed)
        except:
            pass  # User has DMs disabled
    
    @app_commands.command(name="warnings", description="View all warnings for a user")
    @app_commands.describe(user="The user to check warnings for")
    @has_admin_permissions()
    async def warnings(self, interaction: discord.Interaction, user: discord.Member):
        warnings = await self.bot.db.get_warnings(interaction.guild.id, user.id)
        
        if not warnings:
            embed = discord.Embed(
                title="No Warnings",
                description=f"**{user}** has no warnings.",
                color=0x00FF00
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"Warnings for {user}",
            description=f"Total warnings: {len(warnings)}",
            color=0xFFFF00
        )
        
        for i, warning in enumerate(warnings[:10], 1):  # Show max 10 warnings
            moderator = interaction.guild.get_member(warning['moderator_id'])
            moderator_name = moderator.display_name if moderator else "Unknown"
            
            embed.add_field(
                name=f"Warning #{i} (ID: {warning['id']})",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Date:** {warning['timestamp'][:19]}",
                inline=False
            )
        
        if len(warnings) > 10:
            embed.set_footer(text=f"Showing 10 of {len(warnings)} warnings")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="clearwarnings", description="Clear all warnings for a user")
    @app_commands.describe(user="The user to clear warnings for")
    @has_admin_permissions()
    async def clearwarnings(self, interaction: discord.Interaction, user: discord.Member):
        cleared_count = await self.bot.db.clear_warnings(interaction.guild.id, user.id)
        
        if cleared_count == 0:
            await interaction.response.send_message(f"❌ **{user}** has no warnings to clear.", ephemeral=True)
            return
        
        await self.logger.log_action(
            interaction.guild, "Clear Warnings", interaction.user, user,
            details=f"Cleared {cleared_count} warnings",
            color=0x00FF00
        )
        
        embed = await self.logger.create_success_embed(
            "Warnings Cleared",
            f"Cleared {cleared_count} warning(s) for **{user}**."
        )
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="purge", description="Bulk delete messages")
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    @has_admin_permissions()
    async def purge(self, interaction: discord.Interaction, amount: int):
        if not await check_bot_permissions(interaction, "manage_messages"):
            return
        
        if amount < 1 or amount > 100:
            await interaction.response.send_message("❌ Amount must be between 1 and 100.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        try:
            deleted = await interaction.channel.purge(limit=amount)
            
            await self.logger.log_action(
                interaction.guild, "Purge", interaction.user,
                details=f"Deleted {len(deleted)} messages in {interaction.channel.mention}",
                color=0xFF8000
            )
            
            embed = await self.logger.create_success_embed(
                "Messages Purged",
                f"Successfully deleted {len(deleted)} messages."
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to delete messages.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ An error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
