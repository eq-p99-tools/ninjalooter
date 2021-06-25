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
AWARD_MESSAGE_MATCHER = re.compile(r"Gratss \w+ on \[\w+] \(\d+ DKP\)!")


def handle_raidtick(match: re.Match, window: wx.Frame) -> bool:
    tick_time = match.group('time')
    config.LAST_RAIDTICK = dateutil.parser.parse(tick_time)
    return True


def handle_creditt(match: re.Match, window: wx.Frame) -> bool:
    time = match.group('time')
    user = match.group('from')
    message = match.group('message')
    raw_message = match.group(0)
    if AWARD_MESSAGE_MATCHER.match(message):
        return False
    creddit_entry = models.CredittLog(time, user, message, raw_message)
    config.CREDITT_LOG.append(creddit_entry)
    wx.PostEvent(window, models.CredittEvent())
    return True


# pylint: disable=unused-argument
def handle_start_who(match: re.Match, window: wx.Frame) -> bool:
    config.PLAYER_AFFILIATIONS.clear()
    wx.PostEvent(window, models.ClearWhoEvent())
    return True


def handle_end_who(match: re.Match, window: wx.Frame) -> bool:
    who_time = match.group('time')
    parsed_time = dateutil.parser.parse(who_time)
    raidtick_was = datetime.datetime.now() - config.LAST_RAIDTICK
    raidtick_who = False
    if raidtick_was <= datetime.timedelta(seconds=3):
        raidtick_who = True
    log_entry = models.WhoLog(
        parsed_time, copy.copy(config.PLAYER_AFFILIATIONS), raidtick_who)
    config.WHO_LOG.append(log_entry)
    wx.PostEvent(window, models.WhoHistoryEvent())
    wx.PostEvent(window, models.WhoEndEvent())
    utils.store_state()
    return True


def handle_who(match: re.Match, window: wx.Frame) -> bool:
    name = match.group("name")
    guild = match.group("guild")
    pclass = match.group("class") or ""
    if pclass in extra_data.CLASS_TITLES:
        pclass = extra_data.CLASS_TITLES[pclass]
    level = (match.group("level") or "??").strip()
    if name not in config.HISTORICAL_AFFILIATIONS:
        LOG.info("Adding player history for %s as guild %s",
                 name, guild)
        config.HISTORICAL_AFFILIATIONS[name] = guild
    elif guild or (not guild and pclass != "ANONYMOUS"):
        LOG.info("Updating player history for %s from %s to %s",
                 name, config.HISTORICAL_AFFILIATIONS[name], guild)
        config.HISTORICAL_AFFILIATIONS[name] = guild
    LOG.info("Adding player record for %s as guild %s",
             name, config.HISTORICAL_AFFILIATIONS[name])
    config.PLAYER_AFFILIATIONS[name] = config.HISTORICAL_AFFILIATIONS[name]
    wx.PostEvent(window, models.WhoEvent(name, pclass, level, guild))
    return True


def handle_drop(match: re.Match, window: wx.Frame) -> list:
    timestamp = match.group("time")
    name = match.group("name")
    text = match.group("text")
    guild = config.PLAYER_AFFILIATIONS.get(name)
    if text.lower().startswith("looted"):
        LOG.info("Ignoring drop message starting with 'looted'")
        return list()
    if config.RESTRICT_BIDS and guild and guild not in config.ALLIANCE_MAP:
        # Some other guild is talking, discard line
        LOG.info("Ignoring ooc from guild %s", guild)
        return list()

    # Handle text to return a list of items linked
    found_items = utils.get_items_from_text(text)
    for item in found_items:
        if item.lower() in utils.get_active_item_names():
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
    if not found_items:
        return list()
    wx.PostEvent(window, models.DropEvent())
    utils.store_state()
    return found_items


def handle_bid(match: re.Match, window: wx.Frame) -> bool:
    name = match.group("name")
    if name == "You":
        name = config.PLAYER_NAME
    guild = config.PLAYER_AFFILIATIONS.get(name)
    alliance = config.ALLIANCE_MAP.get(guild)
    text = match.group("text")
    bid = int(match.group("bid"))

    if 'BID IN /GU' in text:
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
            utils.store_state()
            return result
    LOG.info("%s attempted to bid for %s but it isn't active", name, item)
    return False


def handle_rand1(match: re.Match, window: wx.Frame) -> str:
    return match.group('name')


def handle_rand2(match: re.Match, window: wx.Frame) -> bool:
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
            utils.store_state()
            return True
    LOG.info("%s rolled %d-%d but that doesn't apply to an active auction.",
             name, rand_from, rand_to)
    return False


def handle_kill(match: re.Match, window: wx.Frame) -> bool:
    time = match.group('time')
    victim = match.group('victim')
    # if victim in extra_data.TIMER_MOBS:
    kt_obj = models.KillTimer(time, victim)
    config.KILL_TIMERS.append(kt_obj)
    wx.PostEvent(window, models.KillEvent())
    utils.store_state()
    return True
    # return False
