# Marcie Bot
Marcie is a discord bot designed to provide discord users access to query for FFTCG cards in chat.

## Community
### Support Discord
- https://discordapp.com/invite/ZUZY7wb

### Discordbots.org Listing
- https://discordbots.org/bot/570428406957735946

## Dependencies
- Rapptz/discord.py
- Python 3.7
- Configured application in discord developer portal

## Installation
```
git clone  https://github.com/japnix/Marcie.git
pip install discord.py
./Python3.7 ./Marcie/marcie.py <bot token from developer portal>
```
### Requirements
Ensure that your bot has the ability to `Read Text Channels & See Voice Channels` and `Send Messages` in the server you have joined it to.

## Commands
```
  help  Shows this message
  image Returns image of card. Takes code or name.  Accepts regex.
  name  Returns text of card. Takes code or name.  Accepts regex.
  tiny  List cards that match the search. Accepts regex. 
```
___

### ?name <name>
```
Returns text of card. Takes code or name.  Accepts regex.

This function only takes one argument, either a name or card code. It will return the text and thumbnail of the card
as an embed. If there are multiple matches on your query, the bot will provide you with a list of cards that you can
respond to by simply sending a message with the corresponding number (this will timeout after 10 seconds).

Known Caveats:
This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
the overall card name.

    Example:
    ?name sarah (mobius) vs ?name sarah \(mobius\)
    ?name Mog (XIII-2) vs ?name Mog \(XIII-2\)

Example:
    ?name auron
    ?name 1-001H
    ?name 1-001
```
___

### ?image <name>
```
Returns image of card. Takes code or name.  Accepts regex.

This function only takes one argument, either a name or card code. It will return the image of the card as an embed.
If there are multiple matches on your query, the bot will provide you with a list of cards that you can respond to
by simply sending a message with the corresponding number (this will timeout after 10 seconds).

Example:
    ?image auron
    ?image 1-001H
    ?image 1-001
```
___

### ?tiny <name>
```
Returns a compacted list of cards. Takes a name.  Accepts regex.

This command was initially created when name and image were less developed.  It takes in a card name and returns a
compacted list of cards.  It is mostly used as a debug tool now.

Known Caveats:
This command is using regex for matching.  As a result special regex characters like '(' and ')' may not match as you
may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of
the overall card name.

    Example:
    ?tiny sarah (mobius) vs ?name sarah \(mobius\)
    ?tiny Mog (XIII-2) vs ?name Mog \(XIII-2\)

Example:
    ?tiny auron
```

### ?prefix <prefix>
```
This command allows guild owners or administrators to change the prefix used for commands.

The default prefix is `?`

Example:
    ?prefix z!

    Then...
    
    z!name WOL
```