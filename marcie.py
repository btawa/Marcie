from discord.ext import commands
from discord import app_commands
import discord
import hashlib
import json
import logging
import argparse
import os
from Fftcg import FFTCG
from Management import Management
from MarcieEmbed import MarcieEmbed
from prefix_store import PrefixStore
from constants import DEFAULT_PREFIX, EMBEDCOLOR

__author__ = "btawa"

log = logging.getLogger('marcie')


# Each argument can also be supplied through an environment variable, which keeps secrets out of `ps` output
def env_argument(parser, short, long, env, help):
    parser.add_argument(short, long, type=str, default=os.environ.get(env), required=env not in os.environ,
                        help=f"{help} (env: {env})")


def cooldownEmbed(user):
    return discord.Embed(description='Command is on cooldown for ' + user.display_name, color=EMBEDCOLOR)


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

        self.tree.on_error = self.on_app_command_error
        await self.syncCommands()

    # Slash commands only need registering with Discord when they change, so a hash of the last synced
    # commands is kept next to marcie.db.  Delete commands.sha256 to force a sync.
    async def syncCommands(self):
        commands_json = json.dumps([command.to_dict(self.tree) for command in self.tree.get_commands()], sort_keys=True)
        digest = hashlib.sha256(f"{self.application_id}:{commands_json}".encode()).hexdigest()
        digest_path = os.path.join(os.path.dirname(self.prefixes.path) or '.', 'commands.sha256')

        try:
            with open(digest_path) as f:
                if f.read().strip() == digest:
                    log.info('Slash commands unchanged, skipping sync')
                    return
        except FileNotFoundError:
            pass

        synced = await self.tree.sync()
        log.info(f"Synced {len(synced)} slash commands with Discord")

        os.makedirs(os.path.dirname(digest_path), exist_ok=True)
        with open(digest_path, 'w') as f:
            f.write(digest)

    async def setGuildPrefix(self, guild, prefix):
        self.prefixes.set(guild.id, prefix, guild.name)

    # This function handles when the bot is removed from a guild under normal operation
    async def on_guild_remove(self, guild):
        self.prefixes.remove(guild.id)
        log.info(f"Guild: {guild.name} has removed Marcie")

    # This function handles when the bot is added to a guild
    async def on_guild_join(self, guild):
        self.prefixes.add(guild.id, guild.name)
        log.info(f"Guild: {guild.name} has added Marcie")

    # Errors from ? commands and from slash commands that are also ? commands.  Replies to slash commands are only
    # visible to the user who ran them.
    async def on_command_error(self, ctx, error):
        # Triggering a command with our prefix that doesn't exist
        if isinstance(error, commands.CommandNotFound):
            log.debug(str(error))

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=cooldownEmbed(ctx.author), ephemeral=True)

        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=MarcieEmbed.toEmbed('You are not the guild owner or administrator.'), ephemeral=True)

        elif isinstance(error, commands.NotOwner):
            await ctx.send(embed=MarcieEmbed.toEmbed('Invalid User', 'Only the bot owner can use this command'),
                           ephemeral=True)

        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send(embed=MarcieEmbed.toEmbed('This command can only be used in a server'), ephemeral=True)

        elif isinstance(error, commands.UserInputError):
            await ctx.send(f"```Usage: {ctx.clean_prefix}{ctx.command.qualified_name} {ctx.command.signature}```")

        else:
            invocation = f"/{ctx.command.qualified_name}" if ctx.interaction else ctx.message.content
            log.error(f"Error in command {ctx.command}: {invocation}",
                          exc_info=(type(error), error, error.__traceback__))
            if ctx.interaction and not ctx.interaction.response.is_done():
                await ctx.send(embed=MarcieEmbed.toEmbed('Something went wrong'), ephemeral=True)

    # Errors from slash only commands (/adv)
    async def on_app_command_error(self, interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            embed = cooldownEmbed(interaction.user)
        else:
            log.error(f"Error in slash command {interaction.command and interaction.command.qualified_name}",
                          exc_info=(type(error), error, error.__traceback__))
            embed = MarcieEmbed.toEmbed('Something went wrong')

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    async def on_ready(self):

        # on_ready gets can run more than just when the bot is started
        # so we don't need to do all the checks everytime
        if not self.firstrun:
            log.info('Re-running on_ready, but not first run so doing nothing.')
            return

        log.info(f"Logged in as {self.user.name} ({self.user.id}), in {len(self.guilds)} guilds")

        botguilds = {guild.id: guild for guild in self.guilds}

        # If when we start the bot there are guilds in the db the bot isn't in, they removed Marcie while it was offline
        for guildid in set(self.prefixes.prefixes) - botguilds.keys():
            log.info(f"Guild {guildid} was removed while the bot was offline.  Removing from db.")
            self.prefixes.remove(guildid)

        # Guilds the bot is in that are missing from the db added Marcie while it was offline
        for guildid in botguilds.keys() - set(self.prefixes.prefixes):
            guild2add = botguilds[guildid]
            log.info(f"Guild {guild2add.name} ({guild2add.id}) was added while the bot was offline.  Adding to db.")
            self.prefixes.add(guild2add.id, guild2add.name)

        self.firstrun = False


def load_prefixes(data_dir):
    return PrefixStore(os.path.join(data_dir, 'marcie.db')).load()


def main():
    # Create argparse parser
    parser = argparse.ArgumentParser(description='Run a Marcie bot')
    env_argument(parser, '-a', '--api', 'MARCIE_API', 'Card API address Ex: http://dev.tawa.wtf:8000/api/')
    env_argument(parser, '-t', '--token', 'DISCORD_BOT_TOKEN', 'Discord bot token that will be used')
    env_argument(parser, '-k', '--key', 'MARCIE_API_KEY', 'Card API key')
    parser.add_argument('--data-dir', '--db-path', dest='data_dir', default=os.environ.get('MARCIE_DATA_DIR', '.'),
                        help='Directory for marcie.db (env: MARCIE_DATA_DIR, default: current directory)')
    parser.add_argument('--log-level', default=os.environ.get('MARCIE_LOG_LEVEL', 'INFO').upper(),
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='How much to log (env: MARCIE_LOG_LEVEL, default: INFO)')
    args = parser.parse_args()

    # Enable logging
    logging.basicConfig(level=args.log_level, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

    bot = Marcie(load_prefixes(args.data_dir), f"{args.api}?api_key={args.key}")
    bot.run(args.token, log_handler=None)


if __name__ == '__main__':
    main()
