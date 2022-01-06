import random
import math

from models import Player






#class Player():
#    name = None
#    pclass = None
#    level = None
#    guild = None
#
#    def __init__(self, name, pclass=None, level=None, guild=""):
#        self.name = name
#        self.pclass = pclass
#        self.level = level
#        self.guild = guild
#
#    def __repr__(self):
#        return (
#            "Player({name}, pclass={pclass}, level={level}, guild={guild})"
#            .format(name=f"'{self.name}'",
#                    pclass=f"'{self.pclass}'" if self.pclass else "None",
#                    level=f"'{self.level}'" if self.level else "None",
#                    guild=f"'{self.guild}'" if self.guild else "None"))
#
#    def __str__(self):
#        return self.__repr__()


class Group():
    
    def __init__(self, group_type = 'General'):
        self.group_type         = group_type
        self.player_list        = []
        self.group_score        = 0
        self.max_group_score    = 0

    def __repr__(self):
        rv = '{:<10} ({}): '.format(self.group_type, len(self.player_list))
        for p in self.player_list:
            rv += p.name + '/'
        rv += '{}'.format(self.max_group_score)
        return rv


class Raid():

    def __init__(self):
        self.group_list = []

    def add_empty_groups(self, player_count):

        full_groups_needed = math.floor(player_count/6)
        total_groups_needed = math.ceil(player_count/6)

        self.group_list.clear()

        # partial group needed?
        if total_groups_needed > full_groups_needed:
            self.group_list.append(Group('General'))
                               
        # 1-3 groups: All General
        if full_groups_needed == 1:
            self.group_list.append(Group('General'))
        if full_groups_needed == 2:
            self.group_list.append(Group('General'))
            self.group_list.append(Group('General'))
        if full_groups_needed == 3:
            self.group_list.append(Group('General'))
            self.group_list.append(Group('General'))
            self.group_list.append(Group('General'))

        # 4 groups: General, Tank, Cleric, Pull
        if full_groups_needed >= 4:
            self.group_list.append(Group('General'))
            self.group_list.append(Group('Tank'))
            self.group_list.append(Group('Cleric'))
            self.group_list.append(Group('Pull'))

        # 5 groups: General, Tank, Cleric, Pull, Tank
        if full_groups_needed >= 5:
            self.group_list.append(Group('Tank'))

        # 6 groups: General, Tank, Cleric, Pull, Tank, Cleric
        if full_groups_needed >= 6:
            self.group_list.append(Group('Cleric'))

        # 7+ groups: General, Tank, Cleric, Pull, Tank, Cleric, (n - 6) General
        if full_groups_needed >= 7:
            cnt = 7
            while cnt <= full_groups_needed:
                self.group_list.append(Group('General'))
                cnt += 1

    def __repr__(self):
        sort_order = {'Pull' : 0, 'Tank' : 1, 'Cleric' : 2, 'General' : 3}
        self.group_list.sort(key = lambda val:sort_order[val.group_type])
        rv = ''
        for gg in self.group_list:
            rv += '{}\n'.format(gg)
        return rv



#
# Group Builder
#
class GroupBuilder:

    def __init__(self):
        self.MAX_SLOT               = 100   # score for having a slot filled with an exact match
        self.MIN_SLOT               = 10    # score for having a slot filled with anyone
        self.LEVEL_PENALTY          = 15    # per level less than 60
        self.CLASS_PENALTY          = 50    # penalty if not an exact class match but using a substitute class
        self.GENERAL_PENALTY        = 0.7   # penalize scores of players in general groups, to encourage their placement in the specific-role groups

        self.INITIAL_ANNEAL_TEMP    = 1500.0
        self.COOLING_RATE           = 0.9
        self.INNER_LOOP_X           = 10

        self.the_raid               = Raid()


    # helper function - true if War, Pal, or SK
    def is_tank(self, player):
        rv = False
        if (player.pclass == 'Warrior') or (player.pclass == 'Paladin') or (player.pclass == 'Shadow Knight'):
            rv = True
        return rv

    # helper function - true if War
    def is_war(self, player):
        rv = False
        if (player.pclass == 'Warrior'):
            rv = True
        return rv

    # helper function - true if Pal, or SK
    def is_knight(self, player):
        rv = False
        if (player.pclass == 'Paladin') or (player.pclass == 'Shadow Knight'):
            rv = True
        return rv


    # helper function - true if priest
    def is_priest(self, player):
        rv = False
        if (player.pclass == 'Cleric') or (player.pclass == 'Druid') or (player.pclass == 'Shaman'):
            rv = True
        return rv

    # helper function - true if torp shaman
    # foo - need to differentiate between has_torp and not have
    def is_torp_shaman(self, player):
        rv = False
        has_torpor = True   # foo - does this player have torpor spell
        if (player.pclass == 'Shaman' and has_torpor):
            rv = True
        return rv

    # helper function - true if shaman
    def is_shaman(self, player):
        rv = False
        if (player.pclass == 'Shaman'):
            rv = True
        return rv

    # helper function - true if cleric
    def is_cleric(self, player):
        rv = False
        if (player.pclass == 'Cleric'):
            rv = True
        return rv

    # helper function - true if melee
    def is_melee(self, player):
        rv = False
        if (player.pclass == 'Bard') or (player.pclass == 'Monk') or (player.pclass == 'Ranger') or (player.pclass == 'Rogue'):
            rv = True
        return rv

    # helper function - true if bard
    def is_bard(self, player):
        rv = False
        if (player.pclass == 'Bard'):
            rv = True
        return rv

    # helper function - true if monk
    def is_monk(self, player):
        rv = False
        if (player.pclass == 'Monk'):
            rv = True
        return rv


    # helper function - true if caster
    def is_caster(self, player):
        rv = False
        if (player.pclass == 'Enchanter') or (player.pclass == 'Magician') or (player.pclass == 'Necromancer') or (player.pclass == 'Wizard'):
            rv = True
        return rv

    # helper function - true if Enchanter
    def is_enchanter(self, player):
        rv = False
        if (player.pclass == 'Enchanter'):
            rv = True
        return rv

    # helper function - true if necro
    def is_necromancer(self, player):
        rv = False
        if (player.pclass == 'Necromancer'):
            rv = True
        return rv

    # helper function - true if wizard
    def is_wizard(self, player):
        rv = False
        if (player.pclass == 'Wizard'):
            rv = True
        return rv

    # helper function - true if coth mage
    # foo - need to differentiate between has_coth and not have
    def is_coth_magician(self, player):
        rv = False
        has_coth = True   # foo - does this player have coth spell
        if (player.pclass == 'Magician' and has_coth):
            rv = True
        return rv



    # Tank group
    # generate a group score compared to ideal 'Tank' group makeup
    #   - War, War
    #   - Shaman w/ Torpor
    #   - Bard
    #   - Ench
    #   - Any
    #
    def tank_group_score(self, group):

        # running group score as positions are filled
        group.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = group.player_list.copy()

        #
        # find top 2 tanks
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if self.is_tank(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a warrior
                if self.is_knight(p):
                    player_score -= self.CLASS_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add scores for top two tanks to group score, and remove top two tanks from available_list
        target_count = len(sorted_target_list)
        if target_count > 2:
            target_count = 2

        while target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)
            target_count -= 1

        #
        # find torp shaman
        #
        target_list.clear()
        for p in available_list:
            if self.is_priest(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a torp shaman
                if not self.is_torp_shaman(p):
                    player_score -= self.CLASS_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        #
        # find bard
        #
        target_list.clear()
        for p in available_list:
            if self.is_bard(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        #
        # find ench
        #
        target_list.clear()
        for p in available_list:
            if self.is_enchanter(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove top target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        # add scores for remaining group members - we get at least a few points for having someone in a slot, rather than an empty slot
        # however, try to avoid duplicates of the classes already added
        for p in available_list:
            if (not self.is_tank(p)) and (not self.is_priest(p)) and (not self.is_bard(p)) and (not self.is_enchanter(p)):
                group.group_score += self.MIN_SLOT

        # return the sum of the player scores, as matched against the ideal group
        return group.group_score



    # Cleric group
    # generate a group score compared to ideal 'Cleric' group makeup
    #   - Cleric x5
    #   - Bard (or maybe necro)
    #
    def cleric_group_score(self, group):
        # running group score as positions are filled
        group.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = group.player_list.copy()

        #
        # find top 5 clerics
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if self.is_priest(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a cleric
                if not self.is_cleric(p):
                    player_score -= self.CLASS_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add scores for top two tanks to group score, and remove top two tanks from available_list
        target_count = len(sorted_target_list)
        if target_count > 5:
            target_count = 5

        while target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)
            target_count -= 1


        #
        # find bard, or possibly necro
        #
        target_list.clear()
        for p in available_list:
            if self.is_bard(p) or self.is_necromancer(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # penalty points if not a torp shaman
                if not self.is_bard(p):
                    player_score -= self.CLASS_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        # return the sum of the player scores, as matched against the ideal group
        return group.group_score



    # Pull group
    # generate a group score compared to ideal 'Pull' group makeup
    #   - Monk x3
    #   - Mage w/ COTH
    #   - Wiz
    #   - Priest
    #
    def pull_group_score(self, group):

        # running group score as positions are filled
        group.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = group.player_list.copy()

        #
        # find top 3 monks
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if self.is_monk(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add scores for top two tanks to group score, and remove top two tanks from available_list
        target_count = len(sorted_target_list)
        if target_count > 3:
            target_count = 3

        while target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)
            target_count -= 1

        #
        # find coth mage
        #
        target_list.clear()
        for p in available_list:
            if self.is_coth_magician(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        #
        # find wizard
        #
        target_list.clear()
        for p in available_list:
            if self.is_wizard(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)



        #
        # find priest
        #
        target_list.clear()
        for p in available_list:
            if self.is_priest(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        # return the sum of the player scores, as matched against the ideal group
        return group.group_score



    # General group
    # generate a group score compared to ideal 'General' group makeup
    #     - Priest
    #     - Tank
    #     - Slower (Enc or Shm)
    #     - 3x other
    #
    def general_group_score(self, group):

        # running group score as positions are filled
        group.group_score = 0

        # keep track of whether a player has been used/counted
        available_list = group.player_list.copy()

        #
        # find priest
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if self.is_priest(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        #
        # find a tank
        #
        target_list = []  # list of (score, Player object) tuples
        for p in available_list:
            if self.is_tank(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to target list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)

        #
        # find a slower
        #
        target_list.clear()
        for p in available_list:
            if self.is_shaman(p) or self.is_enchanter(p):
                # start with top score
                player_score = self.MAX_SLOT

                # penalty points for level < 60
                player_score -= (60 - p.level) * self.LEVEL_PENALTY

                # add to list
                target_list.append((player_score, p))

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)

        # add score for top target to group score, and remove target from available_list
        target_count = len(sorted_target_list)
        if target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group.group_score += player_score
            available_list.remove(player)


        # add scores for remaining group members - we get at least a few points for having someone in a slot, rather than an empty slot
        # however, try to avoid duplicates of the classes already added
        for p in available_list:
            if (not self.is_priest(p)) and (not self.is_tank(p)) and (not self.is_shaman(p)) and (not self.is_enchanter(p)):
                group.group_score += self.MIN_SLOT

        # penalize scores for players in General groups compared to the other more specific groups, to encourage their placement in specific groups
        group.group_score = round(group.group_score * self.GENERAL_PENALTY)

        # return the sum of the player scores, as matched against the ideal group
        return group.group_score


    #
    # use simulated annealing to generate groups from the passed list of Player objects
    #
    def build_groups_sa(self, master_player_list):

        # start by shuffling the input, just for good measure
        random.shuffle(master_player_list)

        # how many groups are needed?  get them created and added to the_raid
        player_count = len(master_player_list)
        self.the_raid.add_empty_groups(player_count)

        # initial conditions for SA iteration
        temp = 1.0 * self.INITIAL_ANNEAL_TEMP
        current_score = -999

        # SA iteration outer loop_count
        converged = False
        while not converged:

            # do 'INNER_LOOP_X * player_count' random moves and see how many result in improvements
            accepted_moves = 0
            loop_count = self.INNER_LOOP_X * player_count
            while loop_count > 0:

                # swap two random players
                from_pos = random.randrange(player_count)

                # ensure from/to aren't the same position
                to_pos = from_pos
                while to_pos == from_pos:
                    to_pos = random.randrange(player_count)

                # do the swap
                pp = master_player_list[to_pos]
                master_player_list[to_pos] = master_player_list[from_pos]
                master_player_list[from_pos] = pp

                # fill the groups with the revised player list
                player_ndx = 0
                group_ndx = 0
                gg = None
                while player_ndx < player_count:

                    # use mod function to know when to get next group
                    if (player_ndx % 6) == 0:
                        gg = self.the_raid.group_list[group_ndx]
                        gg.player_list.clear()
                        group_ndx += 1

                    gg.player_list.append(master_player_list[player_ndx])
                    player_ndx += 1

                # get group score depending on what template type is being requested
                for gg in self.the_raid.group_list:
                    if gg.group_type == 'Tank':
                        self.tank_group_score(gg)
                    elif gg.group_type == 'Cleric':
                        self.cleric_group_score(gg)
                    elif gg.group_type == 'Pull':
                        self.pull_group_score(gg)
                    elif gg.group_type == 'General':
                        self.general_group_score(gg)


                # what is score of new combination
                new_score = 0
                for gg in self.the_raid.group_list:
                    new_score += gg.group_score

                # in this case, higher scores = better
                chance = math.exp(-1.0 * abs((new_score - current_score))/temp)
                rv = random.random()

                # always accept an improved score
                if new_score > current_score:
                    current_score = new_score
                    accepted_moves += 1
                    for gg in self.the_raid.group_list:
                        gg.max_group_score = gg.group_score


                # maybe accept a degraded score, depending on simulated annealing tempterature
                elif (new_score < current_score) and (rv < chance):
                    current_score = new_score
                    accepted_moves += 1
                    for gg in self.the_raid.group_list:
                        gg.max_group_score = gg.group_score

                # if we aren't going to accept the swap, then undo it
                else:
                    pp = master_player_list[to_pos]
                    master_player_list[to_pos] = master_player_list[from_pos]
                    master_player_list[from_pos] = pp

                # inner loop counter
                loop_count -= 1

            # continue these loops until the inner loops of random moves generates no accepted moves
            if accepted_moves == 0:
                converged = True
            else:
                # cool the system a bit, then loop again
                temp *= self.COOLING_RATE

        return current_score



def main():


    master_player_dict = {}


    master_player_dict['War60a']    = Player('War60a', 'Warrior', 60, 'fow')
    master_player_dict['War60b']    = Player('War60b', 'Warrior', 60, 'fow')
    master_player_dict['War59a']    = Player('War59a', 'Warrior', 59, 'fow')
    master_player_dict['War59b']    = Player('War59b', 'Warrior', 59, 'fow')

    master_player_dict['Pal60']     = Player('Pal60', 'Paladin', 60, 'fow')
    master_player_dict['Shd60']     = Player('Shd60', 'Shadow Knight', 60, 'fow')

    master_player_dict['Enc60']     = Player('Enc60', 'Enchanter', 60, 'fow')
    master_player_dict['Enc59']     = Player('Enc59', 'Enchanter', 59, 'fow')
    master_player_dict['Enc58']     = Player('Enc58', 'Enchanter', 58, 'fow')
    master_player_dict['Mag60']     = Player('Mag60', 'Magician', 60, 'fow')
    master_player_dict['Nec60']     = Player('Nec60', 'Necromancer', 60, 'fow')
    master_player_dict['Wiz60']     = Player('Wiz60', 'Wizard', 60, 'fow')

    master_player_dict['Clr60']     = Player('Clr60', 'Cleric', 60, 'fow')
    master_player_dict['Dru60']     = Player('Dru60', 'Druid', 60, 'fow')
    master_player_dict['Shm60']     = Player('Shm60', 'Shaman', 60, 'fow')
    master_player_dict['Shm60torp'] = Player('Shm60torp', 'Shaman', 60, 'fow')
    master_player_dict['Shm59']     = Player('Shm59', 'Shaman', 59, 'fow')

    master_player_dict['Brd60']     = Player('Brd60', 'Bard', 60, 'fow')
    master_player_dict['Brd59']     = Player('Brd59', 'Bard', 59, 'fow')
    master_player_dict['Brd57']     = Player('Brd57', 'Bard', 57, 'fow')
    master_player_dict['Mnk60']     = Player('Mnk60', 'Monk', 60, 'fow')
    master_player_dict['Rng60']     = Player('Rng60', 'Ranger', 60, 'fow')
    master_player_dict['Rog60']     = Player('Rog60', 'Rogue', 60, 'fow')


    master_player_dict['xWar60a']    = Player('xWar60a', 'Warrior', 60, 'fow')
    master_player_dict['xWar60b']    = Player('xWar60b', 'Warrior', 60, 'fow')
    master_player_dict['xWar59a']    = Player('xWar59a', 'Warrior', 59, 'fow')
    master_player_dict['xWar59b']    = Player('xWar59b', 'Warrior', 59, 'fow')
                                                
    master_player_dict['xPal60']     = Player('xPal60', 'Paladin', 60, 'fow')
    master_player_dict['xShd60']     = Player('xShd60', 'Shadow Knight', 60, 'fow')
                                                
    master_player_dict['xEnc60']     = Player('xEnc60', 'Enchanter', 60, 'fow')
    master_player_dict['xEnc59']     = Player('xEnc59', 'Enchanter', 59, 'fow')
    master_player_dict['xEnc58']     = Player('xEnc58', 'Enchanter', 58, 'fow')
    master_player_dict['xMag60']     = Player('xMag60', 'Magician', 60, 'fow')
    master_player_dict['xNec60']     = Player('xNec60', 'Necromancer', 60, 'fow')
    master_player_dict['xWiz60']     = Player('xWiz60', 'Wizard', 60, 'fow')
                                                
    master_player_dict['xClr60']     = Player('xClr60', 'Cleric', 60, 'fow')
    master_player_dict['xDru60']     = Player('xDru60', 'Druid', 60, 'fow')
    master_player_dict['xShm60']     = Player('xShm60', 'Shaman', 60, 'fow')
    master_player_dict['xShm60torp'] = Player('xShm60torp', 'Shaman', 60, 'fow')
    master_player_dict['xShm59']     = Player('xShm59', 'Shaman', 59, 'fow')
                                                
    master_player_dict['xBrd60']     = Player('xBrd60', 'Bard', 60, 'fow')
    master_player_dict['xBrd59']     = Player('xBrd59', 'Bard', 59, 'fow')
    master_player_dict['xBrd57']     = Player('xBrd57', 'Bard', 57, 'fow')
    master_player_dict['xMnk60']     = Player('xMnk60', 'Monk', 60, 'fow')
    master_player_dict['xRng60']     = Player('xRng60', 'Ranger', 60, 'fow')
    master_player_dict['xRog60']     = Player('xRog60', 'Rogue', 60, 'fow')


    master_player_dict['aClr60']     = Player('aClr60', 'Cleric', 60, 'fow')
    master_player_dict['bClr60']     = Player('bClr60', 'Cleric', 60, 'fow')
    master_player_dict['cClr60']     = Player('cClr60', 'Cleric', 60, 'fow')
    master_player_dict['dClr60']     = Player('dClr60', 'Cleric', 60, 'fow')
    master_player_dict['eClr60']     = Player('eClr60', 'Cleric', 60, 'fow')
    master_player_dict['fClr60']     = Player('fClr60', 'Cleric', 60, 'fow')
    master_player_dict['gClr60']     = Player('gClr60', 'Cleric', 60, 'fow')
    master_player_dict['hClr60']     = Player('hClr60', 'Cleric', 60, 'fow')
    master_player_dict['iClr60']     = Player('iClr60', 'Cleric', 60, 'fow')
    master_player_dict['jClr60']     = Player('jClr60', 'Cleric', 60, 'fow')


    print(len(master_player_dict))

    # test the GroupBuilder
    gb = GroupBuilder()


#    print(master_player_dict)

#    # build a test group.  Just for testing, allow the list to exceed 6
#    gg = Group()
#    gg.player_list.append(master_player_dict['Brd60'])
#    gg.player_list.append(master_player_dict['Enc60'])
#    gg.player_list.append(master_player_dict['War59b'])
#    gg.player_list.append(master_player_dict['Pal60'])
#    gg.player_list.append(master_player_dict['War60a'])
#    gg.player_list.append(master_player_dict['Shd60'])
#    gg.player_list.append(master_player_dict['War59a'])
#    gg.player_list.append(master_player_dict['Shm60torp'])
#    gg.player_list.append(master_player_dict['Dru60'])
#    gg.player_list.append(master_player_dict['War60b'])
#
#    print(gg)
#
#    # test group builder
#    gb.tank_group_score(gg)
#    print(gg)



    # list of all players
    master_player_list = list(master_player_dict.values())
    x = gb.build_groups_sa(master_player_list)

    print('----------------------------')
    print(gb.the_raid)
    print(x)


#    gg3 = Group()
#    gg3.player_list.append(master_player_dict['Brd59'])
#    gg3.player_list.append(master_player_dict['Wiz60'])
#    gg3.player_list.append(master_player_dict['Shm60torp'])
#    gg3.player_list.append(master_player_dict['War59b'])
#    gg3.player_list.append(master_player_dict['Enc60'])
#    gg3.player_list.append(master_player_dict['War59a'])
#
#    gb.tank_group_score(gg3)
#    print(gg3)




if __name__ == '__main__':
    main()


