from discord.ext import commands
from discord import app_commands
from typing import Optional
import aiohttp
import DiscordUtils
import asyncio
import discord
import uuid
import logging
import re
import shlex
import argparse
from fftcg_parser import grab_card, grab_cards, grab_cards_beta, prettyCode, tinyOutput, getPack, codeSortKey, cardName, truncate
from constants import (MAX_QUERY, CODE_VALIDATOR, COOLDOWN_USES, COOLDOWN_SECONDS, COMMAND_TIMEOUT, API_TIMEOUT,
                       REQUEST_ID_LENGTH, DISCORD_AUTOCOMPLETE_CHOICES)
from MarcieEmbed import MarcieEmbed


log = logging.getLogger(__name__)


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


ELEMENTS = ['Fire', 'Ice', 'Wind', 'Earth', 'Lightning', 'Water', 'Light', 'Dark']
CARD_TYPES = ['Forward', 'Backup', 'Summon', 'Monster', 'Crystal']
CODE_PREFIX = re.compile(r'^([0-9]+|[bc]|pr|re)-', re.IGNORECASE)

# Shown in the name autocomplete before anything is typed, since Discord shows an empty box otherwise
NAME_HINT = app_commands.Choice(name='Start typing a card name or code\u2026', value='__marcie_hint__')


# Short form of a card for logs, e.g. "1-001H Auron"
def cardLabel(card):
    return f"{card['Code']} {cardName(card)}"


# Describes a MarcieAPI failure without the request URL, which contains the API key
def describeApiError(err):
    if isinstance(err, aiohttp.ClientResponseError):
        return f"HTTP {err.status} {err.message}"
    if isinstance(err, aiohttp.ClientConnectorError):
        return f"cannot connect to {err.host}:{err.port}"
    return type(err).__name__


# Slash command autocomplete for card names.  If the text looks like a card code, suggests codes instead.
async def cardNameAutocomplete(interaction, current):
    cards = interaction.client.get_cog('FFTCG').cards
    current = current.strip().lower()

    if not current:
        return [NAME_HINT]

    if CODE_PREFIX.match(current):
        hits = [card for card in cards if card['Code'].lower().startswith(current)][:DISCORD_AUTOCOMPLETE_CHOICES]
        return [app_commands.Choice(name=truncate(f"{card['Code']} \u00B7 {cardName(card)}"), value=card['Code'])
                for card in hits]

    names = {card['Name_EN'] for card in cards if card['Name_EN'] and current in card['Name_EN'].lower()}
    names = sorted(names, key=lambda n: (not n.lower().startswith(current), n.lower()))[:DISCORD_AUTOCOMPLETE_CHOICES]
    return [app_commands.Choice(name=truncate(n), value=truncate(n)) for n in names]


# Slash command autocomplete for /pack, listing each numbered set with its name
async def packAutocomplete(interaction, current):
    cards = interaction.client.get_cog('FFTCG').cards
    sets = {}
    for card in cards:
        prefix = card['Code'].split('-')[0]
        if prefix.isdigit() and '/' not in card['Code']:
            sets.setdefault(int(prefix), card['Set'])

    choices = [f"{number} \u00B7 {name}" for number, name in sorted(sets.items())]
    choices = [choice for choice in choices if current.strip().lower() in choice.lower()][:DISCORD_AUTOCOMPLETE_CHOICES]
    return [app_commands.Choice(name=choice, value=choice.split(' ')[0]) for choice in choices]


class FFTCG(commands.Cog):
    def __init__(self, bot, api):
        self.bot = bot
        self.api = api
        self.cards = []
        self.session = None
        self.codevalidator = re.compile(CODE_VALIDATOR)

    async def cog_load(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT))
        await self.loadCards()

    async def cog_unload(self):
        await self.session.close()

    # Pulls the card list from MarcieAPI.  On failure the current card list is kept.
    async def loadCards(self):
        try:
            async with self.session.get(self.api) as resp:
                resp.raise_for_status()
                self.cards = sorted(await resp.json(content_type=None), key=codeSortKey)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            log.error(f"Unable to load cards from MarcieAPI: {describeApiError(err)}")
            return False

        log.info(f"Loaded {len(self.cards)} cards from MarcieAPI")
        return True

    # True (after telling the user) if they picked the "Start typing" hint instead of a card
    @staticmethod
    async def pickedHint(ctx, name):
        if name != NAME_HINT.value:
            return False

        await ctx.send(embed=MarcieEmbed.toEmbed('Type a card name or code', 'For example **auron** or **1-001H**'),
                       ephemeral=True)
        return True

    @staticmethod
    def newRequestId(ctx):
        # This UUID is used to track requests in logs for recreation of potential issues
        my_uuid = uuid.uuid1().hex[:REQUEST_ID_LENGTH]

        if ctx.interaction:
            options = ' '.join(f"{key}:{value}" for key, value in vars(ctx.interaction.namespace).items())
            invocation = f"/{ctx.interaction.command.qualified_name} {options}"
        else:
            invocation = ctx.message.content

        log.info(f"{invocation} - ID: {my_uuid}")
        return my_uuid

    @staticmethod
    async def selectLogic(ctx, bot, cards, uuid, embedfn, lang):
        embed = MarcieEmbed.cardlistToEmbed(cards, uuid)
        mymessage = await ctx.send(embed=embed)

        def check(msg):
            return (msg.channel == ctx.channel and msg.author == ctx.author
                    and msg.content.isdigit() and 1 <= int(msg.content) <= len(cards))

        # This is where we wait for a message from the user who initiated the command
        # It will time out after 10 seconds.
        try:
            message = await bot.wait_for('message', check=check, timeout=COMMAND_TIMEOUT)

        # If we don't receive a message after 10 seconds we send a timeout embed
        except asyncio.TimeoutError:
            log.info(f"Command timed out - ID: {uuid}")
            embed = MarcieEmbed.COMMANDTIMEOUT()
            embed.set_footer(text='ID: ' + uuid)
            await mymessage.edit(embed=embed)
            return

        mycard = cards[int(message.content) - 1]
        log.info(f"Choice {message.content}: {cardLabel(mycard)} - ID: {uuid}")

        try:
            await message.delete()
        except discord.Forbidden:
            log.info(f"Marcie does not have permission to delete messages in {ctx.guild} - ID: {uuid}")

        await mymessage.edit(embed=embedfn(mycard, uuid, lang))

    # Shared response for a list of matched cards: no match, a single card, too many, or a selection prompt.
    async def sendCards(self, ctx, cards, my_uuid, embedfn, lang):
        if not cards:
            log.info(f"No match - ID: {my_uuid}")
            embed = MarcieEmbed.NOMATCH()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.send(embed=embed)

        elif len(cards) == 1:
            log.info(f"Result: {cardLabel(cards[0])} - ID: {my_uuid}")
            await ctx.send(embed=embedfn(cards[0], my_uuid, lang))

        # If there are more than MAX_QUERY cards in the list return too many cards as an embed
        elif len(cards) >= MAX_QUERY:
            embed = MarcieEmbed.TOOMANYCARDS()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.send(embed=embed)

        # Else we have to parse through the cards and ask for user input
        else:
            await self.selectLogic(ctx, self.bot, cards, my_uuid, embedfn, lang)

    # Shared body of ?name and ?image.  Searches by code if the input looks like one, otherwise by name.
    async def lookup(self, ctx, name, embedfn):
        if await self.pickedHint(ctx, name):
            return

        my_uuid = self.newRequestId(ctx)

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex
            mycard = grab_card(name.upper(), self.cards)
            mycards = [mycard] if mycard else []
        else:
            mycards = []
            if ctx.interaction:
                mycards = [card for card in self.cards if card['Name_EN'].lower() == name.lower()]
            if not mycards:
                mycards = grab_cards(name.lower(), self.cards)

        await self.sendCards(ctx, mycards, my_uuid, embedfn, 'en')

    async def paginateCards(self, ctx, cards, my_uuid, lang='en'):
        if not cards:
            embed = MarcieEmbed.NOMATCH()
            embed.set_footer(text='ID: ' + my_uuid)
            await ctx.send(embed=embed)
            return

        embed_list = [MarcieEmbed.cardToImageEmbed(card, my_uuid, lang) for card in cards]
        paginator = DiscordUtils.Pagination.AutoEmbedPaginator(ctx, remove_reactions=True)
        await paginator.run(embed_list)

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Compact list of cards matching a name')
    @app_commands.describe(name='Card name or code (regex works too)')
    @app_commands.autocomplete(name=cardNameAutocomplete)
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

        if await self.pickedHint(ctx, name):
            return

        self.newRequestId(ctx)
        await ctx.send(tinyOutput(grab_cards(name.lower(), self.cards), MAX_QUERY))

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
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
            log.info(f"Unable to split ?adv arguments: {err}")
            await ctx.send(embed=MarcieEmbed.toEmbed('ValueError', str(err)))
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
            await ctx.send(f'```{parser.format_usage()}\n{e}```')
            return

        filters = {key: value for key, value in vars(args).items()
                   if key not in ['tiny', 'lang', 'image', 'paginate']}

        if args.tiny:
            output = 'tiny'
        elif args.image:
            output = 'image'
        elif args.paginate:
            output = 'paginate'
        else:
            output = 'text'

        await self.advSearch(ctx, filters, output, args.lang.lower())

    @app_commands.command(name='adv', description='Search cards by any combination of filters')
    @app_commands.describe(name='Card name (regex)', job='Card job (regex)', element='Card element', cost='Card cost',
                           card_type='Card type', category='Card category, e.g. VII or FFCC (regex)',
                           power='Card power, e.g. 9000', output='How to show the results (default: text)',
                           lang='Language of card images (default: English)')
    @app_commands.rename(card_type='type')
    @app_commands.choices(element=[app_commands.Choice(name=e, value=e) for e in ELEMENTS],
                          card_type=[app_commands.Choice(name=t, value=t) for t in CARD_TYPES],
                          output=[app_commands.Choice(name='Text', value='text'),
                                  app_commands.Choice(name='Image', value='image'),
                                  app_commands.Choice(name='Tiny list', value='tiny'),
                                  app_commands.Choice(name='Paginated images', value='paginate')],
                          lang=[app_commands.Choice(name='English', value='en'),
                                app_commands.Choice(name='Japanese', value='jp')])
    @app_commands.autocomplete(name=cardNameAutocomplete)
    @app_commands.checks.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS)
    async def advSlash(self, interaction, name: Optional[str] = None, job: Optional[str] = None,
                       element: Optional[str] = None, cost: Optional[int] = None, card_type: Optional[str] = None,
                       category: Optional[str] = None, power: Optional[int] = None, output: str = 'text',
                       lang: str = 'en'):
        ctx = await commands.Context.from_interaction(interaction)
        if await self.pickedHint(ctx, name):
            return

        filters = {'name': name, 'job': job, 'element': element, 'cost': cost, 'type': card_type,
                   'category': category, 'power': power}

        if not any(value is not None for value in filters.values()):
            await ctx.send(embed=MarcieEmbed.toEmbed('Add at least one filter', 'For example name, element or cost'),
                           ephemeral=True)
            return

        await self.advSearch(ctx, filters, output, lang)

    # Shared body of ?adv and /adv
    async def advSearch(self, ctx, filters, output, lang):
        my_uuid = self.newRequestId(ctx)

        try:
            mycard = grab_cards_beta(self.cards, filters)
        except re.error as err:
            await ctx.send(embed=MarcieEmbed.toEmbed('Invalid regex', str(err)))
            return

        if output == 'tiny':
            await ctx.send(tinyOutput(mycard, MAX_QUERY))
        elif output == 'image':
            await self.sendCards(ctx, mycard, my_uuid, MarcieEmbed.cardToImageEmbed, lang)
        elif output == 'paginate':
            await self.paginateCards(ctx, mycard, my_uuid, lang)
        else:
            await self.sendCards(ctx, mycard, my_uuid, MarcieEmbed.cardToNameEmbed, lang)

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Open a random booster pack from a set')
    @app_commands.describe(opus='Set number, e.g. 8 for Opus VIII or 22 for Hidden Hope')
    @app_commands.autocomplete(opus=packAutocomplete)
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

        await ctx.send(f'```{output}```')

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Show a card\'s text')
    @app_commands.describe(name='Card name or code (regex works too)')
    @app_commands.autocomplete(name=cardNameAutocomplete)
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

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Show a card\'s image')
    @app_commands.describe(name='Card name or code (regex works too)')
    @app_commands.autocomplete(name=cardNameAutocomplete)
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

    @commands.cooldown(COOLDOWN_USES, COOLDOWN_SECONDS, type=commands.BucketType.user)
    @commands.hybrid_command(description='Page through the images of every matching card')
    @app_commands.describe(name='Card name or code (regex works too)')
    @app_commands.autocomplete(name=cardNameAutocomplete)
    async def paginate(self, ctx, *, name: str):
        r"""Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

        This function only takes one argument, a name. It will return the image of the card as an embed.
        If there are multiple matches on your query, the bot will provide react emojis that can be used to page through
        each card. Only the users who create the query will be able to activate these react emojis.

        Known Caveats:
        This command requires the marcie to have `Manage Messages` permission.  Without this permission the react emojis
        will not operate as expected.  If you have any questions please reach out in the support discord.

        This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match
        as you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a
        different substring of the overall card name.

            Example:
            ?paginate sarah (mobius) vs ?paginate sarah \(mobius\)
            ?paginate Mog (XIII-2) vs ?paginate Mog \(XIII-2\)


        Example:
            ?paginate leviathan
        """

        if await self.pickedHint(ctx, name):
            return

        my_uuid = self.newRequestId(ctx)
        await self.paginateCards(ctx, grab_cards(name.lower(), self.cards), my_uuid)

    @commands.is_owner()
    @commands.hybrid_command(description='Reload the card list from MarcieAPI (bot owner only)')
    @app_commands.default_permissions(administrator=True)
    async def refresh(self, ctx):

        """This function enables the ability to refresh the card list the bot uses without restarting the bot
        """

        # As a slash command the reply is only visible to the person who ran it
        await ctx.defer(ephemeral=True)

        if await self.loadCards():
            embed = MarcieEmbed.toEmbed("Cards Refreshed", f"Refreshed {len(self.cards)} cards from MarcieAPI")
        else:
            embed = MarcieEmbed.toEmbed("Refresh Failed", "Unable to reach MarcieAPI, keeping the current card list")
        await ctx.send(embed=embed, ephemeral=True)
