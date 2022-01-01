# pylint: disable=no-member

import copy
import datetime
import re

import dateutil.parser
import wx

from ninjalooter import config
from ninjalooter import extra_data
from ninjalooter import logging
from ninjalooter import models
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)
AWARD_MESSAGE_MATCHER = re.compile(
    r"Gratss (?P<name>\w+) on \[(?P<item>.*?)] \((?P<dkp>\d+) DKP\)!")
NUMBER_MATCHER = re.compile(r".*\d.*")


def handle_raidtick(match: re.Match, window: wx.Frame,
                    skip_store=False) -> bool:
    tick_time = match.group('time')
    config.LAST_RAIDTICK = dateutil.parser.parse(tick_time)
    return True


def handle_creditt(match: re.Match, window: wx.Frame,
                   skip_store=False) -> bool:
    time = match.group('time')
    user = match.group('from')
    message = match.group('message')
    raw_message = match.group(0)
    creddit_entry = models.CredittLog(time, user, message, raw_message)
    config.CREDITT_LOG.append(creddit_entry)
    wx.PostEvent(window, models.CredittEvent())
    return True


def handle_gratss(match: re.Match, window: wx.Frame,
                  skip_store=False) -> bool:
    time = match.group('time')
    user = match.group('from')
    message = match.group('message')
    raw_message = match.group(0)

    # Don't register a gratss message if it's one of our award messages
    award_match = AWARD_MESSAGE_MATCHER.match(message)
    if award_match:
        for old_auction in config.HISTORICAL_AUCTIONS.values():
            # there were no bids on the auction, and this message is for ROT
            if (not old_auction.highest() and
                    award_match.group('name') == 'ROT' and
                    int(award_match.group('dkp')) == 0):
                # don't count this item
                return False
            # there was a bid and it matches player/dkp and item name
            elif (old_auction.highest() and
                    old_auction.highest()[0] == (  #
                            award_match.group('name'),
                            int(award_match.group('dkp'))) and
                    old_auction.item.name == award_match.group('item')):
                # don't count this item
                return False
    gratss_entry = models.GratssLog(time, user, message, raw_message)
    config.GRATSS_LOG.append(gratss_entry)
    wx.PostEvent(window, models.GratssEvent())
    return True


# pylint: disable=unused-argument
def handle_start_who(match: re.Match, window: wx.Frame,
                     skip_store=False) -> bool:
    config.LAST_WHO_SNAPSHOT.clear()
    wx.PostEvent(window, models.ClearWhoEvent())
    return True


def handle_end_who(match: re.Match, window: wx.Frame,
                   skip_store=False) -> bool:
    who_time = match.group('time')
    parsed_time = dateutil.parser.parse(who_time)
    raidtick_was = parsed_time - config.LAST_RAIDTICK
    raidtick_who = False
    if raidtick_was <= datetime.timedelta(seconds=3):
        raidtick_who = True
    log_entry = models.WhoLog(
        parsed_time, copy.copy(config.LAST_WHO_SNAPSHOT), raidtick_who)
    config.ATTENDANCE_LOGS.append(log_entry)
    wx.PostEvent(window, models.WhoHistoryEvent())
    wx.PostEvent(window, models.WhoEndEvent())
    if not skip_store:
        utils.store_state()
    return True


def handle_who(match: re.Match, window: wx.Frame, skip_store=False) -> bool:
    name = match.group("name")
    guild = match.group("guild")
    pclass = match.group("class") or ""
    if pclass in extra_data.CLASS_TITLES:
        pclass = extra_data.CLASS_TITLES[pclass]
    level = (match.group("level") or "??").strip()
    if name not in config.PLAYER_DB:
        LOG.info("Adding player history for %s as guild %s",
                 name, guild)
        config.PLAYER_DB[name] = models.Player(name, pclass,
                                               level, guild)
    elif pclass != "ANONYMOUS":
        LOG.info("Updating player history for %s from %s to %s",
                 name, config.PLAYER_DB[name].guild, guild)
        config.PLAYER_DB[name].pclass = pclass
        config.PLAYER_DB[name].level = level
        config.PLAYER_DB[name].guild = guild
    elif guild:
        LOG.info("Updating player history for RP %s from %s to %s",
                 name, config.PLAYER_DB[name].guild, guild)
        config.PLAYER_DB[name].guild = guild

    LOG.info("Adding player record for %s as guild %s",
             name, config.PLAYER_DB[name].guild)
    config.LAST_WHO_SNAPSHOT[name] = config.PLAYER_DB[name]
    wx.PostEvent(window, models.WhoEvent(name, pclass, level, guild))
    return True


def handle_drop(match: re.Match, window: wx.Frame, skip_store=False) -> list:
    timestamp = match.group("time")
    name = match.group("name")
    text = match.group("text")
    guild = config.LAST_WHO_SNAPSHOT.get(name, models.Player(name)).guild
    if text.lower().startswith("looted"):
        LOG.info("Ignoring drop message starting with 'looted'")
        return list()
    if AWARD_MESSAGE_MATCHER.match(text):
        LOG.info("Ignoring drop message that matches Gratss")
        return list()
    if NUMBER_MATCHER.match(text):
        # line contains a number, it's probably a bid, ignore it
        LOG.info("Ignoring drop message with a number, probably a bid")
        return list()
    if config.RESTRICT_BIDS and guild and guild not in config.ALLIANCE_MAP:
        # Some other guild is talking, discard line
        LOG.info("Ignoring ooc from guild %s", guild)
        return list()

    # Handle text to return a list of items linked
    found_items = utils.get_items_from_text(text)
    used_found_items = []
    now = datetime.datetime.now()
    skip = False
    for item in found_items:
        if item.lower() in utils.get_active_item_names():
            continue
        for pending in config.PENDING_AUCTIONS:
            pending_time = dateutil.parser.parse(pending.timestamp)
            if (item.lower() == pending.name.lower() and
                    (now - pending_time).seconds < config.DROP_COOLDOWN):
                skip = True
                break
        if skip:
            skip = False
            continue
        drop = models.ItemDrop(item, name, timestamp)
        if (config.NODROP_ONLY and
                item in extra_data.EXTRA_ITEM_DATA and
                not extra_data.EXTRA_ITEM_DATA[item].get('nodrop', True)):
            config.IGNORED_AUCTIONS.append(drop)
            LOG.info("Added droppable item to IGNORED AUCTIONS: %s", drop)
        else:
            config.PENDING_AUCTIONS.append(drop)
            LOG.info("Added item to PENDING AUCTIONS: %s", drop)
            used_found_items.append(item)
    if not found_items:
        return list()
    if used_found_items:
        wx.PostEvent(window, models.DropEvent())
    if not skip_store:
        utils.store_state()
    return found_items


def handle_bid(match: re.Match, window: wx.Frame, skip_store=False) -> bool:
    name = match.group("name")
    if name == "You":
        name = config.PLAYER_NAME
    guild = config.LAST_WHO_SNAPSHOT.get(name, models.Player(name)).guild
    alliance = config.ALLIANCE_MAP.get(guild)
    text = match.group("text")
    bid = int(match.group("bid"))

    if text.startswith("~"):
        return False

    found_items = utils.get_items_from_text(text)
    if not found_items:
        # No item found in auction
        LOG.info("%s might have attempted to bid but no item name found: %s",
                 name, text)
        return False
    if len(found_items) > 1:
        # Can't bid on two items at once
        LOG.info("%s attempted to bid for two items at once: %s",
                 name, found_items)
        return False
    item = found_items[0]

    for auc_item in config.ACTIVE_AUCTIONS.values():
        if item.lower() == auc_item.name().lower():
            if not isinstance(auc_item, models.DKPAuction):
                LOG.info(
                    "Ignoring bid by %s because `%s` is a random auction.",
                    name, item)
                return False
            if config.RESTRICT_BIDS and alliance != auc_item.alliance:
                # Player is not in the correct alliance
                LOG.info("%s attempted to bid for %s, but is in the wrong "
                         "guild/alliance: %s/%s", name, item, guild, alliance)
                return False
            result = auc_item.add(bid, name)
            wx.PostEvent(window, models.BidEvent(auc_item))
            if not skip_store:
                utils.store_state()
            return result
    LOG.info("%s attempted to bid for %s but it isn't active", name, item)
    return False


def handle_auc_start(match: re.Match, window: wx.Frame,
                     skip_store=False) -> bool:
    LOG.warning('AUCTION START for %s' % match.groupdict())
    message_time = dateutil.parser.parse(match.group('time'))
    item_name = match.group('item')
    utils.complete_old_auctions(message_time - datetime.timedelta(minutes=30))
    pending_item = None
    for item in reversed(config.PENDING_AUCTIONS):
        if item.name.lower() == item_name.lower():
            pending_item = item
            break
    if 'bid' in match.groupdict() and match.group('bid') is not None:
        active_items = utils.get_active_item_names()
        if item_name.lower() in active_items:
            LOG.debug("Not starting auction for %s, it is still in-progress.",
                      item_name)
            return False
        # check historical auctions to see if we closed one with this exact bid
        historical_auc = None
        item_bidder = [(match.group('player'), int(match.group('bid')))]
        for item in config.HISTORICAL_AUCTIONS.values():
            highest = item.highest()
            if (item.name().lower() == item_name.lower() and
                    highest == item_bidder):
                historical_auc = item
                break
        if historical_auc:
            LOG.debug("Found historical auction for %s/%s/%s, restarting it.",
                      item_name, item_bidder[0][0], item_bidder[0][1])
            config.HISTORICAL_AUCTIONS.pop(historical_auc.item.uuid)
            config.ACTIVE_AUCTIONS[historical_auc.item.uuid] = historical_auc
            return True
        LOG.debug("Failed to find historical auction for %s/%s/%s.",
                  item_name, item_bidder[0][0], item_bidder[0][1])

    if not pending_item:
        LOG.debug("Tried to start auction for %s but one was not pending.",
                  item_name)
        return False

    if 'min_dkp' in match.groupdict():
        start_auction = utils.start_auction_dkp
        if match.group('min_dkp') is not None:
            pending_item.min_dkp_override = int(match.group('min_dkp'))
        number = None
    else:
        start_auction = utils.start_auction_random
        number = int(match.group('number'))

    auc = start_auction(pending_item)
    if not auc:
        LOG.warning("Failed to start auction for %s, old auction pending.",
                    item_name)
        return False
    if number:
        auc.number = number
    auc.start_time = message_time
    if ('player' in match.groupdict() and
            match.group('player') is not None and
            match.group('bid') is not None):
        auc.bids[int(match.group('bid'))] = match.group('player')

    window.bidding_frame.pending_list.SetObjects(config.PENDING_AUCTIONS)
    window.bidding_frame.active_list.SetObjects(
        list(config.ACTIVE_AUCTIONS.values()))
    window.bidding_frame.active_list.SelectObject(auc)
    return True


def handle_auc_end(match: re.Match, window: wx.Frame,
                   skip_store=False) -> bool:
    LOG.warning('AUCTION END for %s' % match.groupdict())
    item_name = match.group('item')
    active_item = None
    for auc_item in config.ACTIVE_AUCTIONS.values():
        if auc_item.name().lower() == item_name.lower():
            active_item = auc_item
            break
    if not active_item:
        LOG.debug("Tried to stop auction for %s but one was not active.",
                  item_name)
        return False

    config.HISTORICAL_AUCTIONS[active_item.item.uuid] = (
        active_item)
    config.ACTIVE_AUCTIONS.pop(active_item.item.uuid)
    window.bidding_frame.active_list.SetObjects(
        list(config.ACTIVE_AUCTIONS.values()))
    window.bidding_frame.history_list.SetObjects(
        list(config.HISTORICAL_AUCTIONS.values()))
    window.bidding_frame.history_list.SelectObject(active_item)
    return True


def handle_rand1(match: re.Match, window: wx.Frame, skip_store=False) -> str:
    return match.group('name')


def handle_rand2(match: re.Match, window: wx.Frame, skip_store=False) -> bool:
    name = match.group('name')
    rand_from = int(match.group('from'))
    rand_to = int(match.group('to'))
    rand_result = int(match.group('result'))
    for item_obj in config.ACTIVE_AUCTIONS.values():
        if (isinstance(item_obj, models.RandomAuction) and
                item_obj.number == rand_to):
            if rand_from > 0:
                LOG.info(
                    "%s rolled from %d instead of 0, not counting it.",
                    name, rand_from)
                return False
            item_obj.add(rand_result, name)
            wx.PostEvent(window, models.BidEvent(item_obj))
            if not skip_store:
                utils.store_state()
            return True
    LOG.info("%s rolled %d-%d but that doesn't apply to an active auction.",
             name, rand_from, rand_to)
    return False


def handle_kill(match: re.Match, window: wx.Frame, skip_store=False) -> bool:
    time = match.group('time')
    victim = match.group('victim')
    # if victim in extra_data.TIMER_MOBS:
    kt_obj = models.KillTimer(time, victim)
    config.KILL_TIMERS.append(kt_obj)
    wx.PostEvent(window, models.KillEvent())
    if not skip_store:
        utils.store_state()
    return True
