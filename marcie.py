from discord.ext import commands
import discord
import logging
import argparse
import os
from Fftcg import FFTCG
from Management import Management
from MarcieEmbed import MarcieEmbed
from prefix_store import PrefixStore
from constants import DEFAULT_PREFIX, EMBEDCOLOR

__author__ = "Japnix"


# Each argument can also be supplied through an environment variable, which keeps secrets out of `ps` output
def env_argument(parser, short, long, env, help):
    parser.add_argument(short, long, type=str, default=os.environ.get(env), required=env not in os.environ,
                        help=f"{help} (env: {env})")


# Read in prefix from the prefix store, falling back to the default for DMs and guilds without a custom prefix
async def get_pre(bot, message):
    if message.guild is None:
        prefix = DEFAULT_PREFIX
    else:
        prefix = bot.prefixes.get(message.guild.id)

    return commands.when_mentioned_or(prefix)(bot, message)


class Marcie(commands.Bot):
    def __init__(self, prefixes, api):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=get_pre, description='Marcie FFTCG Bot', intents=intents)

        self.prefixes = prefixes
        self.api = api
        self.firstrun = True

    async def setup_hook(self):
        await self.add_cog(FFTCG(self, self.api))
        await self.add_cog(Management(self))

    async def setGuildPrefix(self, guild, prefix):
        self.prefixes.set(guild.id, prefix)

    # This function handles when the bot is removed from a guild under normal operation
    async def on_guild_remove(self, guild):
        self.prefixes.remove(guild.id)
        logging.info(f"Guild: {guild.name} has removed Marcie")

    # This function handles when the bot is added to a guild
    async def on_guild_join(self, guild):
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

        # Drop custom prefixes for guilds that removed Marcie while the bot was offline
        botguilds = {guild.id for guild in self.guilds}
        for guildid in set(self.prefixes.prefixes) - botguilds:
            logging.info(f"Guild {guildid} was removed while the bot was offline.  Removing its prefix.")
            self.prefixes.remove(guildid)

        self.firstrun = False


def load_prefixes(data_dir):
    prefixes = PrefixStore(os.path.join(data_dir, 'prefixes.json'))

    # Carry over custom prefixes from the SQLite database used on the ai_test branch
    legacy_db = os.path.join(data_dir, 'marcie.db')
    if not os.path.exists(prefixes.path) and os.path.exists(legacy_db):
        prefixes.importSqlite(legacy_db)

    return prefixes.load()


def main():
    # Create argparse parser
    parser = argparse.ArgumentParser(description='Run a Marcie bot')
    env_argument(parser, '-a', '--api', 'MARCIE_API', 'Card API address Ex: http://dev.tawa.wtf:8000/api/')
    env_argument(parser, '-t', '--token', 'DISCORD_BOT_TOKEN', 'Discord bot token that will be used')
    env_argument(parser, '-k', '--key', 'MARCIE_API_KEY', 'Card API key')
    parser.add_argument('--data-dir', '--db-path', dest='data_dir', default=os.environ.get('MARCIE_DATA_DIR', '.'),
                        help='Directory for prefixes.json (env: MARCIE_DATA_DIR, default: current directory)')
    args = parser.parse_args()

    # Enable logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    bot = Marcie(load_prefixes(args.data_dir), f"{args.api}?api_key={args.key}")
    bot.run(args.token, log_handler=None)


if __name__ == '__main__':
    main()
