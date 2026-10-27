from discord.ext import commands
from pymongo import AsyncMongoClient
import discord
import logging
import argparse
import os
from Fftcg import FFTCG
from Management import Management
from MarcieEmbed import MarcieEmbed
from constants import DEFAULT_PREFIX, EMBEDCOLOR

__author__ = "Japnix"


# Each argument can also be supplied through an environment variable, which keeps secrets out of `ps` output
def env_argument(parser, short, long, env, help):
    parser.add_argument(short, long, type=str, default=os.environ.get(env), required=env not in os.environ,
                        help=f"{help} (env: {env})")


# Read in prefix from the cache that is loaded from mongodb
async def get_pre(bot, message):
    if message.guild is None:
        prefix = DEFAULT_PREFIX
    else:
        prefix = bot.prefixes.get(message.guild.id, DEFAULT_PREFIX)

    return commands.when_mentioned_or(prefix)(bot, message)


class Marcie(commands.Bot):
    def __init__(self, db_url, api):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=get_pre, description='Marcie FFTCG Bot', intents=intents)

        self.db_url = db_url
        self.api = api
        self.mongo = None
        self.settings = None
        self.prefixes = {}
        self.firstrun = True

    async def setup_hook(self):
        self.mongo = AsyncMongoClient(self.db_url)
        self.settings = self.mongo['MarcieProd']['settings']

        self.prefixes = {doc['guildid']: doc.get('prefix', DEFAULT_PREFIX) async for doc in self.settings.find()}

        await self.add_cog(FFTCG(self, self.api))
        await self.add_cog(Management(self))

    async def close(self):
        await super().close()
        if self.mongo:
            await self.mongo.close()

    async def addGuild(self, guild):
        await self.settings.find_one_and_update({'guildid': guild.id},
                                                {'$set': {'guildid': guild.id, 'prefix': DEFAULT_PREFIX,
                                                          'name': guild.name}},
                                                upsert=True)
        self.prefixes[guild.id] = DEFAULT_PREFIX

    async def removeGuild(self, guildid):
        await self.settings.delete_one({'guildid': guildid})
        self.prefixes.pop(guildid, None)

    async def setGuildPrefix(self, guild, prefix):
        await self.settings.find_one_and_update({'guildid': guild.id},
                                                {'$set': {'prefix': prefix, 'name': guild.name}},
                                                upsert=True)
        self.prefixes[guild.id] = prefix

    # This function handles when the bot is removed from a guild under normal operation
    async def on_guild_remove(self, guild):
        await self.removeGuild(guild.id)
        logging.info(f"Guild: {guild.name} has removed Marcie")

    # This function handles when the bot is added to a guild
    async def on_guild_join(self, guild):
        await self.addGuild(guild)
        logging.info(f"Guild: {guild.name} has added Marcie")

    async def on_command_error(self, ctx, error):
        # Triggering a command with our prefix that doesn't exist
        if isinstance(error, commands.CommandNotFound):
            logging.info(str(error))

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(embed=discord.Embed(
                description='Command is on cooldown for ' + ctx.author.display_name,
                color=EMBEDCOLOR))

        elif isinstance(error, commands.MissingPermissions):
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('You are not the guild owner or administrator.'))

        elif isinstance(error, commands.NotOwner):
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('Invalid User', 'Only the bot owner can use this command'))

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('This command can only be used in a server'))

        elif isinstance(error, commands.UserInputError):
            await ctx.channel.send(f"```Usage: {ctx.clean_prefix}{ctx.command.qualified_name} {ctx.command.signature}```")

        else:
            logging.error(f"Error in command {ctx.command}: {ctx.message.content}",
                          exc_info=(type(error), error, error.__traceback__))

    async def on_ready(self):

        # on_ready gets can run more than just when the bot is started
        # so we don't need to do all the checks everytime
        if not self.firstrun:
            logging.info('Re-running on_ready, but not first run so doing nothing.')
            return

        logging.info(f"Logged in as")
        logging.info(f"{self.user.name}")
        logging.info(f"{self.user.id}")
        logging.info(f"Startup Time: {discord.utils.utcnow()}")
        logging.info(f"Guilds Added: {len(self.guilds)}")
        logging.info(f"------")

        dbguilds = {doc['guildid']: doc.get('name') async for doc in self.settings.find()}
        botguilds = {guild.id: guild for guild in self.guilds}

        # Guilds in the db that the bot is no longer in were removed while the bot was offline
        for guildid in dbguilds.keys() - botguilds.keys():
            logging.info(f"Guild {dbguilds[guildid]} ({guildid}) was removed while the bot was offline.  Removing from db.")
            await self.removeGuild(guildid)

        # Guilds the bot is in that are missing from the db were added while the bot was offline
        for guildid in botguilds.keys() - dbguilds.keys():
            guild2add = botguilds[guildid]
            logging.info(f"Guild {guild2add.name} ({guild2add.id}) was added while the bot was offline.  Adding to db.")
            await self.addGuild(guild2add)

        self.firstrun = False


def main():
    # Create argparse parser
    parser = argparse.ArgumentParser(description='Run a Marcie bot')
    env_argument(parser, '-d', '--db', 'MARCIE_DB', 'mongodb:// url with port')
    env_argument(parser, '-a', '--api', 'MARCIE_API', 'Card API address Ex: http://dev.tawa.wtf:8000/api/')
    env_argument(parser, '-t', '--token', 'DISCORD_BOT_TOKEN', 'Discord bot token that will be used')
    env_argument(parser, '-k', '--key', 'MARCIE_API_KEY', 'Card API key')
    args = parser.parse_args()

    # Enable logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    bot = Marcie(args.db, f"{args.api}?api_key={args.key}")
    bot.run(args.token, log_handler=None)


if __name__ == '__main__':
    main()
