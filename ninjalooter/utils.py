import json
import os
import pathlib
import re

from ahocorapy import keywordtree

from ninjalooter import config

RE_EQ_LOGFILE = re.compile(r'.*_(.*)_.*\.txt')
PROJECT_DIR = pathlib.Path(__file__).parent.parent


def generate_pop_roll():
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
    return roll_text, start


def get_character_name_from_logfile(logfile):
    log_name = os.path.split(logfile)[-1]
    char_match = RE_EQ_LOGFILE.search(log_name)
    if char_match:
        char_name = char_match.group(1).capitalize()
    else:
        char_name = "NO MATCH"
    return char_name


def load_latest_logfile(logdir):
    latest_file = None
    latest_file_time = 0
    char_name = None
    logfile = None
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
        logfile = open(latest_file, 'r')
        logfile.seek(0, os.SEEK_END)
        char_name = get_character_name_from_logfile(latest_file)
    return logfile, char_name


def load_item_data():
    with open(os.path.join(PROJECT_DIR, 'data', 'items.json')) as item_file:
        return json.load(item_file)


def setup_aho():
    config.TREE = keywordtree.KeywordTree(case_insensitive=True)
    config.ITEMS = load_item_data()
    for item in config.ITEMS:
        config.TREE.add(item)
    config.TREE.finalize()


def get_next_number():
    number = config.NUMBERS[config.LAST_NUMBER % len(config.NUMBERS)]
    config.LAST_NUMBER += 1
    return number
