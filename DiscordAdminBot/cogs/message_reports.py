import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random
from datetime import datetime
from typing import Optional

class ReportModeration(discord.ui.View):
    def __init__(self, reported_message: discord.Message, reporter: discord.User, reported_user: discord.User):
        super().__init__(timeout=None)
        self.reported_message = reported_message
        self.reporter = reporter
        self.reported_user = reported_user
        self.mod_channel_id = 1410841913111875675
    
    async def create_confirmation_embed(self, moderator: discord.Member, action: str) -> discord.Embed:
        """Create a randomized confirmation embed"""
        confirmations = [
            f"{moderator.mention} handled this report. Issue resolved.",
            f"Report closed by {moderator.mention}. Appropriate action was taken.",
            f"{moderator.mention} reviewed and resolved this case.",
            f"{moderator.mention} completed the moderation action. Case closed.",
            f"Moderation action performed by {moderator.mention}. Report resolved.",
            f"{moderator.mention} successfully processed this report."
        ]
        
        embed = discord.Embed(
            title="✅ Report Action Completed",
            description=random.choice(confirmations),
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Action Taken", value=action, inline=False)
        embed.set_footer(text="Moderation System", icon_url=moderator.guild.icon.url if moderator.guild.icon else None)
        
        return embed
    
    @discord.ui.button(label="Delete Message", emoji="🗑️", style=discord.ButtonStyle.red)
    async def delete_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Delete the reported message
            await self.reported_message.delete()
            
            # Send DM to reported user
            try:
                dm_embed = discord.Embed(
                    title="⚠️ Message Deleted",
                    description="Your message was deleted by moderators due to violation of server rules. Please be careful moving forward.",
                    color=0xFF0000,
                    timestamp=datetime.utcnow()
                )
                dm_embed.set_footer(text=f"Server: {interaction.guild.name}")
                await self.reported_user.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            confirmation_embed = await self.create_confirmation_embed(interaction.user, "Message Deleted")
            await interaction.response.send_message(embed=confirmation_embed)
            
        except discord.NotFound:
            await interaction.response.send_message("❌ Message was already deleted.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to delete this message.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Warn User", emoji="⚠️", style=discord.ButtonStyle.secondary)
    async def warn_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Send DM warning to reported user
            try:
                warning_embed = discord.Embed(
                    title="⚠️ Official Warning",
                    description="You have been officially warned by moderators due to a reported message. Continued violations may result in further punishment.",
                    color=0xFFFF00,
                    timestamp=datetime.utcnow()
                )
                warning_embed.set_footer(text=f"Server: {interaction.guild.name}")
                await self.reported_user.send(embed=warning_embed)
                
                # Add warning to database if the main bot has warning system
                try:
                    bot = interaction.client
                    if hasattr(bot, 'db'):
                        await bot.db.add_warning(
                            interaction.guild.id, 
                            self.reported_user.id, 
                            interaction.user.id, 
                            "Reported message violation"
                        )
                except:
                    pass  # Fallback if warning system not available
                
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            confirmation_embed = await self.create_confirmation_embed(interaction.user, "User Warned")
            await interaction.response.send_message(embed=confirmation_embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="No Action Needed", emoji="✅", style=discord.ButtonStyle.green)
    async def no_action(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Send DM to reporter
            try:
                thanks_embed = discord.Embed(
                    title="✅ Report Reviewed",
                    description="Your report was reviewed by moderators. No action was necessary. Thank you for keeping the community safe!",
                    color=0x00FF00,
                    timestamp=datetime.utcnow()
                )
                thanks_embed.set_footer(text=f"Server: {interaction.guild.name}")
                await self.reporter.send(embed=thanks_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
            # Send confirmation
            confirmation_embed = await self.create_confirmation_embed(interaction.user, "No Action Required")
            await interaction.response.send_message(embed=confirmation_embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Jump To Message", emoji="🔗", style=discord.ButtonStyle.grey)
    async def jump_to_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Create message link
            message_link = f"https://discord.com/channels/{self.reported_message.guild.id}/{self.reported_message.channel.id}/{self.reported_message.id}"
            
            link_embed = discord.Embed(
                title="🔗 Message Link",
                description=f"[Click here to jump to the reported message]({message_link})",
                color=0x808080,
                timestamp=datetime.utcnow()
            )
            
            mod_channel = interaction.client.get_channel(self.mod_channel_id)
            if mod_channel:
                await mod_channel.send(embed=link_embed)
            
            # Send confirmation
            confirmation_embed = await self.create_confirmation_embed(interaction.user, "Message Link Accessed")
            await interaction.response.send_message(embed=confirmation_embed)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="Send Message", emoji="🌏", style=discord.ButtonStyle.primary)
    async def send_message(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            # Send reply under the reported message
            reply_embed = discord.Embed(
                description=f"{self.reported_user.mention}, your message was reported. Moderators are reviewing this case.",
                color=0x0099FF,
                timestamp=datetime.utcnow()
            )
            reply_embed.set_footer(text="Moderation Team")
            
            await self.reported_message.reply(embed=reply_embed)
            
            # Send confirmation
            confirmation_embed = await self.create_confirmation_embed(interaction.user, "Public Moderation Notice Sent")
            await interaction.response.send_message(embed=confirmation_embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to send messages in that channel.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ The original message was not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {str(e)}", ephemeral=True)


class MessageReports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.report_emoji_id = 1406321078086668419  # <:messageReport:1406321078086668419>
        self.mod_channel_id = 1410841913111875675
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore bot reactions
        if user.bot:
            return
        
        # Check if it's the specific report emoji
        if not (hasattr(reaction.emoji, 'id') and reaction.emoji.id == self.report_emoji_id):
            return
        
        # Get the message and its author
        message = reaction.message
        reported_user = message.author
        reporter = user
        
        # Don't allow self-reporting
        if reporter.id == reported_user.id:
            try:
                await reaction.remove(user)
            except:
                pass
            return
        
        # Wait 3-5 seconds then remove the reaction
        await asyncio.sleep(random.randint(3, 5))
        try:
            await reaction.remove(user)
        except:
            pass  # Reaction might already be removed
        
        # Get moderation channel
        mod_channel = self.bot.get_channel(self.mod_channel_id)
        if not mod_channel:
            return
        
        # Create main report embed
        report_embed = discord.Embed(
            title="📢 User Report System",
            color=0xFF6B6B,  # Light red
            timestamp=datetime.utcnow()
        )
        
        # Reporter information
        report_embed.add_field(
            name="👤 Reporter",
            value=f"**ID:** {reporter.id}\n**Username:** {reporter.name}#{reporter.discriminator}\n**Display Name:** {reporter.display_name}",
            inline=True
        )
        
        # Reported user information
        report_embed.add_field(
            name="⚠️ Reported User",
            value=f"**ID:** {reported_user.id}\n**Username:** {reported_user.name}#{reported_user.discriminator}\n**Display Name:** {reported_user.display_name}",
            inline=True
        )
        
        # Message information
        message_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
        if not message_preview:
            message_preview = "*[No text content - possibly embeds/attachments]*"
        
        message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        
        report_embed.add_field(
            name="💬 Reported Message",
            value=f"**Preview:** {message_preview}\n**Channel:** {message.channel.mention}\n**[Jump to Message]({message_link})**",
            inline=False
        )
        
        # Add context info
        report_embed.add_field(
            name="📍 Context",
            value=f"**Server:** {message.guild.name}\n**Channel:** #{message.channel.name}\n**Message ID:** {message.id}",
            inline=False
        )
        
        report_embed.set_footer(text="Report System", icon_url=message.guild.icon.url if message.guild.icon else None)
        
        # Create moderation actions embed
        mod_embed = discord.Embed(
            title="🔧 Moderation Actions",
            description="Choose an appropriate action for this report:",
            color=0x74C0FC,  # Light blue
            timestamp=datetime.utcnow()
        )
        
        mod_embed.set_footer(text="Click a button below to take action")
        
        # Create the view with buttons
        view = ReportModeration(message, reporter, reported_user)
        
        try:
            # Send both embeds
            await mod_channel.send(embed=report_embed)
            await mod_channel.send(embed=mod_embed, view=view)
            
        except discord.Forbidden:
            print(f"Cannot send to moderation channel {self.mod_channel_id} - missing permissions")
        except Exception as e:
            print(f"Error sending report: {e}")
    
    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        # Handle any cleanup if needed when reactions are removed
        pass
    
    @app_commands.command(name="testreport", description="Test the report system (Admin only)")
    @app_commands.describe(message_id="ID of message to create test report for")
    async def test_report(self, interaction: discord.Interaction, message_id: str):
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ You need administrator permissions to use this command.", ephemeral=True)
            return
        
        try:
            message_id_int = int(message_id)
            message = await interaction.channel.fetch_message(message_id_int)
            
            # Simulate a report
            mod_channel = self.bot.get_channel(self.mod_channel_id)
            if not mod_channel:
                await interaction.response.send_message("❌ Moderation channel not found.", ephemeral=True)
                return
            
            # Create test report embed
            report_embed = discord.Embed(
                title="📢 User Report System (TEST)",
                color=0xFF6B6B,
                timestamp=datetime.utcnow()
            )
            
            report_embed.add_field(
                name="👤 Reporter",
                value=f"**ID:** {interaction.user.id}\n**Username:** {interaction.user.name}#{interaction.user.discriminator}\n**Display Name:** {interaction.user.display_name}",
                inline=True
            )
            
            report_embed.add_field(
                name="⚠️ Reported User",
                value=f"**ID:** {message.author.id}\n**Username:** {message.author.name}#{message.author.discriminator}\n**Display Name:** {message.author.display_name}",
                inline=True
            )
            
            message_preview = message.content[:100] + "..." if len(message.content) > 100 else message.content
            if not message_preview:
                message_preview = "*[No text content - possibly embeds/attachments]*"
            
            message_link = f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
            
            report_embed.add_field(
                name="💬 Reported Message",
                value=f"**Preview:** {message_preview}\n**Channel:** {message.channel.mention}\n**[Jump to Message]({message_link})**",
                inline=False
            )
            
            report_embed.set_footer(text="TEST Report System")
            
            mod_embed = discord.Embed(
                title="🔧 Moderation Actions",
                description="Choose an appropriate action for this report:",
                color=0x74C0FC,
                timestamp=datetime.utcnow()
            )
            
            view = ReportModeration(message, interaction.user, message.author)
            
            await mod_channel.send(embed=report_embed)
            await mod_channel.send(embed=mod_embed, view=view)
            
            await interaction.response.send_message("✅ Test report sent to moderation channel!", ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid message ID.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("❌ Message not found.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MessageReports(bot))