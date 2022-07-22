# pylint: disable=too-many-locals,too-many-branches

import collections
import csv
import datetime
import distutils.util
import inspect
import json
import os
import re
import webbrowser

from ahocorapy import keywordtree
import dateutil.parser
import playsound
import pyperclip
import pytz
import requests
import xlsxwriter
import xlsxwriter.exceptions

from ninjalooter import config
from ninjalooter import logger
from ninjalooter import models

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)

RE_EQ_LOGFILE = re.compile(r'.*_(.*)_.*\.txt')
RE_TIMESTAMP = re.compile(config.TIMESTAMP)
LOG.info("Project working directory: %s", config.PROJECT_DIR)


def ignore_pending_item(item: models.ItemDrop) -> None:
    config.IGNORED_AUCTIONS.append(item)
    config.PENDING_AUCTIONS.remove(item)


def start_auction_dkp(item: models.ItemDrop,
                      alliance="") -> models.DKPAuction:
    names = (item.name() for item in config.ACTIVE_AUCTIONS.values())
    if item.name in names:
        LOG.warning("Item %s already pending bid, not starting another.",
                    item.name)
        return None
    auc = models.DKPAuction(item, alliance)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.uuid] = auc
    LOG.info("Started DKP bid for item: %s", item)
    return auc


def start_auction_random(item: models.ItemDrop) -> models.RandomAuction:
    names = (item.name() for item in config.ACTIVE_AUCTIONS.values())
    if item.name in names:
        LOG.warning("Item %s already pending roll, not starting another.",
                    item.name)
        return None
    auc = models.RandomAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item.uuid] = auc
    LOG.info("Started random roll for item: %s", item)
    return auc


def complete_old_auctions(cutoff_time: datetime.datetime):
    for auc in list(config.ACTIVE_AUCTIONS.values()):
        if auc.start_time < cutoff_time:
            LOG.debug("Completing old auction")
            config.ACTIVE_AUCTIONS.pop(auc.item.uuid)
            config.HISTORICAL_AUCTIONS[auc.item.uuid] = auc


def get_pop_numbers(source=None, extras=None) -> dict:
    if source is None:
        source = config.LAST_WHO_SNAPSHOT
    extras = extras or dict()
    pops = collections.OrderedDict()
    for alliance in config.ALLIANCES:
        pops[alliance] = 0
    pops.update(extras)
    for guild in [p.guild for p in source.values()]:
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


def _duplicate_backtick_apostrophes(items: list) -> list:
    backtick_items = {item: link for item, link in items.items()
                      if "`" in item}
    apostrophe_items = {item: link for item, link in items.items()
                        if "'" in item}
    for item, link in backtick_items.items():
        fixed_item_name = item.replace("`", "'")
        if fixed_item_name not in items:
            items[fixed_item_name] = link
    for item, link in apostrophe_items.items():
        fixed_item_name = item.replace("'", "`")
        if fixed_item_name not in items:
            items[fixed_item_name] = link
    return items


def load_item_data():
    with open(os.path.join(config.PROJECT_DIR,
                           'data', 'items.json')) as item_file:
        items = json.load(item_file)
    return _duplicate_backtick_apostrophes(items)


def load_spell_data():
    with open(os.path.join(config.PROJECT_DIR,
                           'data', 'spells.json')) as spell_file:
        spells = json.load(spell_file)
    return _duplicate_backtick_apostrophes(spells)


def setup_aho():
    config.TRIE = keywordtree.KeywordTree(case_insensitive=True)
    config.ITEMS = load_item_data()
    config.SPELLS = load_spell_data()
    for item in config.ITEMS:
        config.TRIE.add(item)
    for spell in config.SPELLS:
        config.TRIE.add("SPELL: %s" % spell)
    # Quick hack so I don't have to separate all the spells/songs
    for spell in config.SPELLS:
        config.TRIE.add("SONG: %s" % spell)
    config.TRIE.finalize()


def open_wiki_url(item: models.ItemDrop) -> None:
    url = config.BASE_WIKI_URL + config.ITEMS[item.name.upper()]
    webbrowser.open(url)


def open_generic_url(url: str) -> None:
    webbrowser.open(url)


def to_clipboard(text: str) -> None:
    pyperclip.copy(text)


def alert_message(title, message, msec=2000):
    if config.TEXT_ALERTS and config.WX_TASKBAR_ICON is not None:
        try:
            config.WX_TASKBAR_ICON.ShowBalloon(title, message, msec)
        except:  # noqa
            LOG.exception("Couldn't show alert balloon.")


def alert_sound(soundfile, block=False):
    if config.AUDIO_ALERTS:
        try:
            playsound.playsound(soundfile, block)
        except:  # noqa
            LOG.exception("Couldn't play soundfile.")


def clear_alerts():
    if config.RAIDTICK_ALERT_TIMER:
        config.RAIDTICK_ALERT_TIMER.cancel()
        config.RAIDTICK_REMINDER_COUNT = 0
    for timer in config.AUCTION_ALERT_TIMERS:
        timer.cancel()


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


def get_pending_item_names() -> list:
    """Return all pending item drops as a list of lowercase item names."""
    pending_items = []
    for item in config.PENDING_AUCTIONS:
        pending_items.append(item.name.lower())
    return pending_items


def get_active_item_names() -> list:
    """Return all active item bids as a list of lowercase item names."""
    active_items = []
    for auc_item in config.ACTIVE_AUCTIONS.values():
        active_items.append(auc_item.name().lower())
    return active_items


def datetime_to_eq_format(
        some_datetime: datetime.datetime, allow_eastern: bool = True) -> str:
    if config.EXPORT_TIME_IN_EASTERN and allow_eastern:
        some_datetime = some_datetime + eastern_time_offset()
    return some_datetime.strftime("%a %b %d %H:%M:%S %Y")


def datetime_from_eq_format(
        some_datetime: str, allow_eastern: bool = True) -> datetime.datetime:
    dt = dateutil.parser.parse(some_datetime)
    if config.EXPORT_TIME_IN_EASTERN and allow_eastern:
        dt = dt + eastern_time_offset()
    return dt


def find_timestamp(lines: list, timestamp: datetime.datetime) -> (int, None):
    # If the list is empty, return None
    if not lines:
        return None

    # find the first timestamp, with line number (return None if no timestamps)
    for first_index, item in enumerate(lines):
        first_ts = get_timestamp(item)
        if first_ts:
            break
    else:
        return None
    # if the first timestamp is equal or after the timestamp, return it
    if first_ts >= timestamp:
        return first_index  # pylint: disable=undefined-loop-variable

    # find the last timestamp, with line number
    for item in reversed(lines):
        last_ts = get_timestamp(item)
        if last_ts:
            break
    else:  # not really necessary, but make pylint happy
        return None
    # if the last time is before the timestamp, return None
    if last_ts < timestamp:
        return None

    # if the list has 1 or less lines, return index 0
    if len(lines) <= 1:
        return 0

    # find the middle timestamp
    middle_index = int(len(lines)/2)
    for item in lines[middle_index:]:
        middle_ts = get_timestamp(item)
        if middle_ts:
            break
    else:
        middle_ts = None

    if middle_ts and middle_ts > timestamp:
        # if the middle timestamp is after our goal, look at the first half
        left = find_timestamp(lines[:middle_index], timestamp)
        if left is not None:
            return left
        # if the middle timestamp was after our timestamp, but the stuff on the
        # left is all before it, then the middle timestamp must be our target
        return middle_index

    # the middle timestamp is equal or before our goal, so check the right
    right = find_timestamp(lines[middle_index:], timestamp)
    if right is not None:
        return middle_index + right
    LOG.error("Couldn't find a timestamp. How did we get here?")


def get_timestamp(logline: str) -> datetime.datetime:
    match = RE_TIMESTAMP.match(logline)
    if match:
        return datetime_from_eq_format(
            match.group("time"), allow_eastern=False)
    return None


def get_first_timestamp(iterable_obj) -> datetime.datetime:
    """Return the first parsed timestamp found.

    :param iterable_obj: an iterator or something otherwise iterable
    :type iterable_obj: iterable
    :raises TypeError, ValueError
    """
    for item in iterable_obj:
        timestamp = get_timestamp(item)
        if timestamp:
            return timestamp
    return datetime.datetime.fromtimestamp(0)


def load_state():
    try:
        with open(config.SAVE_STATE_FILE, 'r') as ssfp:
            json_state = json.load(ssfp, cls=JSONDecoder)
        for key, value in json_state.items():
            # Handle conversion of history data prior to v1.14
            if key == 'PLAYER_AFFILIATIONS':
                key = 'LAST_WHO_SNAPSHOT'
                value = {name: models.Player(name, guild=guild)
                         for name, guild in value.items()}
            elif key == 'HISTORICAL_AFFILIATIONS':
                key = 'PLAYER_DB'
                value = {name: models.Player(name, guild=guild)
                         for name, guild in value.items()}
            elif key == 'WHO_LOG':
                key = 'ATTENDANCE_LOGS'
                for entry in value:
                    entry.log = {name: models.Player(name, guild=guild)
                                 for name, guild in entry.log.items()}

            setattr(config, key, value)
        LOG.info("Loaded state.")
    except FileNotFoundError:
        LOG.info("Failed to load state, no state file found.")
    except json.JSONDecodeError:
        LOG.exception("Failed to load state, couldn't parse JSON.")
    except Exception:
        LOG.exception("Failed to load state, unknown exception.")


def store_state(backup=False):
    statefile_name = config.SAVE_STATE_FILE
    if backup and config.BACKUP_ON_CLEAR:
        now = datetime.datetime.now()
        timestr = now.isoformat().replace(':', '-').split('.')[0]
        statefile_name = "state_{}.json".format(timestr)

    json_state = {
        "PENDING_AUCTIONS": config.PENDING_AUCTIONS,
        "IGNORED_AUCTIONS": config.IGNORED_AUCTIONS,
        "ACTIVE_AUCTIONS": config.ACTIVE_AUCTIONS,
        "HISTORICAL_AUCTIONS": config.HISTORICAL_AUCTIONS,
        "LAST_WHO_SNAPSHOT": config.LAST_WHO_SNAPSHOT,
        "WX_LAST_WHO_SNAPSHOT": config.WX_LAST_WHO_SNAPSHOT,
        "PLAYER_DB": config.PLAYER_DB,
        "ATTENDANCE_LOGS": config.ATTENDANCE_LOGS,
        "KILL_TIMERS": config.KILL_TIMERS,
        "CREDITT_LOG": config.CREDITT_LOG,
        "GRATSS_LOG": config.GRATSS_LOG,
        "CREDITT_SASH_POS": config.CREDITT_SASH_POS,
        "GRATSS_SASH_POS": config.GRATSS_SASH_POS,
        "ACTIVE_SASH_POS": config.ACTIVE_SASH_POS,
        "HISTORICAL_SASH_POS": config.HISTORICAL_SASH_POS,
    }
    with open(statefile_name, 'w') as ssfp:
        json.dump(json_state, ssfp, cls=JSONEncoder)


def eastern_time_offset():
    now = datetime.datetime.utcnow()
    here = now.astimezone().utcoffset()
    eastern = now.astimezone(pytz.timezone("US/Eastern")).utcoffset()
    seconds = (eastern - here).seconds
    return datetime.timedelta(seconds=seconds)


def export_to_excel(filename):
    LOG.info("Exporting to Excel file: %s", filename)

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
            'time': datetime_from_eq_format(auc.item.timestamp),
            'item': auc.name(),
            'winner': auc.highest_players(),
            'type': 'DKP' if dkp_auc else 'Random',
            'bid': auc.highest_number() if dkp_auc else 'N/A',
        }
        excel_data['Completed Auctions'].append(auc_data)

    # Prepare Kill Times
    for killtime in config.KILL_TIMERS:
        killtime_data = {
            'time': datetime_from_eq_format(killtime.time),
            'mob': killtime.name,
            'island': killtime.island(),
        }
        excel_data['Kill Times'].append(killtime_data)

    # Get all raw creditt/gratss messages
    for creditt in config.CREDITT_LOG:
        adjusted_message = creditt.raw_message
        if config.EXPORT_TIME_IN_EASTERN:
            m = config.MATCH_CREDITT.match(adjusted_message)
            time_part = m.groupdict()['time']
            new_time = datetime_to_eq_format(
                datetime_from_eq_format(time_part, allow_eastern=False))
            adjusted_message = adjusted_message.replace(time_part, new_time)
        creditt_data = {'creditt/gratss': adjusted_message}
        excel_data['Creditt & Gratss'].append(creditt_data)
    # Get all raw creditt/gratss messages
    for gratss in config.GRATSS_LOG:
        adjusted_message = gratss.raw_message
        if config.EXPORT_TIME_IN_EASTERN:
            m = config.MATCH_GRATSS.match(adjusted_message)
            time_part = m.groupdict()['time']
            new_time = datetime_to_eq_format(
                datetime_from_eq_format(time_part, allow_eastern=False))
            adjusted_message = adjusted_message.replace(time_part, new_time)
        gratss_data = {'creditt/gratss': adjusted_message}
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
            worksheet.set_column(0, 0, 22)
            worksheet.set_column(1, 1, 30)
            worksheet.set_column(2, 2, 16)
            row_num = 1
            for row in data:
                worksheet.write_row(row_num, 0, row.values())
                row_num += 1
            worksheet.autofilter(0, 0, len(data[0]), len(data[0].keys()) - 1)

    # Write Attendance Logs
    for entry in config.ATTENDANCE_LOGS:
        if entry.log:
            if config.EXPORT_TIME_IN_EASTERN:
                time_str = (
                        entry.time + eastern_time_offset()
                ).strftime('%Y.%m.%d %I.%M.%S %p')
            else:
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

            attendance_sheet.write_row(
                0, 0, ('name', 'level', 'class', 'guild'), bold)
            attendance_sheet.set_column(0, 0, 18)
            attendance_sheet.set_column(1, 1, 8)
            attendance_sheet.set_column(2, 3, 18)
            row_num = 1
            for name, player_obj in entry.log.items():
                attendance_sheet.write_row(
                    row_num, 0,
                    (name,
                     player_obj.level if player_obj.level != 0 else "",
                     player_obj.pclass,
                     player_obj.guild))
                row_num += 1
            attendance_sheet.autofilter(0, 0, row_num - 1, 3)

    # Save the workbook
    try:
        workbook.close()
        return True
    except xlsxwriter.exceptions.FileCreateError:
        return False


def parse_auction_for_loot_export(auction):
    highest = auction.highest()
    if config.EXPORT_TIME_IN_EASTERN:
        item_time = datetime_from_eq_format(
            auction.item.timestamp, allow_eastern=False)
        timestamp = datetime_to_eq_format(item_time)
    else:
        timestamp = auction.item.timestamp
    if highest and isinstance(auction, models.DKPAuction):
        winner, dkp = highest[0]
        text = (
            f"[{timestamp}] You say, 'LOOT: "
            f" {auction.item.name} {winner} {dkp}'"
        )
    elif highest:
        winner, _ = highest[0]
        text = (
            f"[{timestamp}] You say, 'LOOT: "
            f" {auction.item.name} {winner} 0'"
        )
    return text


def export_to_eqdkp(filename):
    LOG.info("Exporting to EQDKP file: %s", filename)

    # Recreate /who lines for each recorded raidtick
    raidtick_logs = []
    for wholog in config.ATTENDANCE_LOGS:
        if wholog.raidtick:
            tick_time = wholog.eqtime(allow_eastern=True)
            tick_lines = []
            for member, player_obj in wholog.log.items():
                guild = player_obj.guild
                if config.RESTRICT_EXPORT and guild not in \
                        config.ALLIANCES[config.DEFAULT_ALLIANCE]:
                    continue
                level_class = None
                if player_obj.level:
                    level_class = f"{player_obj.level} {player_obj.pclass}"
                tick_line = f"[{tick_time}] [ANONYMOUS] {member} <{guild}>"
                if level_class:
                    tick_line += " {%s}" % level_class
                tick_lines.append(tick_line)
            if tick_lines:
                raidtick_logs.append((wholog.tick_name, tick_lines))

    # Get all raw creditt/gratss messages
    creditt_messages = []
    for message in config.CREDITT_LOG:
        adjusted_message = message.raw_message
        if config.EXPORT_TIME_IN_EASTERN:
            m = config.MATCH_CREDITT.match(adjusted_message)
            time_part = m.groupdict()['time']
            new_time = datetime_to_eq_format(
                datetime_from_eq_format(time_part, allow_eastern=False))
            adjusted_message = adjusted_message.replace(time_part, new_time)
        creditt_messages.append(adjusted_message)
    gratss_messages = []
    for message in config.GRATSS_LOG:
        adjusted_message = message.raw_message
        if config.EXPORT_TIME_IN_EASTERN:
            m = config.MATCH_GRATSS.match(adjusted_message)
            time_part = m.groupdict()['time']
            new_time = datetime_to_eq_format(
                datetime_from_eq_format(time_part, allow_eastern=False))
            adjusted_message = adjusted_message.replace(time_part, new_time)
        gratss_messages.append(adjusted_message)

    # Assemble all recorded loots into parsable format
    closed_loots = []
    for auction in config.HISTORICAL_AUCTIONS.values():
        closed_loots.append(parse_auction_for_loot_export(auction))

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
    for tick_name, tick in raidtick_logs:
        tick_timestamp = re.match(config.TIMESTAMP, tick[0]).group('time')
        parsed_time = datetime_from_eq_format(tick_timestamp)
        if tick_name:
            sheet_name = tick_name
        else:
            sheet_name = parsed_time.strftime('%Y.%m.%d %I.%M.%S %p')
        while sheet_name in workbook.sheetnames:
            if sheet_name[-1] in map(str, range(10)):
                sheet_name = sheet_name[:-1] + str(int(sheet_name[-1]) + 1)
            else:
                sheet_name += " 2"
        worksheet = workbook.add_worksheet(sheet_name)
        sheets[parsed_time] = worksheet
        # Write /who logs
        for row, line in enumerate(tick):
            worksheet.write_string(row, 0, line)
            sheet_rows[sheet_name] = row + 1
    # If there weren't any ticks, just make one sheet to hold loot
    if not sheets and closed_loots:
        sheets["Loot"] = workbook.add_worksheet("Loot")
        sheet_rows["Loot"] = -1
    try:
        first_sheet = list(sheets.values())[0]
        last_sheet = list(sheets.values())[-1]
    except IndexError:
        first_sheet = last_sheet = creditt_sheet

    # Loop through sheets and add creditts to them
    for sheet_timestamp in reversed(sheets):
        if sheet_timestamp == "Loot":
            continue
        sheet = sheets[sheet_timestamp]
        # Write creditts after each tick, working backwards
        for creditt in creditt_messages.copy():
            cred_timestamp = re.match(config.TIMESTAMP, creditt).group('time')
            parsed_time = datetime_from_eq_format(cred_timestamp)
            if parsed_time > sheet_timestamp:
                sheet_rows[sheet.name] += 1
                sheet.write_string(sheet_rows[sheet.name], 0, creditt)
                creditt_messages.remove(creditt)

    # Write any remaining creditts to the first sheet -- do we want this?
    for creditt in creditt_messages:
        if first_sheet.name == "Loot":
            break
        sheet_rows[first_sheet.name] += 1
        first_sheet.write_string(sheet_rows[first_sheet.name], 0, creditt)

    # Loop through sheets and add loots to them
    if config.TICK_BEFORE_LOOT:
        for sheet_timestamp in reversed(sheets):
            sheet = sheets[sheet_timestamp]
            # Write loots after each tick, working backwards
            for loot in closed_loots.copy():
                loot_timestamp = re.match(config.TIMESTAMP, loot).group('time')
                parsed_time = datetime_from_eq_format(loot_timestamp)
                if sheet_timestamp == "Loot" or parsed_time > sheet_timestamp:
                    sheet_rows[sheet.name] += 1
                    sheet.write_string(sheet_rows[sheet.name], 0, loot)
                    closed_loots.remove(loot)
        # Write any remaining loots to the earliest sheet
        first_sheet = list(sheets.values())[0]
        for loot in closed_loots:
            sheet_rows[first_sheet.name] += 1
            first_sheet.write_string(sheet_rows[first_sheet.name], 0, loot)
    else:
        for sheet_timestamp in sheets:
            sheet = sheets[sheet_timestamp]
            # Write loots to the current sheet
            for loot in closed_loots.copy():
                loot_timestamp = re.match(config.TIMESTAMP, loot).group('time')
                parsed_time = datetime_from_eq_format(loot_timestamp)
                if sheet_timestamp == "Loot" or parsed_time < sheet_timestamp:
                    sheet_rows[sheet.name] += 1
                    sheet.write_string(sheet_rows[sheet.name], 0, loot)
                    closed_loots.remove(loot)
        # Write any remaining loots to the last sheet
        for loot in closed_loots:
            sheet_rows[last_sheet.name] += 1
            last_sheet.write_string(sheet_rows[last_sheet.name], 0, loot)

    # Save the workbook
    try:
        workbook.close()
        return True
    except xlsxwriter.exceptions.FileCreateError:
        return False


def fetch_google_sheet_data(url):
    # Parse out the spreadsheet ID
    pattern1 = r".*/spreadsheets/d/([\w\-]+)/.*"
    pattern2 = r"^([\w\-]+)$"
    match = re.match(pattern1, url) or re.match(pattern2, url)
    if not match:
        LOG.error("Couldn't parse spreadsheet ID from URL: %s", url)
        return None
    sheet_id = match.group(1)

    # Get the data in CSV format
    new_url = (
        "https://docs.google.com/spreadsheets/d/{id}/export?format=csv"
    ).format(id=sheet_id)
    req = requests.get(new_url)
    if req.status_code != 200:
        LOG.error("Couldn't fetch spreadsheet `%s`: %d",
                  sheet_id, req.status_code)
        return None

    # Load the csv
    try:
        data = csv.DictReader(req.text.splitlines())
    except:  # noqa
        LOG.exception("Couldn't parse spreadsheet data.")
        return None

    return data


def translate_sheet_csv_to_mindkp_json(csv_data):
    output = {}
    for row in csv_data:
        try:
            mindkp_row = row[config.MIN_DKP_VAL_COL] or "1"
            try:
                mindkp_row = int(mindkp_row)
            except ValueError:
                if mindkp_row.lower().strip() == "random":
                    mindkp_row = -1
                elif mindkp_row.lower().strip() == "bank":
                    mindkp_row = -2
                else:
                    mindkp_row = -3
            item = {'min_dkp': mindkp_row}
            try:
                if config.MIN_DKP_RESTR_COL and row[config.MIN_DKP_RESTR_COL]:
                    item['classes'] = list(map(
                        lambda x: x.strip(),
                        row[config.MIN_DKP_RESTR_COL].split(",")))
            except:  # noqa
                LOG.warning("Couldn't parse column `%s` for row: %s",
                            config.MIN_DKP_DROP_COL, row)
            try:
                if config.MIN_DKP_DROP_COL and row[config.MIN_DKP_DROP_COL]:
                    item['nodrop'] = not bool(distutils.util.strtobool(
                        row[config.MIN_DKP_DROP_COL]))
            except:  # noqa
                LOG.warning("Couldn't parse column `%s` for row: %s",
                            config.MIN_DKP_DROP_COL, row)
            output[row[config.MIN_DKP_NAME_COL]] = item
        except:  # noqa
            LOG.warning("Couldn't parse row: %s", row)
            continue
    return output


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
    def default(self, o):  # pylint: disable=arguments-differ
        try:
            return o.to_json()
        except AttributeError:
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            return json.JSONEncoder.default(self, o)


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
