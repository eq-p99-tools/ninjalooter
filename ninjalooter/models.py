# pylint: disable=no-member

from __future__ import annotations
import uuid as uuid_lib

import dateutil.parser
import wx

from ninjalooter import config
from ninjalooter import extra_data
from ninjalooter import logging

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class DictEquals:
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def to_json(self):
        return {
            'json_type': self.__class__.__name__,
            **self.__dict__
        }

    @classmethod
    def from_json(cls, **kwargs) -> DictEquals:
        return cls(**kwargs)


class Player(DictEquals):
    name = None
    pclass = None
    level = None
    guild = None

    def __init__(self, name, pclass, level, guild):
        self.name = name
        self.pclass = pclass
        self.level = level
        self.guild = guild or ""


class WhoLog(DictEquals):
    time = None
    log = None

    def __init__(self, time, log):
        super().__init__()
        self.time = time
        self.log = log

    def populations(self):
        pops = {alliance: 0 for alliance in config.ALLIANCES}
        for guild in self.log.values():
            alliance = config.ALLIANCE_MAP.get(guild)
            if alliance:
                pops[alliance] += 1
        pop_text = None  # '1-24 BL // 25-48 Kingdom //49-61 VCR'
        for alliance, pop in pops.items():
            alliance_text = "{}: {}".format(alliance, pop)
            if not pop_text:
                pop_text = alliance_text
            else:
                pop_text = " // ".join((pop_text, alliance_text))
        return pop_text

    @classmethod
    def from_json(cls, **kwargs) -> DictEquals:
        kwargs['time'] = dateutil.parser.parse(kwargs['time'])
        return cls(**kwargs)


class PopulationPreview(DictEquals):
    alliance = None
    population = None

    def __init__(self, alliance, population):
        super().__init__()
        self.alliance = alliance
        self.population = population


class KillTimer(DictEquals):
    time = None
    name = None

    def __init__(self, time, name):
        super().__init__()
        self.time = time
        self.name = name

    def island(self):
        return extra_data.TIMER_MOBS.get(self.name, "Other")


class ItemDrop(DictEquals):
    name = None
    reporter = None
    timestamp = None
    uuid = None

    def __init__(self, name, reporter, timestamp, uuid=None):
        self.name = name
        self.reporter = reporter
        self.timestamp = timestamp
        self.uuid = uuid or str(uuid_lib.uuid4())
        if name in extra_data.EXTRA_ITEM_DATA:
            for key in extra_data.EXTRA_ITEM_DATA:
                if name.lower() == key.lower():
                    self.name = key

    def classes(self) -> str:
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name)
        if not extra_item_data:
            return ""
        classes = extra_item_data.get('classes', [])
        return ', '.join(classes)

    def droppable(self) -> str:
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name)
        if not extra_item_data:
            return ""
        nodrop = extra_item_data.get('nodrop', False)
        return "NO" if nodrop else "Yes"

    def min_dkp(self) -> int:
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name, {})
        return extra_item_data.get('min_dkp', config.MIN_DKP)

    def __str__(self):
        return "{name} ({reporter} @ {time})".format(
            name=self.name, reporter=self.reporter, time=self.timestamp)


class Auction(DictEquals):
    item = None
    complete = None

    def __init__(self, item: ItemDrop, complete=False):
        self.item = item
        self.complete = complete

    def add(self, number: int, player: str) -> bool:
        raise NotImplementedError()

    def highest(self) -> list:
        raise NotImplementedError()

    def bid_text(self) -> str:
        raise NotImplementedError()

    def win_text(self) -> str:
        raise NotImplementedError()

    def highest_number(self) -> str:
        highest = self.highest()
        number = "None"
        if highest:
            number = highest[0][1]
        return number

    def highest_players(self) -> str:
        players = []
        for one in self.highest():
            players.append(one[0])
        players = ', '.join(players)
        return players or "None"

    def name(self) -> str:
        return self.item.name

    def classes(self) -> str:
        return self.item.classes()

    def droppable(self) -> str:
        return self.item.droppable()

    def get_target_min(self) -> str:
        return getattr(self, 'number',
                       getattr(self, 'min_dkp', config.MIN_DKP))


class DKPAuction(Auction):
    bids = None
    min_dkp = None
    alliance = None

    def __init__(self, item: ItemDrop, alliance: str, bids=None,
                 min_dkp=None, **kwargs):
        super().__init__(item, **kwargs)
        self.alliance = alliance
        if bids:
            self.bids = {int(bid): name for bid, name in bids.items()}
        else:
            self.bids = dict()
        self.min_dkp = min_dkp or self.item.min_dkp()

    def add(self, number: int, player: str) -> bool:
        if not number:
            # Not a real bid
            LOG.info("%s attempted to bid for %s but didn't post a number",
                     player, self.item)
            return False
        if number < self.min_dkp:
            # Bid too low
            LOG.info("%s attempted to bid for %s but bid too low: %d < %d",
                     player, self.item, number, self.min_dkp)
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

    def highest(self) -> list:
        if not self.bids:
            LOG.info("No bids yet for %s", self.item)
            return list()
        bid = max(self.bids)
        bidder = self.bids[bid]
        return [(bidder, bid)]  # noqa

    def bid_text(self) -> str:
        current_bid = self.highest_number()
        classes = ' ({})'.format(self.classes()) if self.classes() else ""
        if current_bid != 'None':
            bid_message = (
                "/shout [{item}]{classes} - `{alliance}` BID IN SHOUT. "
                "You MUST include the item name in your bid! Currently: "
                "`{player}` with {number} DKP - Closing Soon! ").format(
                player=self.highest_players(),
                item=self.item.name, alliance=self.alliance,
                number=current_bid, classes=classes)
        else:
            bid_message = (
                "/shout [{item}]{classes} - `{alliance}` BID IN SHOUT, "
                "MIN {min} DKP. "
                "You MUST include the item name in your bid! ").format(
                item=self.item.name, alliance=self.alliance,
                min=self.get_target_min(), classes=classes)
        return bid_message

    def win_text(self) -> str:
        return "/shout Grats {player} on [{item}] ({number} DKP)!".format(
            player=self.highest_players(), number=self.highest_number(),
            item=self.item.name)


def get_next_number():
    number = config.NUMBERS[config.LAST_NUMBER % len(config.NUMBERS)]
    config.LAST_NUMBER += 1
    return number


class RandomAuction(Auction):
    rolls = None
    number = None

    def __init__(self, item: ItemDrop, rolls=None, number=None, **kwargs):
        super().__init__(item, **kwargs)
        self.rolls = rolls or dict()
        self.number = number or get_next_number()

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

    def highest(self) -> list:
        if not self.rolls:
            LOG.info("No rolls yet for %s", self.item)
            return list()
        high = max(self.rolls.values())
        rollers = [(player, roll) for player, roll in self.rolls.items()
                   if roll == high]
        return rollers

    def bid_text(self) -> str:
        classes = ' ({})'.format(self.classes()) if self.classes() else ""
        return "/shout [{item}]{classes} ROLL {number} NOW!".format(
            item=self.item.name, number=self.number, classes=classes)
        # TODO: alliance

    def win_text(self) -> str:
        return ("/shout Grats {player} on [{item}] with {roll} / {target}!"
                .format(player=self.highest_players(), item=self.item.name,
                        roll=self.highest_number(), target=self.number))


EVT_DROP = wx.NewId()
EVT_BID = wx.NewId()
EVT_WHO = wx.NewId()
EVT_CLEAR_WHO = wx.NewId()
EVT_WHO_HISTORY = wx.NewId()
EVT_WHO_END = wx.NewId()
EVT_KILL = wx.NewId()
EVT_APP_CLEAR = wx.NewId()
EVT_IGNORE = wx.NewId()


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


class WhoHistoryEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_WHO_HISTORY)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class WhoEndEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_WHO_END)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class KillEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_KILL)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class AppClearEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_APP_CLEAR)

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class IgnoreEvent(wx.PyEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_IGNORE)

    def __eq__(self, other):
        return isinstance(other, self.__class__)
