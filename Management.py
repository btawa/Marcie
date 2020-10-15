from discord.ext import commands
import time
import datetime
import pymongo
import discord
import logging
from constants import EMBEDCOLOR


class Management(commands.Cog):
    def __init__(self, bot, mongoaddress):
        self.bot = bot
        self.appstart = time.time()
        self.mongoclient = pymongo.MongoClient(mongoaddress)
        self.db = self.mongoclient['MarcieProd']
        self.settings = self.db['settings']

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

            self.settings.find_one_and_update({'guildid': ctx.guild.id}, {'$set': {'prefix': prefix}})

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