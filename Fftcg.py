from discord.ext import commands
import DiscordUtils
import discord
from fftcg_parser import *
import uuid
import logging
import re
import shlex
import argparse
from constants import EMBEDCOLOR, MAX_QUERY, CODE_VALIDATOR
from MarcieEmbed import MarcieEmbed
from ffdecks_deck_parser import ffdecksParse


class Arguments(argparse.ArgumentParser):
    def error(self, message):
        raise RuntimeError(message)


class FFTCG(commands.Cog):
    def __init__(self, bot, api):
        self.bot = bot
        self.api = api
        self.cards = loadJson(api)
        self.codevalidator = re.compile(CODE_VALIDATOR)

    @staticmethod
    async def selectLogic(ctx, bot, cards, uuid, querytype, lang):
        embed = MarcieEmbed.cardlistToEmbed(cards, uuid)
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
            embed = MarcieEmbed.COMMANDTIMEOUT()
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
                embed = MarcieEmbed.cardToNameEmbed(mycard, uuid, lang.lower())
            elif querytype == "imagequery":
                embed = MarcieEmbed.cardToImageEmbed(mycard, uuid, lang.lower())
            await mymessage.edit(embed=embed)
        except Exception as err:
            print(err)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def tiny(self, ctx, *, name: str):
        """Returns a compacted list of cards. Takes a name.  Accepts regex.

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

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def adv(self, ctx, *, arg):

        """This command allows card querying by providing arguments to filter off of.
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
            logging.info(f"?adv {arg}")
            query = shlex.split(arg)
        except ValueError as err:
            logging.info(err)
            await ctx.channel.send(embed=MarcieEmbed.toEmbed('ValueError', str(err)))
            return

        parser = Arguments(description="Advanced argument parser", add_help=False)
        parser.add_argument('-j', '--job', type=str)
        parser.add_argument('-e', '--element', type=str)
        parser.add_argument('-c', '--cost', type=str)
        parser.add_argument('-t', '--type', type=str)
        parser.add_argument('-n', '--name', type=str)
        parser.add_argument('-g', '--category', type=str)
        parser.add_argument('-p', '--power', type=str)
        parser.add_argument('-y', '--tiny', action="store_true")
        parser.add_argument('-l', '--lang', type=str, default='en')
        parser.add_argument('-i', '--image', action="store_true")
        parser.add_argument('-a', '--paginate', action="store_true")

        try:
            args = parser.parse_args(query)
        except RuntimeError as e:
            await ctx.channel.send(f'```{parser.format_usage()}\n{e}```')
            return

        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")

        mycard = grab_cards_beta(self.cards, vars(args))

        # Checks for tiny flag to modify output.
        # If no --tiny then we do our normal selection logic
        if args.tiny is False:
            if args.image is True:
                if len(mycard) == 0:
                    await ctx.channel.send(embed=MarcieEmbed.NOMATCH)
                elif len(mycard) == 1:
                    await ctx.channel.send(embed=MarcieEmbed.cardToImageEmbed(mycard[0], my_uuid, args.lang.lower()))
                elif len(mycard) >= MAX_QUERY:
                    await ctx.channel.send(embed=MarcieEmbed.TOOMANYCARDS())
                else:
                    await self.selectLogic(ctx, self.bot, mycard, my_uuid, "imagequery", args.lang.lower())

            elif args.paginate is True:
                embed_list = [MarcieEmbed.cardToImageEmbed(card, my_uuid, 'en') for card in mycard]
                paginator = DiscordUtils.Pagination.AutoEmbedPaginator(ctx, remove_reactions=True)
                await paginator.run(embed_list)

            else:
                if len(mycard) == 0:
                    await ctx.channel.send(embed=MarcieEmbed.NOMATCH)
                elif len(mycard) == 1:
                    await ctx.channel.send(embed=MarcieEmbed.cardToNameEmbed(mycard[0], my_uuid, args.lang.lower()))
                elif len(mycard) >= MAX_QUERY:
                    await ctx.channel.send(embed=MarcieEmbed.TOOMANYCARDS())
                else:
                    await self.selectLogic(ctx, self.bot, mycard, my_uuid, "namequery", args.lang.lower())

        # If we do have --tiny flag then we print our cards in tiny
        else:
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

        # This UUID is used to track requests in logs for recreation of potential issues
        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex

            mycard = grab_card(name.upper(), self.cards)  # Trying to grab that card

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = MarcieEmbed.NOMATCH()
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)
            # Print the card information as an embed
            else:
                logging.info('\n' + prettyCard(mycard))
                embed = MarcieEmbed.cardToNameEmbed(mycard, my_uuid, 'en')
                await ctx.channel.send(embed=embed)

        # If we don't match a code, the we assume we are searching by name
        else:

            mycard = grab_cards(name.lower(), self.cards, "Name")  # Grabbing our cards to parse

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = MarcieEmbed.NOMATCH()
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # When we do match
            else:

                # If there are more than MAX_QUERY cards in the list return too many cards as an embed
                if len(mycard) >= MAX_QUERY:
                    embed = MarcieEmbed.TOOMANYCARDS()
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)

                # If there is only one match, return that card as an embed
                elif len(mycard) == 1:
                    logging.info('\n' + prettyCard(mycard[0]))
                    embed = MarcieEmbed.cardToNameEmbed(mycard[0], my_uuid, 'en')
                    await ctx.channel.send(embed=embed)

                # Else we have to parse through the cards and ask for user input
                else:
                    await self.selectLogic(ctx, self.bot, mycard, my_uuid, "namequery", 'en')

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def image(self, ctx, *, name: str):
        """Returns image of card. Takes code or name.  Accepts regex.

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

        # This UUID is used to track requests in logs for recreation of potential issues
        my_uuid = uuid.uuid1().hex[:10]
        logging.info(f"{ctx.message.content} - ID: {my_uuid}")

        if re.match(self.codevalidator, name):  # Checking to see if we match a code with regex

            mycard = grab_card(name.upper(), self.cards)  # Trying to grab that card

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = MarcieEmbed.NOMATCH()
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)
            # Print the card information as an embed
            else:
                logging.info('\n' + prettyCard(mycard))
                embed = MarcieEmbed.cardToImageEmbed(mycard, my_uuid, 'en')
                await ctx.channel.send(embed=embed)

        # If we don't match a code, the we assume we are searching by name
        else:

            mycard = grab_cards(name.lower(), self.cards, "Name")  # Grabbing our cards to parse

            # When we don't match return no match as embed
            if not mycard:
                logging.info('No Match')
                embed = MarcieEmbed.NOMATCH()
                embed.set_footer(text='ID: ' + my_uuid)
                await ctx.channel.send(embed=embed)

            # When we do match
            else:

                # If there are more than MAX_QUERY cards in the list return too many cards as an embed
                if len(mycard) >= MAX_QUERY:
                    embed = MarcieEmbed.TOOMANYCARDS()
                    embed.set_footer(text='ID: ' + my_uuid)
                    await ctx.channel.send(embed=embed)

                # If there is only one match, return that card as an embed
                elif len(mycard) == 1:
                    logging.info('\n' + prettyCard(mycard[0]))
                    embed = MarcieEmbed.cardToImageEmbed(mycard[0], my_uuid, 'en')
                    await ctx.channel.send(embed=embed)

                # Else we have to parse through the cards and ask for user input
                else:
                    await self.selectLogic(ctx, self.bot, mycard, my_uuid, "imagequery", 'en')

    @commands.command()
    async def paginate(self, ctx, *, name: str):
        """Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

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

        my_uuid = uuid.uuid1().hex[:10]
        mycards = grab_cards(name.lower(), self.cards, "Name")

        embed_list = [MarcieEmbed.cardToImageEmbed(card, my_uuid, 'en') for card in mycards]

        paginator = DiscordUtils.Pagination.AutoEmbedPaginator(ctx, remove_reactions=True)

        await paginator.run(embed_list)

    @commands.command()
    async def refresh(self, ctx):

        """This function enables the ability to refresh the card list the bot uses without restarting the bot
        """

        if ctx.message.author.id == 137703200458407936:
            self.cards = loadJson(self.api)
            embed = MarcieEmbed.toEmbed("Cards Refreshed", "Refreshed cards from MarcieAPI")
            await ctx.channel.send(embed=embed)
        else:
            embed = MarcieEmbed.toEmbed("Invalid User", f"You are not Japnix")
            await ctx.channel.send(embed=embed)

    @commands.command()
    async def ffdeck(self, ctx, url):
        """ This function returns an ascii decklist of an ffdecks deck url (https://ffdecks.com/deck/<deckid>)
        """

        print(url)
        if re.search(r'.*ffdecks.com/deck/\d+.*', url):
            parser = ffdecksParse(url)
            ascii_list = parser.ascii_decklist

            if ascii_list:
                await ctx.channel.send('```' + ascii_list + '```')
            else:
                embed = MarcieEmbed.toEmbed("Bad Request", "This request didn't return a decklist")
                await ctx.channel.send(embed=embed)

        else:
            embed = MarcieEmbed.toEmbed("Bad Request", "This request didn't return a decklist")
            await ctx.channel.send(embed=embed)

    @ffdeck.error
    @tiny.error
    @adv.error
    @pack.error
    @name.error
    @image.error
    @paginate.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(embed=discord.Embed(
                description='Command is on cooldown for ' + ctx.author.display_name,
                color=EMBEDCOLOR))
