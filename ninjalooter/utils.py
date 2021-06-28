# pylint: disable=too-many-locals,too-many-branches

import collections
import datetime
import inspect
import json
import os
import pathlib
import re
import webbrowser

from ahocorapy import keywordtree
import dateutil.parser
import pyperclip
import xlsxwriter
import xlsxwriter.exceptions

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import models

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)

RE_EQ_LOGFILE = re.compile(r'.*_(.*)_.*\.txt')
RE_TIMESTAMP = re.compile(config.TIMESTAMP)
PROJECT_DIR = pathlib.Path(__file__).parent.parent
LOG.info("Project working directory: %s", PROJECT_DIR)


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
    for guild in source.values():
        alliance = config.ALLIANCE_MAP.get(guild)
        if alliance:
            pops[alliance] += 1
    return pops


def generate_pop_roll(source=None, extras=None) -> tuple:
    pops = get_pop_numbers(source, extras)
    if set(pops.values()) == {0}:
        LOG.info("No population data exists, can't generate text.")
        return "", ""
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
             start - 1, roll_text)
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
    config.TRIE = keywordtree.KeywordTree(case_insensitive=True)
    config.ITEMS = load_item_data()
    for item in config.ITEMS:
        config.TRIE.add(item)
    config.TRIE.finalize()


def open_wiki_url(item: models.ItemDrop) -> None:
    url = config.BASE_WIKI_URL + config.ITEMS[item.name.upper()]
    webbrowser.open(url)


def to_clipboard(text: str) -> None:
    pyperclip.copy(text)


# Thanks rici from StackOverflow for saving me time!
# Based on https://stackoverflow.com/a/30472781
def compose_ranges(ranges: list, text: str) -> list:
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


def get_items_from_text(text: str) -> list:
    found_items = config.TRIE.search_all(text)
    found_items = list(found_items)
    match_ranges = []
    for item in found_items:
        match_ranges.append((item[1], len(item[0]) + item[1]))
    item_names = compose_ranges(match_ranges, text)
    return item_names


def get_active_item_names() -> list:
    """Return all active item bids as a list of lowercase item names."""
    active_items = []
    for auc_item in config.ACTIVE_AUCTIONS.values():
        active_items.append(auc_item.name().lower())
    return active_items


def get_timestamp(iterable_obj) -> datetime.datetime:
    """Return the first parsed timestamp found.

    :param iterable_obj: an iterator or something otherwise iterable
    :type iterable_obj: iterable
    :raises TypeError, ValueError
    """
    for item in iterable_obj:
        match = RE_TIMESTAMP.match(item)
        if match:
            return dateutil.parser.parse(match.group("time"))
    return datetime.datetime.fromtimestamp(0)


def load_state():
    try:
        with open(config.SAVE_STATE_FILE, 'r') as ssfp:
            json_state = json.load(ssfp, cls=JSONDecoder)
        for key, value in json_state.items():
            setattr(config, key, value)
        LOG.info("Loaded state.")
    except FileNotFoundError:
        LOG.info("Failed to load state, no state file found.")
    except json.JSONDecodeError:
        LOG.exception("Failed to load state, couldn't parse JSON.")
    except Exception:
        LOG.exception("Failed to load state, unknown exception.")


def store_state():
    json_state = {
        "PENDING_AUCTIONS": config.PENDING_AUCTIONS,
        "IGNORED_AUCTIONS": config.IGNORED_AUCTIONS,
        "ACTIVE_AUCTIONS": config.ACTIVE_AUCTIONS,
        "HISTORICAL_AUCTIONS": config.HISTORICAL_AUCTIONS,
        "PLAYER_AFFILIATIONS": config.PLAYER_AFFILIATIONS,
        "WX_PLAYER_AFFILIATIONS": config.WX_PLAYER_AFFILIATIONS,
        "HISTORICAL_AFFILIATIONS": config.HISTORICAL_AFFILIATIONS,
        "WHO_LOG": config.WHO_LOG,
        "KILL_TIMERS": config.KILL_TIMERS,
        "CREDITT_LOG": config.CREDITT_LOG,
        "GRATSS_LOG": config.GRATSS_LOG,
        "CREDITT_SASH_POS": config.CREDITT_SASH_POS,
        "GRATSS_SASH_POS": config.GRATSS_SASH_POS,
        "ACTIVE_SASH_POS": config.ACTIVE_SASH_POS,
        "HISTORICAL_SASH_POS": config.HISTORICAL_SASH_POS,
    }
    with open(config.SAVE_STATE_FILE, 'w') as ssfp:
        json.dump(json_state, ssfp, cls=JSONEncoder)


def export_to_excel(filename):
    LOG.warning("Export to filename %s: NOT IMPLEMENTED",
                filename)

    # Completed Auctions
    excel_data = {
        'Completed Auctions': [],
        'Kill Times': [],
        'Creditt & Gratss': [],
    }

    # Prepare Completed Auctions
    for auc in config.HISTORICAL_AUCTIONS.values():
        dkp_auc = isinstance(auc, models.DKPAuction)
        auc_data = {
            'time': dateutil.parser.parse(auc.item.timestamp),
            'item': auc.name(),
            'winner': auc.highest_players(),
            'type': 'DKP' if dkp_auc else 'Random',
            'bid': auc.highest_number() if dkp_auc else 'N/A',
        }
        excel_data['Completed Auctions'].append(auc_data)

    # Prepare Kill Times
    for killtime in config.KILL_TIMERS:
        killtime_data = {
            'time': dateutil.parser.parse(killtime.time),
            'mob': killtime.name,
            'island': killtime.island(),
        }
        excel_data['Kill Times'].append(killtime_data)

    # Get all raw creditt/gratss messages
    for creditt in config.CREDITT_LOG:
        creditt_data = {'creditt/gratss': creditt.raw_message}
        excel_data['Creditt & Gratss'].append(creditt_data)
    # Get all raw creditt/gratss messages
    for gratss in config.GRATSS_LOG:
        gratss_data = {'creditt/gratss': gratss.raw_message}
        excel_data['Creditt & Gratss'].append(gratss_data)

    # Set up the workbook
    workbook = xlsxwriter.Workbook(
        filename, {'default_date_format': 'm/d/yyyy h:mm:ss AM/PM'})
    bold = workbook.add_format({'bold': True})

    # Write "Basic Data" into the workbook
    for page, data in excel_data.items():
        if data:
            worksheet = workbook.add_worksheet(page)
            worksheet.write_row(0, 0, data[0].keys(), bold)
            worksheet.set_column(0, 1, 22)
            row_num = 1
            for row in data:
                worksheet.write_row(row_num, 0, row.values())
                row_num += 1
            worksheet.autofilter(0, 0, len(data[0]), len(data[0].keys()) - 1)

    # Write Attendance Logs
    for entry in config.WHO_LOG:
        if entry.log:
            time_str = entry.time.strftime('%Y.%m.%d %I.%M.%S %p')
            worksheet_name = time_str
            worksheet_name_append = 0
            attendance_sheet = None
            while attendance_sheet is None:
                try:
                    if worksheet_name_append > 0:
                        worksheet_name = "{0} ({1})".format(
                            time_str, worksheet_name_append)
                    attendance_sheet = workbook.add_worksheet(worksheet_name)
                except xlsxwriter.exceptions.DuplicateWorksheetName:
                    worksheet_name_append += 1
                except Exception:
                    return False

            attendance_sheet.write_row(0, 0, ('name', 'guild'), bold)
            attendance_sheet.set_column(0, 1, 18)
            row_num = 1
            for name, guild in entry.log.items():
                attendance_sheet.write_row(row_num, 0, (name, guild))
                row_num += 1
            attendance_sheet.autofilter(0, 0, row_num - 1, 1)

    # Save the workbook
    try:
        workbook.close()
        return True
    except xlsxwriter.exceptions.FileCreateError:
        return False


def export_to_eqdkp(filename):
    # Recreate /who lines for each recorded raidtick
    raidtick_logs = []
    for wholog in config.WHO_LOG:
        if wholog.raidtick:
            tick_time = wholog.eqtime()
            tick_lines = []
            for member, guild in wholog.log.items():
                tick_line = f"[{tick_time}] [ANONYMOUS] {member} <{guild}>"
                tick_lines.append(tick_line)
            if tick_lines:
                raidtick_logs.append(tick_lines)

    # Get all raw creditt/gratss messages
    creditt_messages = [x.raw_message for x in config.CREDITT_LOG]
    gratss_messages = [x.raw_message for x in config.GRATSS_LOG]

    # Assemble all recorded loots into parsable format
    closed_loots = []
    for auction in config.HISTORICAL_AUCTIONS.values():
        highest = auction.highest()
        if highest and isinstance(auction, models.DKPAuction):
            winner, dkp = highest[0]
            closed_loots.append(
                f"[{auction.item.timestamp}] You say, 'LOOT: "
                f" {auction.item.name} {winner} {dkp}'"
            )
        elif highest:
            winner, _ = highest[0]
            closed_loots.append(
                f"[{auction.item.timestamp}] You say, 'LOOT: "
                f" {auction.item.name} {winner} 0'"
            )

    # Set up the workbook
    workbook = xlsxwriter.Workbook(
        filename, {'default_date_format': 'm/d/yyyy h:mm:ss AM/PM'})
    sheets = collections.OrderedDict()
    sheet_rows = {}

    # Make a sheet for creditt and gratss adjustments
    creditt_sheet = workbook.add_worksheet("Creditt & Gratss")
    for row, creditt in enumerate(creditt_messages):
        creditt_sheet.write_string(row, 0, creditt)
    for row, gratss in enumerate(gratss_messages):
        creditt_sheet.write_string(len(creditt_messages) + row + 1, 0, gratss)

    # Create a page per raidtick
    for tick in raidtick_logs:
        tick_timestamp = re.match(config.TIMESTAMP, tick[0]).group('time')
        parsed_time = dateutil.parser.parse(tick_timestamp)
        time_str = parsed_time.strftime('%Y.%m.%d %I.%M.%S %p')
        worksheet = workbook.add_worksheet(time_str)
        sheets[parsed_time] = worksheet
        # Write /who logs
        for row, line in enumerate(tick):
            worksheet.write_string(row, 0, line)
            sheet_rows[time_str] = row + 1
    # If there weren't any ticks, just make one sheet to hold loot
    if not sheets and closed_loots:
        sheets["Loot"] = workbook.add_worksheet("Loot")
        sheet_rows["Loot"] = -1

    for sheet_timestamp in reversed(sheets):
        sheet = sheets[sheet_timestamp]
        # Write loots after each tick, working backwards
        for loot in closed_loots.copy():
            loot_timestamp = re.match(config.TIMESTAMP, loot).group('time')
            parsed_time = dateutil.parser.parse(loot_timestamp)
            if sheet_timestamp == "Loot" or parsed_time > sheet_timestamp:
                sheet_rows[sheet.name] += 1
                sheet.write_string(sheet_rows[sheet.name], 0, loot)
                closed_loots.remove(loot)

    # Write any remaining loots to the earliest sheet
    first_sheet = list(sheets.values())[0]
    for loot in closed_loots:
        sheet_rows[first_sheet.name] += 1
        first_sheet.write_string(sheet_rows[first_sheet.name], 0, loot)

    # Save the workbook
    try:
        workbook.close()
        return True
    except xlsxwriter.exceptions.FileCreateError:
        return False


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


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=arguments-differ
        try:
            return obj.to_json()
        except AttributeError:
            if isinstance(obj, datetime.datetime):
                return obj.isoformat()
            return json.JSONEncoder.default(self, obj)


# Mutated from https://github.com/AlexisGomes/JsonEncoder/
class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):  # pylint: disable=method-hidden
        if isinstance(obj, dict):
            if 'json_type' in obj:
                json_type = obj.pop('json_type')
                model_type = getattr(models, json_type)
                if model_type and issubclass(model_type, models.DictEquals):
                    return model_type.from_json(**obj)

        # handling the resolution of nested objects
        if isinstance(obj, dict):
            for key in list(obj):
                obj[key] = self.object_hook(obj[key])

        return obj
