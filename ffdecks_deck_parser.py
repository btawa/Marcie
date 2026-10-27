import re
import logging
import aiohttp


class ffdecksParse:
    def __init__(self, url):
        # inputs
        self.url = url

        # outputs
        self.deck = {}
        self.deck_id = ''
        self.ascii_decklist = ''

        # utility
        self._root_url = 'https://ffdecks.com/api/deck?deck_id='

        self.get_deck_id()

    # Fetches the deck from ffdecks and builds the outputs.  Must be awaited before reading
    # deck or ascii_decklist.
    async def load(self, session):
        await self.get_ffdeck_deck(session)
        if self.deck:
            self.gen_ascii_decklist()

        return self

    def get_deck_id(self):
        match = re.search(r'ffdecks\.com/deck/(\d+)', self.url)
        if match:
            self.deck_id = match.group(1)

        return self

    async def get_ffdeck_deck(self, session):
        link = self._root_url + self.deck_id

        forwards = []
        backups = []
        summons = []
        monsters = []

        try:
            async with session.get(link) as req:
                req.raise_for_status()
                ffdecks_dict = await req.json(content_type=None)

            cards_dict = ffdecks_dict['cards']

            self.deck['deck_name'] = ffdecks_dict['name']
            self.deck['creator'] = ffdecks_dict.get('creator') or None

            for card in cards_dict:
                cur_card = card['card']

                name = cur_card['name']
                cost = cur_card['cost']
                card_type = cur_card['type']
                serial = cur_card['serial_number']
                quantity = card['quantity']

                element = '/'.join(cur_card['elements'][:2])

                card_dict = {'name': name,
                             'cost': cost,
                             'type': card_type,
                             'serial': serial,
                             'quantity': quantity,
                             'element': element}

                if card_type == 'Forward':
                    forwards.append(card_dict)
                elif card_type == 'Summon':
                    summons.append(card_dict)
                elif card_type == 'Monster':
                    monsters.append(card_dict)
                elif card_type == 'Backup':
                    backups.append(card_dict)

            self.deck['forwards'] = sorted(forwards, key=lambda d: d['cost'])
            self.deck['backups'] = sorted(backups, key=lambda d: d['cost'])
            self.deck['monsters'] = sorted(monsters, key=lambda d: d['cost'])
            self.deck['summons'] = sorted(summons, key=lambda d: d['cost'])

            return self

        except (aiohttp.ClientError, ValueError, KeyError, TypeError, IndexError) as e:
            logging.info(f"ffdecks lookup failed for deck {self.deck_id}: {e!r}")
            self.deck = {}
            return self

    def gen_ascii_decklist(self):

        output = f"Deck Name: {self.deck['deck_name']}\n"

        if self.deck['creator']:
            output += f"Creator: {self.deck['creator']}\n\n"
        else:
            output += "\n"

        for section in ['forwards', 'summons', 'monsters', 'backups']:
            if self.deck[section]:
                output += f"{section.capitalize()}:\n"
                for card in self.deck[section]:
                    output += f"{card['quantity']}x ({card['element']}) {card['cost']} {card['name']} ({card['serial']})\n"
                output += '\n'

        self.ascii_decklist = output
        return self
