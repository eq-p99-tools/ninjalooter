# pylint: disable=no-member

import wx

from ninjalooter import config
from ninjalooter import logging

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class Player:  # pylint: disable=too-few-public-methods
    name = None
    pclass = None
    level = None
    guild = None

    def __init__(self, name, pclass, level, guild):
        self.name = name
        self.pclass = pclass
        self.level = level
        self.guild = guild


class ItemDrop:
    name = None
    reporter = None
    timestamp = None

    def __init__(self, name, reporter, timestamp):
        self.name = name
        self.reporter = reporter
        self.timestamp = timestamp

    def classes(self) -> str:
        return "TODO"

    def droppable(self) -> str:
        return "TODO"

    def __str__(self):
        return "{name} ({reporter} @ {time})".format(
            name=self.name, reporter=self.reporter, time=self.timestamp)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return ((self.name, self.reporter, self.timestamp) ==
                (other.name, other.reporter, other.timestamp))


class Auction:
    item = None
    complete = False

    def __init__(self, item: ItemDrop):
        self.item = item

    def add(self, number: int, player: str) -> bool:
        raise NotImplementedError()

    def highest(self) -> iter:
        raise NotImplementedError()

    def bid_text(self) -> str:
        raise NotImplementedError()

    def win_text(self) -> str:
        raise NotImplementedError()

    def highest_number(self) -> str:
        highest = self.highest()
        if highest:
            highest = list(highest)
        number = "None"
        if highest:
            number = highest[0][1]
        return number

    def highest_players(self) -> str:
        highest = self.highest() or []
        players = []
        for one in highest:
            players.append(one[0])
        players = ', '.join(players)
        return players or "None"

    def name(self) -> str:
        return self.item.name

    def classes(self) -> str:
        return self.item.classes()

    def droppable(self) -> str:
        return self.item.droppable()


class DKPAuction(Auction):
    bids = None

    def __init__(self, item: ItemDrop):
        super().__init__(item)
        self.bids = dict()

    def add(self, number: int, player: str) -> bool:
        if not number:
            # Not a real bid
            LOG.info("%s attempted to bid for %s but didn't post a number",
                     player, self.item)
            return False
        if not self.bids or number > max(self.bids):
            # Valid bid
            self.bids[number] = player
            LOG.info("Bid added for %s: %s = %d",
                     self.item, player, number)
            return True
        # Bid isn't higher than existing bids
        LOG.info("%s attempted to bid for %s but bid too low: %d",
                 player, self.item, number)
        return False

    def highest(self) -> iter:
        if not self.bids:
            LOG.info("No bids yet for %s", self.item)
            return None
        bid = max(self.bids)
        bidder = self.bids[bid]
        return ((bidder, bid),)  # noqa

    def bid_text(self) -> str:
        return "{name} {alliance} BID IN SHOUT, MIN {min} DKP".format(
            name=self.item.name, alliance="???", min=5)  # TODO: alliance/min

    def win_text(self) -> str:
        return "Grats {player} {number} DKP {item}!".format(
            player=self.highest_players(), number=self.highest_number(),
            item=self.item.name)


def get_next_number():
    number = config.NUMBERS[config.LAST_NUMBER % len(config.NUMBERS)]
    config.LAST_NUMBER += 1
    return number


class RandomAuction(Auction):
    item = None
    rolls = None
    number = None

    def __init__(self, item: ItemDrop):
        super().__init__(item)
        self.item = item
        self.rolls = dict()
        self.number = get_next_number()

    def add(self, number: int, player: str) -> bool:
        if not number:
            # Not a real roll
            LOG.info("%s attempted to roll for %s but didn't roll a number?",
                     player, self.item)
            return False
        if player in self.rolls:
            # Player already rolled
            LOG.info("Ignoring duplicate roll by %s for %s",
                     player, self.item)
            return False
        # Valid roll
        self.rolls[player] = number
        LOG.info("Accepted roll by %s for %s", player, self.item)
        return True

    def highest(self) -> iter:
        if not self.rolls:
            LOG.info("No rolls yet for %s", self.item)
            return None
        high = max(self.rolls.values())
        rollers = ((player, roll) for player, roll in self.rolls.items()
                   if roll == high)
        return rollers

    def bid_text(self) -> str:
        return "{name} {alliance} ROLL {number} NOW".format(
            name=self.item.name, alliance="???", number=self.number)
        # TODO: alliance

    def win_text(self) -> str:
        return "Grats {player} on {item}!".format(
            player=self.highest_players(), item=self.item.name)


EVT_DROP = wx.NewId()
EVT_BID = wx.NewId()
EVT_WHO = wx.NewId()
EVT_CLEAR_WHO = wx.NewId()


class DropEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_DROP)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class BidEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.SetEventType(EVT_BID)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.item == other.item


class WhoEvent(wx.PyEvent):
    def __init__(self, name, pclass, level, guild):
        super().__init__()
        self.SetEventType(EVT_WHO)
        self.name = name
        self.pclass = pclass
        self.level = level
        self.guild = guild

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.name, self.pclass, self.level, self.guild) == (
                other.name, other.pclass, other.level, other.guild)

    def __repr__(self):
        return "WhoEvent({}, {}, {}, {})".format(
            self.name, self.pclass, self.level, self.guild)


class ClearWhoEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_CLEAR_WHO)

    def __eq__(self, other):
        return isinstance(other, self.__class__)
