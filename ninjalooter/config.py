import logging
import re
import threading

# Configurable Stuff
LOG_LEVEL = logging.INFO
ALLIANCES = {
    'BL': ('Black Lotus',),
    'Kingdom': ('Kingdom', 'Karens of Karana'),
    'VCR': ('Venerate', 'Castle', 'Reconstructed'),
}
NUMBERS = (1111, 2222, 3333, 4444, 5555, 6666, 7777, 8888, 9999)

# Calculated variables
PENDING_AUCTIONS = list()
ACTIVE_AUCTIONS = dict()
ACTIVE_ROLLS = dict()
HISTORICAL_AUCTIONS = dict()
PLAYER_AFFILIATIONS = dict()
ALLIANCE_MAP = dict()
for alliance, guilds in ALLIANCES.items():
    for guild in guilds:
        ALLIANCE_MAP[guild] = alliance
TREE = None
ITEMS = dict()
LAST_NUMBER = 0
LOGFILE_LOOP_RUN = threading.Event()

# Constants
BASE_WIKI_URL = 'http://wiki.project1999.com'

# Regexes
MATCH_WHO = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" +(?:AFK +)?\[(?P<level>\d+ )?(?P<class>[A-z ]+)\] +"
    r"(?P<name>\w+)(?: *\((?P<race>[\w ]+)\))?(?: *<(?P<guild>[\w ]+)>)?")
MATCH_OOC = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<name>\w+) says out of character, '(?P<text>.*)'")
MATCH_AUC = re.compile(
    r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\]"
    r" (?P<name>\w+) auctions, '(?P<text>.*?(?P<bid>\d+).*)'")
