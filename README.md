# Marcie Bot  
Marcie is a discord bot designed to provide discord users access to query for FFTCG cards in chat.  
  
## Community  
### Support Discord  
- https://discord.gg/ZUZY7wb  
  
### top.gg Listing  
- https://top.gg/bot/570428406957735946  
  
## Dependencies  
- Python 3.10+ (the Docker image uses 3.12)
- Configured application in the [Discord developer portal](https://discord.com/developers/applications) with the **Message Content** privileged intent enabled  
- MarcieAPI  
  + If you need access to this please reach out to Japnix in the support discord  
- MongoDB  

### Python Libraries
See `requirements.txt`:
- discord.py 2.x
- pymongo 4.13+ (uses the native async client)

## Configuration
Each setting can be passed as a command line flag or an environment variable. Environment variables are preferred for the token and API key so they don't show up in process listings.

| Flag | Environment variable | Description |
|------|----------------------|-------------|
| `--token` | `DISCORD_BOT_TOKEN` | Discord bot token |
| `--key` | `MARCIE_API_KEY` | MarcieAPI key |
| `--api` | `MARCIE_API` | MarcieAPI address, e.g. `http://dev.tawa.wtf:8000/api/` |
| `--db` | `MARCIE_DB` | MongoDB url, e.g. `mongodb://db:27017` |

## Installation
### Normal

    git clone https://github.com/japnix/Marcie.git
    cd Marcie
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

    export DISCORD_BOT_TOKEN=... MARCIE_API_KEY=... MARCIE_API=http://dev.tawa.wtf:8000/api/ MARCIE_DB=mongodb://db:27017
    .venv/bin/python marcie.py

### Docker

    docker build -t marcie .
    docker run -d --name marcie \
        -e DISCORD_BOT_TOKEN -e MARCIE_API_KEY \
        -e MARCIE_API=http://dev.tawa.wtf:8000/api/ \
        -e MARCIE_DB=mongodb://db:27017 \
        marcie

### Requirements  
Ensure that your bot has the ability to `Read Text Channels & See Voice Channels` and `Send Messages` in the server you have joined it to.

`Manage Messages` is optional. With it, Marcie deletes the number you type when choosing a card from a selection list.  

Commands can be triggered with the server's prefix or by mentioning Marcie, e.g. `@Marcie name auron`.
  
## Commands  

    FFTCG: 
        adv This command allows card querying by providing arguments to filter... 
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
This command returns a randomized pack of the requested FFTCG set. Named sets use their number, e.g. 15 is Crystal Dominion and 22 is Hidden Hope.

    Example:  
        ?pack 5
        ?pack 22

### ?adv
This command allows card querying by providing arguments to filter off of.

    Filters:
    -n, --name - Card Name (Yuna, Vaelfor, etc. (takes regex))
    -j, --job - Card Job (Summoner, Samurai, etc. (takes regex))
    -e, --element - Card Element (Fire, Ice, Light, etc.)
    -c, --cost - Card Cost (Int)
    -t, --type - Card Type (Forward, Backup, etc.)
    -g, --category - Card Category (FFCC, X, etc.)
    -p, --power - Card Power (9000, 3000, etc.)

    Output options:
    -y, --tiny - Print cards in tiny output
    -i, --image - Return card as image format
    -l, --lang - Language of returned image/thumbnail (en, jp)
    -a, --paginate - Returned cards will provide pagination buttons

    Example:
        ?adv --name yuna --type backup --cost 2
#### Known Caveats
- If using card name or card job which has spaces please surround argument in quotes.
    - `?adv --name "Cloud of Darkness" --type forward --cost 5`

- Special regex characters need to be escaped.
    - `?adv --name "Cid \(Mobius\)"`

### ?paginate
Returns image of card(s) as a paginated embed. Takes name.  Accepts regex.

This function only takes one argument, a name. It will return the image of the card as an embed. If there are multiple matches on your query, the bot will provide buttons that can be used to page through each card. Only the user who created the query will be able to use these buttons.

    Example:
        ?paginate leviathan

#### Known Caveats
- This command is using regex for matching.  As a result special regex characters like '(' and ')' may not matches you may expect.  In these cases it is necessary to either escape the regex character '\(' or search a different substring of the overall card name.

        Example:
            ?paginate sarah (mobius) vs ?paginate sarah \(mobius\)
            ?paginate Mog (XIII-2) vs ?paginate Mog \(XIII-2\)


### ?support
Marcie will ping you a invite to the support discord

