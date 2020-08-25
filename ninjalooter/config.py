import configparser
import logging
import re
import sys

if len(sys.argv) > 1:
    CONFIG_FILENAME = sys.argv[1]
else:
    CONFIG_FILENAME = 'ninjalooter.ini'
CONF = configparser.ConfigParser()
CONF.read(CONFIG_FILENAME)

# Configurable Stuff
LOG_DIRECTORY = CONF.get("default", "logdir", fallback="C:\\Everquest\\")
LOG_LEVEL = CONF.getint("default", "loglevel", fallback=logging.INFO)
NUMBERS = CONF.get(
    "default", "numbers",
    fallback="1111, 2222, 3333, 4444, 5555, 6666, "
             "7777, 8888, 9999")
NUMBERS = [int(num.strip()) for num in NUMBERS.split(',')]
ALLIANCES = {
    'BL': ('Black Lotus',),
    'Kingdom': ('Kingdom', 'Karens of Karana'),
    'VCR': ('Venerate', 'Castle', 'Reconstructed'),
}

# Calculated variables
PENDING_AUCTIONS = list()
IGNORED_AUCTIONS = list()
ACTIVE_AUCTIONS = dict()
HISTORICAL_AUCTIONS = dict()
PLAYER_AFFILIATIONS = dict()
HISTORICAL_AFFILIATIONS = dict()
WHO_LOG = list()
KILL_TIMERS = list()
ALLIANCE_MAP = dict()
for alliance, guilds in ALLIANCES.items():
    for guild in guilds:
        ALLIANCE_MAP[guild] = alliance
TREE = None
ITEMS = dict()
LAST_NUMBER = 0
PLAYER_NAME = None

# Constants
BASE_WIKI_URL = 'http://wiki.project1999.com'

# Regexes
MATCH_START_WHO = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\] "
    r"Players on EverQuest:")
MATCH_WHO = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" +(?:AFK +)?\[(?P<level>\d+ )?(?P<class>[A-z ]+)\] +"
    r"(?P<name>\w+)(?: *\((?P<race>[\w ]+)\))?(?: *<(?P<guild>[\w ]+)>)?")
MATCH_END_WHO = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\] "
    r"There (are|is) (?P<count>\d+) players? in (?P<zone>[\w ]+)\.")
MATCH_OOC_ONLY = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<name>\w+) says? out of character, '(?P<text>.*)'")
MATCH_OOC_OR_SAY = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<name>\w+) says?( out of character)?, '(?P<text>.*)'")
MATCH_OOC = MATCH_OOC_OR_SAY  # Use either for now until we clarify
MATCH_AUC = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<name>\w+) auctions?, '(?P<text>.*?(?P<bid>\d+).*)'")
MATCH_RAND1 = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" \*\*A Magic Die is rolled by (?P<name>\w+)\.")
MATCH_RAND2 = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" \*\*It could have been any number from (?P<from>\d+) to (?P<to>\d+), "
    r"but this time it turned up a (?P<result>\d+)\.(?P<name>\w+)")
MATCH_KILL = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<victim>[\w ]+) has been slain by (?P<killer>[\w ]+)!")
