import random
import math

from models import Player
from models import Raid


#
# Group Builder
#
# Uses Simulated Annealing to search for an optimized match of (available
# raid classes) to (ideal raid groups and classes)
#
class GroupBuilder:

    def __init__(self):
        self.INITIAL_ANNEAL_TEMP = 1500.0
        self.COOLING_RATE = 0.9
        self.INNER_LOOP_X = 10

        self.the_raid = Raid()

    #
    # use simulated annealing to generate groups from the passed list of
    # Player objects
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

            # do 'INNER_LOOP_X * player_count' random moves and see how many
            # result in improvements
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

                # get group score depending on what template type is
                # being requested
                for gg in self.the_raid.group_list:
                    if gg.group_type == 'Tank':
                        gg.tank_score()
                    elif gg.group_type == 'Cleric':
                        gg.cleric_score()
                    elif gg.group_type == 'Pull':
                        gg.pull_score()
                    elif gg.group_type == 'General':
                        gg.general_score()

                # what is score of new combination
                new_score = 0
                for gg in self.the_raid.group_list:
                    new_score += gg.group_score

                # in this case, higher scores = better
                chance = math.exp(-1.0*abs((new_score-current_score))/temp)
                rv = random.random()

                # always accept an improved score
                if new_score > current_score:
                    current_score = new_score
                    accepted_moves += 1
                    for gg in self.the_raid.group_list:
                        gg.max_group_score = gg.group_score

                # maybe accept a degraded score, depending on simulated
                # annealing tempterature
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

            # continue these loops until the inner loops of random moves
            # generates no accepted moves
            if accepted_moves == 0:
                converged = True
            else:
                # cool the system a bit, then loop again
                temp *= self.COOLING_RATE

        return current_score


def main():
    master_player_dict = {}

    master_player_dict['War60a'] = Player('War60a', 'Warrior', 60, 'fow')
    master_player_dict['War60b'] = Player('War60b', 'Warrior', 60, 'fow')
    master_player_dict['War59a'] = Player('War59a', 'Warrior', 59, 'fow')
    master_player_dict['War59b'] = Player('War59b', 'Warrior', 59, 'fow')

    master_player_dict['Pal60'] = Player('Pal60', 'Paladin', 60, 'fow')
    master_player_dict['Shd60'] = Player('Shd60', 'Shadow Knight', 60, 'fow')

    master_player_dict['Enc60'] = Player('Enc60', 'Enchanter', 60, 'fow')
    master_player_dict['Enc59'] = Player('Enc59', 'Enchanter', 59, 'fow')
    master_player_dict['Enc58'] = Player('Enc58', 'Enchanter', 58, 'fow')
    master_player_dict['Mag60'] = Player('Mag60', 'Magician', 60, 'fow')
    master_player_dict['Nec60'] = Player('Nec60', 'Necromancer', 60, 'fow')
    master_player_dict['Wiz60'] = Player('Wiz60', 'Wizard', 60, 'fow')

    master_player_dict['Clr60'] = Player('Clr60', 'Cleric', 60, 'fow')
    master_player_dict['Dru60'] = Player('Dru60', 'Druid', 60, 'fow')
    master_player_dict['Shm60'] = Player('Shm60', 'Shaman', 60, 'fow')
    master_player_dict['Shm60torp'] = Player('Shm60torp', 'Shaman', 60, 'fow')
    master_player_dict['Shm59'] = Player('Shm59', 'Shaman', 59, 'fow')

    master_player_dict['Brd60'] = Player('Brd60', 'Bard', 60, 'fow')
    master_player_dict['Brd59'] = Player('Brd59', 'Bard', 59, 'fow')
    master_player_dict['Brd57'] = Player('Brd57', 'Bard', 57, 'fow')
    master_player_dict['Mnk60'] = Player('Mnk60', 'Monk', 60, 'fow')
    master_player_dict['Rng60'] = Player('Rng60', 'Ranger', 60, 'fow')
    master_player_dict['Rog60'] = Player('Rog60', 'Rogue', 60, 'fow')

    master_player_dict['xWar60a'] = Player('xWar60a', 'Warrior', 60, 'fow')
    master_player_dict['xWar60b'] = Player('xWar60b', 'Warrior', 60, 'fow')
    master_player_dict['xWar59a'] = Player('xWar59a', 'Warrior', 59, 'fow')
    master_player_dict['xWar59b'] = Player('xWar59b', 'Warrior', 59, 'fow')

    master_player_dict['xPal60'] = Player('xPal60', 'Paladin', 60, 'fow')
    master_player_dict['xShd60'] = Player('xShd60', 'Shadow Knight', 60, 'fow')

    master_player_dict['xEnc60'] = Player('xEnc60', 'Enchanter', 60, 'fow')
    master_player_dict['xEnc59'] = Player('xEnc59', 'Enchanter', 59, 'fow')
    master_player_dict['xEnc58'] = Player('xEnc58', 'Enchanter', 58, 'fow')
    master_player_dict['xMag60'] = Player('xMag60', 'Magician', 60, 'fow')
    master_player_dict['xNec60'] = Player('xNec60', 'Necromancer', 60, 'fow')
    master_player_dict['xWiz60'] = Player('xWiz60', 'Wizard', 60, 'fow')

    master_player_dict['xClr60'] = Player('xClr60', 'Cleric', 60, 'fow')
    master_player_dict['xDru60'] = Player('xDru60', 'Druid', 60, 'fow')
    master_player_dict['xShm60'] = Player('xShm60', 'Shaman', 60, 'fow')
    master_player_dict['xShm60torp'] = Player('xShm60torp', 'Shaman', 60, 'fw')
    master_player_dict['xShm59'] = Player('xShm59', 'Shaman', 59, 'fow')

    master_player_dict['xBrd60'] = Player('xBrd60', 'Bard', 60, 'fow')
    master_player_dict['xBrd59'] = Player('xBrd59', 'Bard', 59, 'fow')
    master_player_dict['xBrd57'] = Player('xBrd57', 'Bard', 57, 'fow')
    master_player_dict['xMnk60'] = Player('xMnk60', 'Monk', 60, 'fow')
    master_player_dict['xRng60'] = Player('xRng60', 'Ranger', 60, 'fow')
    master_player_dict['xRog60'] = Player('xRog60', 'Rogue', 60, 'fow')

    master_player_dict['aClr60'] = Player('aClr60', 'Cleric', 60, 'fow')
    master_player_dict['bClr60'] = Player('bClr60', 'Cleric', 60, 'fow')
    master_player_dict['cClr60'] = Player('cClr60', 'Cleric', 60, 'fow')
    master_player_dict['dClr60'] = Player('dClr60', 'Cleric', 60, 'fow')
    master_player_dict['eClr60'] = Player('eClr60', 'Cleric', 60, 'fow')
    master_player_dict['fClr60'] = Player('fClr60', 'Cleric', 60, 'fow')
    master_player_dict['gClr60'] = Player('gClr60', 'Cleric', 60, 'fow')
    master_player_dict['hClr60'] = Player('hClr60', 'Cleric', 60, 'fow')
    master_player_dict['iClr60'] = Player('iClr60', 'Cleric', 60, 'fow')
    master_player_dict['jClr60'] = Player('jClr60', 'Cleric', 60, 'fow')

    print(len(master_player_dict))

    # test the GroupBuilder
    gb = GroupBuilder()

    # list of all players
    master_player_list = list(master_player_dict.values())
    x = gb.build_groups_sa(master_player_list)

    print('----------------------------')
    print(gb.the_raid)
    print(x)


if __name__ == '__main__':
    main()
