# pylint: disable=no-member

import re

import wx

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import models

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


# pylint: disable=unused-argument
def handle_new_who(match: re.Match, window: wx.Frame) -> bool:
    config.PLAYER_AFFILIATIONS.clear()
    wx.PostEvent(window, models.ClearWhoEvent())
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
    if item not in config.ACTIVE_AUCTIONS:
        # Item is not currently up for bid
        LOG.info("%s attempted to bid for %s but it isn't active", name, item)
        return False
    result = config.ACTIVE_AUCTIONS[item].add(bid, name)
    wx.PostEvent(window, models.BidEvent(config.ACTIVE_AUCTIONS[item]))
    return result


def handle_rand(match: re.Match, window: wx.Frame) -> bool:
    return False
