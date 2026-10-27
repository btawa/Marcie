import re
import random
import logging

# Helpful jq
#
# jq '.cards[] | select(.Code == "1-028R")'  ./cards.json
#
# JSON Keys
#
# Code      Power       Ex_Burst    Text        Text_EN     Text_DE     Text_ES     Text_FR     Text_IT     Type_NA
# Element   Category_1  Name        Name_EN     Name_DE     Name_ES     Name_FR     Name_IT     Set     Name_NA
# Rarity        Category_2  Type        Type_EN     Type_DE     Type_ES     Type_FR     Type_IT     Text_NA
# Cost      Multicard   Job     Job_EN      Job_DE      Job_ES      Job_FR      Job_IT      Job_NA


# This function reads in a request, and a cards dictionary.
# Based on the request it will search the dictionary for a match
# based on the FFTCG card code and return a single card.

def grab_card(req, cards):
    our_card = ''

    try:
        req = re.compile('^' + req)
    except re.error:
        return our_card

    for x in cards:
        if re.search(req, x['Code'].upper()):
            our_card = x
    return our_card


# This function reads in a request, and a cards dictionary.
# Based on the request it will search for a match based on the
# Name_EN value in the cards dictionary.  This function can
# return a single card or multiple cards.

def grab_cards(req, cards):
    try:
        req = re.compile(req)
    except re.error:
        return []

    return [x for x in cards if re.search(req, x['Name_EN'].lower())]


# Fields that ?adv can filter on, grouped by how they are matched
REGEX_FILTERS = {'name': 'Name_EN', 'job': 'Job_EN', 'category': 'Category_1'}
EXACT_FILTERS = {'type': 'Type_EN'}
INT_FILTERS = {'cost': 'Cost', 'power': 'Power'}


# MarcieAPI returns Cost as a string and Power as an int

def toInt(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# Applies every non-empty filter in filters to cards and returns what is left.
# Raises re.error if a regex filter isn't a valid pattern.

def grab_cards_beta(cards, filters):
    our_cards = cards

    for key, value in filters.items():
        if value is None:
            continue

        if key in REGEX_FILTERS:
            cardre = re.compile(value.lower())
            our_cards = [card for card in our_cards if re.search(cardre, str(card[REGEX_FILTERS[key]]).lower())]
        elif key == 'element':
            # Multi element cards like Fire/Ice match either element or the full pair
            our_cards = [card for card in our_cards
                         if value.lower() in [str(card['Element']).lower()] + str(card['Element']).lower().split('/')]
        elif key in EXACT_FILTERS:
            our_cards = [card for card in our_cards if str(card[EXACT_FILTERS[key]]).lower() == value.lower()]
        elif key in INT_FILTERS:
            our_cards = [card for card in our_cards if toInt(card[INT_FILTERS[key]]) == value]

    return our_cards


# Crystal cards (C-001) come back from MarcieAPI with no name or element

def cardName(card):
    return card['Name_EN'] or card['Type_EN']


def elementCost(card):
    return f"{card['Element']} {card['Cost']} \u00B7 " if card['Element'] else ''


# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the tinycode function.

def prettyCode(card):
    # Multicard Check
    if card['Multicard'] is True:
        multicard = f"· (Generic)"
    else:
        multicard = ''

    line1 = f"{card['Code']} \u00B7 {cardName(card)} \u00B7 {elementCost(card)}{card['Type_EN']} {multicard}"
    return line1


# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the name and code functions.

def prettyCard(card):
    if card['Multicard'] is True:
        multicard = f"· (Generic)"
    else:
        multicard = ''

    #  Prepping different lines for return
    line1 = f"{cardName(card)} \u00B7 {elementCost(card)}({card['Code']}) {multicard}"

    if card['Type_EN'] == "Summon" or not card['Job_EN']:
        line2 = f"{card['Type_EN']} · {card['Category_1']}"
    else:
        line2 = f"{card['Type_EN']} · {card['Job_EN']} · {card['Category_1']}"

    line3 = ''

    if card['Text_EN']:
        for line in card['Text_EN']:
            line3 += f"{line}\n"
    line4 = f"{card['Power']}"

    # Modify return string based on whether card has power or not
    if not card['Power']:
        finished_string = f"{line1}\n{line2}\n{line3}"
    else:
        finished_string = f"{line1}\n{line2}\n{line3}{line4}"

    # Fixes #16, this is needed because markup converts []() to links
    # This causes issue with outputting to discord via embed
    finished_string = finished_string.replace('[', r'\[')
    finished_string = finished_string.replace(']', r'\]')

    return finished_string


# Builds the compact one-card-per-line output used by ?tiny and ?adv --tiny

def tinyOutput(cards, max_query):
    if not cards:
        return '```No Match```'

    if len(cards) >= max_query:
        return 'Too many cards please be more specific'

    output = '\n'.join(prettyCode(card) for card in cards)

    if len(output) >= 1990:
        return '```Too many characters for discord, please be more specific```'

    return f'```{output}```'


# Builds a 12 card pack from the numbered set (1 = Opus I, 15 = Crystal Dominion, ...).  Cards are matched
# on their code prefix since sets after Opus XIV use names instead of numbers.

def getPack(opusnumber, cards):

    heroics = []
    commons = []
    legendaries = []
    rares = []
    pack = []

    try:
        opusnumber = int(opusnumber)
    except ValueError:
        return None

    mycards = [card for card in cards if card['Code'].startswith(f'{opusnumber}-')]

    try:
        for card in mycards:
            if re.search(r'H', card['Rarity']):
                heroics.append(card)
            elif re.search(r'C', card['Rarity']):
                commons.append(card)
            elif re.search(r'L', card['Rarity']):
                legendaries.append(card)
            elif re.search(r'R', card['Rarity']):
                rares.append(card)

        random.shuffle(heroics)
        random.shuffle(commons)
        random.shuffle(rares)
        random.shuffle(legendaries)
        random.shuffle(mycards)

        for x in range(0, 12):
            if x <= 6:
                randomindex = random.randint(0, len(commons) - 1)
                pack.append(commons[randomindex])
                commons.pop(randomindex)
            elif 7 <= x <= 9:
                randomindex = random.randint(0, len(rares) - 1)
                pack.append(rares[randomindex])
                rares.pop(randomindex)
            elif x == 10:
                pack.append(mycards[random.randint(0, len(mycards) - 1)])
            elif x == 11:
                if random.randint(1, 10) <= 2:
                    pack.append(legendaries[random.randint(0, len(legendaries) - 1)])
                else:
                    pack.append(heroics[random.randint(0, len(heroics) - 1)])
        return pack

    except (ValueError, IndexError) as e:
        logging.info(e)
        return None
