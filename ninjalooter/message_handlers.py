# pylint: disable=no-member

import copy
import re

import dateutil.parser
import wx

from ninjalooter import config
from ninjalooter import extra_data
from ninjalooter import logging
from ninjalooter import models

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


# pylint: disable=unused-argument
def handle_start_who(match: re.Match, window: wx.Frame) -> bool:
    config.PLAYER_AFFILIATIONS.clear()
    wx.PostEvent(window, models.ClearWhoEvent())
    return True


def handle_end_who(match: re.Match, window: wx.Frame) -> bool:
    who_time = match.group('time')
    parsed_time = dateutil.parser.parse(who_time)
    log_entry = models.WhoLog(
        parsed_time, copy.copy(config.PLAYER_AFFILIATIONS))
    config.WHO_LOG.append(log_entry)
    wx.PostEvent(window, models.WhoHistoryEvent())
    return True


def handle_who(match: re.Match, window: wx.Frame) -> bool:
    if not match:
        # No match was made, probably junk
        return False
    name = match.group("name")
    guild = match.group("guild")
    pclass = match.group("class") or ""
    level = (match.group("level") or "??").strip()
    if name not in config.HISTORICAL_AFFILIATIONS:
        LOG.info("Adding player history for %s as guild %s",
                 name, guild)
        config.HISTORICAL_AFFILIATIONS[name] = guild
    elif guild is not None or (guild is None and pclass != "ANONYMOUS"):
        LOG.info("Updating player history for %s from %s to %s",
                 name, config.HISTORICAL_AFFILIATIONS[name], guild)
        config.HISTORICAL_AFFILIATIONS[name] = guild
    LOG.info("Adding player record for %s as guild %s",
             name, config.HISTORICAL_AFFILIATIONS[name])
    config.PLAYER_AFFILIATIONS[name] = config.HISTORICAL_AFFILIATIONS[name]
    wx.PostEvent(window, models.WhoEvent(name, pclass, level, guild))
    return True


def handle_ooc(match: re.Match, window: wx.Frame) -> tuple:
    if not match:
        # No match was made, probably junk
        return tuple()
    timestamp = match.group("time")
    name = match.group("name")
    text = match.group("text")
    guild = config.PLAYER_AFFILIATIONS.get(name)
    if guild and guild not in config.ALLIANCE_MAP:
        # Some other guild is talking, discard line
        LOG.info("Ignoring ooc from guild %s", guild)
        return tuple()

    # Handle text to return a list of items linked
    found_items = config.TREE.search_all(text)
    item_names = tuple(item[0] for item in found_items)
    for item in item_names:
        drop = models.ItemDrop(item, name, timestamp)
        config.PENDING_AUCTIONS.append(drop)
        LOG.info("Added item to PENDING AUCTIONS: %s", drop)
    if not item_names:
        return tuple()
    wx.PostEvent(window, models.DropEvent())
    return item_names


def handle_auc(match: re.Match, window: wx.Frame) -> bool:
    if not match:
        # No match was made, probably junk
        return False
    name = match.group("name")
    if name == "You":
        name = config.PLAYER_NAME
    guild = config.PLAYER_AFFILIATIONS.get(name)
    text = match.group("text")
    bid = int(match.group("bid"))

    found_items = tuple(config.TREE.search_all(text))
    if not found_items:
        # No item found in auction
        LOG.info("%s might have attempted to bid but no item name found: %s",
                 name, text)
        return False
    found_items = tuple(found_items)
    if len(found_items) > 1:
        # Can't bid on two items at once
        LOG.info("%s attempted to bid for two items at once: %s",
                 name, found_items)
        return False
    item, _ = found_items[0]

    if guild not in config.ALLIANCE_MAP:
        # Player is not in the alliance
        LOG.info("%s attempted to bid for %s, but is in the wrong guild: %s",
                 name, item, guild)
        return False
    for auc_item in config.ACTIVE_AUCTIONS.values():
        if item == auc_item.name().upper():
            result = auc_item.add(bid, name)
            wx.PostEvent(window, models.BidEvent(auc_item))
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
            return True
    LOG.info("%s rolled %d-%d but that doesn't apply to an active auction.",
             name, rand_from, rand_to)
    return False


def handle_kill(match: re.Match, window: wx.Frame) -> bool:
    time = match.group('time')
    victim = match.group('victim')
    if victim in extra_data.TIMER_MOBS:
        kt_obj = models.KillTimer(time, victim)
        config.KILL_TIMERS.append(kt_obj)
        wx.PostEvent(window, models.KillEvent())
        return True
    return False
