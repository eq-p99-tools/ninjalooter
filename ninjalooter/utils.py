import inspect
import json
import os
import pathlib
import re
import webbrowser

from ahocorapy import keywordtree
import pyperclip

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import models

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)

RE_EQ_LOGFILE = re.compile(r'.*_(.*)_.*\.txt')
PROJECT_DIR = pathlib.Path(__file__).parent.parent


def ignore_pending_item(item: models.ItemDrop) -> None:
    config.IGNORED_AUCTIONS.append(item)
    config.PENDING_AUCTIONS.remove(item)


def start_auction_dkp(item: models.ItemDrop,
                      alliance: str) -> models.DKPAuction:
    names = (item.name() for item in config.ACTIVE_AUCTIONS.values())
    if item.name in names:
        LOG.warning("Item %s already pending bid, not starting another.")
        return None
    auc = models.DKPAuction(item, alliance)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.uuid] = auc
    LOG.info("Started DKP bid for item: %s", item)
    return auc


def start_auction_random(item: models.ItemDrop) -> models.RandomAuction:
    names = (item.name() for item in config.ACTIVE_AUCTIONS.values())
    if item.name in names:
        LOG.warning("Item %s already pending roll, not starting another.")
        return None
    auc = models.RandomAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.uuid] = auc
    LOG.info("Started random roll for item: %s", item)
    return auc


def get_pop_numbers(source=None, extras=None) -> dict:
    if source is None:
        source = config.PLAYER_AFFILIATIONS
    extras = extras or dict()
    pops = {alliance: 0 for alliance in config.ALLIANCES}
    pops.update(extras)
    for _, guild in source.items():
        alliance = config.ALLIANCE_MAP.get(guild)
        if alliance:
            pops[alliance] += 1
    return pops


def generate_pop_roll(source=None, extras=None) -> tuple:
    pops = get_pop_numbers(source, extras)
    roll_text = None  # '1-24 BL // 25-48 Kingdom //49-61 VCR'
    start = 1
    end = 1
    for alliance, pop in pops.items():
        if pop < 1:
            continue
        end = start + pop - 1
        alliance_text = "{}-{} {}".format(start, end, alliance)
        if not roll_text:
            roll_text = alliance_text
        else:
            roll_text = " // ".join((roll_text, alliance_text))
        start = end + 1
    if roll_text:
        roll_text = "/shout " + roll_text
    else:
        frame = inspect.currentframe()
        roll_text = '/tell Toald break in `{func}:{line}`'.format(
            func=frame.f_code.co_name,
            line=frame.f_lineno - 1
        )
    rand_text = "/random 1 {}".format(end)
    LOG.info("Generated pop roll with %d players: %s",
             start, roll_text)
    return roll_text, rand_text


def get_character_name_from_logfile(logfile: str) -> str:
    log_name = os.path.split(logfile)[-1]
    char_match = RE_EQ_LOGFILE.search(log_name)
    if char_match:
        char_name = char_match.group(1).capitalize()
    else:
        char_name = "NO MATCH"
    return char_name


def get_latest_logfile(logdir: str) -> tuple:
    latest_file = None
    latest_file_time = 0
    char_name = None
    if logdir.endswith('.txt'):
        latest_file = logdir
    else:
        for root, _, files in os.walk(logdir):
            for basename in files:
                if not basename.startswith("eqlog"):
                    continue
                filename = os.path.join(root, basename)
                status = os.stat(filename)
                if status.st_mtime > latest_file_time:
                    latest_file_time = status.st_mtime
                    latest_file = filename
    if latest_file:
        char_name = get_character_name_from_logfile(latest_file)
    return latest_file, char_name


def load_item_data():
    with open(os.path.join(PROJECT_DIR, 'data', 'items.json')) as item_file:
        return json.load(item_file)


def setup_aho():
    config.TREE = keywordtree.KeywordTree(case_insensitive=True)
    config.ITEMS = load_item_data()
    for item in config.ITEMS:
        config.TREE.add(item)
    config.TREE.finalize()


def open_wiki_url(item: models.ItemDrop) -> None:
    url = config.BASE_WIKI_URL + config.ITEMS[item.name.upper()]
    webbrowser.open(url)


def to_clipboard(text: str) -> None:
    pyperclip.copy(text)


# Thanks rici from StackOverflow for saving me time!
# Based on https://stackoverflow.com/a/30472781
def compose_ranges(ranges: list, text: str):
    starts, ends = [], []
    for start, end in ranges:
        starts.append(start)
        ends.append(end)
    starts.sort()
    ends.sort()
    i, j, active = 0, 0, 0
    combined = []
    while True:
        if i < len(ranges) and starts[i] < ends[j]:
            if active == 0:
                combined.append({'start': starts[i]})
            active += 1
            i += 1
        elif j < len(ranges):
            active -= 1
            if active == 0:
                combined[len(combined) - 1]['end'] = ends[j]
            j += 1
        else:
            break
    combined_texts = []
    for item_range in combined:
        combined_texts.append(
            text[item_range['start']:item_range['end']])
    return combined_texts


def add_sample_data():
    copper_disc = models.ItemDrop(
        'Copper Disc', 'Bob', 'Mon Aug 17 07:15:39 2020')
    platinum_disc1 = models.ItemDrop(
        'Platinum Disc', 'Jim', 'Mon Aug 17 07:16:05 2020')
    platinum_disc2 = models.ItemDrop(
        'Platinum Disc', 'Bill', 'Mon Aug 17 07:16:05 2020')
    config.PENDING_AUCTIONS.append(copper_disc)
    config.PENDING_AUCTIONS.append(platinum_disc1)
    config.PENDING_AUCTIONS.append(platinum_disc2)
