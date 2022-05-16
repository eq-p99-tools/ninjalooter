import configparser
import datetime
import logging
import os
import pathlib
import re
import semver

SEMVER = semver.VersionInfo(
    major=1,
    minor=14,
    patch=11,
)
VERSION = str(SEMVER)

PROJECT_DIR = pathlib.Path(__file__).parent.parent
NEEDS_WRITE = False
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
DEFAULT_BID_MESSAGE_NEW = (
    "[{item}]{classes} - BID IN /{channel}, MIN {min} DKP. "
    "You MUST include the item name in your bid! Closing in "
    "{time_remaining}. ")
BID_MESSAGE_NEW = CONF.get(
    "default", "bid_message_new",
    fallback=DEFAULT_BID_MESSAGE_NEW
)
BID_MESSAGE_NEW = BID_MESSAGE_NEW.strip("\"\'")
DEFAULT_BID_MESSAGE_REMINDER = (
    "[{item}]{classes} - BID IN /{channel}. "
    "You MUST include the item name in your bid! Currently: "
    "`{player}` with {number} DKP - Closing in {time_remaining}! ")
BID_MESSAGE_REMINDER = CONF.get(
    "default", "bid_message_reminder",
    fallback=DEFAULT_BID_MESSAGE_REMINDER
)
BID_MESSAGE_REMINDER = BID_MESSAGE_REMINDER.strip("\"\'")
DEFAULT_ROLL_MESSAGE = "[{item}]{classes} ROLL {target} NOW!"
ROLL_MESSAGE = CONF.get(
    "default", "roll_message",
    fallback=DEFAULT_ROLL_MESSAGE
)
ROLL_MESSAGE = ROLL_MESSAGE.strip("\"\'")
DEFAULT_GRATS_MESSAGE_BID = (
    "Gratss {player} on [{item}] ({number} DKP)!")
GRATS_MESSAGE_BID = CONF.get(
    "default", "grats_message_bid",
    fallback=DEFAULT_GRATS_MESSAGE_BID
)
GRATS_MESSAGE_BID = GRATS_MESSAGE_BID.strip("\"\'")
DEFAULT_GRATS_MESSAGE_ROLL = (
    "Gratss {player} on [{item}] with {roll} / {target}!")
GRATS_MESSAGE_ROLL = CONF.get(
    "default", "grats_message_roll",
    fallback=DEFAULT_GRATS_MESSAGE_ROLL
)
GRATS_MESSAGE_ROLL = GRATS_MESSAGE_ROLL.strip("\"\'")
MIN_DKP_OLD = CONF.getint("default", "min_dkp", fallback=1)
MIN_BID_TIME = CONF.getint("default", "min_bid_time", fallback=150) + 1
RESTRICT_BIDS = CONF.getboolean("default", "restrict_bids", fallback=False)
NODROP_ONLY = CONF.getboolean("default", "nodrop_only", fallback=True)
ALWAYS_ON_TOP = CONF.getboolean("default", "always_on_top", fallback=False)
SHOW_RAIDTICK_ONLY = CONF.getboolean("default", "raidtick_filter",
                                     fallback=False)
HIDE_ROTS = CONF.getboolean("default", "hide_rots", fallback=False)
DROP_COOLDOWN = CONF.getint("default", "drop_cooldown", fallback=60)
BACKUP_ON_CLEAR = CONF.getboolean("default", "backup_on_clear", fallback=True)
AUTO_SWAP_LOGFILE = CONF.getboolean("default", "auto_swap_logfile",
                                    fallback=True)
ALLOW_EXCEL_EXPORT = CONF.getboolean("default", "allow_excel_export",
                                     fallback=False)
EXPORT_TIME_IN_EASTERN = CONF.getboolean("default", "export_time_in_eastern",
                                         fallback=False)
LAST_RUN_VERSION = CONF.get("default", "last_run_version", fallback=None)

if not CONF.has_section("min_dkp"):
    CONF.add_section("min_dkp")
MIN_DKP = CONF.getint("min_dkp", "default", fallback=MIN_DKP_OLD)
MIN_DKP_SHEET_URL = CONF.get("min_dkp", "sheet_url", fallback=None)
MIN_DKP_NAME_COL = CONF.get("min_dkp", "sheet_name_column", fallback='Item')
MIN_DKP_VAL_COL = CONF.get("min_dkp", "sheet_value_column", fallback='Minimum')
MIN_DKP_RESTR_COL = CONF.get(
    "min_dkp", "sheet_restrictions_column", fallback='Restrictions')
MIN_DKP_DROP_COL = CONF.get(
    "min_dkp", "sheet_droppable_column", fallback='Droppable')

SAFE_COLOR = CONF.get("theme", "safe_color", fallback="#CCE2CB")
WARN_COLOR = CONF.get("theme", "warn_color", fallback="#F6EAC2")
DANGER_COLOR = CONF.get("theme", "danger_color", fallback="#FFAEA5")
# Writeback new theme data
if not CONF.has_section("theme"):
    CONF.add_section("theme")
    CONF.set("theme", "safe_color", SAFE_COLOR)
    CONF.set("theme", "warn_color", WARN_COLOR)
    CONF.set("theme", "danger_color", DANGER_COLOR)
    NEEDS_WRITE = True

# Alerts
AUDIO_ALERTS = CONF.getboolean("alerts", "audio_enabled", fallback=True)
TEXT_ALERTS = CONF.getboolean("alerts", "text_enabled", fallback=True)
SECOND_MAIN_REMINDER_DKP = CONF.getint("alerts", "second_main_reminder_dkp",
                                       fallback=None)
ALT_REMINDER_DKP = CONF.getint("alerts", "alt_reminder_dkp",
                               fallback=None)
if not CONF.has_section("alerts"):
    CONF.add_section("alerts")
    CONF.set("alerts", "audio_enabled", str(AUDIO_ALERTS))
    CONF.set("alerts", "text_enabled", str(TEXT_ALERTS))
    NEEDS_WRITE = True

NEW_DROP_SOUND = CONF.get(
    "alerts", "new_drop",
    fallback=os.path.join(PROJECT_DIR, "data", "sounds", "new_drop.wav"))
AUC_EXPIRING_SOUND = CONF.get(
    "alerts", "auction_expiring",
    fallback=os.path.join(PROJECT_DIR, "data", "sounds", "auc_expiring.wav"))
RAIDTICK_REMINDER_SOUND = CONF.get(
    "alerts", "raidtick_reminder",
    fallback=os.path.join(PROJECT_DIR, "data", "sounds",
                          "raidtick_reminder.wav"))
NEW_RAIDTICK_SOUND = CONF.get(
    "alerts", "new_raidtick",
    fallback=os.path.join(PROJECT_DIR, "data", "sounds",
                          "new_raidtick.wav"))

CONF_ALLIANCES = CONF.get(
    "default", "alliances",
    fallback="Force of Will:Force of Will,Venerate;"
             "Castle:Castle,Ancient Blood,Gathered Might,Freya's Chariot,Black Lotus;"
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
LAST_WHO_SNAPSHOT = dict()
PLAYER_DB = dict()
ATTENDANCE_LOGS = list()
CREDITT_LOG = list()
GRATSS_LOG = list()
KILL_TIMERS = list()
RAID_GROUPS = None
CREDITT_SASH_POS = 400
GRATSS_SASH_POS = 150
ACTIVE_SASH_POS = 215
HISTORICAL_SASH_POS = 215
RAIDTICK_ALERT_TIMER = None
RAIDTICK_REMINDER_COUNT = 0
AUCTION_ALERT_TIMERS = []

# Calculated variables
WX_LAST_WHO_SNAPSHOT = None
WX_TASKBAR_ICON = None
ALLIANCE_MAP = dict()
for alliance, guilds in ALLIANCES.items():
    for guild in guilds:
        ALLIANCE_MAP[guild] = alliance
TRIE = None
ITEMS = dict()
SPELLS = dict()
LAST_RAIDTICK = datetime.datetime.now()
LAST_NUMBER = 0
PLAYER_NAME = ""
LATEST_LOGFILE = None
WX_FILESYSTEM_WATCHER = None

# Constants
BASE_WIKI_URL = 'http://wiki.project1999.com'
SAVE_STATE_FILE = 'state.json'

# Regexes
TIMESTAMP = r"\[(?P<time>\w{3} \w{3} \d{2} \d\d:\d\d:\d\d \d{4})\] +"

# Drop Matchers
MATCH_DROP_SAY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says?, '(?P<text>.*)'")
MATCH_DROP_OOC = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says? out of character, '(?P<text>.*)'")
MATCH_DROP_AUC = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) auctions?, '(?P<text>.*)'")
MATCH_DROP_SHOUT = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) shouts?, '(?P<text>.*)'")
MATCH_DROP_GU = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild),"
    r" '(?P<text>.*)'")

# Bid Matchers
MATCH_BID_SAY = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says?, '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_BID_OOC = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) says? out of character, "
    r"'(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_BID_AUC = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) auctions?, '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_BID_SHOUT = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) shouts?, '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")
MATCH_BID_GU = re.compile(
    TIMESTAMP +
    r"(?P<name>\w+) (tells the guild|say to your guild),"
    r" '(?P<text>.*?(?P<bid>\d+(?!nd)).*)'")

# Random Matchers
MATCH_RAND1 = re.compile(
    TIMESTAMP +
    r"\*\*A Magic Die is rolled by (?P<name>\w+)\.")
MATCH_RAND2 = re.compile(
    TIMESTAMP +
    r"\*\*It could have been any number from (?P<from>\d+) to (?P<to>\d+), "
    r"but this time it turned up a (?P<result>\d+)\.(?P<name>\w+)")

# Other Matchers
MATCH_START_WHO = re.compile(
    TIMESTAMP + r"Players [oi]n EverQuest:")
MATCH_WHO = re.compile(
    TIMESTAMP +
    r"(?:AFK +)?(?:<LINKDEAD>)?\[(?P<level>\d+ )?(?P<class>[A-z ]+)\] +"
    r"(?P<name>\w+)(?: *\((?P<race>[\w ]+)\))?(?: *<(?P<guild>[\w \']+)>)?")
MATCH_END_WHO = re.compile(
    TIMESTAMP +
    r"There (are|is) (?P<count>\d+) players? in (?P<zone>[\w' ]+)\.")
MATCH_KILL = re.compile(
    TIMESTAMP +
    r"(?P<victim>[\w ]+) has been slain by (?P<killer>[\w ]+)!")
MATCH_RAIDTICK = re.compile(
    TIMESTAMP +
    r".*RAID ?TICK.*",
    flags=re.IGNORECASE
)
MATCH_CREDITT = re.compile(
    TIMESTAMP +
    r"(?P<from>.*) (-> (?P<name>\w+): |tells you, ')"
    r"(?P<message>.*creditt.*?)'?$",
    flags=re.IGNORECASE
)
MATCH_GRATSS = re.compile(
    TIMESTAMP +
    r"(?P<from>.*?) .*?(, '|: )(?P<message>.*gratss.*?)'?$",
    flags=re.IGNORECASE
)

DROP_CHANNEL_OPTIONS = {
    "say": MATCH_DROP_SAY,
    "ooc": MATCH_DROP_OOC,
    "auc": MATCH_DROP_AUC,
    "shout": MATCH_DROP_SHOUT,
    "gu": MATCH_DROP_GU
}
BID_CHANNEL_OPTIONS = {
    "say": MATCH_BID_SAY,
    "ooc": MATCH_BID_OOC,
    "auc": MATCH_BID_AUC,
    "shout": MATCH_BID_SHOUT,
    "gu": MATCH_BID_GU
}

MATCH_DROP = CONF.get(
    "default", "drop_channels",
    fallback="say, ooc")
MATCH_DROP = [DROP_CHANNEL_OPTIONS[chan.strip().lower()]
              for chan in MATCH_DROP.split(',')
              if chan.strip().lower() in DROP_CHANNEL_OPTIONS]
MATCH_BID = CONF.get(
    "default", "bid_channels",
    fallback="say, auc, shout, gu")
MATCH_BID = [BID_CHANNEL_OPTIONS[chan.strip().lower()]
             for chan in MATCH_BID.split(',')
             if chan.strip().lower() in BID_CHANNEL_OPTIONS]
PRIMARY_BID_CHANNEL = CONF.get("default", "primary_bid_channel",
                               fallback="unset")

if NEEDS_WRITE:
    write()
