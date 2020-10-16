# Marcie Bot  
Marcie is a discord bot designed to provide discord users access to query for FFTCG cards in chat.  
  
## Community  
### Support Discord  
- https://discordapp.com/invite/ZUZY7wb  
  
### Discordbots.org Listing  
- https://discordbots.org/bot/570428406957735946  
  
## Dependencies  
- Python 3.x
- Configured application in discord developer portal  
- MarcieAPI  
  + If you need access to this please reach out to Japnix in the support discord  
- MongoDB  

### Python Libraries
- discord.py
- roman
- requests
- pymongo
- DiscordUtils
  
## Installation
### Normal

    git clone  https://github.com/japnix/Marcie.git  
    pip3 install discord.py roman requests pymongo DiscordUtils
    python3 ./Marcie/marcie.py --token $DISCORD_BOT_TOKEN --key $API_KEY --api $API --db $DB
    
    Example:
    python3 ./Marcie/marcie.py --token thisisnotarealtokenbutyouwouldgetthisfromyourdeveloperportal \
    --key lolbbq \
    --api http://dev.tawa.wtf:8000/api/ \
    --db mongodb://db.:27017
    
### Docker
Marcie is also available as a docker container.  For more information please check its readme on dockerhub.
- https://hub.docker.com/r/japnix/marcie

### Requirements  
Ensure that your bot has the ability to `Read Text Channels & See Voice Channels` and `Send Messages` in the server you have joined it to.

Marcie has some functionality which utilizes `Manage Messages` specifically paginate, which allows for using emoji reacts to page through card embeds.  Additionally, with selection logic Marcie will attempt to delete the response message which contains the selection.  
  
## Commands  

    FFTCG: 
        beta This command allows card querying by providing arguments to filter... 
        image Returns image of card. Takes code or name. Accepts regex. 
        name Returns text of card. Takes code or name. Accepts regex. 
        pack Returns a randomized pack based on the opus you provide. 
        paginate Returns image of card(s) as a paginated embed. Takes name. Accept... 
        tiny Returns a compacted list of cards. Takes a name. Accepts regex. 
    Management: 
        prefix This command allows guild owners or administrators to change the p... 
        support Marcie will ping you a invite to the support discord uptime Returns how long marcie has been running. ​
    No Category: 
        help Shows this message

 
___  
  
### ?name
Returns text of card. Takes code or name.  Accepts regex.

This function only takes one argument, either a name or card code. It will return the text and thumbnail of thecard as an embed. If there are multiple matches on your query, the bot will provide you with a list of cardsthat you can respond to by simply sending a message with the corresponding number (this will timeout after 10 seconds).

    Example:
        ?name auron
        ?name 1-001H
        ?name 1-001 

#### Known Caveats:
This command is using regex for matching.  As a result special regex characters like '(' and ')' may not matchas you may expect.  In these cases it is necessary to either escape the regex character '\(' or search adifferent substring of the overall card name.

    Example:
        ?name sarah (mobius) vs ?name sarah \(mobius\)
        ?name Mog (XIII-2) vs ?name Mog \(XIII-2\)

### ?image  
Returns image of card. Takes code or name.  Accepts regex.

This function only takes one argument, either a name or card code. It will return the image of the card as anembed. If there are multiple matches on your query, the bot will provide you with a list of cards that you canrespond to by simply sending a message with the corresponding number (this will timeout after 10 seconds).

    Example:
        ?image auron
        ?image 1-001H
        ?image 1-001
        
#### Known Caveats:
This command is using regex for matching.  As a result special regex characters like '(' and ')' may not matchas you may expect.  In these cases it is necessary to either escape the regex character '\(' or search adifferent substring of the overall card name.

    Example:
        ?image sarah (mobius) vs ?name sarah \(mobius\)
        ?image Mog (XIII-2) vs ?name Mog \(XIII-2\)

### ?tiny
Returns a compacted list of cards. Takes a name.  Accepts regex.

This command was initially created when name and image were less developed.  It takes in a card name and returns a compacted list of cards.  It is mostly used as a debug tool now.

    Example:
        ?tiny sarah (mobius) vs ?name sarah \(mobius\)
        ?tiny Mog (XIII-2) vs ?name Mog \(XIII-2\)

#### Known Caveats:
This command is using regex for matching.  As a result special regex characters like '(' and ')' may not matchas you may expect.  In these cases it is necessary to either escape the regex character '\(' or search adifferent substring of the overall card name.
  
### ?prefix
This command allows guild owners or administrators to change the prefix used for commands.  
  
The default prefix is `?`  
  
    Example:  
        ?prefix z!  
        Then...     
        z!name WOL  

  
### ?pack
This command returns a randomized pack of the requested FFTCG set.  

    Example:  
        ?pack 5

### ?beta
This command allows card querying by providing arguments to filter off of.

    Filters:
    -n, --name - Card Name (Yuna, Vaelfor, etc. (takes regex))
    -j, --job - Card Job (Summoner, Samurai, etc. (takes regex))
    -e, --element - Card Element (Fire, Ice, Light, etc.)
    -c, --cost - Card Cost (Int)
    -t, --type - Card Type (Forward, Backup, etc.)
    -g, --category - Card Category (FFCC, X, etc.)
    -p, --power - Card Power (9000, 3000, etc.)

    Example:
        ?beta --name yuna --type backup --cost 2
#### Known Caveats
- If using card name or card job which has spaces please surround argument in quotes.
    - `?beta --name "Cloud of Darkness" --type forward --cost 5`

- Special regex characters need to be escaped.
    - `?beta --name "Cid \(Mobius\)"`

### ?paginate
Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

This function only takes one argument, a name. It will return the image of the card as an embed. If there are multiple matches on your query, the bot will provide react emojis that can be used to page througheach card. Only the users who create the query will be able to activate these react emojis.

    Example:
        ?paginate leviathan

#### Known Caveats
- This command requires the marcie to have `Manage Messages` permission.  Without this permission the react emojis will not operate as expected.  If you have any questions please reach out in the support discord.

- This command is using regex for matching.  As a result special regex characters like '(' and ')' may not matches you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of the overall card name.

        Example:
            ?paginate sarah (mobius) vs ?paginate sarah \(mobius\)
            ?paginate Mog (XIII-2) vs ?paginate Mog \(XIII-2\)


### ?support
Marcie will ping you a invite to the support discord

