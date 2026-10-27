from discord.ext import commands
from discord import app_commands
import time
import datetime
import discord
import logging
from MarcieEmbed import MarcieEmbed
from constants import COOLDOWN_USES, COOLDOWN_SECONDS, SECONDS_PER_MINUTE, SECONDS_PER_HOUR, SECONDS_PER_DAY


log = logging.getLogger(__name__)


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.appstart = time.time()

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='How long Marcie has been running')
    async def uptime(self, ctx):
        """Returns how long marcie has been running.
        """
        s = int(time.time() - self.appstart)
        days = s // SECONDS_PER_DAY
        hours = (s % SECONDS_PER_DAY) // SECONDS_PER_HOUR
        minutes = (s % SECONDS_PER_HOUR) // SECONDS_PER_MINUTE

        parts = []
        if s >= SECONDS_PER_DAY: parts.append(f"{days} day{'s' if days != 1 else ''}")
        if s >= SECONDS_PER_HOUR: parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if s >= SECONDS_PER_MINUTE: parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

        uptime = f"```up {', '.join(parts) if parts else 'less than a minute'}```"

        await ctx.send(uptime)

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Get an invite to the Marcie support Discord')
    async def support(self, ctx):
        """Marcie will ping you a invite to the support discord
        """
        msg = "Thanks for using Marcie! If you have any problems or suggestions let Japnix know!\n" \
              "Support Discord: https://discord.gg/ZUZY7wb"

        # Slash commands can reply privately, prefix commands DM the user
        if ctx.interaction:
            await ctx.send(msg, ephemeral=True)
            return

        try:
            await ctx.author.send(msg)
        except discord.Forbidden:
            await ctx.send(msg)

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.hybrid_command(description='Change the prefix for Marcie\'s text commands in this server')
    @app_commands.describe(prefix='New prefix, e.g. z!')
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def prefix(self, ctx, prefix):
        """This command allows guild owners or administrators to change the prefix used for commands.

        The default prefix is `?`

        Example:
            ?prefix z!

            Then...

            z!name WOL
        """

        log.info(f"{ctx.guild.name} ({ctx.guild.id}) changed prefix to {prefix}")

        await self.bot.setGuildPrefix(ctx.guild, prefix)

        await ctx.send(embed=MarcieEmbed.toEmbed('Switched prefix to ' + prefix))
