from ninjalooter import utils


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
            return False
        if not self.bids or number > max(self.bids):
            # Valid bid
            self.bids[number] = player
            return True
        # Bid isn't higher than existing bids
        return False

    def highest(self) -> iter:
        if not self.bids:
            return None
        return (self.bids[max(self.bids)],)  # noqa


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
            return False
        if player in self.rolls:
            # Player already rolled
            return False
        # Valid roll
        self.rolls[player] = number
        return True

    def highest(self) -> iter:
        if not self.rolls:
            return None
        high = max(self.rolls.values())
        rollers = (player for player, roll in self.rolls.items()
                   if roll == high)
        return rollers
