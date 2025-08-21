from discord.ext import commands
import time
import datetime
import discord
import logging
from constants import EMBEDCOLOR


class Management(commands.Cog):
    def __init__(self, bot, database_path):
        self.bot = bot
        self.appstart = time.time()
        # SQLite database path is stored but not used directly (using db_manager instead)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def uptime(self, ctx):
        """Returns how long marcie has been running.
        """
        s = int(time.time() - self.appstart)
        parts = []
        if s >= 86400: parts.append(f"{s//86400} day{'s' if s//86400 != 1 else ''}")
        if s >= 3600: parts.append(f"{(s%86400)//3600} hour{'s' if (s%86400)//3600 != 1 else ''}")
        if s >= 60: parts.append(f"{(s%3600)//60} minute{'s' if (s%3600)//60 != 1 else ''}")
        
        uptime = f"```up {', '.join(parts) if parts else 'less than a minute'}```"
        await ctx.channel.send(uptime)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def support(self, ctx):
        """Marcie will ping you a invite to the support discord
        """
        msg = "Thanks for using Marcie! If you have any problems or suggestions let Japnix know!\n" \
              "Support Discord: https://discord.gg/ZUZY7wb"

        await ctx.author.send(msg)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def prefix(self, ctx, prefix):
        """This command allows guild owners or administrators to change the prefix used for commands.

        The default prefix is `?`

        Example:
            ?prefix z!

            Then...

            z!name WOL
        """

        if ctx.message.author.id == ctx.guild.owner_id or ctx.message.author.guild_permissions.administrator is True:
            logging.info(ctx.guild.name + ' (' + str(ctx.guild.id) + ') ' + 'changed prefix to ' + prefix)

            from database import db_manager
            db_manager.update_setting_prefix(ctx.guild.id, prefix)

            embed = discord.Embed(title='Switched prefix to ' + str(prefix), color=EMBEDCOLOR,
                                  timestamp=datetime.datetime.utcnow())

        else:
            embed = discord.Embed(title='You are not the guild owner or administrator.', color=EMBEDCOLOR,
                                  timestamp=datetime.datetime.utcnow())
        await ctx.channel.send(embed=embed)

    @support.error
    @uptime.error
    @prefix.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(embed=discord.Embed(
                description='Command is on cooldown for ' + ctx.author.display_name,
                color=EMBEDCOLOR))