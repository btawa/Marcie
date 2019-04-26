import discord
from discord.ext import commands
from fftcg_parser import *
import sys
import re
import datetime


# For FFTCG Parser Commands
fftcgURL = 'https://fftcg.square-enix-games.com/getcards'
cards = loadJson(fftcgURL)
MAX_QUERY = 35
embedcolor=0xd93fb6
codevalidator = re.compile('^[0-9]+\-[0-9]{3}[a-zA-Z]$|^[0-9]+\-[0-9]{3}$|^[Pp][Rr]\-\d{3}$')

# Used to pass token as a variable when launching bot
# Allows to not post sensitive data to github
# python3 <marcie.py> 'token'
mytoken = sys.argv[1]

description = '''Marcie FFTCG Bot
'''

bot = commands.Bot(command_prefix='?', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def tiny(ctx, name: str):
    """List cards that match the search."""

    mycard = grab_cards(name.lower(), cards)

    output = ''

    if mycard == []:
        await ctx.channel.send('```No Match```')
    else:
        # print(len(mycard))
        if len(mycard) >= MAX_QUERY:
            output = 'Too many cards please be more specific'
        else:
            for x in mycard:
                # print(prettyCard(x))
                output = output + prettyCode(x) + "\n"

        if len(output) >= 2000:
            await ctx.channel.send('```Too many characters for discord, please be more specific````')
        else:
            await ctx.channel.send('```' + output + '```')
        # print(len(output))


@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def name(ctx, name: str):
    """Returns text of card. Takes code or name.  Accepts regex."""

    if re.match(codevalidator, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=embedcolor))
        else:
            embed = discord.Embed(title=prettyCard(mycard).split('\n', 1)[0], timestamp=datetime.datetime.now(),
                                  description=str(prettyCard(mycard).split('\n', 1)[1]), color=0xd93fb6)
            embed.set_thumbnail(url=getimageURL(mycard[u'Code']))
            await ctx.channel.send(embed=embed)

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=embedcolor))
        else:
            # print(len(mycard))
            if len(mycard) >= MAX_QUERY:
                await ctx.channel.send(embed=discord.Embed(title='Too many cards please be more specific',
                                                           color=embedcolor))

            elif len(mycard) == 1:
                embed = discord.Embed(title=str(prettyCard(mycard[0]).split('\n', 1)[0]),
                                      timestamp=datetime.datetime.now(),
                                      description=str(prettyCard(mycard[0]).split('\n', 1)[1]),
                                      color=0xd93fb6)
                embed.set_thumbnail(url=getimageURL(mycard[0][u'Code']))
                mymessage = await ctx.channel.send(embed=embed)

            else:
                for x in mycard:
                    # print(prettyCard(x))
                    output = output + str(mycard.index(x) + 1) + ".) " + prettyCode(x) + "\n"

                if len(output) >= 2000:
                    await ctx.channel.send(embed=discord.Embed(
                        title='Too many characters for discord, please be more specific', color=embedcolor))
                else:
                    embed = discord.Embed(title='Please choose a card by typing its number', timestamp=datetime.datetime.now(),
                                          description=output, color=0xd93fb6)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        # print('check ran')
                        if re.match('^\d+$', str(msg.content)) and msg.channel == ctx.channel:
                            if len(mycard) >= int(msg.content) >= 1:
                                # print(len(mycard))
                                return True
                        else:
                            return False

                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    except:
                        return

                    else:
                        embed = discord.Embed(title=str(prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[0]),
                                              timestamp=datetime.datetime.now(),
                                              description=str(
                                                  prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[1]),
                                              color=0xd93fb6)
                        embed.set_thumbnail(url=getimageURL(mycard[int(message.content) - 1][u'Code']))
                        await mymessage.edit(embed=embed)


# Testing embed functionality
@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def image(ctx, name: str):
    """Returns text of card. Takes code or name.  Accepts regex."""

    if re.match(codevalidator, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=embedcolor))
        else:
            embed = discord.Embed(timestamp=datetime.datetime.now(), color=0xd93fb6)
            embed.set_image(url=getimageURL(mycard[u'Code']))
            await ctx.channel.send(embed=embed)

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=embedcolor))
        else:
            # print(len(mycard))
            if len(mycard) >= MAX_QUERY:
                await ctx.channel.send(embed=discord.Embed(title='Too many cards please be more specific',
                                                           color=embedcolor))

            elif len(mycard) == 1:
                embed = discord.Embed(timestamp=datetime.datetime.now(), color=0xd93fb6)
                embed.set_image(url=getimageURL(mycard[0][u'Code']))
                mymessage = await ctx.channel.send(embed=embed)

            else:
                for x in mycard:
                    # print(prettyCard(x))
                    output = output + str(mycard.index(x) + 1) + ".) " + prettyCode(x) + "\n"

                if len(output) >= 2000:
                    await ctx.channel.send(embed=discord.Embed(
                        title='Too many characters for discord, please be more specific', color=embedcolor))
                else:
                    embed = discord.Embed(title='Please choose a card by typing its number', timestamp=datetime.datetime.now(),
                                          description=output, color=0xd93fb6)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        # print('check ran')
                        if re.match('^\d+$', str(msg.content)) and msg.channel == ctx.channel:
                            if len(mycard) >= int(msg.content) >= 1:
                                # print(len(mycard))
                                return True
                        else:
                            return False

                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    except:
                        return

                    else:
                        embed = discord.Embed(timestamp=datetime.datetime.now(), color=0xd93fb6)
                        embed.set_image(url=getimageURL(mycard[int(message.content) - 1][u'Code']))
                        await mymessage.edit(embed=embed)


# Error handling for cooldowns
@name.error
@image.error
@tiny.error
async def cooldown_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(embed=discord.Embed(title='```Command is on cooldown for ' + ctx.author.display_name + '```', color=embedcolor))


bot.run(mytoken)
