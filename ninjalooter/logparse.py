from ninjalooter import config
from ninjalooter import message_handlers
from ninjalooter import models
from ninjalooter import utils

LOG_MATCHERS = {
    config.MATCH_WHO: message_handlers.handle_who,
    config.MATCH_OOC: message_handlers.handle_ooc,
    config.MATCH_AUC: message_handlers.handle_auc,
}


def start_auction_dkp(item):
    auc = models.DKPAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item] = auc


def start_auction_random(item):
    auc = models.RandomAuction(item)
    config.PENDING_AUCTIONS.remove(item)
    config.ACTIVE_AUCTIONS[item] = auc


def match_line(line) -> tuple:
    for matcher in LOG_MATCHERS:
        match = matcher.match(line)
        if match:
            return LOG_MATCHERS[matcher](match)
    # Nothing matched, not a useful line
    return tuple()


def parse_logfile(logfile):
    utils.setup_aho()

    with open(logfile, 'r') as lfp:
        for line in lfp.readline():
            result = match_line(line)
            if result:
                print("Handled line")
            else:
                print("Line ignored")
