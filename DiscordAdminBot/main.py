import discord
from discord.ext import commands
import asyncio
import os
import json
import logging
from bot_config import BotConfig
from database import Database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class AdminBot(commands.Bot):
    def __init__(self):
        # Define intents
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',  # Fallback prefix, mainly using slash commands
            intents=intents,
            help_command=None
        )
        
        self.config = BotConfig()
        self.db = Database()
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        # Initialize database
        await self.db.initialize()
        
        # Load all cogs
        cog_files = [
            'cogs.moderation',
            'cogs.utility', 
            'cogs.server_management',
            'cogs.special_commands',
            'cogs.message_reports'
        ]
        
        for cog in cog_files:
            try:
                await self.load_extension(cog)
                logging.info(f'Loaded cog: {cog}')
            except Exception as e:
                logging.error(f'Failed to load cog {cog}: {e}')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logging.info(f'Synced {len(synced)} commands')
        except Exception as e:
            logging.error(f'Failed to sync commands: {e}')
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logging.info(f'{self.user} has logged in and is ready!')
        logging.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="for /help | Advanced Admin Bot"
            )
        )
    
    async def on_guild_join(self, guild):
        """Called when bot joins a new guild"""
        logging.info(f'Joined new guild: {guild.name} (ID: {guild.id})')
        
        # Initialize guild settings in database
        await self.db.setup_guild(guild.id)
    
    async def on_command_error(self, ctx, error):
        """Global error handler for prefix commands"""
        if isinstance(error, commands.CommandNotFound):
            return
        
        logging.error(f'Command error in {ctx.command}: {error}')
        
        if ctx.interaction:
            if not ctx.interaction.response.is_done():
                await ctx.interaction.response.send_message(
                    f"An error occurred: {str(error)}", 
                    ephemeral=True
                )
    
    async def on_app_command_error(self, interaction: discord.Interaction, error):
        """Global error handler for slash commands"""
        logging.error(f'Slash command error: {error}')
        
        error_message = "An unexpected error occurred."
        
        if isinstance(error, discord.app_commands.MissingPermissions):
            error_message = "You don't have permission to use this command."
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            error_message = "I don't have the required permissions to execute this command."
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            error_message = f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds."
        
        try:
            if interaction.response.is_done():
                await interaction.followup.send(error_message, ephemeral=True)
            else:
                await interaction.response.send_message(error_message, ephemeral=True)
        except:
            pass

# Main execution
async def main():
    bot = AdminBot()
    
    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logging.error('DISCORD_TOKEN environment variable not found!')
        return
    
    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logging.info('Bot shutdown requested by user')
    except Exception as e:
        logging.error(f'Bot encountered an error: {e}')
    finally:
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
