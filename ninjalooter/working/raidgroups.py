import random
import math





class Player():
    name = None
    pclass = None
    level = None
    guild = None

    def __init__(self, name, pclass=None, level=None, guild=""):
        self.name = name
        self.pclass = pclass
        self.level = level
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


class Group():
    
    def __init__(self):
        self.player_list = []
        self.max_group_score = 0

    def __repr__(self):
        rv = ''
        for p in self.player_list:
            rv += p.name + '/'
        rv += '{}'.format(self.max_group_score)
        return rv


class Raid():

    def __init__(self):
        self.group_list = []




#
# Group Builder
#
#

class GroupBuilder:

    def __init__(self):
        self.MAX_SLOT               = 100   # score for having a slot filled with an exact match
        self.MIN_SLOT               = 10    # score for having a slot filled with anyone
        self.LEVEL_PENALTY          = 15    # per level less than 60
        self.CLASS_PENALTY          = 50    # penalty if not an exact class match but using a substitute class

        self.INITIAL_ANNEAL_TEMP    = 1500.0
        self.COOLING_RATE           = 0.95
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


    #
    # test a group score against the ideal target group makeup
    #   - War, War
    #   - Shaman w/ Torpor
    #   - Bard
    #   - Ench
    #   - Any
    #
    def main_tank_group_score(self, group):

        # running group score as positions are filled
        group_score = 0

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
                if not self.is_war(p):
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
            group_score += player_score
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
            group_score += player_score
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
            group_score += player_score
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
            group_score += player_score
            available_list.remove(player)

        # add scores for remaining group members - we get at least a few points for having someone in a slot, rather than an empty slot
        # however, try to avoid duplicates of the classes already added
        for p in available_list:
            if (not self.is_tank(p)) and (not self.is_priest(p)) and (not self.is_bard(p)) and (not self.is_enchanter(p)):
                group_score += self.MIN_SLOT

        # return the sum of the player scores, as matched against the ideal group
        return group_score





    def cleric_group(self):
        pass

    def puller_group(self):
        pass

    def general_group(self):
        pass


    #
    # use simulated annealing to generate groups from the passed list of Player objects
    #
    def build_groups_sa(self, master_player_list):


        random.shuffle(master_player_list)
        player_count = len(master_player_list)

        groups_needed = math.ceil(player_count/6)



        temp = 1.0 * self.INITIAL_ANNEAL_TEMP

        current_score = -999
        converged = False

        # get group storage set up - foo
        self.the_raid.group_list.append(Group())
        self.the_raid.group_list.append(Group())

        while not converged:


            accepted_moves = 0

            # do 'INNER_LOOP_X * player_count' random moves and see how many result in improvements
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


                # foo - figure out how to do multiple groups here

                ndx = 0
                for gg in self.the_raid.group_list:
                    gg.player_list.clear()

                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1
                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1
                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1
                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1
                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1
                    gg.player_list.append(master_player_list[ndx])
                    ndx += 1



                g1_score = self.main_tank_group_score(self.the_raid.group_list[0])
                g2_score = self.main_tank_group_score(self.the_raid.group_list[1])
                new_score = g1_score + g2_score

                # in this case, higher scores = better
                chance = math.exp(-1.0 * abs((new_score - current_score))/temp)
                rv = random.random()

                # always accept an improved score
                if new_score > current_score:
                    current_score = new_score
                    accepted_moves += 1
                    self.the_raid.group_list[0].max_group_score = g1_score
                    self.the_raid.group_list[1].max_group_score = g2_score
                # maybe accept a degraded score, depending on simulated annealing tempterature
                elif (new_score < current_score) and (rv < chance):
                    current_score = new_score
                    accepted_moves += 1
                    self.the_raid.group_list[0].max_group_score = g1_score
                    self.the_raid.group_list[1].max_group_score = g2_score
                # if we aren't going to accept the move, then undo it
                else:
                    pp = master_player_list[to_pos]
                    master_player_list[to_pos] = master_player_list[from_pos]
                    master_player_list[from_pos] = pp

                loop_count -= 1

            # continue these loops until the inner loops of random moves generates no accepted moves
            if accepted_moves == 0:
                converged = True
            else:
                # cool the system a bit, then loop again
                temp *= self.COOLING_RATE

        # foo - figure out how to communicate results
        print('----------------------------')
        print(self.the_raid.group_list[0])
        print(self.the_raid.group_list[1])
        print('{}, {}, {}'.format(current_score, self.the_raid.group_list[0].max_group_score, self.the_raid.group_list[1].max_group_score))
        return current_score



def main():


    master_player_dict = {}


    master_player_dict['War60a']    = Player('War60a', 'Warrior', 60, 'fow')
    master_player_dict['War60b']    = Player('War60b', 'Warrior', 60, 'fow')
    master_player_dict['War59a']    = Player('War59a', 'Warrior', 59, 'fow')
    master_player_dict['War59b']    = Player('War59b', 'Warrior', 59, 'fow')
#    master_player_dict['War60c']    = Player('War60c', 'Warrior', 60, 'fow')
#    master_player_dict['War60d']    = Player('War60d', 'Warrior', 60, 'fow')

    master_player_dict['Pal60']     = Player('Pal60', 'Paladin', 60, 'fow')
    master_player_dict['Shd60']     = Player('Shd60', 'Shadow Knight', 60, 'fow')

    master_player_dict['Enc60']     = Player('Enc60', 'Enchanter', 60, 'fow')
    master_player_dict['Enc59']     = Player('Enc59', 'Enchanter', 59, 'fow')
    master_player_dict['Enc58']     = Player('Enc58', 'Enchanter', 58, 'fow')
#    master_player_dict['Enc60b']     = Player('Enc60b', 'Enchanter', 60, 'fow')
    master_player_dict['Mag60']     = Player('Mag60', 'Magician', 60, 'fow')
    master_player_dict['Nec60']     = Player('Nec60', 'Necromancer', 60, 'fow')
    master_player_dict['Wiz60']     = Player('Wiz60', 'Wizard', 60, 'fow')

    master_player_dict['Clr60']     = Player('Clr60', 'Cleric', 60, 'fow')
    master_player_dict['Dru60']     = Player('Dru60', 'Druid', 60, 'fow')
    master_player_dict['Shm60']     = Player('Shm60', 'Shaman', 60, 'fow')
    master_player_dict['Shm60torp'] = Player('Shm60torp', 'Shaman', 60, 'fow')    # foo - how do we show this shaman as having torpor
    master_player_dict['Shm59']     = Player('Shm59', 'Shaman', 59, 'fow')

    master_player_dict['Brd60']     = Player('Brd60', 'Bard', 60, 'fow')
    master_player_dict['Brd59']     = Player('Brd59', 'Bard', 59, 'fow')
    master_player_dict['Brd57']     = Player('Brd57', 'Bard', 57, 'fow')
#    master_player_dict['Brd60b']     = Player('Brd60b', 'Bard', 60, 'fow')
    master_player_dict['Mnk60']     = Player('Mnk60', 'Monk', 60, 'fow')
    master_player_dict['Rng60']     = Player('Rng60', 'Ranger', 60, 'fow')
    master_player_dict['Rog60']     = Player('Rog60', 'Rogue', 60, 'fow')


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
#    gb.main_tank_group_score(gg)
#    print(gg)



    # list of all players
    master_player_list = list(master_player_dict.values())
    x = gb.build_groups_sa(master_player_list)

#    gg3 = Group()
#    gg3.player_list.append(master_player_dict['Brd59'])
#    gg3.player_list.append(master_player_dict['Wiz60'])
#    gg3.player_list.append(master_player_dict['Shm60torp'])
#    gg3.player_list.append(master_player_dict['War59b'])
#    gg3.player_list.append(master_player_dict['Enc60'])
#    gg3.player_list.append(master_player_dict['War59a'])
#
#    gb.main_tank_group_score(gg3)
#    print(gg3)




if __name__ == '__main__':
    main()


