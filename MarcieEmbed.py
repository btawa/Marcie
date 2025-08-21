"""Discord embed utilities for the Marcie bot."""

from typing import List, Dict, Any
import discord
import datetime
from constants import EMBEDCOLOR, DISCORD_CACHE_BYPASS
from fftcg_parser import prettyCard, prettyCode


class MarcieEmbed:
    """Utility class for creating Discord embeds for FFTCG cards."""

    @staticmethod
    def NOMATCH() -> discord.Embed:
        embed = discord.Embed(title='No Match',
                              color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
        return embed

    @staticmethod
    def TOOMANYCARDS() -> discord.Embed:
        embed = discord.Embed(title='Too many cards please be more specific',
                              color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
        return embed

    @staticmethod
    def TOOMANYCHAR() -> discord.Embed:
        embed = discord.Embed(title='Too many characters please be more specific',
                              color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
        return embed

    @staticmethod
    def COMMANDTIMEOUT() -> discord.Embed:
        embed = discord.Embed(title='Command timed out',
                              color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
        return embed

    @staticmethod
    def PARSERERROR() -> discord.Embed:
        embed = discord.Embed(title='Unable to parse inputs.  Please check inputs and try again',
                              color=EMBEDCOLOR,
                              timestamp=datetime.datetime.utcnow())
        return embed

    @staticmethod
    def toEmbed(title: str, text: str) -> discord.Embed:
        return discord.Embed(title=title, description=text, color=EMBEDCOLOR, timestamp=datetime.datetime.utcnow())

    @staticmethod
    def cardlistToEmbed(cards: List[Dict[str, Any]], uuid: str) -> discord.Embed:
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
    def cardToNameEmbed(card: Dict[str, Any], uuid: str, lang: str) -> discord.Embed:
        mycard = prettyCard(card)

        embed = discord.Embed(title=mycard.split('\n', 1)[0],
                              timestamp=datetime.datetime.utcnow(),
                              description=mycard.split('\n', 1)[1],
                              color=EMBEDCOLOR)
        embed.set_footer(text='ID: ' + uuid)

        if lang == 'en' and card['image_url']:
            embed.set_thumbnail(url=card['image_url'] + DISCORD_CACHE_BYPASS)
        elif lang == 'jp':
            try:
                if card['image_url_jp']:
                    embed.set_thumbnail(url=card['image_url_jp'] + DISCORD_CACHE_BYPASS)
            except KeyError:
                pass
        else:
            pass

        return embed

    @staticmethod
    def cardToImageEmbed(card: Dict[str, Any], uuid: str, lang: str) -> discord.Embed:
        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), color=EMBEDCOLOR)

        if lang == 'en' and card['image_url']:
            embed.set_image(url=card['image_url'] + DISCORD_CACHE_BYPASS)
        elif lang == 'jp':
            try:
                if card['image_url_jp']:
                    embed.set_image(url=card['image_url_jp'] + DISCORD_CACHE_BYPASS)
            except KeyError:
                pass
        else:
            pass

        embed.set_footer(text='ID: ' + uuid)

        return embed
