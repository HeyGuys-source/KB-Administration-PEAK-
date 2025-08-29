import discord
from discord.ext import commands
from discord import app_commands
from utils.permissions import has_admin_permissions, check_bot_permissions, check_hierarchy
from utils.logging_utils import ModerationLogger
from datetime import datetime

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = ModerationLogger(bot)
    
    @app_commands.command(name="serverinfo", description="Display detailed server information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        # Count different channel types
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        
        # Count members by status
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = len([m for m in guild.members if m.status == discord.Status.offline])
        
        # Count bots
        bots = len([m for m in guild.members if m.bot])
        humans = len([m for m in guild.members if not m.bot])
        
        embed = discord.Embed(
            title=f"📊 {guild.name} Server Information",
            color=0x2F3136,
            timestamp=datetime.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Basic info
        embed.add_field(
            name="🏷️ Basic Info",
            value=f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
                  f"**Created:** <t:{int(guild.created_at.timestamp())}:F>\n"
                  f"**Server ID:** {guild.id}",
            inline=False
        )
        
        # Member statistics
        embed.add_field(
            name="👥 Members ({:,})".format(guild.member_count),
            value=f"**Humans:** {humans:,}\n"
                  f"**Bots:** {bots:,}\n"
                  f"**Online:** {online:,}\n"
                  f"**Idle:** {idle:,}\n"
                  f"**DND:** {dnd:,}\n"
                  f"**Offline:** {offline:,}",
            inline=True
        )
        
        # Channel statistics
        embed.add_field(
            name="📁 Channels ({})".format(len(guild.channels)),
            value=f"**Text:** {text_channels}\n"
                  f"**Voice:** {voice_channels}\n"
                  f"**Categories:** {categories}",
            inline=True
        )
        
        # Server boost info
        embed.add_field(
            name="💎 Boosts",
            value=f"**Level:** {guild.premium_tier}\n"
                  f"**Boosts:** {guild.premium_subscription_count}\n"
                  f"**Boosters:** {len(guild.premium_subscribers)}",
            inline=True
        )
        
        # Roles info
        embed.add_field(
            name="🎭 Roles",
            value=f"**Total:** {len(guild.roles)}\n"
                  f"**Highest:** {guild.roles[-1].mention if len(guild.roles) > 1 else 'None'}",
            inline=True
        )
        
        # Features
        if guild.features:
            features = []
            feature_mapping = {
                'COMMUNITY': 'Community',
                'DISCOVERABLE': 'Discoverable',
                'PARTNERED': 'Partnered',
                'VERIFIED': 'Verified',
                'VANITY_URL': 'Vanity URL',
                'BANNER': 'Banner',
                'ANIMATED_ICON': 'Animated Icon'
            }
            
            for feature in guild.features:
                if feature in feature_mapping:
                    features.append(feature_mapping[feature])
            
            if features:
                embed.add_field(
                    name="✨ Features",
                    value=", ".join(features[:5]),  # Show max 5 features
                    inline=True
                )
        
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Display detailed information about a user")
    @app_commands.describe(user="The user to get information about")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"👤 {user.display_name}",
            color=user.color if user.color != discord.Color.default() else 0x2F3136,
            timestamp=datetime.utcnow()
        )
        
        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)
        
        # Basic info
        embed.add_field(
            name="🏷️ Basic Info",
            value=f"**Username:** {user.name}\n"
                  f"**Discriminator:** #{user.discriminator}\n"
                  f"**ID:** {user.id}\n"
                  f"**Bot:** {'Yes' if user.bot else 'No'}",
            inline=False
        )
        
        # Dates
        embed.add_field(
            name="📅 Dates",
            value=f"**Account Created:** <t:{int(user.created_at.timestamp())}:F>\n"
                  f"**Joined Server:** <t:{int(user.joined_at.timestamp())}:F>" if user.joined_at else "**Joined Server:** Unknown",
            inline=False
        )
        
        # Roles
        if len(user.roles) > 1:  # Exclude @everyone
            roles = [role.mention for role in sorted(user.roles[1:], key=lambda r: r.position, reverse=True)]
            roles_text = ", ".join(roles[:10])  # Show max 10 roles
            if len(user.roles) > 11:
                roles_text += f" and {len(user.roles) - 11} more..."
        else:
            roles_text = "None"
        
        embed.add_field(
            name=f"🎭 Roles ({len(user.roles) - 1})",
            value=roles_text,
            inline=False
        )
        
        # Permissions
        if user.guild_permissions.administrator:
            perms_text = "Administrator (All Permissions)"
        else:
            key_perms = []
            perm_checks = [
                ('manage_guild', 'Manage Server'),
                ('manage_channels', 'Manage Channels'),
                ('manage_roles', 'Manage Roles'),
                ('manage_messages', 'Manage Messages'),
                ('kick_members', 'Kick Members'),
                ('ban_members', 'Ban Members'),
                ('manage_nicknames', 'Manage Nicknames'),
                ('mute_members', 'Mute Members'),
                ('deafen_members', 'Deafen Members'),
                ('move_members', 'Move Members')
            ]
            
            for perm, name in perm_checks:
                if getattr(user.guild_permissions, perm):
                    key_perms.append(name)
            
            perms_text = ", ".join(key_perms[:5]) if key_perms else "None"
            if len(key_perms) > 5:
                perms_text += f" and {len(key_perms) - 5} more..."
        
        embed.add_field(
            name="🔑 Key Permissions",
            value=perms_text,
            inline=False
        )
        
        # Status and activity
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        status_text = f"{status_emoji.get(user.status, '❓')} {user.status.name.title()}"
        if user.activity:
            status_text += f"\n**Activity:** {user.activity.name}"
        
        embed.add_field(
            name="📱 Status",
            value=status_text,
            inline=True
        )
        
        # Get warning count if in database
        try:
            warning_count = await self.bot.db.get_warning_count(interaction.guild.id, user.id)
            if warning_count > 0:
                embed.add_field(
                    name="⚠️ Warnings",
                    value=str(warning_count),
                    inline=True
                )
        except:
            pass
        
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="avatar", description="Show a user's avatar in high resolution")
    @app_commands.describe(user="The user whose avatar to display")
    async def avatar(self, interaction: discord.Interaction, user: discord.Member = None):
        if user is None:
            user = interaction.user
        
        embed = discord.Embed(
            title=f"🖼️ {user.display_name}'s Avatar",
            color=user.color if user.color != discord.Color.default() else 0x2F3136
        )
        
        if user.avatar:
            avatar_url = user.avatar.url
            embed.set_image(url=avatar_url)
            embed.add_field(
                name="Download Links",
                value=f"[PNG]({avatar_url}?format=png) | [JPG]({avatar_url}?format=jpg) | [WEBP]({avatar_url}?format=webp)",
                inline=False
            )
        else:
            embed.description = "This user has no custom avatar."
            default_avatar = user.default_avatar.url
            embed.set_image(url=default_avatar)
        
        embed.set_footer(text=f"Requested by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="poll", description="Create a poll with reactions for voting")
    @app_commands.describe(
        question="The poll question",
        options="Poll options separated by commas (max 10)"
    )
    @has_admin_permissions()
    async def poll(self, interaction: discord.Interaction, question: str, options: str):
        option_list = [option.strip() for option in options.split(',')]
        
        if len(option_list) < 2:
            await interaction.response.send_message("❌ You need at least 2 options for a poll.", ephemeral=True)
            return
        
        if len(option_list) > 10:
            await interaction.response.send_message("❌ Maximum 10 options allowed.", ephemeral=True)
            return
        
        # Reaction emojis (numbers)
        reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        embed = discord.Embed(
            title="📊 Poll",
            description=f"**{question}**",
            color=0x2F3136,
            timestamp=datetime.utcnow()
        )
        
        poll_text = ""
        for i, option in enumerate(option_list):
            poll_text += f"{reactions[i]} {option}\n"
        
        embed.add_field(name="Options", value=poll_text, inline=False)
        embed.set_footer(text=f"Poll created by {interaction.user}")
        
        await interaction.response.send_message(embed=embed)
        
        # Get the message to add reactions
        message = await interaction.original_response()
        for i in range(len(option_list)):
            await message.add_reaction(reactions[i])
        
        await self.logger.log_action(
            interaction.guild, "Poll Created", interaction.user,
            details=f"Question: {question}\nOptions: {len(option_list)}",
            color=0x2F3136
        )
    
    @app_commands.command(name="announce", description="Send a styled announcement to a channel")
    @app_commands.describe(
        channel="The channel to send the announcement to",
        message="The announcement message"
    )
    @has_admin_permissions()
    async def announce(self, interaction: discord.Interaction, channel: discord.TextChannel, message: str):
        if not await check_bot_permissions(interaction, "send_messages", "embed_links"):
            return
        
        embed = discord.Embed(
            title="📢 Announcement",
            description=message,
            color=0x00FF00,
            timestamp=datetime.utcnow()
        )
        
        embed.set_footer(text=f"Announced by {interaction.user}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        try:
            await channel.send(embed=embed)
            
            await self.logger.log_action(
                interaction.guild, "Announcement", interaction.user,
                details=f"Channel: {channel.mention}\nMessage: {message[:100]}{'...' if len(message) > 100 else ''}",
                color=0x00FF00
            )
            
            success_embed = await self.logger.create_success_embed(
                "Announcement Sent",
                f"Announcement sent to {channel.mention}"
            )
            await interaction.response.send_message(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ I don't have permission to send messages in {channel.mention}.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))
