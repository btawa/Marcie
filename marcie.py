from discord.ext import commands
import discord
import datetime
import logging
from Fftcg import FFTCG
from Management import Management
from config import initialize_config
from database import db_manager

__author__ = "Japnix"

# Initialize configuration
config = initialize_config()

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')


# Read in prefix from SQLite database
async def get_pre(bot, message):
    setting = db_manager.find_one_setting(message.guild.id)
    if setting:
        return setting['prefix']
    return '?'  # Default prefix if guild not found

description = '''Marcie FFTCG Bot
'''

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=get_pre, description=description, intents=intents)

async def setup_cogs():
    await bot.add_cog(FFTCG(bot, config.api_complete_url))
    await bot.add_cog(Management(bot, config.database_path))


# This function handles when the bot is removed from a guild under normal operation
@bot.event
async def on_guild_remove(ctx):
    db_manager.delete_one_setting(ctx.id)
    logging.info(f"Guild: {str(ctx.name)} has removed Marcie")


# This function handles when we try to trigger a command with our prefix that doesn't exist
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(str(error))


# This function handles when the bot is added to a guild
@bot.event
async def on_guild_join(ctx):
    db_manager.upsert_setting(ctx.id, '?', ctx.name)
    logging.info(f"Guild: {ctx.name} has added Marcie")


@bot.event
async def on_ready():
    # Setup cogs when bot is ready
    if config.first_run is True:
        await setup_cogs()

    # on_ready gets can run more than just when the bot is started
    # so we don't need to do all the checks everytime
    
    if config.first_run is True:
        logging.info(f"Logged in as")
        logging.info(f"{bot.user.name}")
        logging.info(f"{bot.user.id}")
        logging.info(f"Startup Time: {str(datetime.datetime.now(datetime.UTC))}")
        logging.info(f"Guilds Added: {str(len(bot.guilds))}")
        logging.info(f"------")

        # Get all settings from database
        all_settings = db_manager.find_all_settings()
        dbguilds = [setting['guildid'] for setting in all_settings]
        botguilds = [guild.id for guild in bot.guilds]

        # If when we start the bot there are more guilds in the db then the bot see's as joined
        # we remove those guilds from the db
        if len(dbguilds) > len(botguilds):
            for guildid in dbguilds:
                if guildid not in botguilds:
                    setting = db_manager.find_one_setting(guildid)
                    if setting:
                        logging.info(f"Guild {setting['name']} ({guildid}) was removed while the bot was offline.  Removing from db.")
                        db_manager.delete_one_setting(guildid)

        # Else if the bot see's more guilds than what is present in settings we add the missing guilds with default
        # settings
        elif len(dbguilds) < len(botguilds):
            for guildid in botguilds:
                if guildid not in dbguilds:
                    guild2add = bot.get_guild(guildid)
                    logging.info(f"Guild {guild2add.name} ({guild2add.id}) was added while the bot was offline.  Adding to db.")
                    db_manager.upsert_setting(guild2add.id, '?', guild2add.name)
        config.first_run = False
    else:
        logging.info('Re-running on_ready, but not first run so doing nothing.')

bot.run(config.discord_token)
