import json
import re
import urllib.request
import io
import roman
import random
import requests

# Helpful jq
#
# jq '.cards[] | select(.Code == "1-028R")'  ./cards.json
#
# JSON Keys
#
# Code		Power		Ex_Burst	Text		Text_EN		Text_DE		Text_ES		Text_FR		Text_IT		Type_NA
# Element	Category_1	Name		Name_EN		Name_DE		Name_ES		Name_FR		Name_IT		Set		Name_NA
# Rarity		Category_2	Type		Type_EN		Type_DE		Type_ES		Type_FR		Type_IT		Text_NA
# Cost		Multicard	Job		Job_EN		Job_DE		Job_ES		Job_FR		Job_IT		Job_NA

# This function reads in a request, and a cards dictionary.
# Based on the request it will search the dictionary for a match
# based on the FFTCG card code and return a single card.

def grab_card(req, cards):
    our_card = ''

    try:
        req = re.compile(req)
    except:
        return our_card
    else:
        for x in cards:
            if re.search(req, x[u'Code'].upper()):
                our_card = x
        return our_card


# This function reads in a request, and a cards dictionary.
# Based on the request it will search for a match based on the
# Name_EN value in the cards dictionary.  This function can
# return a single card or multiple cards.

def grab_cards(req, cards):
    our_cards = []

    try:
        req = re.compile(req)
    except:
        return our_cards
    else:

        for x in cards:
            if re.search(req, x[u'Name_EN'].lower()):
                our_cards.append(x)
        return our_cards


# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the tinycode function.

def prettyCode(card):
    # Multicard Check
    if card[u'Multicard'] == u"\u25cb":
        multicard = f"\u00B7 (Generic)"
    else:
        multicard = ''

    # Determine what the element is and convert character to word
    if card[u'Element'] == u"\u571F":
        element = "Earth"
    elif card[u'Element'] == u"\u6c34":
        element = "Water"
    elif card[u'Element'] == u"\u706b":
        element = "Fire"
    elif card[u'Element'] == u"\u98a8":
        element = "Wind"
    elif card[u'Element'] == u"\u6c37":
        element = "Ice"
    elif card[u'Element'] == u"\u5149":
        element = "Light"
    elif card[u'Element'] == u"\u95c7":
        element = "Dark"
    elif card[u'Element'] == u"\u96f7":
        element = "Lightning"
    else:
        element = ''

    line1 = f"{card[u'Code']} \u00B7 {card[u'Name_EN']} \u00B7 {element} {card[u'Cost']} \u00B7 {card[u'Type_EN']} {multicard}"

    return line1


# This reads in a card likely from grab_card or grab_cards and
# Takes the input formats it to get find and replace unusual unicode
# characters.  Once this is complete it creates a formatted string.
# In marciebot this is used specifically for the name and code functions.

def prettyCard(card):
    # Determine what the element is and convert character to word
    if card[u'Element'] == u"\u571F":
        element = "Earth"
    elif card[u'Element'] == u"\u6c34":
        element = "Water"
    elif card[u'Element'] == u"\u706b":
        element = "Fire"
    elif card[u'Element'] == u"\u98a8":
        element = "Wind"
    elif card[u'Element'] == u"\u6c37":
        element = "Ice"
    elif card[u'Element'] == u"\u5149":
        element = "Light"
    elif card[u'Element'] == u"\u95c7":
        element = "Dark"
    elif card[u'Element'] == u"\u96f7":
        element = "Lightning"
    else:
        element = ''

    if card[u'Multicard'] == u"\u25cb":
        multicard = f"\u00B7 (Generic)"
    else:
        multicard = ''

    #  Prepping different lines for return
    line1 = f"{card[u'Name_EN']} \u00B7 {element} {card[u'Cost']} \u00B7 ({card[u'Code']}) {multicard}"
    line2 = f"{card[u'Type_EN']} \u00B7 {card[u'Job_EN']} \u00B7 {card[u'Category_1']}"
    line3 = f"{card[u'Text_EN']}"
    line4 = f"{card[u'Power']}"

    # Modify return string based on whether card has power or not
    if card[u'Power'] == "":
        finished_string = f"{line1}\n{line2}\n{line3}"
    else:
        finished_string = f"{line1}\n{line2}\n{line3}\n{line4}"

    # Replace EX Burst
    finished_string = finished_string.replace('[[ex]]', '')
    finished_string = finished_string.replace('[[/]]', '')
    finished_string = finished_string.replace('EX BURST', '\[EX BURST\]')

    # Special Switch
    finished_string = finished_string.replace(u"\u300a"u"\u0053"u"\u300b", '\[Special\]')

    # Formatting Fixes
    finished_string = finished_string.replace('[[', '<')
    finished_string = finished_string.replace(']]', '>')
    finished_string = finished_string.replace('<s>', '')
    finished_string = finished_string.replace('</>', '')
    finished_string = finished_string.replace('<i>', '')
    finished_string = finished_string.replace('<br> ', '\n')
    finished_string = finished_string.replace('<br>', '\n')

    # Replace Logos
    finished_string = finished_string.replace(u"\u571F", '(Earth)')
    finished_string = finished_string.replace(u"\u6c34", '(Water)')
    finished_string = finished_string.replace(u"\u706b", '(Fire)')
    finished_string = finished_string.replace(u"\u98a8", '(Wind)')
    finished_string = finished_string.replace(u"\u6c37", '(Ice)')
    finished_string = finished_string.replace(u"\u5149", '(Light)')
    finished_string = finished_string.replace(u"\u95c7", '(Dark)')
    finished_string = finished_string.replace(u"\u96f7", '(Lightning)')

    # Replace Fullwidth Numbers with normal numbers
    finished_string = finished_string.replace(u"\uFF11", '(1)')
    finished_string = finished_string.replace(u"\uFF12", '(2)')
    finished_string = finished_string.replace(u"\uFF13", '(3)')
    finished_string = finished_string.replace(u"\uFF14", '(4)')
    finished_string = finished_string.replace(u"\uFF15", '(5)')
    finished_string = finished_string.replace(u"\uFF16", '(6)')
    finished_string = finished_string.replace(u"\uFF17", '(7)')
    finished_string = finished_string.replace(u"\uFF18", '(8)')
    finished_string = finished_string.replace(u"\uFF19", '(9)')
    finished_string = finished_string.replace(u"\uFF10", '(0)')

    # Non full width
    finished_string = finished_string.replace(u"\u300a"u"\u0031"u"\u300b", '(1)')
    finished_string = finished_string.replace(u"\u300a"u"\u0032"u"\u300b", '(2)')
    finished_string = finished_string.replace(u"\u300a"u"\u0033"u"\u300b", '(3)')
    finished_string = finished_string.replace(u"\u300a"u"\u0034"u"\u300b", '(4)')
    finished_string = finished_string.replace(u"\u300a"u"\u0035"u"\u300b", '(5)')
    finished_string = finished_string.replace(u"\u300a"u"\u0036"u"\u300b", '(6)')
    finished_string = finished_string.replace(u"\u300a"u"\u0037"u"\u300b", '(7)')
    finished_string = finished_string.replace(u"\u300a"u"\u0038"u"\u300b", '(8)')
    finished_string = finished_string.replace(u"\u300a"u"\u0039"u"\u300b", '(9)')
    finished_string = finished_string.replace(u"\u300a"u"\u0030"u"\u300b", '(0)')
    finished_string = finished_string.replace(u"\u300a" + "X" + u"\u300b", '(X)')
    finished_string = finished_string.replace(u"\u4E00"u"\u822C", '(Generic)')  # Fixes #1

    # Tap Symbol
    finished_string = finished_string.replace(u"\u30C0"u"\u30EB", '(Dull)')

    # Weird bracket removal:
    finished_string = finished_string.replace(u"\u300a", '')
    finished_string = finished_string.replace(u"\u300b", '')
    finished_string = finished_string.replace('&middot;', u"\u00B7")

    # Double quotes with YURI?
    finished_string = finished_string.replace("\"\"", '\"')

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
    if re.search(r'[0-9]+\-[0-9]{3}[a-zA-Z]/[0-9]+\-[0-9]{3}[a-zA-Z]', code):
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code[-6:] + '_eg.jpg'
    else:
        URL = 'https://fftcg.cdn.sewest.net/images/cards/full/' + code + '_eg.jpg'

    return URL


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
        cards_list = data['cards']

        return cards_list


def prettyTrice(string):

    # Weird bracket removal:
    string = string.replace(u"\u300a", '(')
    string = string.replace(u"\u300b", ')')
    string = string.replace('&middot;', u"\u00B7")

    # Replace Element Logos
    string = string.replace(u"\u571F", 'Earth')
    string = string.replace(u"\u6c34", 'Water')
    string = string.replace(u"\u706b", 'Fire')
    string = string.replace(u"\u98a8", 'Wind')
    string = string.replace(u"\u6c37", 'Ice')
    string = string.replace(u"\u5149", 'Light')
    string = string.replace(u"\u95c7", 'Dark')
    string = string.replace(u"\u96f7", 'Lightning')

    # Replace EX Burst
    string = string.replace('[[ex]]', '')
    string = string.replace('[[/]]', '')
    string = string.replace('EX BURST', '[EX BURST]')

    # Special Switch
    string = string.replace(u"\u300a"u"\u0053"u"\u300b", '[Special]')

    # Formatting Fixes
    string = string.replace('[[', '<')
    string = string.replace(']]', '>')
    string = string.replace('<s>', '')
    string = string.replace('</>', '')
    string = string.replace('<i>', '')
    string = string.replace('<br> ', '\n')
    string = string.replace('<br>', '\n')

    # Formatting Fixes
    string = string.replace('[[', '<')
    string = string.replace(']]', '>')
    string = string.replace('<s>', '')
    string = string.replace('</>', '')
    string = string.replace('<i>', '')
    string = string.replace('<br> ', '\n')
    string = string.replace('<br>', '\n')

    # Replace Fullwidth Numbers with normal numbers
    string = string.replace(u"\uFF11", '1')
    string = string.replace(u"\uFF12", '2')
    string = string.replace(u"\uFF13", '3')
    string = string.replace(u"\uFF14", '4')
    string = string.replace(u"\uFF15", '5')
    string = string.replace(u"\uFF16", '6')
    string = string.replace(u"\uFF17", '7')
    string = string.replace(u"\uFF18", '8')
    string = string.replace(u"\uFF19", '9')
    string = string.replace(u"\uFF10", '0')

    string = string.replace(u"\u4E00"u"\u822C", 'Generic')  # Fixes #1

    # Tap Symbol
    string = string.replace(u"\u30C0"u"\u30EB", 'Dull')

    # Double quotes with YURI?
    string = string.replace("\"\"", '\"')

    return string


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
            if re.search(r'H', mycards[x]['Code']):
                heroics.append(mycards[x])
            elif re.search(r'C', mycards[x]['Code']):
                commons.append(mycards[x])
            elif re.search(r'L', mycards[x]['Code']):
                legendaries.append(mycards[x])
            elif re.search(r'R', mycards[x]['Code']):
                rares.append(mycards[x])
            elif re.search(r'S', mycards[x]['Code']):
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
        print(e)
        return None


def createstrawpoll(pollname, cards):

    strawpoll_url = 'https://www.strawpoll.me/api/v2/polls'
    options = []

    for x in range(len(cards)):
        options.append(prettyTrice(f"{cards[x]['Name_NA']} {cards[x]['Code']}"))

    req = {'title': pollname, 'options': options}

    try:
        response = requests.post(strawpoll_url, json.dumps(req))
        response_json = json.loads(response.text)
        requests.post(strawpoll_url, headers={'Connection':'close'})
        return response_json
    except:
        print('Exception with strawpoll')
        return





