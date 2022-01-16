import random
import math

from ninjalooter import constants
from ninjalooter import models


class GroupBuilder:
    """Group Builder

    Uses Simulated Annealing to search for an optimized match of (available
    raid classes) to (ideal raid groups and classes)
    """
    def __init__(self):
        self.INITIAL_ANNEAL_TEMP = 1500.0
        self.COOLING_RATE = 0.9
        self.INNER_LOOP_X = 10

        self.raid = models.Raid()

    def build_groups(self, master_player_list) -> int:
        """Use simulated annealing to generate groups from the a player list

        :param master_player_list: a list of Player objects
        :type master_player_list: list(ninjalooter.models.Player)
        :return: the group's score
        """

        # start by shuffling the input, just for good measure
        random.shuffle(master_player_list)

        # how many groups are needed?  get them created and added to raid
        player_count = len(master_player_list)
        self.raid.add_empty_groups(player_count)

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
                        gg = self.raid.groups[group_ndx]
                        gg.player_list.clear()
                        group_ndx += 1

                    gg.player_list.append(master_player_list[player_ndx])
                    player_ndx += 1

                # get group score depending on what template type is
                # being requested
                for gg in self.raid.groups:
                    if gg.group_type == constants.GT_TANK:
                        gg.tank_score()
                    elif gg.group_type == constants.GT_CLERIC:
                        gg.cleric_score()
                    elif gg.group_type == constants.GT_PULL:
                        gg.pull_score()
                    elif gg.group_type == constants.GT_GENERAL:
                        gg.general_score()

                # what is score of new combination
                new_score = 0
                for gg in self.raid.groups:
                    new_score += gg.group_score

                # in this case, higher scores = better
                chance = math.exp(-1.0*abs((new_score-current_score))/temp)
                rv = random.random()

                # always accept an improved score
                if new_score > current_score:
                    current_score = new_score
                    accepted_moves += 1
                    for gg in self.raid.groups:
                        gg.max_group_score = gg.group_score

                # maybe accept a degraded score, depending on simulated
                # annealing tempterature
                elif (new_score < current_score) and (rv < chance):
                    current_score = new_score
                    accepted_moves += 1
                    for gg in self.raid.groups:
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
