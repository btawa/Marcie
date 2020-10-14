from discord.ext import commands
import DiscordUtils
import discord
from fftcg_parser import *
import uuid
import logging
import re
import shlex
import argparse
import datetime
from constants import EMBEDCOLOR, MAX_QUERY

NOMATCH_EMBED = discord.Embed(title='No Match', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())
TOOMANYCARDS_EMBED = discord.Embed(title='Too many cards please be more specific', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())
TOOMANYCHAR_EMBED = discord.Embed(title='Too many characters please be more specific', color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())


def cardlistToEmbed(cards, uuid):
    output = str()

    for card in cards:
        if cards.index(card) == 0:
            output = str(cards.index(card) + 1) + ".) " + prettyCode(card)
        else:
            output = output + "\n" + str(cards.index(card) + 1) + ".) " + prettyCode(card)

    embed = discord.Embed(title='Please choose a card by typing its number',
                          timestamp=datetime.datetime.utcnow(),
                          description=output,
                          color=EMBEDCOLOR)
    embed.set_footer(text='ID: ' + uuid)

    return embed


def cardToNameEmbed(card, uuid):
    mycard = prettyCard(card)

    embed = discord.Embed(title=mycard.split('\n', 1)[0],
                          timestamp=datetime.datetime.utcnow(),
                          description=mycard.split('\n', 1)[1],
                          color=EMBEDCOLOR)
    embed.set_footer(text='ID: ' + uuid)
    embed.set_thumbnail(url=card['image_url'])

    return embed


def cardToImageEmbed(card, uuid):
    embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)
    embed.set_image(url=card[u'image_url'])
    embed.set_footer(text='ID: ' + uuid)

    return embed


async def selectLogic(ctx, bot, cards, uuid, querytype):
    embed = cardlistToEmbed(cards, uuid)
    mymessage = await ctx.channel.send(embed=embed)
    
    def check(msg):
        if re.match(r'^\d+$', str(msg.content)) and msg.channel == ctx.channel and ctx.author == msg.author:
            if len(cards) >= int(msg.content) >= 1:
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
        embed.set_footer(text='ID: ' + uuid)
        await mymessage.edit(embed=embed)
        return

    logging.info('\n' + prettyCard(cards[int(message.content) - 1]))

    try:
        mycard = cards[int(message.content) - 1]

        try:
            await message.delete()
        except discord.Forbidden:
            logging.info(f'Marcie does not have permission to delete messages in {ctx.guild.name}')
        finally:
            pass

        if querytype == "namequery":
            embed = cardToNameEmbed(mycard, uuid)
        elif querytype == "imagequery":
            embed = cardToImageEmbed(mycard, uuid)
        await mymessage.edit(embed=embed)
    except Exception as err:
        print(err)


class FFTCG(commands.Cog):
    def __init__(self, bot, api):
        self.bot = bot
        self.api = api
        self.cards = loadJson(api)
        self.codevalidator = re.compile(r'^[0-9]+\-[0-9]{3}[a-zA-Z]$|^[0-9]+\-[0-9]{3}$|^[Pp][Rr]\-\d{3}$|^[0-9]+\-[0-9]{3}[a-zA-Z]\/?')

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def tiny(self, ctx, *, name: str):
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

        mycard = grab_cards(name.lower(), self.cards, "Name")

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

    @commands.command()
    async def beta(self, ctx, *, arg):

        """This command allows card querying by providing arguments to filter off of.
            -n, --name - Card Name (Yuna, Vaelfor, etc. (takes regex))
            -j, --job - Card Job (Summoner, Samurai, etc. (takes regex))
            -e, --element - Card Element (Fire, Ice, Light, etc.)
            -c, --cost - Card Cost (Int)
            -t, --type - Card Type (Forward, Backup, etc.)
            -g, --category - Card Category (FFCC, X, etc.)
            -p, --power - Card Power (9000, 3000, etc.)

        Example:
            ?beta --name yuna --type backup --cost 2

        Known Caveats:
            - If using card name or card job which has spaces please surround argument in quotes:
                ?beta --name "Cloud of Darkness" --type forward --cost 5

            - Special regex characters need to be escaped.:
                ?beta --name "Cid \(Mobius\)"
        """

        query = shlex.split(arg)

        parser = argparse.ArgumentParser(description="beta argument parser")
        parser.add_argument('-j', '--job', type=str)
        parser.add_argument('-e', '--element', type=str)
        parser.add_argument('-c', '--cost', type=str)
        parser.add_argument('-t', '--type', type=str)
        parser.add_argument('-n', '--name', type=str)
        parser.add_argument('-g', '--category', type=str)
        parser.add_argument('-p', '--power', type=str)

        try:
            args = parser.parse_args(query)
        except SystemExit as err:
            await ctx.channel.send('```marcie.py [-j JOB] [-p POWER] [-g CATEGORY] [-e ELEMENT] [-c COST] [-t TYPE] [-n NAME]```')
            return

        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")

        mycard = grab_cards_beta(self.cards, vars(args))

        if len(mycard) == 0:
            await ctx.channel.send(embed=NOMATCH_EMBED)
        elif len(mycard) == 1:
            await ctx.channel.send(embed=cardToNameEmbed(mycard[0], my_uuid))
        else:
            await selectLogic(ctx, self.bot, mycard, my_uuid, "namequery")

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def pack(self, ctx, opus, *args):
        """Returns a randomized pack based on the opus you provide.

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
        mycard = getPack(opus, self.cards)

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
    @commands.command()
    async def name(self, ctx, *, name: str):
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

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex

            mycard = grab_card(name.upper(), self.cards)  # Trying to grab that card

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = NOMATCH_EMBED
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)
            # Print the card information as an embed
            else:
                logging.info('\n' + prettyCard(mycard))
                embed = cardToNameEmbed(mycard, my_uuid)
                await ctx.channel.send(embed=embed)

        # If we don't match a code, the we assume we are searching by name
        else:

            mycard = grab_cards(name.lower(), self.cards, "Name")  # Grabbing our cards to parse

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = NOMATCH_EMBED
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # When we do match
            else:

                # If there are more than MAX_QUERY cards in the list return too many cards as an embed
                if len(mycard) >= MAX_QUERY:
                    embed = TOOMANYCARDS_EMBED
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)

                # If there is only one match, return that card as an embed
                elif len(mycard) == 1:
                    logging.info('\n' + prettyCard(mycard[0]))
                    embed = cardToNameEmbed(mycard[0], my_uuid)
                    await ctx.channel.send(embed=embed)

                # Else we have to parse through the cards and ask for user input
                else:
                    await selectLogic(ctx, self.bot, mycard, my_uuid, "namequery")

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def image(self, ctx, *, name: str):
        """Returns image of card. Takes code or name.  Accepts regex.

        This function only takes one argument, either a name or card code. It will return the image of the card as an embed.
        If there are multiple matches on your query, the bot will provide you with a list of cards that you can respond to
        by simply sending a message with the corresponding number (this will timeout after 10 seconds).

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
        may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
        the overall card name.

            Example:
            ?image sarah (mobius) vs ?name sarah \(mobius\)
            ?image Mog (XIII-2) vs ?name Mog \(XIII-2\)


        Example:
            ?image auron
            ?image 1-001H
            ?image 1-001
        """

        # This UUID is used to track requests in logs for recreation of potential issues
        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex

            mycard = grab_card(name.upper(), self.cards)  # Trying to grab that card

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = NOMATCH_EMBED
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)
            # Print the card information as an embed
            else:
                logging.info('\n' + prettyCard(mycard))
                embed = cardToImageEmbed(mycard, my_uuid)
                await ctx.channel.send(embed=embed)

        # If we don't match a code, the we assume we are searching by name
        else:

            mycard = grab_cards(name.lower(), self.cards, "Name")  # Grabbing our cards to parse

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = NOMATCH_EMBED
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # When we do match
            else:

                # If there are more than MAX_QUERY cards in the list return too many cards as an embed
                if len(mycard) >= MAX_QUERY:
                    embed = TOOMANYCARDS_EMBED
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)

                # If there is only one match, return that card as an embed
                elif len(mycard) == 1:
                    logging.info('\n' + prettyCard(mycard[0]))
                    embed = cardToImageEmbed(mycard[0], my_uuid)
                    await ctx.channel.send(embed=embed)

                # Else we have to parse through the cards and ask for user input
                else:
                    await selectLogic(ctx, self.bot, mycard, my_uuid, "imagequery")

    @commands.command()
    async def paginate(self, ctx, *, name: str):
        """Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

        This function only takes one argument, a name. It will return the image of the card as an embed.
        If there are multiple matches on your query, the bot will provide react emojis that can be used to page through each card.
        Only the users who create the query will be able to activate these react emojis.

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
        may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
        the overall card name.

            Example:
            ?paginate sarah (mobius) vs ?paginate sarah \(mobius\)
            ?paginate Mog (XIII-2) vs ?paginate Mog \(XIII-2\)


        Example:
            ?paginate leviathan
        """

        my_uuid = uuid.uuid1().hex[:10]
        mycards = grab_cards(name.lower(), self.cards, "Name")

        embed_list = [cardToImageEmbed(card, my_uuid) for card in mycards]

        paginator = DiscordUtils.Pagination.AutoEmbedPaginator(ctx)
        await paginator.run(embed_list)

    @tiny.error
    @beta.error
    @pack.error
    @name.error
    @image.error
    @paginate.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(embed=discord.Embed(
                description='Command is on cooldown for ' + ctx.author.display_name,
                color=EMBEDCOLOR))