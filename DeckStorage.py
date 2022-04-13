import pymongo
from discord.ext import commands
from DeckParser import DeckParser
import re
import discord
import Constants
import datetime
import logging

class DeckStorage(commands.Cog):
    def __init__(self, bot : commands.Bot, mongoaddress):
        self.bot = bot
        self.mongoclient = pymongo.MongoClient(mongoaddress)
        self.db = self.mongoclient['MarcieProd']
        self.decks = self.db['decks']

    @commands.command()
    async def save(self, ctx, url):
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

    @commands.command()
    async def mydecks(self, ctx):
        user_id = ctx.message.author.id

        query = {'user_id_who_saved': user_id }
        cursor = self.db.decks.find(query)
        doc_count = self.decks.count_documents(query)

        if doc_count == 0:
            await ctx.channel.send(f"```You have no decks```")
            return
        else:
            output = ""
            for deck in cursor:
                output += f"\"{deck['deck_name']}\" - {deck['url']}\n"

            title = f"{ctx.message.author.name}'s Decks"

            embed = discord.Embed(title=title, description=output, color=Constants.EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

            await ctx.channel.send(embed=embed)


    @commands.command()
    async def lookup(self, ctx, user):

        try:
            cursor = self.decks.find({'user_name': user})
            query = {'user_name': user}
            doc_count = self.decks.count_documents(query)

            if doc_count == 0:
                await ctx.channel.send("```Can't find this users data```")
            else:
                output = ""
                for deck in cursor:
                    output += f"\"{deck['deck_name']}\" - {deck['url']}\n"

                title = f"{user}'s Decks"

                embed = discord.Embed(title=title, description=output, color=Constants.EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

                await ctx.channel.send(embed=embed)
        except Exception as e:
            logging.info(str(e))

    @commands.command()
    async def flushdecks(self, ctx):
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

    @commands.command()
    async def delete(self, ctx, deck_name):
        user_id = ctx.message.author.id

        query = {'user_id_who_saved': user_id, 'deck_name': deck_name }

        deletion = self.decks.delete_one(query)

        if deletion.deleted_count > 0:
            body = f"```\"{deck_name}\" was deleted from the database.```"
        else:
            body = f"```\"{deck_name}\" was not found in the database.```"

        await ctx.channel.send(body)
