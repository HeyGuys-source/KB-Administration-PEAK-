import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_admin_permissions, check_bot_permissions
from utils.logging_utils import ModerationLogger
from datetime import datetime
from typing import Literal, List

class SpecialCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = ModerationLogger(bot)
        self.locked_channels = {}  # Store locked channels for masslockdown
    
    @app_commands.command(name="echo", description="Make the bot echo a message in plain text or embed format")
    @app_commands.describe(
        message="The message content to echo",
        format_type="Choose between Plain Text or Embed format",
        message_id="Optional: ID of a message to reply to"
    )
    @has_admin_permissions()
    async def echo(self, interaction: discord.Interaction, 
                   message: str, 
                   format_type: Literal["Plain Text", "Embed"],
                   message_id: str = None):
        
        if not await check_bot_permissions(interaction, "send_messages"):
            return
        
        # Handle message reply if message_id is provided
        reply_to = None
        if message_id:
            try:
                message_id_int = int(message_id)
                reply_to = await interaction.channel.fetch_message(message_id_int)
            except (ValueError, discord.NotFound):
                await interaction.response.send_message("❌ Invalid message ID or message not found.", ephemeral=True)
                return
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to access that message.", ephemeral=True)
                return
        
        try:
            if format_type == "Embed":
                # Create embed
                embed = discord.Embed(
                    description=message,
                    color=0x2F3136,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"Echoed by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
                
                if reply_to:
                    await reply_to.reply(embed=embed)
                else:
                    await interaction.channel.send(embed=embed)
            else:
                # Plain text
                if reply_to:
                    await reply_to.reply(message)
                else:
                    await interaction.channel.send(message)
            
            # Log the action
            await self.logger.log_action(
                interaction.guild, "Echo Command", interaction.user,
                details=f"Format: {format_type}\nMessage: {message[:100]}{'...' if len(message) > 100 else ''}" +
                       (f"\nReplied to message ID: {message_id}" if message_id else ""),
                color=0x2F3136
            )
            
            # Confirm to user
            confirmation = await self.logger.create_success_embed(
                "Message Echoed",
                f"Message sent in {format_type.lower()} format" + 
                (f" as a reply to message {message_id}" if message_id else "")
            )
            await interaction.response.send_message(embed=confirmation, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(name="vcmassmove", description="Disconnect all users from a voice channel")
    @app_commands.describe(vc_channel="The voice channel to clear")
    @has_admin_permissions()
    async def vcmassmove(self, interaction: discord.Interaction, vc_channel: discord.VoiceChannel):
        if not await check_bot_permissions(interaction, "move_members"):
            return
        
        # Get all members in the voice channel
        members_in_vc = vc_channel.members
        
        if not members_in_vc:
            await interaction.response.send_message(f"❌ No members are currently in {vc_channel.name}.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success_count = 0
        failed_count = 0
        failed_members = []
        
        for member in members_in_vc:
            try:
                await member.move_to(None)  # Disconnect from voice
                success_count += 1
            except discord.Forbidden:
                failed_count += 1
                failed_members.append(member.display_name)
            except Exception:
                failed_count += 1
                failed_members.append(member.display_name)
        
        # Log the action
        await self.logger.log_action(
            interaction.guild, "Voice Mass Move", interaction.user,
            details=f"Channel: {vc_channel.name}\nDisconnected: {success_count}\nFailed: {failed_count}",
            color=0xFF8000
        )
        
        # Create result embed
        embed = await self.logger.create_success_embed(
            "Voice Channel Cleared",
            f"Successfully disconnected {success_count} members from **{vc_channel.name}**"
        )
        
        if failed_count > 0:
            embed.add_field(
                name="⚠️ Failed to Disconnect",
                value=f"{failed_count} members (insufficient permissions or hierarchy)",
                inline=False
            )
            
            if len(failed_members) <= 10:  # Show names if not too many
                embed.add_field(
                    name="Failed Members",
                    value=", ".join(failed_members),
                    inline=False
                )
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="masslockdown", description="Lock multiple channels at once")
    @app_commands.describe(channels="Channels to lock (separate multiple channels with spaces)")
    @has_admin_permissions()
    async def masslockdown(self, interaction: discord.Interaction, channels: str):
        if not await check_bot_permissions(interaction, "manage_channels"):
            return
        
        # Parse channel mentions/IDs
        channel_list = []
        channel_parts = channels.split()
        
        for channel_part in channel_parts:
            # Remove < # > if present (mention format)
            channel_id_str = channel_part.strip('<>#')
            
            try:
                channel_id = int(channel_id_str)
                channel = interaction.guild.get_channel(channel_id)
                
                if channel and isinstance(channel, discord.TextChannel):
                    channel_list.append(channel)
                else:
                    await interaction.response.send_message(f"❌ Channel with ID {channel_id} not found or is not a text channel.", ephemeral=True)
                    return
            except ValueError:
                await interaction.response.send_message(f"❌ Invalid channel format: {channel_part}", ephemeral=True)
                return
        
        if not channel_list:
            await interaction.response.send_message("❌ No valid channels provided.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success_channels = []
        failed_channels = []
        everyone_role = interaction.guild.default_role
        
        # Store original permissions for potential unlock
        guild_id = interaction.guild.id
        if guild_id not in self.locked_channels:
            self.locked_channels[guild_id] = {}
        
        for channel in channel_list:
            try:
                # Store original permission
                original_perms = channel.overwrites_for(everyone_role)
                self.locked_channels[guild_id][channel.id] = {
                    'original_send_messages': original_perms.send_messages,
                    'locked_by': interaction.user.id,
                    'locked_at': datetime.utcnow()
                }
                
                # Lock the channel
                await channel.set_permissions(everyone_role, send_messages=False)
                success_channels.append(channel)
                
            except discord.Forbidden:
                failed_channels.append(channel)
            except Exception:
                failed_channels.append(channel)
        
        # Log the action
        await self.logger.log_action(
            interaction.guild, "Mass Lockdown", interaction.user,
            details=f"Locked: {len(success_channels)} channels\nFailed: {len(failed_channels)} channels\nChannels: {', '.join([c.name for c in success_channels])}",
            color=0xFF0000
        )
        
        # Create result embed
        embed = discord.Embed(
            title="🔒 Mass Lockdown Complete",
            color=0xFF0000,
            timestamp=datetime.utcnow()
        )
        
        if success_channels:
            embed.add_field(
                name=f"✅ Locked Channels ({len(success_channels)})",
                value="\n".join([f"🔒 {channel.mention}" for channel in success_channels]),
                inline=False
            )
        
        if failed_channels:
            embed.add_field(
                name=f"❌ Failed to Lock ({len(failed_channels)})",
                value="\n".join([f"❌ {channel.mention}" for channel in failed_channels]),
                inline=False
            )
        
        embed.set_footer(text=f"Use /massunlock to restore permissions")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="massunlock", description="Unlock channels that were locked with masslockdown")
    @app_commands.describe(channels="Channels to unlock (leave empty to unlock all previously locked channels)")
    @has_admin_permissions()
    async def massunlock(self, interaction: discord.Interaction, channels: str = None):
        if not await check_bot_permissions(interaction, "manage_channels"):
            return
        
        guild_id = interaction.guild.id
        
        if guild_id not in self.locked_channels or not self.locked_channels[guild_id]:
            await interaction.response.send_message("❌ No channels were previously locked with mass lockdown.", ephemeral=True)
            return
        
        channel_list = []
        
        if channels:
            # Parse specific channels
            channel_parts = channels.split()
            
            for channel_part in channel_parts:
                channel_id_str = channel_part.strip('<>#')
                
                try:
                    channel_id = int(channel_id_str)
                    channel = interaction.guild.get_channel(channel_id)
                    
                    if channel and isinstance(channel, discord.TextChannel):
                        if channel_id in self.locked_channels[guild_id]:
                            channel_list.append(channel)
                        else:
                            await interaction.response.send_message(f"❌ {channel.mention} was not locked with mass lockdown.", ephemeral=True)
                            return
                    else:
                        await interaction.response.send_message(f"❌ Channel with ID {channel_id} not found.", ephemeral=True)
                        return
                except ValueError:
                    await interaction.response.send_message(f"❌ Invalid channel format: {channel_part}", ephemeral=True)
                    return
        else:
            # Unlock all previously locked channels
            for channel_id in list(self.locked_channels[guild_id].keys()):
                channel = interaction.guild.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    channel_list.append(channel)
        
        if not channel_list:
            await interaction.response.send_message("❌ No valid channels to unlock.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        success_channels = []
        failed_channels = []
        everyone_role = interaction.guild.default_role
        
        for channel in channel_list:
            try:
                # Restore original permissions
                channel_data = self.locked_channels[guild_id][channel.id]
                original_send_messages = channel_data['original_send_messages']
                
                await channel.set_permissions(everyone_role, send_messages=original_send_messages)
                success_channels.append(channel)
                
                # Remove from locked channels
                del self.locked_channels[guild_id][channel.id]
                
            except discord.Forbidden:
                failed_channels.append(channel)
            except Exception:
                failed_channels.append(channel)
        
        # Log the action
        await self.logger.log_action(
            interaction.guild, "Mass Unlock", interaction.user,
            details=f"Unlocked: {len(success_channels)} channels\nFailed: {len(failed_channels)} channels\nChannels: {', '.join([c.name for c in success_channels])}",
            color=0x00FF00
        )
        
        # Create result embed
        embed = discord.Embed(
            title="🔓 Mass Unlock Complete",
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        
        if success_channels:
            embed.add_field(
                name=f"✅ Unlocked Channels ({len(success_channels)})",
                value="\n".join([f"🔓 {channel.mention}" for channel in success_channels]),
                inline=False
            )
        
        if failed_channels:
            embed.add_field(
                name=f"❌ Failed to Unlock ({len(failed_channels)})",
                value="\n".join([f"❌ {channel.mention}" for channel in failed_channels]),
                inline=False
            )
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SpecialCommands(bot))
