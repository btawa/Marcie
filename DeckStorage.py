import pymongo
from discord.ext import commands
from DeckParser import DeckParser
import re
import discord
import Constants
import datetime
from DeckListBuilder import DeckListBuilder
import logging
import time
from Constants import EMBEDCOLOR


class DeckStorage(commands.Cog):
    def __init__(self, bot: commands.Bot, mongoaddress):
        self.bot = bot
        self.mongoclient = pymongo.MongoClient(mongoaddress)
        self.db = self.mongoclient['MarcieProd']
        self.decks = self.db['decks']

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def save(self, ctx, url: str):

        """This function saves a ffdecks link to the database to share with others

        It takes in input url which must be in the format:
            https://ffdecks.com/deck/<deck id>
        """

        user_id = ctx.message.author.id
        user_name = ctx.message.author.name

        if re.search(r'ffdecks.com/deck/\d+$', url):
            parser = DeckParser(url)
            if parser.deck:
                what_to_store = {'url': parser.url,
                                 'user_id_who_saved': user_id,
                                 'deck_name': parser.deck['deck_name'],
                                 'user_name': user_name}

                query = {'url': parser.url,
                         'user_id_who_saved': user_id}

                self.decks.find_one_and_replace(query, what_to_store, upsert=True)
                await ctx.channel.send(f"```\"{parser.deck['deck_name']}\" was saved```")
            else:
                await ctx.channel.send('We couldn\'t parse this deck.  Is it valid?')
        else:
            await ctx.channel.send(f"```This doesn't look like an ffdecks deck link.```")

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def mydecks(self, ctx):

        """This function returns the users saved decks
        """

        user_id = ctx.message.author.id

        query = {'user_id_who_saved': user_id }
        cursor = self.db.decks.find(query)
        doc_count = self.decks.count_documents(query)  # This is a requirement of mongodb 4.0

        if doc_count == 0:
            await ctx.channel.send(f"```You have no decks```")
            return
        else:
            output = ""
            for deck in cursor:
                output += f"[{deck['deck_name']}]({deck['url']})\n"

            title = f"{ctx.message.author.name}'s Decks"

            embed = discord.Embed(title=title, description=output, color=Constants.EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

            await ctx.channel.send(embed=embed)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def lookup(self, ctx, *, user: str):
        """ This function allows users to look up other peoples saved decks.

        It takes input user which is the first part of the persons discord account name.

        Example:
            Account Name: Yuna#1234
            ?lookup Yuna
        """

        cursor = self.decks.find({'user_name': user})
        query = {'user_name': user}
        doc_count = self.decks.count_documents(query)

        if doc_count == 0:
            await ctx.channel.send(f"```Found no decks for user: {user}```")
        else:
            output = ""
            for deck in cursor:
                output += f"[{deck['deck_name']}]({deck['url']})\n"

            title = f"{user}'s Decks"

            embed = discord.Embed(title=title, description=output, color=Constants.EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

            await ctx.channel.send(embed=embed)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def flushdecks(self, ctx):

        """This command flushes all decks for command user.
        """

        user_id = ctx.message.author.id

        query = {'user_id_who_saved': user_id}

        question = await ctx.channel.send("```Are you sure? (10s) (yes/no)```")

        def check(msg):
            if msg.content.lower() == 'yes' or msg.content.lower() == 'no':
                return True
            else:
                return False

        try:
            message = await self.bot.wait_for('message', check=check, timeout=10)

        except:
            await question.edit(content="```Took too long to respond```")
            return

        if message.content.lower() == 'yes':
            self.decks.delete_many(query)
            await question.edit(content=f"```Flushed all of {ctx.message.author.name}'s decks from db.```")
        else:
            await question.edit(content=f"```Cancelled flushing {ctx.message.author.name}'s decks from db.```")
            return

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def delete(self, ctx, *, deck_name: str):

        """This function deletes a users single deck from the database

        It takes the input deck_name which is the name of the deck in the DB.

        Example:
            ?delete "Mono Wind"
        """

        user_id = ctx.message.author.id

        query = {'user_id_who_saved': user_id, 'deck_name': deck_name }

        deletion = self.decks.delete_one(query)

        if deletion.deleted_count > 0:
            body = f"```\"{deck_name}\" was deleted from the database.```"
        else:
            body = f"```\"{deck_name}\" was not found in the database.```"

        await ctx.channel.send(body)

    @commands.cooldown(2, 10, type=commands.BucketType.user)
    @commands.command()
    async def decklist(self, ctx, url):

        """This command takes in a ffdecks url and prints out a image of the decklist laid out.

            Example: ?decklist https://ffdecks.com/deck/<deck id>
        """
        parser = DeckParser(url)
        try:
            if parser.deck:
                deck_list_image = DeckListBuilder(parser.deck_id)
                filename = int(time.time())
                await ctx.channel.send(file=discord.File(fp=deck_list_image.bytes_image, filename=f'{filename}.jpg'))
        except Exception as e:
            logging.info(e)

    @decklist.error
    @delete.error
    @flushdecks.error
    @lookup.error
    @mydecks.error
    @save.error
    async def cooldown_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.channel.send(embed=discord.Embed(
                description='Command is on cooldown for ' + ctx.author.display_name,
                color=EMBEDCOLOR))