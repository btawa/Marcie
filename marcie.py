from discord.ext import commands
import datetime
import logging
import pymongo
import argparse
from Fftcg import FFTCG
from Management import Management

__author__ = "Japnix"

# Create argparse parser
parser = argparse.ArgumentParser(description='Run a Marcie bot"')
parser.add_argument('-d', '--db', type=str ,help='mongob:// url with port', required=True)
parser.add_argument('-a', '--api', type=str, help='Card API address Ex: http://dev.tawa.wtf:8000', required=True)
parser.add_argument('-t', '--token', type=str, help='Discord bot token that will be used', required=True)
parser.add_argument('-k', '--key', type=str, help='Card API key', required=True)
args = parser.parse_args()

# MongoDB Client
MYCLIENT = pymongo.MongoClient(args.db)
MYDB = MYCLIENT['MarcieProd']

# Marcie API Args
API_KEY = args.key
API = args.api
API_COMPLETE = f"{API}?api_key={API_KEY}"

# Discord Bot Args
DISCORD_TOKEN = args.token

# Marcie Globals
FIRSTRUN = True

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')


# Read in prefix from mongodb
async def get_pre(bot, message):
    mycol = MYDB['settings']
    dbq = mycol.find_one({'guildid': message.guild.id})
    prefix = dbq['prefix']

    return prefix

description = '''Marcie FFTCG Bot
'''

bot = commands.Bot(command_prefix=get_pre, description=description)
bot.add_cog(FFTCG(bot, API_COMPLETE))
bot.add_cog(Management(bot, args.db))


# This function handles when the bot is removed from a guild under normal operation
@bot.event
async def on_guild_remove(ctx):
    mycol = MYDB['settings']
    mycol.delete_one({'guildid': ctx.id})
    logging.info(f"Guild: {str(ctx.name)} has removed Marcie")


# This function handles when we try to trigger a command with our prefix that doesn't exist
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(str(error))


# This function handles when the bot is added to a guild
@bot.event
async def on_guild_join(ctx):
    mycol = MYDB['settings']
    mycol.find_one_and_update({'guildid': ctx.id},
                              {'$set': {'guildid': ctx.id, 'prefix': '?', 'name': ctx.name}},
                              upsert=True)
    logging.info(f"Guild: {ctx.name} has added Marcie")


@bot.event
async def on_ready():

    # on_ready gets can run more than just when the bot is started
    # so we don't need to do all the checks everytime
    global FIRSTRUN
    
    if FIRSTRUN is True:
        logging.info(f"Logged in as")
        logging.info(f"{bot.user.name}")
        logging.info(f"{bot.user.id}")
        logging.info(f"Startup Time: {str(datetime.datetime.utcnow())}")
        logging.info(f"Guilds Added: {str(len(bot.guilds))}")
        logging.info(f"------")

        mycol = MYDB['settings']
        dbq = mycol.find()

        dbguilds = [doc['guildid'] for doc in dbq]
        botguilds = [guild.id for guild in bot.guilds]


        # If when we start the bot there are more guilds in the db then the bot see's as joined
        # we remove those guilds from the db
        if len(dbguilds) > len(botguilds):
            for guildid in dbguilds:
                if guildid not in botguilds:
                    dbq = mycol.find_one({"guildid": guildid})
                    logging.info(f"Guild {dbq['name']} ({guildid}) was removed while the bot was offline.  Removing from db.")
                    mycol.delete_one({'guildid': guildid})

        # Else if the bot see's more guilds than what is present in settings.json we add the missing guilds with default
        # settings
        elif len(dbguilds) < len(botguilds):
            for guildid in botguilds:
                if guildid not in dbguilds:
                    guild2add = bot.get_guild(guildid)
                    logging.info(f"Guild {guild2add.name} ({guild2add.id}) was added while the bot was offline.  Adding to db.")
                    mycol.find_one_and_update({'guildid': guild2add.id},
                                              {'$set': {'guildid': guild2add.id, 'prefix': '?', 'name': guild2add.name}},
                                              upsert=True)
        FIRSTRUN = False
    else:
        logging.info('Re-running on_ready, but not first run so doing nothing.')

bot.run(DISCORD_TOKEN)
