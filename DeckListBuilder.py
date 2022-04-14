import io
from PIL import Image
import requests
from io import BytesIO
import urllib.request, json
import math
import re

__author__ = "mostly laorik, some tawa"


class DeckListBuilder:
    def __init__(self, deck_id):

        # Inputs
        self.deck_id = deck_id

        # For Drawing
        self.CARD_SPACER = 10
        self.CARDS_PER_ROW = 7
        self.IMAGE_WIDTH = 100
        self.IMAGE_HEIGHT = 140
        self.CARD_VERTICAL_SPACING = 12

        # Output
        self.deck_list_image = None
        self.bytes_image = None

        # Create image on instantiation
        self.create_decklist_image()
        self.make_bytes()

    class Card:
        def __init__(self, name, image, quantity, cost):
            self.name = name
            self.image = image
            self.quantity = quantity
            self.cost = cost

    def create_image(self, cards):
        rows = int(math.ceil(len(cards) / self.CARDS_PER_ROW))
        card_index = 0
        row_index = 0
        card_height = [0] * rows
        for card in cards:
            if card.quantity > card_height[row_index]:
                card_height[row_index] = card.quantity
            row_index = int((card_index + 1) / self.CARDS_PER_ROW)
            card_index = card_index + 1
        image_height = rows * self.IMAGE_HEIGHT
        for height in card_height:
            image_height += height * self.CARD_VERTICAL_SPACING
        new_image = Image.new(mode='RGBA', size=(
        self.IMAGE_WIDTH * self.CARDS_PER_ROW + self.CARD_SPACER * (self.CARDS_PER_ROW - 1), image_height - self.CARD_VERTICAL_SPACING),
                              color=(0, 0, 0, 0))

        i = 0
        x = 0
        row_y = 0
        for card in cards:
            y = 0
            for quantity_index in range(card.quantity):
                new_image.paste(card.image, (x, row_y + y))
                if card.quantity > 1:
                    y = y + self.CARD_VERTICAL_SPACING
            x = x + self.IMAGE_WIDTH + self.CARD_SPACER
            if (i + 1) % self.CARDS_PER_ROW == 0:
                row_y = row_y + self.IMAGE_HEIGHT + (card_height[int(i / self.CARDS_PER_ROW)] * self.CARD_VERTICAL_SPACING)
                x = 0
            i = i + 1
        self.deck_list_image = new_image
        return self

    def get_deck(self, deck_id):
        deck_url = "https://ffdecks.com/api/deck?deck_id=" + deck_id
        with urllib.request.urlopen(deck_url) as url:
            data = json.loads(url.read().decode())
            return data

    def sort_deck_data(self):
        deck_data = self.get_deck(self.deck_id)

        forwards = []
        summons = []
        monsters = []
        backups = []

        for card in deck_data['cards']:
            image_url = re.search(r'(https://storage.*\.[a-zA-Z]+)', card['card']['image']).group(1)

            image = requests.get(image_url)
            card_image = Image.open(BytesIO(image.content))
            card_image = card_image.resize((self.IMAGE_WIDTH, self.IMAGE_HEIGHT))

            if card['card']['type'] == "Forward":
                mycard = self.Card(card['card']['name'], card_image, card['quantity'], card['card']['cost'])
                forwards.append(mycard)
            elif card['card']['type'] == "Summon":
                mycard = self.Card(card['card']['name'], card_image, card['quantity'], card['card']['cost'])
                summons.append(mycard)
            elif card['card']['type'] == "Monster":
                mycard = self.Card(card['card']['name'], card_image, card['quantity'], card['card']['cost'])
                monsters.append(mycard)
            elif card['card']['type'] == "Backup":
                mycard = self.Card(card['card']['name'], card_image, card['quantity'], card['card']['cost'])
                backups.append(mycard)

        forwards = sorted(forwards, key=lambda x: x.cost)
        backups = sorted(backups, key=lambda x: x.cost)
        summons = sorted(summons, key=lambda x: x.cost)
        monsters = sorted(monsters, key=lambda x: x.cost)

        # make the list in order
        deck = []

        for card in forwards:
            deck.append(card)
        for card in summons:
            deck.append(card)
        for card in monsters:
            deck.append(card)
        for card in backups:
            deck.append(card)

        return deck

    def create_decklist_image(self):
        deck = self.sort_deck_data()
        self.create_image(deck)
        return self.deck_list_image

    def make_bytes(self):
        bytes = io.BytesIO()
        self.deck_list_image.save(bytes, 'PNG')
        bytes.seek(0)

        self.bytes_image = bytes

        return self
