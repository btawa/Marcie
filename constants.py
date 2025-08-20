"""Constants used throughout the Marcie Discord bot."""

from typing import Final
import re

EMBEDCOLOR: Final[int] = 0xd93fb6
MAX_QUERY: Final[int] = 35
CODE_VALIDATOR_PATTERN: Final[str] = r'^[bB]-[0-9]{3}|^[0-9]+\-[0-9]{3}[a-zA-Z]$|^[0-9]+\-[0-9]{3}$|^[Pp][Rr]\-\d{3}$|^[0-9]+\-[0-9]{3}[a-zA-Z]\/?'
CODE_VALIDATOR: Final[re.Pattern[str]] = re.compile(CODE_VALIDATOR_PATTERN)

DEFAULT_PREFIX: Final[str] = '?'
COMMAND_TIMEOUT: Final[int] = 10
DISCORD_CACHE_BYPASS: Final[str] = '?1'
DISCORD_MESSAGE_LIMIT: Final[int] = 2000
