import json
import re
import urllib.request
import io
import roman
import random
import requests
import time
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')


def grab_card(req, cards):
    our_card = ''

    try:
        req = re.compile('^'+req)
    except:
        return our_card
    else:
        for x in cards:
            if re.search(req, f"{x[u'Code']}{x['Rarity']}".upper()):
                our_card = x
        return our_card


# This function reads in a request, and a cards dictionary.
# Based on the request it will search for a match based on the
# Name_EN value in the cards dictionary.  This function can
# return a single card or multiple cards.

def grab_cards(req, cards, type):
    our_cards = []

    try:
        req = re.compile(req)
    except:
        return our_cards
    else:

        for x in cards:
            if type == "Name":
                if re.search(req, f"{x[u'Name_EN']}".lower()):
                    our_cards.append(x)
            elif type == "Job":
                if re.search(req, f"{x[u'Job_EN']}".lower()):
                    our_cards.append(x)
            elif type == "Title":
                if re.search(req, f"{x[u'Category_1']}".lower()):
                    our_cards.append(x)

        return our_cards


def grab_cards_beta(cards, filters):
    our_cards = cards

    def filterCards(cards, req, qtype):
        filteredcards = []

        try:            
            for card in cards:
                if qtype == 'name':
                    cardre = re.compile(req.lower())
                    if re.search(cardre, card[u'Name_EN'].lower()):
                        filteredcards.append(card)
                elif qtype == 'job':
                    cardre = re.compile(req.lower())
                    if re.search(cardre, card[u'Job_EN'].lower()):
                        filteredcards.append(card)
                elif qtype == 'type':
                    if req.lower() == card[u'Type_EN'].lower():
                        filteredcards.append(card)
                elif qtype == 'power':
                    try:
                        req = int(req)
                        if req == card[u'Power']:
                            filteredcards.append(card)
                    except Exception as err:
                        logging.info(err)
                        return
                elif qtype == 'cost':
                    try:
                        req = int(req)
                        if req == card[u'Cost']:
                            filteredcards.append(card)
                    except Exception as err:
                        logging.info(err)
                        return
                elif qtype == 'category':
                    cardre = re.compile(req.lower())
                    if re.search(cardre, card[u'Category_1'].lower()):
                        filteredcards.append(card)
                elif qtype == 'element':
                    if req.lower() == card[u'Element'].lower():
                        filteredcards.append(card)

            return filteredcards

        except Exception as err:
            logging.info(err)
            return 

    try:

        exclude_filters = ['tiny', 'lang', 'image', 'paginate']
        f = [f for f in filters.keys() if filters[f] is not None and f not in exclude_filters]

        for key in f:
            our_cards = filterCards(our_cards, filters[key], key)

        return our_cards

    except Exception as err:
        logging.info(err)
        return our_cards



# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the tinycode function.

def prettyCode(card):
    # Multicard Check
    if card['Multicard'] is True:
        multicard = f"\u00B7 (Generic)"
    else:
        multicard = ''

    if card['Rarity'] in ["P", "B"]:
        line1 = f"{card['Code']} \u00B7 {card['Name_EN']} \u00B7 {card['Element']} {card['Cost']} \u00B7 {card['Type_EN']} {multicard}"
    elif re.search(r'\/', card['Code']):
        line1 = f"{card['Code']} \u00B7 {card['Name_EN']} \u00B7 {card['Element']} {card['Cost']} \u00B7 {card['Type_EN']} {multicard}"
    else:
        line1 = f"{card['Code']}{card['Rarity']} \u00B7 {card['Name_EN']} \u00B7 {card['Element']} {card['Cost']} \u00B7 {card['Type_EN']} {multicard}"
    return line1


# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the name and code functions.

def prettyCard(card):
    if card[u'Multicard'] is True:
        multicard = f"\u00B7 (Generic)"
    else:
        multicard = ''

    #  Prepping different lines for return
    if card['Rarity'] in ["P", "B"]:
        line1 = f"{card[u'Name_EN']} \u00B7 {card[u'Element']} {card[u'Cost']} \u00B7 ({card[u'Code']}) {multicard}"
    elif re.search(r'\/', card['Code']):
        line1 = f"{card[u'Name_EN']} \u00B7 {card[u'Element']} {card[u'Cost']} \u00B7 ({card[u'Code']}) {multicard}"
    else:
        line1 = f"{card[u'Name_EN']} \u00B7 {card[u'Element']} {card[u'Cost']} \u00B7 ({card[u'Code']}{card[u'Rarity']}) {multicard}"

    if card[u'Type_EN'] == "Summon":
        line2 = f"{card[u'Type_EN']} \u00B7 {card[u'Category_1']}"
    else:
        line2 = f"{card[u'Type_EN']} \u00B7 {card[u'Job_EN']} \u00B7 {card[u'Category_1']}"

    line3 = ''

    if card['Text_EN']:
        for line in card[u'Text_EN']:
            line3 += f"{line}\n"
    line4 = f"{card[u'Power']}"

    # Modify return string based on whether card has power or not
    if card[u'Power'] is None:
        finished_string = f"{line1}\n{line2}\n{line3}"
    else:
        finished_string = f"{line1}\n{line2}\n{line3}{line4}"

    # Fixes #16, this is needed because markup converts []() to links
    # This causes issue with outputting to discord via embed
    finished_string = finished_string.replace('[', '\[')
    finished_string = finished_string.replace(']', '\]')

    return finished_string


def getImage(code):
    """This function takes in a code as a string and returns and image that can be sent to a discord channel"""

    if re.search(r'[0-9]+\-[0-9]{3}[a-zA-Z]/[0-9]+\-[0-9]{3}[a-zA-Z]', code):
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code[-6:] + '_eg.jpg'
    else:
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code + '_eg.jpg'

    try:
        card_img = urllib.request.urlopen(URL)
    except:
        return
    else:
        data = io.BytesIO(card_img.read())
        return data
    finally:
        urllib.request.urlcleanup()


def getimageURL(code):
    """This function takes in a code as a string and returns an image link which points to square"""

    if re.search(r'[0-9]+\-[0-9]{3}[a-zA-Z]/[0-9]+\-[0-9]{3}[a-zA-Z]', code):
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code[-6:] + '_eg.jpg'
    else:
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code + '_eg.jpg'

    return URL


def urlset(cards_list):
    """This function takes in list of cards and creates a list of URL's and returns it as a list"""

    url_list = []
    for card in cards_list:
        if re.search(r'\/', card['Code']):
            for x in card['Code'].split('/'):
                if re.search(r'H|R|P|C|L', x):
                    url_list.append('https://storage.googleapis.com/marcieapi-images/' + x + '_eg.jpg?' + str(int(time.time())))
                else:
                    url_list.append('https://storage.googleapis.com/marcieapi-images/' + x + card['Rarity'] + '_eg.jpg?' + str(int(time.time())))
        elif card['Rarity'] == "P":
            url_list.append('https://storage.googleapis.com/marcieapi-images/' + card['Code'] + '_eg.jpg?' + str(int(time.time())))
        else:
            url_list.append('https://storage.googleapis.com/marcieapi-images/' + card['Code'] + card['Rarity'] + '_eg.jpg?' + str(int(time.time())))

    return list(dict.fromkeys(url_list))


# Loading JSON from file and load it into a variable
# data - untouched JSON from file
# card_list - list of cards

def loadJson(path):
    try:
        data = urllib.request.urlopen(path)
    except:
        return
    else:
        content = data.read().decode('utf-8')
        data = json.loads(content)
        cards_list = data

        return cards_list


def getPack(opusnumber, cards):

    mycards = []
    heroics = []
    commons = []
    legendaries = []
    rares = []
    starters = []
    pack = []

    try:
        opus = roman.toRoman(int(opusnumber))
        opus = f'Opus {opus}'
    except:
        return None

    try:
        for card in cards:
            if card['Set'] == opus:
                mycards.append(card)

        for x in range(0,len(mycards)):
            if re.search(r'H', mycards[x]['Rarity']):
                heroics.append(mycards[x])
            elif re.search(r'C', mycards[x]['Rarity']):
                commons.append(mycards[x])
            elif re.search(r'L', mycards[x]['Rarity']):
                legendaries.append(mycards[x])
            elif re.search(r'R', mycards[x]['Rarity']):
                rares.append(mycards[x])
            elif re.search(r'S', mycards[x]['Rarity']):
                starters.append(mycards[x])

        random.shuffle(heroics)
        random.shuffle(commons)
        random.shuffle(rares)
        random.shuffle(legendaries)
        random.shuffle(mycards)

        for x in range(0,12):
            if x <= 6:
                randomindex = random.randint(0,len(commons) - 1)
                pack.append(commons[randomindex])
                commons.pop(randomindex)
            elif 7 <= x <= 9:
                randomindex = random.randint(0, len(rares) - 1)
                pack.append(rares[randomindex])
                rares.pop(randomindex)
            elif x == 10:
                pack.append(mycards[random.randint(0, len(mycards) - 1)])
            elif x == 11:
                if random.randint(1,10) <= 2:
                    pack.append(legendaries[random.randint(0, len(legendaries) - 1)])
                else:
                    pack.append(heroics[random.randint(0, len(heroics) - 1)])
        return pack

    except Exception as e:
        logging.info(e)
        return None


def createstrawpoll(pollname, cards):

    strawpoll_url = 'https://www.strawpoll.me/api/v2/polls'
    options = []

    for x in range(len(cards)):
        options.append(f"{cards[x]['Name_EN']} {cards[x]['Code']}{cards[x]['Rarity']}")

    req = {'title': pollname, 'options': options}

    try:
        response = requests.post(strawpoll_url, json.dumps(req))
        response_json = json.loads(response.text)
        requests.post(strawpoll_url, headers={'Connection':'close'})
        return response_json
    except:
        print('Exception with strawpoll')
        return

