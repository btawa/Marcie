import discord
import os
import re
from discord.ext import commands
from fftcg_parser import *
import io
from urllib.error import URLError, HTTPError

# For FFTCG Parser Commands
fftcgURL = 'https://fftcg.square-enix-games.com/getcards'
cards = loadJson(fftcgURL)
installdir = '/home/btawa/fftcg_parser/'
MAX_QUERY = 35

# Used to pass token as a variable when launching bot
# Allows to not post sensitive data to github
# python3 <marcie.py> 'token'
mytoken = sys.argv[1]

description = '''Tawa's inefficient FFTCG bot
'''

bot = commands.Bot(command_prefix='?', description=description)

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')


@bot.command()
async def code(ctx, code: str):
    """Pass an FFTCG Card Code to get output"""

    # Input validation to ensure code is 1-234A or 1-234
    if re.match('^[0-9]+\-[0-9]{3}[a-zA-Z]$', code):
        mycard = grab_card(code.upper(), cards)
    elif re.match('^[0-9]+\-[0-9]{3}$', code):
        mycard = grab_card(code.upper(), cards)
    elif re.match('^[Pp][Rr]\-\d{3}$', code):
        mycard = grab_card(code.upper(), cards)
    else:
        mycard = ''

    if mycard == '':
        await ctx.channel.send('```No Match```')
    else:
        await ctx.channel.send('```' + prettyCard(mycard) + '```')


@bot.command()
async def tiny(ctx, name: str):
    """Pass a card name without code to get card.\n
    If card has spaces put card name in quotes."""

    # Input validation to prevent re exceptions
    # Don't let {} , +, or * be only variable
    if name == "+":
        mycard = []
    elif name == "*":
        mycard = []
    elif re.match('^\{\d+\}$', name):
        mycard = []
    else:
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


@bot.command()
async def name(ctx, name: str):
    """BETA : This request takes in a card name and then asks which card you\n would like in name format"""

    # Input validation to prevent re exceptions
    # Don't let {} , +, or * be only variable
    if name == "+" or name == "*" or re.match('^\{\d+\}$', name):
        mycard = []
    else:
        mycard = grab_cards(name.lower(), cards)

    output = ''

    if mycard == []:
        await ctx.channel.send('```No Match```')
    else:
        # print(len(mycard))
        if len(mycard) >= MAX_QUERY:
            await ctx.channel.send('```' + 'Too many cards please be more specific' + '```')
        elif len(mycard) == 1:
            await ctx.channel.send('```' + str(prettyCard(mycard[0])) + '```')
        else:
            for x in mycard:
                # print(prettyCard(x))
                output = output + str(mycard.index(x) + 1) + ".) " + prettyCode(x) + "\n"

            if len(output) >= 2000:
                await ctx.channel.send('```Too many characters for discord, please be more specific````')
            else:
                mymessage = await ctx.channel.send(
                    '```' + output + '\nPlease respond with the card you would like (Ex: 1) [Timeout: 10s]: ' + '```')

                # This is what we use to check to see if our input is within
                # the range of our card index
                def check(msg):
                    # print('check ran')
                    if re.match('^\d+$', str(msg.content)) and msg.channel == ctx.channel:
                        if int(msg.content) <= len(mycard) and int(msg.content) >= 1:
                            # print(len(mycard))
                            return True
                    else:
                        return False

                try:
                    message = await bot.wait_for('message', check=check, timeout=10)

                except:
                    return

                else:
                    await mymessage.edit(content='```' + str(prettyCard(mycard[int(message.content) - 1])) +
                                                 "\n\nYour Choice: " + message.content + '```')


@bot.command()
async def image(ctx, code: str):
    """Pass a card code to get an image of the card"""
    mycard = grab_card(code.upper(), cards)

    if mycard == '':
        await ctx.channel.send('```No Match```')
    else:
        if re.match('^[0-9]+\-[0-9]{3}[a-zA-Z]/[0-9]+\-[0-9]{3}[a-zA-Z]$', mycard[u'Code']):
            URL = 'https://fftcg.square-enix-games.com/theme/tcg/images/cards/full/' + mycard[u'Code'][-6:] + '_eg.jpg'
        else:
            URL = 'https://fftcg.square-enix-games.com/theme/tcg/images/cards/full/' + mycard[u'Code'] + '_eg.jpg'
        if 'linux' or 'darwin' in sys.platform:
            urllib.request.urlretrieve(URL, os.path.dirname(__file__) + '/card.jpg')
            await ctx.channel.send(file=discord.File(os.path.dirname(__file__) + '/card.jpg'))
        elif 'win' in sys.platform:
            urllib.request.urlretrieve(URL, os.path.dirname(__file__) + '\\\\card.jpg')
            await ctx.channel.send(file=discord.File(os.path.dirname(__file__) + '\\\\card.jpg'))
        urllib.request.urlcleanup()


bot.run(mytoken)
