import configparser
import datetime
import logging
import re
import sys

VERSION = "1.10.4"

if len(sys.argv) > 1:
    CONFIG_FILENAME = sys.argv[1]
else:
    CONFIG_FILENAME = 'ninjalooter.ini'
CONF = configparser.ConfigParser()
CONF.read(CONFIG_FILENAME)


def write():
    with open(CONFIG_FILENAME, 'w') as file_pointer:
        CONF.write(file_pointer)


# Configurable Stuff
if not CONF.has_section('default'):
    CONF.add_section('default')
LOG_DIRECTORY = CONF.get("default", "logdir", fallback="C:\\Everquest\\")
LOG_LEVEL = CONF.getint("default", "loglevel", fallback=logging.INFO)
NUMBERS = CONF.get(
    "default", "numbers",
    fallback="1111, 2222, 3333, 4444, 5555, 6666, "
             "7777, 8888, 9999")
NUMBERS = [int(num.strip()) for num in NUMBERS.split(',')]
MIN_DKP = CONF.getint("default", "min_dkp", fallback=1)
MIN_BID_TIME = CONF.getint("default", "min_bid_time", fallback=150) + 1
RESTRICT_BIDS = CONF.getboolean("default", "restrict_bids", fallback=False)
NODROP_ONLY = CONF.getboolean("default", "nodrop_only", fallback=True)
ALWAYS_ON_TOP = CONF.getboolean("default", "always_on_top", fallback=False)
SHOW_RAIDTICK_ONLY = CONF.getboolean("default", "raidtick_filter",
                                     fallback=False)
SAFE_COLOR = CONF.get("theme", "safe_color", fallback="#CCE2CB")
WARN_COLOR = CONF.get("theme", "warn_color", fallback="#F6EAC2")
DANGER_COLOR = CONF.get("theme", "danger_color", fallback="#FFAEA5")
# Writeback new theme data
if not CONF.has_section("theme"):
    CONF.add_section("theme")
    CONF.set("theme", "safe_color", SAFE_COLOR)
    CONF.set("theme", "warn_color", WARN_COLOR)
    CONF.set("theme", "danger_color", DANGER_COLOR)
    write()

CONF_ALLIANCES = CONF.get(
    "default", "alliances",
    fallback="Force of Will:Force of Will,Venerate,Black Lotus;"
             "Castle:Castle;"
             "Kingdom:Kingdom,Karens of Karana;"
             "Seal Team:Seal Team"
)
ALLIANCES = {}
for alliance in CONF_ALLIANCES.split(";"):
    alliance, members = alliance.split(":")
    members = tuple(map(lambda x: x.strip(), members.split(",")))
    ALLIANCES[alliance] = members
DEFAULT_ALLIANCE = CONF.get("default", "default_alliance",
                            fallback=tuple(ALLIANCES.keys())[0])

# Data store variables
PENDING_AUCTIONS = list()
IGNORED_AUCTIONS = list()
ACTIVE_AUCTIONS = dict()
HISTORICAL_AUCTIONS = dict()
PLAYER_AFFILIATIONS = dict()
HISTORICAL_AFFILIATIONS = dict()
WHO_LOG = list()
CREDITT_LOG = list()
GRATSS_LOG = list()
KILL_TIMERS = list()
CREDITT_SASH_POS = 400
GRATSS_SASH_POS = 150
ACTIVE_SASH_POS = 215
HISTORICAL_SASH_POS = 215

# Calculated variables
WX_PLAYER_AFFILIATIONS = None
ALLIANCE_MAP = dict()
for alliance, guilds in ALLIANCES.items():
    for guild in guilds:
        ALLIANCE_MAP[guild] = alliance
TRIE = None
ITEMS = dict()
LAST_RAIDTICK = datetime.datetime.now()
LAST_NUMBER = 0
PLAYER_NAME = ""

# Constants
BASE_WIKI_URL = 'http://wiki.project1999.com'
SAVE_STATE_FILE = 'state.json'

# Regexes
TIMESTAMP = r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\] +"
MATCH_START_WHO = re.compile(
    TIMESTAMP + r"Players on EverQuest:")
MATCH_WHO = re.compile(
    TIMESTAMP +
    r"(?:AFK +)?\[(?P<level>\d+ )?(?P<class>[A-z ]+)\] +"
    r"(?P<name>\w+)(?: *\((?P<race>[\w ]+)\))?(?: *<(?P<guild>[\w ]+)>)?")
MATCH_END_WHO = re.compile(
    TIMESTAMP +
    r"There (are|is) (?P<count>\d+) players? in (?P<zone>[\w ]+)\.")
MATCH_OOC_ONLY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says? out of character, '(?P<text>.*)'")
MATCH_OOC_OR_SAY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says?( out of character)?, '(?P<text>.*)'")
MATCH_GU_OR_SAY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) (says?|tells the guild|say to your guild)?,"
    r" '(?P<text>.*)'")
MATCH_AUC_ONLY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) auctions?, '(?P<text>.*?(?P<bid>\d+).*)'")
MATCH_AUC_OR_SHOUT = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) (shout|auction)s?, '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_GU_AUC_OR_SHOUT = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) (shouts?|auctions?|tells the guild|say to your guild),"
    r" '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_RAND1 = re.compile(
    TIMESTAMP +
    r"\*\*A Magic Die is rolled by (?P<name>\w+)\.")
MATCH_RAND2 = re.compile(
    TIMESTAMP +
    r"\*\*It could have been any number from (?P<from>\d+) to (?P<to>\d+), "
    r"but this time it turned up a (?P<result>\d+)\.(?P<name>\w+)")
MATCH_KILL = re.compile(
    TIMESTAMP +
    r"(?P<victim>[\w ]+) has been slain by (?P<killer>[\w ]+)!")
MATCH_RAIDTICK = re.compile(
    TIMESTAMP +
    r".*RAIDTICK.*"
)
MATCH_CREDITT = re.compile(
    TIMESTAMP +
    r"(?P<from>.*) (-> {}: |tells you, ')".format(PLAYER_NAME) +
    r"(?P<message>.*creditt.*?)'?$",
    flags=re.IGNORECASE
)
MATCH_GRATSS = re.compile(
    TIMESTAMP +
    r"(?P<from>.*?) .*?(, '|: )(?P<message>.*gratss.*?)'?$",
    flags=re.IGNORECASE
)

MATCH_DROP = MATCH_GU_OR_SAY
MATCH_BID = MATCH_GU_AUC_OR_SHOUT
