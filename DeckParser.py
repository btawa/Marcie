import requests
import json
import re


class DeckParser:
    def __init__(self, url):
        # inputs
        self.url = url

        # outputs
        self.deck = {}
        self.deck_id = ''
        self.ascii_decklist = ''

        # utility
        self._root_url = 'https://ffdecks.com/api/deck?deck_id='

        # creates and modifies outputs
        self.get_deck_id()
        self.get_ffdeck_deck()
        if self.deck:
            self.gen_ascii_decklist()

    def get_deck_id(self):
        if re.search(r'ffdecks.com/deck/', self.url):
            self.deck_id = re.search(r'(deck/)(\d+)', self.url).group(2)

        return self

    def get_ffdeck_deck(self):
        link = self._root_url + self.deck_id

        forwards = []
        backups = []
        summons = []
        monsters = []

        try:
            req = requests.get(link)
            ffdecks_dict = json.loads(req.text)
            cards_dict = ffdecks_dict['cards']

            self.deck['deck_name'] = ffdecks_dict['name']

            if ffdecks_dict['creator']:
                self.deck['creator'] = ffdecks_dict['creator']
            else:
                self.deck['creator'] = None

            for card in cards_dict:
                cur_card = card['card']

                name = cur_card['name']
                cost = cur_card['cost']
                card_type = cur_card['type']
                serial = cur_card['serial_number']
                quantity = card['quantity']

                element = cur_card['elements']
                if len(element) > 1:
                    element = f"{element[0]}/{element[1]}"
                else:
                    element = element[0]

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

        except Exception as e:
            self.deck = {}
            return self

    def gen_ascii_decklist(self):

        output = f"Deck Name: {self.deck['deck_name']}\n"

        if self.deck['creator']:
            output += f"Creator: {self.deck['creator']}\n\n"
        else:
            output += "\n"

        if self.deck['forwards']:
            output += "Forwards:\n"
            for card in self.deck['forwards']:
                line = f"{card['quantity']}x ({card['element']}) {card['cost']} {card['name']} ({card['serial']})\n"
                output += line
            output += '\n'

        if self.deck['summons']:
            output += "Summons:\n"
            for card in self.deck['summons']:
                line = f"{card['quantity']}x ({card['element']}) {card['cost']} {card['name']} ({card['serial']})\n"
                output += line
            output += '\n'

        if self.deck['monsters']:
            output += "Monsters:\n"
            for card in self.deck['monsters']:
                line = f"{card['quantity']}x ({card['element']}) {card['cost']} {card['name']} ({card['serial']})\n"
                output += line
            output += '\n'

        if self.deck['backups']:
            output += "Backups:\n"
            for card in self.deck['backups']:
                line = f"{card['quantity']}x ({card['element']}) {card['cost']} {card['name']} ({card['serial']})\n"
                output += line
            output += '\n'

        self.ascii_decklist = output
        return self
