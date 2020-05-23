import discord
from discord.ext import commands
from fftcg_parser import *
import sys
import re
import datetime
import logging
import uuid
import os
import json
import pymongo

__author__ = "Japnix"

# MongoDB Client
MONGODB = "mongodb://127.0.0.1:27017"
MYCLIENT = pymongo.MongoClient(MONGODB)
MYDB = MYCLIENT['MarcieProd']

# Enable logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')


# Read in prefix from settings.json
async def get_pre(bot, message):
    mycol = MYDB['settings']
    dbq = mycol.find_one({'guildid': message.guild.id})
    prefix = dbq['prefix']

    return prefix


description = '''Marcie FFTCG Bot
'''

bot = commands.Bot(command_prefix=get_pre, description=description)


# This function handles when the bot is removed from a guild under normal operation
@bot.event
async def on_guild_remove(ctx):
    mycol = MYDB['settings']
    mycol.delete_one({'guildid': ctx.id})


# This function handles when we try to trigger a command with our prefix that doesn't exist
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        logging.info(str(error))


# This function handles when the bot is added to a build
@bot.event
async def on_guild_join(ctx):
    mycol = MYDB['settings']
    mycol.find_one_and_update({'guildid': ctx.id},
                              {'$set': {'guildid': ctx.id, 'prefix': '?', 'name': ctx.name}},
                              upsert=True)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('Startup Time: ' + str(datetime.datetime.utcnow()))
    print('Guilds Added: ' + str(len(bot.guilds)))
    print('------')

    mycol = MYDB['settings']
    dbq = mycol.find()

    dbguilds = [doc['guildid'] for doc in dbq]
    botguilds = [guild.id for guild in bot.guilds]


    # If when we start the bot there are more guilds in settings.json then the bot see's as joined
    # we remove those bots from settings.json
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
    logging.info(f"{ctx.message.content} - ID: {my_uuid}")

    mycard = grab_cards(name.lower(), cards)

    output = ''

    if not mycard:
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
async def pack(ctx, opus, *args):
    """BETA - Returns a randomized pack based on the opus you provide.

    The -sp flag can be used to generate a strawpoll for pack 1 pick 1

    Example:
    ?pack 8

    """

    strawpoll = False

    for arg in args:
        if arg == '-sp':
            strawpoll = True
        else:
            strawpoll = False

    my_uuid = uuid.uuid1().hex[:10]
    logging.info(f"{ctx.message.content} - ID: {my_uuid}")
    mycard = getPack(opus, cards)

    output = ''

    if mycard is None:
        output = 'Issue with pack command'
    else:
        for x in mycard:
            output = output + prettyCode(x) + "\n"

    output = '```' + output + '```'

    if strawpoll is True:
        mypoll = createstrawpoll('Marcie Pack 1 Pick 1 Strawpoll', mycard)
        output = output + f"\n<https://www.strawpoll.me/{mypoll['id']}>"
        logging.info(f"https://www.strawpoll.me/{mypoll['id']}")
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

    # This UUID is used to track requests in logs for recreation of potential issues
    my_uuid = uuid.uuid1().hex[:10]
    logging.info(f"{ctx.message.content} - ID: {my_uuid}")

    if re.match(CODEVALIDATOR, name):  # Checking to see if we match a code with regex

        mycard = grab_card(name.upper(), cards)  # Trying to grab that card

        # If we return a card format its text into a pretty string
        if not mycard:
            mycard_pretty = None
        else:
            mycard_pretty = prettyCard(mycard)

        # When we don't match return no match as embed
        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
        # Print the card information as an embed
        else:
            logging.info('\n' + prettyCard(mycard))
            embed = discord.Embed(title=mycard_pretty.split('\n', 1)[0],
                                  timestamp=datetime.datetime.utcnow(),
                                  description=mycard_pretty.split('\n', 1)[1],
                                  color=EMBEDCOLOR)
            embed.set_footer(text='ID: ' + my_uuid)
            embed.set_thumbnail(url=mycard['image_url'])
            await ctx.channel.send(embed=embed)

    # If we don't match a code, the we assume we are searching by name
    else:

        mycard = grab_cards(name.lower(), cards)  # Grabbing our cards to parse

        output = ''

        # When we don't match return no match as embed
        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)

        # When we do match
        else:
            # If there are more than MAX_QUERY cards in the list return too many cards as an embed
            if len(mycard) >= MAX_QUERY:
                embed = discord.Embed(title='Too many cards please be more specific', color=EMBEDCOLOR,
                                      timestamp=datetime.datetime.utcnow())
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # If there is only one match, return that card as an embed
            elif len(mycard) == 1:
                logging.info('\n' + prettyCard(mycard[0]))
                embed = discord.Embed(title=str(prettyCard(mycard[0]).split('\n', 1)[0]),
                                      timestamp=datetime.datetime.utcnow(),
                                      description=str(prettyCard(mycard[0]).split('\n', 1)[1]),
                                      color=EMBEDCOLOR)
                embed.set_thumbnail(url=mycard[0]['image_url'])
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # Else we have to parse through the cards and ask for user input
            else:

                # Preparing our list of cards string to be sent.
                for x in mycard:
                    if mycard.index(x) == 0:
                        output = str(mycard.index(x) + 1) + ".) " + prettyCode(x)
                    else:
                        output = output + "\n" + str(mycard.index(x) + 1) + ".) " + prettyCode(x)

                # If output is more than 2000 characters (Discord Limit) than we send error embed
                if len(output) >= 2000:
                    embed = discord.Embed(title='Too many characters please be more specific', color=EMBEDCOLOR,
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)

                else:

                    # Print list of cards as an embed
                    embed = discord.Embed(title='Please choose a card by typing its number',
                                          timestamp=datetime.datetime.utcnow(),
                                          description=output,
                                          color=EMBEDCOLOR)
                    embed.set_footer(text='ID: ' + my_uuid)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        if re.match(r'^\d+$', str(msg.content)) and msg.channel == ctx.channel and ctx.author == msg.author:
                            if len(mycard) >= int(msg.content) >= 1:
                                logging.info(f"Choice: {msg.content}")
                                return True
                        else:
                            return False

                    # This is where we wait for a message from the user who initiated the command
                    # It will time out after 10 seconds.
                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    # If we don't receive a message after 10 seconds we send a timeout embed
                    except:
                        logging.info('Command timed out')
                        embed = discord.Embed(title='Command timed out', color=EMBEDCOLOR,
                                              timestamp=datetime.datetime.utcnow())
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)
                        return

                    # Else we send the card at the requested index as an embed by editing the message that was initially
                    # sent as a list of cards
                    else:
                        logging.info('\n' + prettyCard(mycard[int(message.content) - 1]))
                        embed = discord.Embed(
                            title=str(prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[0]),
                            timestamp=datetime.datetime.utcnow(),
                            description=str(prettyCard(mycard[int(message.content) - 1]).split('\n', 1)[1]),
                            color=EMBEDCOLOR)
                        embed.set_thumbnail(url=mycard[int(message.content) - 1]['image_url'])
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)


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
    logging.info(f"{ctx.message.content} - ID: {my_uuid}")

    if re.match(CODEVALIDATOR, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            logging.info('No Match')
            embed = discord.Embed(title='No Match', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
        else:
            logging.info(mycard[u'image_url'])
            embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)
            embed.set_image(url=mycard[u'image_url'])
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            logging.info('No Match')
            await ctx.channel.send(embed=discord.Embed(title='No Match', color=EMBEDCOLOR))
        else:
            if len(mycard) >= MAX_QUERY:
                embed = discord.Embed(title='Too many cards please be more specific', color=EMBEDCOLOR,
                                      timestamp=datetime.datetime.utcnow())
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            elif len(mycard) == 1:
                logging.info(mycard[0][u'image_url'])
                embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)
                embed.set_image(url=mycard[0][u'image_url'])
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            else:
                for x in mycard:
                    if mycard.index(x) == 0:
                        output = str(mycard.index(x) + 1) + ".) " + prettyCode(x)
                    else:
                        output = output + "\n" + str(mycard.index(x) + 1) + ".) " + prettyCode(x)

                if len(output) >= 2000:
                    embed = discord.Embed(title='Too many characters please be more specific', color=EMBEDCOLOR,
                                          timestamp=datetime.datetime.utcnow())
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)
                else:
                    embed = discord.Embed(title='Please choose a card by typing its number',
                                          timestamp=datetime.datetime.utcnow(),
                                          description=output,
                                          color=EMBEDCOLOR)
                    embed.set_footer(text='ID: ' + my_uuid)
                    mymessage = await ctx.channel.send(embed=embed)

                    # This is what we use to check to see if our input is within
                    # the range of our card index
                    def check(msg):
                        if re.match(r'^\d+$', str(msg.content)) and msg.channel == ctx.channel and ctx.author == msg.author:
                            if len(mycard) >= int(msg.content) >= 1:
                                logging.info(f"Choice: {msg.content}")
                                return True
                        else:
                            return False

                    try:
                        message = await bot.wait_for('message', check=check, timeout=10)

                    except:
                        logging.info('Command timed out')
                        embed = discord.Embed(title='Command timed out', color=EMBEDCOLOR,
                                              timestamp=datetime.datetime.utcnow())
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)
                        return

                    else:
                        logging.info(getimageURL(mycard[int(message.content) - 1][u'Code']))
                        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)
                        embed.set_image(url=mycard[int(message.content) - 1][u'image_url'])
                        embed.set_footer(text='ID: ' + my_uuid)
                        await mymessage.edit(embed=embed)


@pack.error
@name.error
@image.error
@tiny.error
async def cooldown_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send(embed=discord.Embed(
            description='Command is on cooldown for ' + ctx.author.display_name,
            color=EMBEDCOLOR))


@bot.command()
async def prefix(ctx, prefix):
    """This command allows guild owners or administrators to change the prefix used for commands.

    The default prefix is `?`

    Example:
        ?prefix z!

        Then...

        z!name WOL
    """

    mycol = MYDB['settings']

    if ctx.message.author.id == ctx.guild.owner.id or ctx.message.author.guild_permissions.administrator is True:
        logging.info(ctx.guild.name + ' (' + str(ctx.guild.id) + ') ' + 'changed prefix to ' + prefix)

        mycol.find_one_and_update({'guildid': ctx.guild.id}, {'$set': {'prefix': prefix}})

        embed = discord.Embed(title='Switched prefix to ' + str(prefix), color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())

    else:
        embed = discord.Embed(title='You are not the guild owner or administrator.', color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
    await ctx.channel.send(embed=embed)


# For FFTCG Parser Commands

with open(os.path.dirname(__file__) + '/marcieapi.json', 'r') as infile:
    keys = json.load(infile)

fftcgURL = f"http://dev.tawa.wtf:8000/api/?api_key={keys['API_KEY']}"
cards = loadJson(fftcgURL)
MAX_QUERY = 35
EMBEDCOLOR=0xd93fb6
CODEVALIDATOR = re.compile(r'^[0-9]+\-[0-9]{3}[a-zA-Z]$|^[0-9]+\-[0-9]{3}$|^[Pp][Rr]\-\d{3}$|^[0-9]+\-[0-9]{3}[a-zA-Z]\/?')

# Used to pass token as a variable when launching bot
# Allows to not post sensitive data to github
# python3 <marcie.py> 'token'
mytoken = sys.argv[1]

bot.run(mytoken)

