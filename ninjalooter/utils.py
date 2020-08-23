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


def start_auction_dkp(item: models.ItemDrop) -> models.DKPAuction:
    if item.name in config.ACTIVE_AUCTIONS:
        LOG.warning("Item %s already pending bid, not starting another.")
        return None
    auc = models.DKPAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.name] = auc
    # auc.add(1, "Tom")
    LOG.info("Started DKP bid for item: %s", item)
    return auc


def start_auction_random(item: models.ItemDrop) -> models.RandomAuction:
    if item.name in config.ACTIVE_AUCTIONS:
        LOG.warning("Item %s already pending roll, not starting another.")
        return None
    auc = models.RandomAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.name] = auc
    # auc.add(1, "Tom")
    # auc.add(1, "Bill")
    LOG.info("Started random roll for item: %s", item)
    return auc


def generate_pop_roll() -> tuple:
    pops = {alliance: 0 for alliance in config.ALLIANCES}
    for _, guild in config.PLAYER_AFFILIATIONS.items():
        alliance = config.ALLIANCE_MAP.get(guild)
        if alliance:
            pops[alliance] += 1
    roll_text = None  # '1-24 BL // 25-48 Kingdom //49-61 VCR'
    start = 1
    for alliance, pop in pops.items():
        next_start = start + pop
        alliance_text = "{}-{} {}".format(start, next_start - 1, alliance)
        if not roll_text:
            roll_text = alliance_text
        else:
            roll_text = " // ".join((roll_text, alliance_text))
        start = next_start
    rand_text = "/random 1 {}".format(start - 1)
    LOG.info("Generated pop roll with %d players: %s",
             start, roll_text)
    return "/shout " + roll_text, rand_text


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
