from discord.ext import commands
import time
import datetime
import discord
import logging
from MarcieEmbed import MarcieEmbed


class Management(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.appstart = time.time()

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Returns how long marcie has been running.
        """
        uptime = f"```{datetime.timedelta(seconds=time.time() - self.appstart)}```"

        await ctx.channel.send(uptime)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def support(self, ctx):
        """Marcie will ping you a invite to the support discord
        """
        msg = "Thanks for using Marcie! If you have any problems or suggestions let Japnix know!\n" \
              "Support Discord: https://discord.gg/ZUZY7wb"

        try:
            await ctx.author.send(msg)
        except discord.Forbidden:
            await ctx.channel.send(msg)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    @commands.command()
    async def prefix(self, ctx, prefix):
        """This command allows guild owners or administrators to change the prefix used for commands.

        The default prefix is `?`

        Example:
            ?prefix z!

            Then...

            z!name WOL
        """

        logging.info(f"{ctx.guild.name} ({ctx.guild.id}) changed prefix to {prefix}")

        await self.bot.setGuildPrefix(ctx.guild, prefix)

        await ctx.channel.send(embed=MarcieEmbed.toEmbed('Switched prefix to ' + prefix))
