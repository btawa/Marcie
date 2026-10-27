from discord.ext import commands
import aiohttp
import asyncio
import discord
import uuid
import logging
import re
import shlex
import argparse
from fftcg_parser import grab_card, grab_cards, grab_cards_beta, prettyCard, prettyCode, tinyOutput, getPack
from constants import MAX_QUERY, CODE_VALIDATOR
from MarcieEmbed import MarcieEmbed
from paginator import CardPaginator
from ffdecks_deck_parser import ffdecksParse


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class FFTCG(commands.Cog):
    def __init__(self, bot, api):
        self.bot = bot
        self.api = api
        self.cards = []
        self.session = None
        self.codevalidator = re.compile(CODE_VALIDATOR)

    async def cog_load(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))
        await self.loadCards()

    async def cog_unload(self):
        await self.session.close()

    # Pulls the card list from MarcieAPI.  On failure the current card list is kept.
    async def loadCards(self):
        try:
            async with self.session.get(self.api) as resp:
                resp.raise_for_status()
                self.cards = await resp.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            logging.error(f"Unable to load cards from MarcieAPI: {err!r}")
            return False

        logging.info(f"Loaded {len(self.cards)} cards from MarcieAPI")
        return True

    @staticmethod
    def newRequestId(ctx):
        # This UUID is used to track requests in logs for recreation of potential issues
        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")
        return my_uuid

    @staticmethod
    async def selectLogic(ctx, bot, cards, uuid, embedfn, lang):
        embed = MarcieEmbed.cardlistToEmbed(cards, uuid)
        mymessage = await ctx.channel.send(embed=embed)

        def check(msg):
            return (msg.channel == ctx.channel and msg.author == ctx.author
                    and msg.content.isdigit() and 1 <= int(msg.content) <= len(cards))

        # This is where we wait for a message from the user who initiated the command
        # It will time out after 10 seconds.
        try:
            message = await bot.wait_for('message', check=check, timeout=10)

        # If we don't receive a message after 10 seconds we send a timeout embed
        except asyncio.TimeoutError:
            logging.info('Command timed out')
            embed = MarcieEmbed.COMMANDTIMEOUT()
            embed.set_footer(text='ID: ' + uuid)
            await mymessage.edit(embed=embed)
            return

        logging.info(f"Choice: {message.content}")
        mycard = cards[int(message.content) - 1]
        logging.info('\n' + prettyCard(mycard))

        try:
            await message.delete()
        except discord.Forbidden:
            logging.info(f'Marcie does not have permission to delete messages in {ctx.guild}')

        await mymessage.edit(embed=embedfn(mycard, uuid, lang))

    # Shared response for a list of matched cards: no match, a single card, too many, or a selection prompt.
    async def sendCards(self, ctx, cards, my_uuid, embedfn, lang):
        if not cards:
            logging.info('No Match')
            embed = MarcieEmbed.NOMATCH()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)

        elif len(cards) == 1:
            logging.info('\n' + prettyCard(cards[0]))
            await ctx.channel.send(embed=embedfn(cards[0], my_uuid, lang))

        # If there are more than MAX_QUERY cards in the list return too many cards as an embed
        elif len(cards) >= MAX_QUERY:
            embed = MarcieEmbed.TOOMANYCARDS()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)

        # Else we have to parse through the cards and ask for user input
        else:
            await self.selectLogic(ctx, self.bot, cards, my_uuid, embedfn, lang)

    # Shared body of ?name and ?image.  Searches by code if the input looks like one, otherwise by name.
    async def lookup(self, ctx, name, embedfn):
        my_uuid = self.newRequestId(ctx)

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex
            mycard = grab_card(name.upper(), self.cards)
            mycards = [mycard] if mycard else []
        else:
            mycards = grab_cards(name.lower(), self.cards)

        await self.sendCards(ctx, mycards, my_uuid, embedfn, 'en')

    async def paginateCards(self, ctx, cards, my_uuid, lang='en'):
        if not cards:
            embed = MarcieEmbed.NOMATCH()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.channel.send(embed=embed)
            return

        embed_list = [MarcieEmbed.cardToImageEmbed(card, my_uuid, lang) for card in cards]
        await CardPaginator(ctx.author, embed_list).send(ctx)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def tiny(self, ctx, *, name: str):
        r"""Returns a compacted list of cards. Takes a name.  Accepts regex.

        This command was initially created when name and image were less developed.  It takes in a card name and returns
         a compacted list of cards.  It is mostly used as a debug tool now.

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match
        as you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a
        different substring of the overall card name.

            Example:
            ?tiny sarah (mobius) vs ?name sarah \(mobius\)
            ?tiny Mog (XIII-2) vs ?name Mog \(XIII-2\)

        Example:
            ?tiny auron
        """

        self.newRequestId(ctx)
        await ctx.channel.send(tinyOutput(grab_cards(name.lower(), self.cards), MAX_QUERY))

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def adv(self, ctx, *, arg):

        r"""This command allows card querying by providing arguments to filter off of.
            -n, --name - Card Name (Yuna, Vaelfor, etc. (takes regex))
            -j, --job - Card Job (Summoner, Samurai, etc. (takes regex))
            -e, --element - Card Element (Fire, Ice, Light, etc.)
            -c, --cost - Card Cost (Int)
            -t, --type - Card Type (Forward, Backup, etc.)
            -g, --category - Card Category (FFCC, X, etc.)
            -p, --power - Card Power (9000, 3000, etc.)
            -y, --tiny - Print cards in tiny output
            -i, --image - Return card as image format
            -l, --lang - Language of returned image/thumbnail (en, jp)
            -a, --paginate - Returned cards will provide pagination embed

        Example:
            ?adv --name yuna --type backup --cost 2

        Known Caveats:
            - If using card name or card job which has spaces please surround argument in quotes:
                ?adv --name "Cloud of Darkness" --type forward --cost 5

            - Special regex characters need to be escaped.:
                ?adv --name "Cid \(Mobius\)"
        """

        try:
            query = shlex.split(arg)
        except ValueError as err:
            logging.info(err)
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('ValueError', str(err)))
            return

        parser = Arguments(description="Advanced argument parser", add_help=False)
        parser.add_argument('-j', '--job', type=str)
        parser.add_argument('-e', '--element', type=str)
        parser.add_argument('-c', '--cost', type=int)
        parser.add_argument('-t', '--type', type=str)
        parser.add_argument('-n', '--name', type=str)
        parser.add_argument('-g', '--category', type=str)
        parser.add_argument('-p', '--power', type=int)
        parser.add_argument('-y', '--tiny', action="store_true")
        parser.add_argument('-l', '--lang', type=str, default='en')
        parser.add_argument('-i', '--image', action="store_true")
        parser.add_argument('-a', '--paginate', action="store_true")

        try:
            args = parser.parse_args(query)
        except RuntimeError as e:
            await ctx.channel.send(f'```{parser.format_usage()}\n{e}```')
            return

        my_uuid = self.newRequestId(ctx)
        lang = args.lang.lower()

        filters = {key: value for key, value in vars(args).items()
                   if key not in ['tiny', 'lang', 'image', 'paginate']}

        try:
            mycard = grab_cards_beta(self.cards, filters)
        except re.error as err:
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('Invalid regex', str(err)))
            return

        if args.tiny:
            await ctx.channel.send(tinyOutput(mycard, MAX_QUERY))
        elif args.image:
            await self.sendCards(ctx, mycard, my_uuid, MarcieEmbed.cardToImageEmbed, lang)
        elif args.paginate:
            await self.paginateCards(ctx, mycard, my_uuid, lang)
        else:
            await self.sendCards(ctx, mycard, my_uuid, MarcieEmbed.cardToNameEmbed, lang)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def pack(self, ctx, opus):
        """Returns a randomized pack based on the opus you provide.

        Named sets use their number, e.g. 15 is Crystal Dominion and 22 is Hidden Hope.

        Example:
        ?pack 8
        ?pack 22

        """

        self.newRequestId(ctx)
        mycard = getPack(opus, self.cards)

        if mycard is None:
            output = 'Issue with pack command'
        else:
            output = '\n'.join(prettyCode(x) for x in mycard)

        await ctx.channel.send(f'```{output}```')

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def name(self, ctx, *, name: str):
        r"""Returns text of card. Takes code or name.  Accepts regex.

        This function only takes one argument, either a name or card code. It will return the text and thumbnail of the
        card as an embed. If there are multiple matches on your query, the bot will provide you with a list of cards
        that you can respond to by simply sending a message with the corresponding number (this will timeout after 10
        seconds).

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match
        as you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a
        different substring of the overall card name.

            Example:
            ?name sarah (mobius) vs ?name sarah \(mobius\)
            ?name Mog (XIII-2) vs ?name Mog \(XIII-2\)

        Example:
            ?name auron
            ?name 1-001H
            ?name 1-001
        """

        await self.lookup(ctx, name, MarcieEmbed.cardToNameEmbed)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def image(self, ctx, *, name: str):
        r"""Returns image of card. Takes code or name.  Accepts regex.

        This function only takes one argument, either a name or card code. It will return the image of the card as an
        embed. If there are multiple matches on your query, the bot will provide you with a list of cards that you can
        respond to by simply sending a message with the corresponding number (this will timeout after 10 seconds).

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match
        as you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a
        different substring of the overall card name.

            Example:
            ?image sarah (mobius) vs ?name sarah \(mobius\)
            ?image Mog (XIII-2) vs ?name Mog \(XIII-2\)


        Example:
            ?image auron
            ?image 1-001H
            ?image 1-001
        """

        await self.lookup(ctx, name, MarcieEmbed.cardToImageEmbed)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def paginate(self, ctx, *, name: str):
        r"""Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

        This function only takes one argument, a name. It will return the image of the card as an embed.
        If there are multiple matches on your query, the bot will provide buttons that can be used to page through
        each card. Only the user who created the query will be able to use these buttons.

        Known Caveats:
        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match
        as you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a
        different substring of the overall card name.

            Example:
            ?paginate sarah (mobius) vs ?paginate sarah \(mobius\)
            ?paginate Mog (XIII-2) vs ?paginate Mog \(XIII-2\)


        Example:
            ?paginate leviathan
        """

        my_uuid = self.newRequestId(ctx)
        await self.paginateCards(ctx, grab_cards(name.lower(), self.cards), my_uuid)

    @commands.is_owner()
    @commands.command()
    async def refresh(self, ctx):

        """This function enables the ability to refresh the card list the bot uses without restarting the bot
        """

        if await self.loadCards():
            embed = MarcieEmbed.toEmbed("Cards Refreshed", f"Refreshed {len(self.cards)} cards from MarcieAPI")
        else:
            embed = MarcieEmbed.toEmbed("Refresh Failed", "Unable to reach MarcieAPI, keeping the current card list")
        await ctx.channel.send(embed=embed)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def ffdeck(self, ctx, url):
        """ This function returns an ascii decklist of an ffdecks deck url (https://ffdecks.com/deck/<deckid>)
        """

        self.newRequestId(ctx)
        parser = ffdecksParse(url)

        if parser.deck_id:
            await parser.load(self.session)

        if parser.ascii_decklist:
            await ctx.channel.send('```' + parser.ascii_decklist + '```')
        else:
            embed = MarcieEmbed.toEmbed("Bad Request", "This request didn't return a decklist")
            await ctx.channel.send(embed=embed)
