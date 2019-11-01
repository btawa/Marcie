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
            if re.search(req, f"{x[u'Code']}{x['Rarity']}".upper()):
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
            if re.search(req, f"{x[u'Name_EN']}".lower()):
                our_cards.append(x)
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

    if card['Rarity'] == "P":
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
    if card['Rarity'] == "P":
        line1 = f"{card[u'Name_EN']} \u00B7 {card[u'Element']} {card[u'Cost']} \u00B7 ({card[u'Code']}) {multicard}"
    else:
        line1 = f"{card[u'Name_EN']} \u00B7 {card[u'Element']} {card[u'Cost']} \u00B7 ({card[u'Code']}{card[u'Rarity']}) {multicard}"

    if card[u'Type_EN'] == "Summon":
        line2 = f"{card[u'Type_EN']} \u00B7 {card[u'Category_1']}"
    else:
        line2 = f"{card[u'Type_EN']} \u00B7 {card[u'Job_EN']} \u00B7 {card[u'Category_1']}"

    line3 = ''

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
                    url_list.append('https://storage.googleapis.com/marceapi-images/' + x + '_eg.jpg')
                else:
                    url_list.append('https://storage.googleapis.com/marceapi-images/' + x + card['Rarity'] + '_eg.jpg')
        elif card['Rarity'] == "P":
            url_list.append('https://storage.googleapis.com/marceapi-images/' + card['Code'] + '_eg.jpg')
        else:
            url_list.append('https://storage.googleapis.com/marceapi-images/' + card['Code'] + card['Rarity'] + '_eg.jpg')

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

    # Bubble used for Multicard and Ex_Burst
    string = string.replace(u'\u25CB', 'True')
    string = string.replace(u'\u3007', 'False')

    # Horizontal Bar
    string = string.replace(u'\u2015', '')

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
    string = string.replace(u"\u2015", "-") # Damage 5 from Opus X cards
    string = string.replace(u"\u00fa", "u")  # Cuchulainn u with tilda

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
        print(e)
        return None


def createstrawpoll(pollname, cards):

    strawpoll_url = 'https://www.strawpoll.me/api/v2/polls'
    options = []

    for x in range(len(cards)):
        options.append(prettyTrice(f"{cards[x]['Name_EN']} {cards[x]['Code']}{cards[x]['Rarity']}"))

    req = {'title': pollname, 'options': options}

    try:
        response = requests.post(strawpoll_url, json.dumps(req))
        response_json = json.loads(response.text)
        requests.post(strawpoll_url, headers={'Connection':'close'})
        return response_json
    except:
        print('Exception with strawpoll')
        return


# This function is used to convert information from ffdecks JSON
# to marcieapi JSON.  FFDecks uses different characters to denote
# different things.

def ffdeckstostring(string):
    string = string.replace('{s}', '[Special]')
    string = string.replace('{a}', '(Water)')
    string = string.replace('{w}', '(Wind)')
    string = string.replace('{e}', '(Earth)')
    string = string.replace('{f}', '(Fire)')
    string = string.replace('{i}', '(Ice)')
    string = string.replace('{l}', '(Lightning)')
    string = string.replace('{d}', '(Dull)')

    string = string.replace('{x}', '[EX BURST]')
    string = string.replace('{0}', '(0)')
    string = string.replace('{1}', '(1)')
    string = string.replace('{2}', '(2)')
    string = string.replace('{3}', '(3)')
    string = string.replace('{4}', '(4)')
    string = string.replace('{5}', '(5)')
    string = string.replace('{6}', '(6)')
    string = string.replace('{7}', '(7)')
    string = string.replace('{8}', '(8)')
    string = string.replace('{9}', '(9)')

    string = string.replace('*', '')
    string = string.replace('%', '')
    string = string.replace('~', '')
    string = string.replace(u"\u2015", "-") # Damage 5 from Opus X cards
    string = string.replace(u"\u00fa", "u")  # Cuchulainn u with tilda

    return string


# This function converts ffdecks inputs to marcieapi output

def ffdeckstomarcieapi(listofdicts):

    converted = []

    for x in range(0,len(listofdicts)):
        converted.append({})

    for card in range(0, len(listofdicts)):
        converted[card]['Category_1'] = ffdeckstostring(listofdicts[card]['category'])
        converted[card]['Code'] = ffdeckstostring(listofdicts[card]['serial_number'])
        converted[card]['Cost'] = listofdicts[card]['cost']
        converted[card]['Element'] = ffdeckstostring(listofdicts[card]['element'])
        converted[card]['Ex_Burst'] = listofdicts[card]['is_ex_burst']
        converted[card]['Job_EN'] = ffdeckstostring(listofdicts[card]['job'])
        converted[card]['Multicard'] = listofdicts[card]['is_multi_playable']
        converted[card]['Name_EN'] = ffdeckstostring(listofdicts[card]['name'])
        converted[card]['Power'] = listofdicts[card]['power']
        converted[card]['Rarity'] = ffdeckstostring(listofdicts[card]['rarity'])[0]

        if re.search(r'^PR-' , converted[card]['Code']):
            converted[card]['Set'] = None
        else:
            setnumber = int(re.search(r'^\d+', converted[card]['Code']).group(0))
            converted[card]['Set'] = 'Opus ' + roman.toRoman(setnumber)
        converted[card]['Type_EN'] = ffdeckstostring(listofdicts[card]['type'])
        converted[card]['Text_EN'] = []

        for line in range(0, len(listofdicts[card]['abilities'])):
            converted[card]['Text_EN'].append(ffdeckstostring(str(listofdicts[card]['abilities'][line])))
    return converted


def addimageurltojson(cards_list, image_list):
    for card in cards_list:
        for url in image_list:
            if card['Code'] in url:
                card['image_url'] = url

    return cards_list


# This function makes a cards JSON from square and writes it to cards.json in the local directory

def squaretomarcieapi(cards):

    mykeys = ('Element', 'Name_EN', 'Cost', 'Code', 'Multicard', 'Type_EN', 'Category_1', 'Text_EN', 'Job_EN', 'Power',
              'Ex_Burst', 'Set', 'Rarity')

    for card in cards:
        for key in list(card):
            if key in mykeys:
                if key == "Multicard" or key == "Ex_Burst":
                    card[key] = prettyTrice(card[key])
                    if card[key] == "True":
                        card[key] = True
                    else:
                        card[key] = False
                elif key == 'Power':
                    if card[key] == "":
                        card[key] = None
                    elif re.search(r'\u2015', card[key]):
                        card[key] = None
                    elif re.search(r'\－', card[key]):
                        card[key] = None
                    else:
                        card[key] = int(card[key])
                elif key == "Rarity":
                    card[key] = card[key][0]
                elif key == "Code":
                    if re.search(r'PR-\d{3}', card[key]):
                        card[key] = card[key]
                    elif re.search(r'\/', card[key]):
                        card[key] = card[key]
                    else:
                        card[key] = card[key][:-1]
                elif key == "Cost":
                    card[key] = int(card[key])
                else:
                    card[key] = prettyTrice(card[key])
            else:
                del card[key]

        card['Text_EN'] = card['Text_EN'].split('\n')

    myjson = json.dumps(cards)
    mydict = json.loads(myjson)

    return mydict

