EMBEDCOLOR = 0xd93fb6
MAX_QUERY = 35
# Card codes: 1-001H, 15-001R/9-002H, B-001, C-001, PR-001, Re-001H/12-002H
CODE_VALIDATOR = r'^([0-9]+|[bB]|[cC]|[pP][rR]|[rR][eE])-[0-9]{3}'
DEFAULT_PREFIX = '?'

# Commands can be used COOLDOWN_USES times per COOLDOWN_SECONDS per user
COOLDOWN_USES = 2
COOLDOWN_SECONDS = 10

# Seconds to wait for a user to type a card number when several cards match
COMMAND_TIMEOUT = 10
# Seconds before a request to MarcieAPI gives up
API_TIMEOUT = 30
# Length of the request ID logged with each command and shown in embed footers
REQUEST_ID_LENGTH = 10
# Appended to image URLs so Discord fetches updated card images
DISCORD_CACHE_BYPASS = "?1"

# Discord limits
DISCORD_MESSAGE_LIMIT = 2000
DISCORD_AUTOCOMPLETE_CHOICES = 25
DISCORD_CHOICE_TEXT_LIMIT = 100

SECONDS_PER_MINUTE = 60
SECONDS_PER_HOUR = 60 * SECONDS_PER_MINUTE
SECONDS_PER_DAY = 24 * SECONDS_PER_HOUR

# Booster pack layout for ?pack: commons, rares, one card of any rarity, then a heroic or legend
PACK_COMMONS = 7
PACK_RARES = 3
PACK_LEGEND_CHANCE = 0.2

# Server activity counts (commands per server, no user information)
ACTIVITY_DAILY_DAYS = 90
ACTIVITY_MONTHLY_MONTHS = 24
ACTIVITY_FLUSH_SECONDS = 5 * SECONDS_PER_MINUTE
MONTHS_PER_YEAR = 12
