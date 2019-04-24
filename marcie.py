import discord
from discord.ext import commands
from fftcg_parser import *
import io
import sys
import re


# For FFTCG Parser Commands
fftcgURL = 'https://fftcg.square-enix-games.com/getcards'
cards = loadJson(fftcgURL)
MAX_QUERY = 35
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

# @commands.cooldown(2, 10, type=commands.BucketType.user)
# @bot.command()
# async def code(ctx, code: str):
#     """Pass an FFTCG Card Code to get output"""
#
#     # Input validation to ensure code is 1-234A or 1-234
#     if re.match(codevalidator, code):
#         mycard = grab_card(code.upper(), cards)
#     else:
#         mycard = ''
#
#     if mycard == '':
#         await ctx.channel.send('```No Match```')
#     else:
#         await ctx.channel.send('```' + prettyCard(mycard) + '```')

@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def tiny(ctx, name: str):
    """Pass a card name without code to get card.  For spaces use quotes."""

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
    """This request takes in a card name and then asks which card you would like in name format"""

    if re.match(codevalidator, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            await ctx.channel.send('```No Match```')
        else:
            await ctx.channel.send('```' + prettyCard(mycard) + '```')

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
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
                        await mymessage.edit(content='```' + str(prettyCard(mycard[int(message.content) - 1])) +
                                                     "\n\nYour Choice: " + message.content + '```')


@commands.cooldown(2, 10, type=commands.BucketType.user)
@bot.command()
async def image(ctx, name:str):
    """BETA: Send a card name with user input.  Returns a the image of the card selected"""

    if re.match(codevalidator, name):
        mycard = grab_card(name.upper(), cards)

        if not mycard:
            await ctx.channel.send('```No Match```')
        else:
            await ctx.channel.send(file=discord.File(getImage(mycard[u'Code']), 'card.jpg'))

    else:
        mycard = grab_cards(name.lower(), cards)

        output = ''

        if not mycard:
            await ctx.channel.send('```No Match```')
        else:
            # print(len(mycard))
            if len(mycard) >= MAX_QUERY:
                await ctx.channel.send('```' + 'Too many cards please be more specific' + '```')
            elif len(mycard) == 1:
                await ctx.channel.send(file=discord.File(getImage(mycard[0][u'Code']), 'card.jpg'))
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
                        await mymessage.edit(content='```You chose: ' +
                                                     prettyCode(mycard[int(message.content) - 1 ]) + '```')
                        await ctx.channel.send(file=discord.File(getImage(mycard[int(message.content) - 1][u'Code'])
                                                                 , 'card.jpg'))


#@debug.error
@name.error
@image.error
#@code.error
@tiny.error
async def cooldown_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.channel.send('```Command is on cooldown for ' + ctx.author.display_name + '```')


bot.run(mytoken)
