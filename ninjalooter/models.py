# pylint: disable=no-member,too-many-lines

from __future__ import annotations
import datetime
import math
import threading
import uuid as uuid_lib

import dateutil.parser
import wx

from ninjalooter import config
from ninjalooter import constants
from ninjalooter import extra_data
from ninjalooter import logger

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)


class DictEquals:
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        self_dict = {key: self.__dict__[key] for key in self.__dict__
                     if not key.startswith("_")}
        other_dict = {key: other.__dict__[key] for key in other.__dict__
                      if not key.startswith("_")}
        return self_dict == other_dict

    def to_json(self):
        json_dict = {key: self.__dict__[key] for key in self.__dict__
                     if not key.startswith("_")}
        return {
            'json_type': self.__class__.__name__,
            **json_dict
        }

    @classmethod
    def from_json(cls, **kwargs) -> DictEquals:
        return cls(**kwargs)


class Player(DictEquals):
    name = None
    pclass = None
    level = None
    guild = None

    def __init__(self, name, pclass=None, level=None, guild=""):
        self.name = name
        self.pclass = pclass
        try:
            self.level = int(level)
        except (ValueError, TypeError):
            self.level = 0
        self.guild = guild

    def __repr__(self):
        return (
            "Player({name}, pclass={pclass}, level={level}, guild={guild})"
            .format(name=f"'{self.name}'",
                    pclass=f"'{self.pclass}'" if self.pclass else "None",
                    level=f"'{self.level}'" if self.level else "None",
                    guild=f"'{self.guild}'" if self.guild else "None"))

    def __str__(self):
        return self.__repr__()

    # helper function - true if War, Pal, or SK
    def is_tank(self):
        return self.pclass in constants.TANKS

    # helper function - true if War
    def is_war(self):
        return self.pclass == constants.WARRIOR

    # helper function - true if Pal, or SK
    def is_knight(self):
        return self.pclass in constants.KNIGHTS

    # helper function - true if priest
    def is_priest(self):
        return self.pclass in constants.PRIESTS

    # helper function - true if torp shaman
    # todo - need to differentiate between has_torp and not have
    def is_torp_shaman(self):
        has_torpor = True  # fixme - does this player have torpor spell
        return self.pclass == constants.SHAMAN and has_torpor

    # helper function - true if shaman
    def is_shaman(self):
        return self.pclass == constants.SHAMAN

    # helper function - true if cleric
    def is_cleric(self):
        return self.pclass == constants.CLERIC

    # helper function - true if melee
    def is_melee(self):
        return self.pclass in constants.MELEE

    # helper function - true if bard
    def is_bard(self):
        return self.pclass == constants.BARD

    # helper function - true if monk
    def is_monk(self):
        return self.pclass == constants.MONK

    # helper function - true if caster
    def is_caster(self):
        return self.pclass in constants.CASTERS

    # helper function - true if Enchanter
    def is_enchanter(self):
        return self.pclass == constants.ENCHANTER

    # helper function - true if necro
    def is_necromancer(self):
        return self.pclass == constants.NECROMANCER

    # helper function - true if wizard
    def is_wizard(self):
        return self.pclass == constants.WIZARD

    # helper function - true if coth mage
    # todo - need to differentiate between has_coth and not have
    def is_coth_magician(self):
        has_coth = True  # fixme - does this player have coth spell
        return self.pclass == constants.MAGICIAN and has_coth


class Group(DictEquals):
    """Class to represent an EQ Group"""
    # info to support assigning a score to this group reflecting how
    # well it matches a target profile
    MAX_SLOT = 100  # slot filled with an exact match
    MIN_SLOT = 10  # slot filled with anyone
    LEVEL_PENALTY = 15  # per level less than 60
    CLASS_PENALTY = 50  # penalty if not an exact class match
    GENERAL_PENALTY = 0.7  # penalize scores of players in general

    def __init__(self, group_type=constants.GT_GENERAL):
        self.group_type = group_type
        self.player_list = []
        self.group_score = 0
        self.max_group_score = 0

    def __repr__(self):
        rv = '{:<10} Members: ({}): '.format(self.group_type,
                                             len(self.player_list))
        for p in self.player_list:
            rv += p.name + ', '
        rv += '(SA score: {})'.format(self.max_group_score)
        return rv

    def tank_score(self) -> int:
        """Tank group

        Generate a group score compared to ideal 'Tank' group makeup:
          - War, War
          - Shaman w/ Torpor
          - Bard
          - Enchanter
          - Any
        """
        # running group score as positions are filled
        self.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = self.player_list.copy()

        #
        # find top 2 tanks
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if p.is_tank():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a warrior
                if p.is_knight():
                    player_score -= self.CLASS_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add scores for top two tanks to group score, and remove top two
        # tanks from available_list
        target_count = min(len(sorted_target_list), 2)

        while target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)
            target_count -= 1

        #
        # find torp shaman
        #
        target_list.clear()
        for p in available_list:
            if p.is_priest():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a torp shaman
                if not p.is_torp_shaman():
                    player_score -= self.CLASS_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find bard
        #
        target_list.clear()
        for p in available_list:
            if p.is_bard():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target from
        # available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find ench
        #
        target_list.clear()
        for p in available_list:
            if p.is_enchanter():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove top target from
        # available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        # add scores for remaining group members - we get at least a few
        # points for having someone in a slot, rather than an empty slot
        # however, try to avoid duplicates of the classes already added
        for p in available_list:
            if not (p.is_tank() or p.is_priest() or
                    p.is_bard() or p.is_enchanter()):
                self.group_score += self.MIN_SLOT

        # return the sum of the player scores, as matched against the ideal
        return self.group_score

    def cleric_score(self) -> int:
        """Cleric group

        Generate a group score compared to ideal 'Cleric' group makeup
          - Cleric x5
          - Bard (or maybe Necromancer)
        """
        # running group score as positions are filled
        self.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = self.player_list.copy()

        #
        # find top 5 clerics
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if p.is_priest():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a cleric
                if not p.is_cleric():
                    player_score -= self.CLASS_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add scores for top two tanks to group score, and remove top five
        # clerics from available_list
        target_count = min(len(sorted_target_list), 5)

        while target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)
            target_count -= 1

        #
        # find bard, or possibly necro
        #
        target_list.clear()
        for p in available_list:
            if p.is_bard() or p.is_necromancer():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a torp shaman
                if not p.is_bard():
                    player_score -= self.CLASS_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        # return the sum of the player scores, as matched against the ideal
        return self.group_score

    def pull_score(self) -> int:
        """Pull group

        Generate a group score compared to ideal 'Pull' group makeup
          - Monk x3
          - Mage w/ COTH
          - Wiz
          - Priest
        """

        # running group score as positions are filled
        self.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = self.player_list.copy()

        #
        # find top 3 monks
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if p.is_monk():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add scores for top two tanks to group score, and remove top three
        # monks from available_list
        target_count = min(len(sorted_target_list), 3)

        while target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)
            target_count -= 1

        #
        # find coth mage
        #
        target_list.clear()
        for p in available_list:
            if p.is_coth_magician():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find wizard
        #
        target_list.clear()
        for p in available_list:
            if p.is_wizard():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find priest
        #
        target_list.clear()
        for p in available_list:
            if p.is_priest():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        # return the sum of the player scores, as matched against the ideal
        return self.group_score

    def general_score(self) -> int:
        """General group

        Generate a group score compared to ideal 'General' group makeup
          - Priest
          - Tank
          - Slower (Enchanter or Shaman)
          - 3x other
        """

        # running group score as positions are filled
        self.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = self.player_list.copy()

        #
        # find priest
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if p.is_priest():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find a tank
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if p.is_tank():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        #
        # find a slower
        #
        target_list.clear()
        for p in available_list:
            if p.is_shaman() or p.is_enchanter():
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list,
                                    key=lambda x: x[0],
                                    reverse=True)

        # add score for top target to group score, and remove target
        # from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            player_score, player = sorted_target_list.pop(0)
            self.group_score += player_score
            available_list.remove(player)

        # add scores for remaining group members - we get at least a few
        # points for having someone in a slot, rather than an empty slot
        # however, try to avoid duplicates of the classes already added
        for p in available_list:
            if not (p.is_priest() or p.is_tank() or
                    p.is_shaman() or p.is_enchanter()):
                self.group_score += self.MIN_SLOT

        # penalize scores for players in General groups compared to the
        # other more specific groups, to encourage their placement in
        # specific groups
        self.group_score = round(self.group_score * self.GENERAL_PENALTY)

        # return the sum of the player scores, as matched against the ideal
        return self.group_score


class Raid(DictEquals):
    """Class to represent an EQ raid. Contains multiple Groups.

    Also has the knowledge, given how many total raiders are available, about
    how many groups and what group types / profiles are desired.
    """

    def __init__(self):
        self.groups = []

    def add_empty_groups(self, player_count) -> None:

        full_groups_needed = math.floor(player_count / 6)
        total_groups_needed = math.ceil(player_count / 6)

        self.groups.clear()

        # partial group needed?
        if total_groups_needed > full_groups_needed:
            self.groups.append(Group(constants.GT_GENERAL))

        # 1-3 groups: All General
        if full_groups_needed == 1:
            self.groups.append(Group(constants.GT_GENERAL))
        if full_groups_needed == 2:
            self.groups.append(Group(constants.GT_GENERAL))
            self.groups.append(Group(constants.GT_GENERAL))
        if full_groups_needed == 3:
            self.groups.append(Group(constants.GT_GENERAL))
            self.groups.append(Group(constants.GT_GENERAL))
            self.groups.append(Group(constants.GT_GENERAL))

        # 4 groups: General, Tank, Cleric, Pull
        if full_groups_needed >= 4:
            self.groups.append(Group(constants.GT_GENERAL))
            self.groups.append(Group(constants.GT_TANK))
            self.groups.append(Group(constants.GT_CLERIC))
            self.groups.append(Group(constants.GT_PULL))

        # 5 groups: General, Tank, Cleric, Pull, Tank
        if full_groups_needed >= 5:
            self.groups.append(Group(constants.GT_TANK))

        # 6 groups: General, Tank, Cleric, Pull, Tank, Cleric
        if full_groups_needed >= 6:
            self.groups.append(Group(constants.GT_CLERIC))

        # 7+ groups: General, Tank, Cleric, Pull, Tank, Cleric, (n - 6) General
        if full_groups_needed >= 7:
            cnt = 7
            while cnt <= full_groups_needed:
                self.groups.append(Group(constants.GT_GENERAL))
                cnt += 1

        # now sort the groups into a sensible order
        sort_order = {constants.GT_PULL: 0,
                      constants.GT_TANK: 1,
                      constants.GT_CLERIC: 2,
                      constants.GT_GENERAL: 3}
        self.groups.sort(key=lambda val: sort_order[val.group_type])

    def __repr__(self):
        return '\n'.join([str(g) for g in self.groups])


class CredittLog(DictEquals):
    time = None
    user = None
    message = None
    raw_message = None

    def __init__(self, time, user, message, raw_message):
        self.time = time
        self.user = user
        self.message = message
        self.raw_message = raw_message

    def target(self) -> str:
        try:
            message_cleaned = (self.message.lower().split('creditt')[1]
                               .strip().capitalize())
        except:  # noqa
            message_cleaned = self.message
        return message_cleaned


class GratssLog(DictEquals):
    time = None
    user = None
    message = None
    raw_message = None

    def __init__(self, time, user, message, raw_message):
        self.time = time
        self.user = user
        self.message = message
        self.raw_message = raw_message

    def target(self) -> str:
        try:
            message_cleaned = (self.message.lower().split('gratss')[1]
                               .split(' ')[1].strip().capitalize())
        except:  # noqa
            message_cleaned = self.message
        return message_cleaned


class WhoLog(DictEquals):
    time = None
    log = None
    raidtick = False

    def __init__(self, time, log, raidtick=False):
        super().__init__()
        self.time = time
        self.log = log
        self.raidtick = raidtick

    def eqtime(self) -> str:
        return self.time.strftime("%a %b %d %H:%M:%S %Y")

    def raidtick_display(self):
        return "✔️" if self.raidtick else ""  # or "❌"?

    def populations(self):
        pops = {alliance: 0 for alliance in config.ALLIANCES}
        for player in self.log.values():
            alliance = config.ALLIANCE_MAP.get(player.guild)
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
        return str(extra_data.TIMER_MOBS.get(self.name, "Other"))


class ItemDrop(DictEquals):
    name = None
    reporter = None
    timestamp = None
    uuid = None
    min_dkp_override = None

    def __init__(self, name, reporter, timestamp, uuid=None,
                 min_dkp_override=None):
        self.name = name
        self.reporter = reporter
        self.timestamp = timestamp
        self.uuid = uuid or str(uuid_lib.uuid4())
        self.min_dkp_override = min_dkp_override
        if name in extra_data.EXTRA_ITEM_DATA:
            for key in extra_data.EXTRA_ITEM_DATA:
                if name.lower() == key.lower():
                    self.name = key

    def classes(self) -> str:
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name)
        if not extra_item_data:
            return ""
        classes = extra_item_data.get('classes', [])
        return ', '.join(map(lambda x: x.strip(), classes))

    def droppable(self) -> str:
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name)
        if not extra_item_data:
            return ""
        nodrop = extra_item_data.get('nodrop', False)
        return "NO" if nodrop else "Yes"

    def min_dkp(self) -> int:
        if self.min_dkp_override:
            return self.min_dkp_override
        extra_item_data = extra_data.EXTRA_ITEM_DATA.get(self.name, {})
        return extra_item_data.get('min_dkp', config.MIN_DKP)

    def __str__(self):
        return "{name} ({reporter} @ {time})".format(
            name=self.name, reporter=self.reporter, time=self.timestamp)


class Auction(DictEquals):
    item = None
    start_time = None
    _alert_timer = None

    def __init__(self, item: ItemDrop, start_time=None, **_):
        self.item = item
        if start_time:
            self.start_time = dateutil.parser.DEFAULTPARSER.parse(start_time)
        else:
            self.start_time = datetime.datetime.now()

        if self.time_remaining().seconds > 0:
            self._alert_timer = threading.Timer(
                self.time_remaining().seconds, self._do_alert)
            config.AUCTION_ALERT_TIMERS.append(self._alert_timer)
            self._alert_timer.start()

    def _do_alert(self):
        # import utils at runtime rather than on load to avoid circular error
        # pylint: disable=import-outside-toplevel
        from ninjalooter import utils
        utils.alert_message(
            "Auction Ending Soon",
            "The auction for '%s' is ending soon!" % self.item.name
        )
        config.AUCTION_ALERT_TIMERS.remove(self._alert_timer)
        utils.alert_sound(config.AUC_EXPIRING_SOUND)

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
        return players or ""

    def name(self) -> str:
        return self.item.name

    def classes(self) -> str:
        return self.item.classes()

    def droppable(self) -> str:
        return self.item.droppable()

    def get_target_min(self) -> str:
        return getattr(self, 'number',
                       getattr(self, 'min_dkp', config.MIN_DKP))

    def time_remaining(self) -> datetime.timedelta:
        elapsed = datetime.datetime.now() - self.start_time
        min_bid_time = datetime.timedelta(seconds=config.MIN_BID_TIME)
        return max(min_bid_time - elapsed, datetime.timedelta(0))

    def time_remaining_text(self) -> str:
        remaining = self.time_remaining()
        if remaining.seconds <= 30:
            return "a few moments"
        minutes = int(remaining.seconds / 60)
        seconds = remaining.seconds % 60
        if minutes:
            time_remaining = "{}m{:02d}s".format(minutes, seconds)
        else:
            time_remaining = "{}s".format(seconds)
        return time_remaining

    def cancel(self):
        if self._alert_timer:
            self._alert_timer.cancel()

    def complete(self):
        if self._alert_timer:
            self._alert_timer.cancel()


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
            LOG.debug("No bids yet for %s", self.item)
            return list()
        bid = max(self.bids)
        bidder = self.bids[bid]
        return [(bidder, bid)]  # noqa

    def bid_text(self) -> str:
        current_bid = self.highest_number()
        classes = ' ({})'.format(self.classes()) if self.classes() else ""
        if current_bid != 'None':
            try:
                bid_message = (
                    "/{channel} ~" + config.BID_MESSAGE_REMINDER
                ).format(
                    channel=config.PRIMARY_BID_CHANNEL.upper(),
                    player=self.highest_players(),
                    item=self.item.name,
                    number=current_bid,
                    min=self.get_target_min(), classes=classes,
                    time_remaining=self.time_remaining_text(),
                )
            except KeyError:
                bid_message = config.DEFAULT_BID_MESSAGE_REMINDER.format(
                    channel=config.PRIMARY_BID_CHANNEL.upper(),
                    player=self.highest_players(),
                    item=self.item.name,
                    number=current_bid,
                    min=self.get_target_min(), classes=classes,
                    time_remaining=self.time_remaining_text(),
                )
        else:
            try:
                bid_message = (
                    "/{channel} ~" + config.BID_MESSAGE_NEW
                ).format(
                    channel=config.PRIMARY_BID_CHANNEL.upper(),
                    player=None,
                    item=self.item.name,
                    number=None,
                    min=self.get_target_min(), classes=classes,
                    time_remaining=self.time_remaining_text(),
                )
            except KeyError:
                bid_message = config.DEFAULT_BID_MESSAGE_NEW.format(
                    channel=config.PRIMARY_BID_CHANNEL.upper(),
                    player=None,
                    item=self.item.name,
                    number=None,
                    min=self.get_target_min(), classes=classes,
                    time_remaining=self.time_remaining_text(),
                )
        return bid_message

    def win_text(self) -> str:
        player = self.highest_players()
        if not player:
            player = "ROT"
        dkp = self.highest_number()
        if dkp == "None":
            dkp = "0"
        try:
            grats_message = (
                "/{channel} ~" + config.GRATS_MESSAGE_BID
            ).format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                player=player, number=dkp,
                item=self.item.name
            )
        except KeyError:
            grats_message = config.DEFAULT_GRATS_MESSAGE_BID.format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                player=player, number=dkp,
                item=self.item.name
            )
        return grats_message


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
            LOG.debug("No rolls yet for %s", self.item)
            return list()
        high = max(self.rolls.values())
        rollers = [(player, roll) for player, roll in self.rolls.items()
                   if roll == high]
        return rollers

    def bid_text(self) -> str:
        classes = ' ({})'.format(self.classes()) if self.classes() else ""
        try:
            bid_text = (
                "/{channel} " + config.ROLL_MESSAGE
            ).format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                item=self.item.name, target=self.number, classes=classes
            )
        except KeyError:
            bid_text = config.DEFAULT_ROLL_MESSAGE.format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                item=self.item.name, target=self.number, classes=classes
            )
        return bid_text

    def win_text(self) -> str:
        player = self.highest_players()
        if player in ("None", ""):
            player = "ROT"
        roll = self.highest_number()
        if roll == "None":
            roll = "0"
        try:
            win_text = (
                "/{channel} " + config.GRATS_MESSAGE_ROLL
            ).format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                player=player, item=self.item.name,
                roll=roll, target=self.number
            )
        except KeyError:
            win_text = config.DEFAULT_GRATS_MESSAGE_ROLL.format(
                channel=config.PRIMARY_BID_CHANNEL.upper(),
                player=player, item=self.item.name,
                roll=roll, target=self.number
            )
        return win_text


EVT_DROP = wx.NewId()
EVT_BID = wx.NewId()
EVT_WHO = wx.NewId()
EVT_CLEAR_WHO = wx.NewId()
EVT_WHO_HISTORY = wx.NewId()
EVT_WHO_END = wx.NewId()
EVT_KILL = wx.NewId()
EVT_CREDITT = wx.NewId()
EVT_GRATSS = wx.NewId()
EVT_CALC_RAIDGROUPS = wx.NewId()
EVT_APP_CLEAR = wx.NewId()
EVT_IGNORE = wx.NewId()


class LogEvent(wx.PyEvent):
    def __eq__(self, other):
        return isinstance(other, self.__class__)


class DropEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_DROP)


class BidEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self, item):
        super().__init__()
        self.item = item
        self.SetEventType(EVT_BID)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.item == other.item


class WhoEvent(LogEvent):
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


class ClearWhoEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_CLEAR_WHO)


class WhoHistoryEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_WHO_HISTORY)


class WhoEndEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_WHO_END)


class KillEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_KILL)


class CredittEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_CREDITT)


class GratssEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_GRATSS)


class CalcRaidGroupsEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_CALC_RAIDGROUPS)


class AppClearEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_APP_CLEAR)


class IgnoreEvent(LogEvent):  # pylint: disable=too-few-public-methods
    def __init__(self):
        super().__init__()
        self.SetEventType(EVT_IGNORE)
