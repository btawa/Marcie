import discord
from discord.ext import commands
from fftcg_parser import *
import sys
import re
import datetime
import logging
import uuid

__author__ = "Japnix"

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# For FFTCG Parser Commands
fftcgURL = 'https://fftcg.square-enix-games.com/getcards'
cards = loadJson(fftcgURL)
MAX_QUERY = 35
embedcolor=0xd93fb6
codevalidator = re.compile(r'^[0-9]+\-[0-9]{3}[a-zA-Z]$|^[0-9]+\-[0-9]{3}$|^[Pp][Rr]\-\d{3}$')

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
    print('Startup Time: ' + str(datetime.datetime.utcnow()))
    print('Guilds Added: ' + str(len(bot.guilds)))
    print('------')



@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def tiny(ctx, *, name: str):
    """Returns a compacted list of cards. Takes a name.  Accepts regex.

    This command was initially created when name and image were less developed.  It takes in a card name and returns a
    compacted list of cards.  It is mostly used as a debug tool now.

    Known Caveats:
    This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
    may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
    the overall card name.

        Example:
        ?tiny sarah (mobius) vs ?name sarah \(mobius\)
        ?tiny Mog (XIII-2) vs ?name Mog \(XIII-2\)

    Example:
        ?tiny auron
    """

    my_uuid = uuid.uuid1().hex[:10]
    logging.info(str(ctx.prefix) + str(ctx.command) + ' ' + str(name) + ' - ID: ' + my_uuid)

    mycard = grab_cards(name.lower(), cards)

    output = ''

    if mycard == []:
        output = '```No Match```'
    else:
        if len(mycard) >= MAX_QUERY:
            output = 'Too many cards please be more specific'
        else:
            for x in mycard:
                output = output + prettyCode(x) + "\n"

        if len(output) >= 2000:
            output = '```Too many characters for discord, please be more specific````'
        else:
            output = '```' + output + '```'

    await ctx.channel.send(output)


@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def name(ctx, *, name: str):
    """Returns text of card. Takes code or name.  Accepts regex.

    This function only takes one argument, either a name or card code. It will return the text and thumbnail of the card
    as an embed. If there are multiple matches on your query, the bot will provide you with a list of cards that you can
    respond to by simply sending a message with the corresponding number (this will timeout after 10 seconds).

    Known Caveats:
    This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
    may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
    the overall card name.

        Example:
        ?name sarah (mobius) vs ?name sarah \(mobius\)
        ?name Mog (XIII-2) vs ?name Mog \(XIII-2\)

    Example:
        ?name auron
        ?name 1-001H
        ?name 1-001
    """

    my_uuid = uuid.uuid1().hex[:10]
    logging.info(str(ctx.prefix) + str(ctx.command) + ' ' + str(name) + ' - ID: ' + my_uuid)

    if re.match(codevalidator, name):

        mycard = grab_card(name.upper(), cards)

        if not mycard:
            mycard_pretty = None
        else:
            mycard_pretty = prettyCard(mycard)

        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=embedcolor, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
        else:
            logging.info('\n' + prettyCard(mycard))
            embed = discord.Embed(title=mycard_pretty.split('\n', 1)[0],
                                  timestamp=datetime.datetime.utcnow(),
                                  description=mycard_pretty.split('\n', 1)[1],
                                  color=embedcolor)
            embed.set_footer(text='ID: ' + my_uuid)
            embed.set_thumbnail(url=getimageURL(mycard[u'Code']))
            await ctx.channel.send(embed=embed)

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=embedcolor, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
        else:
            if len(mycard) >= MAX_QUERY:
                embed = discord.Embed(title='Too many cards please be more specific', color=embedcolor,
                                      timestamp=datetime.datetime.utcnow())
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            elif len(mycard) == 1:
                logging.info('\n' + prettyCard(mycard[0]))
                embed = discord.Embed(title=str(prettyCard(mycard[0]).split('\n', 1)[0]),
                                      timestamp=datetime.datetime.utcnow(),
                                      description=str(prettyCard(mycard[0]).split('\n', 1)[1]),
                                      color=embedcolor)
                embed.set_thumbnail(url=getimageURL(mycard[0][u'Code']))
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            else:
                for x in mycard:
                    if mycard.index(x) == 0:
                        output = str(mycard.index(x) + 1) + ".) " + prettyCode(x)
                    else:
                        output = output + "\n" + str(mycard.index(x) + 1) + ".) " + prettyCode(x)

                if len(output) >= 2000:
                    embed = discord.Embed(title='Too many characters please be more specific', color=embedcolor,
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title='Please choose a card by typing its number',
                                          timestamp=datetime.datetime.utcnow(),
                                          description=output,
                                          color=embedcolor)
                    embed.set_footer(text='ID: ' + my_uuid)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        if re.match(r'^\d+$', str(msg.content)) and msg.channel == ctx.channel and ctx.author == msg.author:
                            if len(mycard) >= int(msg.content) >= 1:
                                logging.info('Choice: ' + msg.content)
                                return True
                        else:
                            return False

                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    except:
                        logging.info('Command timed out')
                        embed = discord.Embed(title='Command timed out', color=embedcolor,
                                              timestamp=datetime.datetime.utcnow())
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)
                        return

                    else:
                        logging.info('\n' + prettyCard(mycard[int(message.content) - 1]))
                        embed = discord.Embed(
                            title=str(prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[0]),
                            timestamp=datetime.datetime.utcnow(),
                            description=str(prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[1]),
                            color=embedcolor)
                        embed.set_thumbnail(url=getimageURL(mycard[int(message.content) - 1][u'Code']))
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)


# Testing embed functionality
@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def image(ctx, *, name: str):
    """Returns image of card. Takes code or name.  Accepts regex.

    This function only takes one argument, either a name or card code. It will return the image of the card as an embed.
    If there are multiple matches on your query, the bot will provide you with a list of cards that you can respond to
    by simply sending a message with the corresponding number (this will timeout after 10 seconds).

    Example:
        ?image auron
        ?image 1-001H
        ?image 1-001
    """

    my_uuid = uuid.uuid1().hex[:10]
    logging.info(str(ctx.prefix) + str(ctx.command) + ' ' + str(name) + ' - ID: ' + my_uuid)

    if re.match(codevalidator, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=embedcolor, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
        else:
            logging.info(getimageURL(mycard[u'Code']))
            embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=embedcolor)
            embed.set_image(url=getimageURL(mycard[u'Code']))
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            logging.info('No Match')
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=embedcolor))
        else:
            if len(mycard) >= MAX_QUERY:
                embed = discord.Embed(title='Too many cards please be more specific', color=embedcolor,
                                      timestamp=datetime.datetime.utcnow())
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            elif len(mycard) == 1:
                logging.info(getimageURL(mycard[0][u'Code']))
                embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=embedcolor)
                embed.set_image(url=getimageURL(mycard[0][u'Code']))
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            else:
                for x in mycard:
                    if mycard.index(x) == 0:
                        output = str(mycard.index(x) + 1) + ".) " + prettyCode(x)
                    else:
                        output = output + "\n" + str(mycard.index(x) + 1) + ".) " + prettyCode(x)

                if len(output) >= 2000:
                    embed = discord.Embed(title='Too many characters please be more specific', color=embedcolor,
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title='Please choose a card by typing its number',
                                          timestamp=datetime.datetime.utcnow(),
                                          description=output,
                                          color=embedcolor)
                    embed.set_footer(text='ID: ' + my_uuid)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        if re.match(r'^\d+$', str(msg.content)) and msg.channel == ctx.channel and ctx.author == msg.author:
                            if len(mycard) >= int(msg.content) >= 1:
                                logging.info('Choice: ' + msg.content)
                                return True
                        else:
                            return False

                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    except:
                        logging.info('Command timed out')
                        embed = discord.Embed(title='Command timed out', color=embedcolor,
                                              timestamp=datetime.datetime.utcnow())
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)
                        return

                    else:
                        logging.info(getimageURL(mycard[int(message.content) - 1][u'Code']))
                        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=embedcolor)
                        embed.set_image(url=getimageURL(mycard[int(message.content) - 1][u'Code']))
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)


@name.error
@image.error
@tiny.error
async def cooldown_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(embed=discord.Embed(
            description='Command is on cooldown for ' + ctx.author.display_name,
            color=embedcolor))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(str(error))

@bot.event
async def on_guild_join(ctx):
    logging.info('Guild ' + ctx.name + ' added ' + ctx.me.display_name + '.')


bot.run(mytoken)
