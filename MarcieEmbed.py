import discord
import datetime
from constants import EMBEDCOLOR
from fftcg_parser import *


class MarcieEmbed:

    NOMATCH = discord.Embed(
        title='No Match',
        color=EMBEDCOLOR,
        imestamp=datetime.datetime.utcnow())

    TOOMANYCARDS = discord.Embed(
        title='Too many cards please be more specific',
        color=EMBEDCOLOR,
        timestamp=datetime.datetime.utcnow())

    TOOMANYCHAR = discord.Embed(
        title='Too many characters please be more specific',
        color=EMBEDCOLOR,
        timestamp=datetime.datetime.utcnow())

    COMMANDTIMEOUT = discord.Embed(
        title='Command timed out',
        color=EMBEDCOLOR,
        timestamp=datetime.datetime.utcnow())

    PARSERERROR = discord.Embed(
        title='Unable to parse inputs.  Please check inputs and try again',
        color=EMBEDCOLOR,
        timestamp=datetime.datetime.utcnow())

    DISCORD_CACHE_BYPASS = "?1"

    @staticmethod
    def toEmbed(title, text):
        return discord.Embed(title=title, description=text, color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

    @staticmethod
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

    @staticmethod
    def cardToNameEmbed(card, uuid, lang):
        mycard = prettyCard(card)

        embed = discord.Embed(title=mycard.split('\n', 1)[0],
                              timestamp=datetime.datetime.utcnow(),
                              description=mycard.split('\n', 1)[1],
                              color=EMBEDCOLOR)
        embed.set_footer(text='ID: ' + uuid)

        if lang == 'en':
            embed.set_thumbnail(url=card['image_url'] + MarcieEmbed.DISCORD_CACHE_BYPASS)
        elif lang == 'jp':
            try:
                embed.set_thumbnail(url=card['image_url_jp'] + MarcieEmbed.DISCORD_CACHE_BYPASS)
            except:
                pass
        else:
            pass

        return embed

    @staticmethod
    def cardToImageEmbed(card, uuid, lang):
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)

        if lang == 'en':
            embed.set_image(url=card[u'image_url'] + MarcieEmbed.DISCORD_CACHE_BYPASS)
        elif lang == 'jp':
            try:
                embed.set_image(url=card[u'image_url_jp'] + MarcieEmbed.DISCORD_CACHE_BYPASS)
            except:
                pass
        else:
            pass

        embed.set_footer(text='ID: ' + uuid)

        return embed
