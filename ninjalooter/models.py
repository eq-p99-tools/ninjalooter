from ninjalooter import logging
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class Auction:
    item = None
    player = None
    complete = False

    def __init__(self, item):
        self.item = item

    def add(self, number: int, player: str) -> bool:
        raise NotImplementedError()

    def highest(self) -> iter:
        raise NotImplementedError()


class DKPAuction(Auction):
    bids = None

    def __init__(self, item):
        super(DKPAuction, self).__init__(item)
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


class RandomAuction(Auction):
    item = None
    rolls = None

    def __init__(self, item):
        super(RandomAuction, self).__init__(item)
        self.item = item
        self.rolls = dict()
        self.number = utils.get_next_number()

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
