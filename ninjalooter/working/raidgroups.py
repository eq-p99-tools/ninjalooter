





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

    def __repr__(self):
        rv = ''
        for p in self.player_list:
            rv += '\''
            rv += p.name + '\''
        return rv


class Raid():

    def __init__(self):
        self.group_list = []




#
# Group Scores
#
# Assigned as follows:
#

class GroupScore:

    def __init__(self):
        self.MAX_SLOT           = 100   # score for having a slot filled with an exact match
        self.MIN_SLOT           = 10    # score for having a slot filled with anyone
        self.LEVEL_PENALTY      = 10    # per level less than 60
        self.CLASS_PENALTY      = 50    # penalty if not an exact class match but using a substitute class


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

#        print('---')
#        print(available_list)

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

#        print(target_list)

        # sort target list to find highest-scoring targets
        sorted_target_list = sorted(target_list, key = lambda tuple:tuple[0], reverse = True)
#        print(sorted_target_list)

        # add scores for top two tanks to group score, and remove top two tanks from available_list
        target_count = len(sorted_target_list)
        if target_count > 2:
            target_count = 2

        while target_count > 0:
            (player_score, player) = sorted_target_list.pop(0)
            group_score += player_score
            available_list.remove(player)
            target_count -= 1

#        print(sorted_target_list)
#        print('---')
#        print(available_list)


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

#        print('---')
#        print(available_list)

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

#        print('---')
#        print(available_list)

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

#        print('---')
#        print(available_list)
#        print('---')
#        print(group.player_list)

        # add scores for remaining group members - we get at least a few points for having someone in a slot, rather than an empty slot
        group_score += len(available_list) * self.MIN_SLOT

        # return the sum of the player scores, as matched against the ideal group
        return group_score





    def cleric_group(self):
        pass

    def puller_group(self):
        pass

    def general_group(self):
        pass



def main():


    master_player_dict = {}


    master_player_dict['War60a']    = Player('War60a', 'Warrior', 60, 'fow')
    master_player_dict['War60b']    = Player('War60b', 'Warrior', 60, 'fow')
    master_player_dict['War59a']    = Player('War59a', 'Warrior', 59, 'fow')
    master_player_dict['War59b']    = Player('War59b', 'Warrior', 59, 'fow')

    master_player_dict['Pal60']     = Player('Pal60', 'Paladin', 60, 'fow')
    master_player_dict['Shd60']     = Player('Shd60', 'Shadow Knight', 60, 'fow')

    master_player_dict['Enc60']     = Player('Enc60', 'Enchanter', 60, 'fow')
    master_player_dict['Mag60']     = Player('Mag60', 'Magician', 60, 'fow')
    master_player_dict['Nec60']     = Player('Nec60', 'Necromancer', 60, 'fow')
    master_player_dict['Wiz60']     = Player('Wiz60', 'Wizard', 60, 'fow')

    master_player_dict['Clr60']     = Player('Clr60', 'Cleric', 60, 'fow')
    master_player_dict['Dru60']     = Player('Dru60', 'Druid', 60, 'fow')
    master_player_dict['Shm60']     = Player('Shm60', 'Shaman', 60, 'fow')
    master_player_dict['Shm60torp'] = Player('Shm60torp', 'Shaman', 60, 'fow')    # foo - how do we show this shaman as having torpor

    master_player_dict['Brd60']     = Player('Brd60', 'Bard', 60, 'fow')
    master_player_dict['Mnk60']     = Player('Mnk60', 'Monk', 60, 'fow')
    master_player_dict['Rng60']     = Player('Rng60', 'Ranger', 60, 'fow')
    master_player_dict['Rog60']     = Player('Rog60', 'Rogue', 60, 'fow')


    print(len(master_player_dict))
#    print(master_player_dict)

    # build a test group.  Just for testing, allow the list to exceed 6
    gg = Group()
    gg.player_list.append(master_player_dict['Brd60'])
    gg.player_list.append(master_player_dict['Enc60'])
    gg.player_list.append(master_player_dict['War59b'])
    gg.player_list.append(master_player_dict['Pal60'])
    gg.player_list.append(master_player_dict['War60a'])
    gg.player_list.append(master_player_dict['Shd60'])
    gg.player_list.append(master_player_dict['War59a'])
    gg.player_list.append(master_player_dict['Shm60torp'])
#    gg.player_list.append(master_player_dict['Dru60'])
    gg.player_list.append(master_player_dict['War60b'])

    print(gg)

    # test groupScore
    gs = GroupScore()
    x = gs.main_tank_group_score(gg)
    print(x)





if __name__ == '__main__':
    main()


