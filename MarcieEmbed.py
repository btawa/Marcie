import discord
from constants import EMBEDCOLOR, DISCORD_CACHE_BYPASS
from fftcg_parser import prettyCode, prettyCard


class MarcieEmbed:

    @staticmethod
    def NOMATCH():
        return MarcieEmbed.toEmbed('No Match')

    @staticmethod
    def TOOMANYCARDS():
        return MarcieEmbed.toEmbed('Too many cards please be more specific')

    @staticmethod
    def TOOMANYCHAR():
        return MarcieEmbed.toEmbed('Too many characters please be more specific')

    @staticmethod
    def COMMANDTIMEOUT():
        return MarcieEmbed.toEmbed('Command timed out')

    @staticmethod
    def PARSERERROR():
        return MarcieEmbed.toEmbed('Unable to parse inputs.  Please check inputs and try again')

    @staticmethod
    def toEmbed(title, text=None):
        return discord.Embed(title=title, description=text, color=EMBEDCOLOR, timestamp=discord.utils.utcnow())

    @staticmethod
    def cardlistToEmbed(cards, uuid):
        output = '\n'.join(f"{index}.) {prettyCode(card)}" for index, card in enumerate(cards, start=1))

        embed = discord.Embed(title='Please choose a card by typing its number',
                              timestamp=discord.utils.utcnow(),
                              description=output,
                              color=EMBEDCOLOR)
        embed.set_footer(text='ID: ' + uuid)

        return embed

    @staticmethod
    def _imageUrl(card, lang):
        if lang == 'en':
            url = card.get('image_url')
        elif lang == 'jp':
            url = card.get('image_url_jp')
        else:
            url = None

        return url + DISCORD_CACHE_BYPASS if url else None

    @staticmethod
    def cardToNameEmbed(card, uuid, lang):
        mycard = prettyCard(card)

        embed = discord.Embed(title=mycard.split('\n', 1)[0],
                              timestamp=discord.utils.utcnow(),
                              description=mycard.split('\n', 1)[1],
                              color=EMBEDCOLOR)
        embed.set_footer(text='ID: ' + uuid)

        url = MarcieEmbed._imageUrl(card, lang)
        if url:
            embed.set_thumbnail(url=url)

        return embed

    @staticmethod
    def cardToImageEmbed(card, uuid, lang):
        embed = discord.Embed(timestamp=discord.utils.utcnow(), color=EMBEDCOLOR)

        url = MarcieEmbed._imageUrl(card, lang)
        if url:
            embed.set_image(url=url)

        embed.set_footer(text='ID: ' + uuid)

        return embed
