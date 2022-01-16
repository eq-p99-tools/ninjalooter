import random

from ninjalooter import constants as c
from ninjalooter import models
from ninjalooter.tests import base
from ninjalooter import raidgroups


class TestRaidgroups(base.NLTestBase):
    def setUp(self) -> None:
        self.master_player_dict = {
            'War60a': models.Player('War60a', c.WARRIOR, 60, 'FoW'),
            'War60b': models.Player('War60b', c.WARRIOR, 60, 'FoW'),
            'War59a': models.Player('War59a', c.WARRIOR, 59, 'FoW'),
            'War59b': models.Player('War59b', c.WARRIOR, 59, 'FoW'),
            'Pal60': models.Player('Pal60', c.PALADIN, 60, 'FoW'),
            'Shd60': models.Player('Shd60', c.SHADOW_KNIGHT, 60, 'FoW'),
            'Enc60': models.Player('Enc60', c.ENCHANTER, 60, 'FoW'),
            'Enc59': models.Player('Enc59', c.ENCHANTER, 59, 'FoW'),
            'Enc58': models.Player('Enc58', c.ENCHANTER, 58, 'FoW'),
            'Mag60': models.Player('Mag60', c.MAGICIAN, 60, 'FoW'),
            'Nec60': models.Player('Nec60', c.NECROMANCER, 60, 'FoW'),
            'Wiz60': models.Player('Wiz60', c.WIZARD, 60, 'FoW'),
            'Clr60': models.Player('Clr60', c.CLERIC, 60, 'FoW'),
            'Dru60': models.Player('Dru60', c.DRUID, 60, 'FoW'),
            'Shm60': models.Player('Shm60', c.SHAMAN, 60, 'FoW'),
            'Shm60torp': models.Player('Shm60torp', c.SHAMAN, 60, 'FoW'),
            'Shm59': models.Player('Shm59', c.SHAMAN, 59, 'FoW'),
            'Brd60': models.Player('Brd60', c.BARD, 60, 'FoW'),
            'Brd59': models.Player('Brd59', c.BARD, 59, 'FoW'),
            'Brd57': models.Player('Brd57', c.BARD, 57, 'FoW'),
            'Mnk60': models.Player('Mnk60', c.MONK, 60, 'FoW'),
            'Rng60': models.Player('Rng60', c.RANGER, 60, 'FoW'),
            'Rog60': models.Player('Rog60', c.ROGUE, 60, 'FoW'),
            'xWar60a': models.Player('xWar60a', c.WARRIOR, 60, 'FoW'),
            'xWar60b': models.Player('xWar60b', c.WARRIOR, 60, 'FoW'),
            'xWar59a': models.Player('xWar59a', c.WARRIOR, 59, 'FoW'),
            'xWar59b': models.Player('xWar59b', c.WARRIOR, 59, 'FoW'),
            'xPal60': models.Player('xPal60', c.PALADIN, 60, 'FoW'),
            'xShd60': models.Player('xShd60', c.SHADOW_KNIGHT, 60, 'FoW'),
            'xEnc60': models.Player('xEnc60', c.ENCHANTER, 60, 'FoW'),
            'xEnc59': models.Player('xEnc59', c.ENCHANTER, 59, 'FoW'),
            'xEnc58': models.Player('xEnc58', c.ENCHANTER, 58, 'FoW'),
            'xMag60': models.Player('xMag60', c.MAGICIAN, 60, 'FoW'),
            'xNec60': models.Player('xNec60', c.NECROMANCER, 60, 'FoW'),
            'xWiz60': models.Player('xWiz60', c.WIZARD, 60, 'FoW'),
            'xClr60': models.Player('xClr60', c.CLERIC, 60, 'FoW'),
            'xDru60': models.Player('xDru60', c.DRUID, 60, 'FoW'),
            'xShm60': models.Player('xShm60', c.SHAMAN, 60, 'FoW'),
            'xShm60torp': models.Player('xShm60torp', c.SHAMAN, 60, 'fw'),
            'xShm59': models.Player('xShm59', c.SHAMAN, 59, 'FoW'),
            'xBrd60': models.Player('xBrd60', c.BARD, 60, 'FoW'),
            'xBrd59': models.Player('xBrd59', c.BARD, 59, 'FoW'),
            'xBrd57': models.Player('xBrd57', c.BARD, 57, 'FoW'),
            'xMnk60': models.Player('xMnk60', c.MONK, 60, 'FoW'),
            'xRng60': models.Player('xRng60', c.RANGER, 60, 'FoW'),
            'xRog60': models.Player('xRog60', c.ROGUE, 60, 'FoW'),
            'aClr60': models.Player('aClr60', c.CLERIC, 60, 'FoW'),
            'bClr60': models.Player('bClr60', c.CLERIC, 60, 'FoW'),
            'cClr60': models.Player('cClr60', c.CLERIC, 60, 'FoW'),
            'dClr60': models.Player('dClr60', c.CLERIC, 60, 'FoW'),
            'eClr60': models.Player('eClr60', c.CLERIC, 60, 'FoW'),
            'fClr60': models.Player('fClr60', c.CLERIC, 60, 'FoW'),
            'gClr60': models.Player('gClr60', c.CLERIC, 60, 'FoW'),
            'hClr60': models.Player('hClr60', c.CLERIC, 60, 'FoW'),
            'iClr60': models.Player('iClr60', c.CLERIC, 60, 'FoW'),
            'jClr60': models.Player('jClr60', c.CLERIC, 60, 'FoW')
        }

        self.assertEqual(56, len(self.master_player_dict))

    def test_groupbuilder(self):
        gb = raidgroups.GroupBuilder()

        # list of all players
        master_player_list = list(self.master_player_dict.values())

        rand_state = random.getstate()
        # Test with a defined random seed so we can get predictable results
        expected_groups_1 = [
            ['Mag60', 'Mnk60', 'xMnk60', 'Wiz60', 'xDru60', 'xWar59b'],
            ['War60b', 'Enc60', 'Brd60', 'xWar60a', 'hClr60', 'xShm60'],
            ['War60a', 'xBrd60', 'xEnc60', 'Rng60', 'Shm60', 'xWar60b'],
            ['bClr60', 'aClr60', 'fClr60', 'iClr60', 'Brd59', 'Clr60'],
            ['gClr60', 'Rog60', 'xBrd59', 'eClr60', 'cClr60', 'jClr60'],
            ['xShm60torp', 'xBrd57', 'Enc59', 'Shd60', 'xMag60', 'xWar59a'],
            ['Nec60', 'dClr60', 'xNec60', 'xRng60', 'Pal60', 'Shm60torp'],
            ['xWiz60', 'War59a', 'xShm59', 'xEnc59', 'War59b', 'Enc58'],
            ['xShd60', 'xEnc58', 'Dru60', 'Brd57', 'xRog60', 'Shm59'],
            ['xClr60', 'xPal60']]

        random.seed(1)
        gb.build_groups(master_player_list)
        random.setstate(rand_state)

        generated_groups = []
        for group in gb.raid.groups:
            generated_groups.append([p.name for p in group.player_list])
        self.assertListEqual(expected_groups_1, generated_groups)

        # Test again with a different seed to ensure the results change
        expected_groups_2 = [
            ['Mnk60', 'Enc58', 'Mag60', 'xWiz60', 'xMnk60', 'xShm60torp'],
            ['Brd60', 'Nec60', 'xEnc60', 'xWar60b', 'War60a', 'Shm60'],
            ['Shm60torp', 'xBrd59', 'War60b', 'Rng60', 'Enc60', 'xWar60a'],
            ['xClr60', 'Clr60', 'dClr60', 'cClr60', 'Brd59', 'jClr60'],
            ['iClr60', 'gClr60', 'fClr60', 'eClr60', 'hClr60', 'xBrd60'],
            ['xWar59b', 'xRog60', 'xShm59', 'Dru60', 'Pal60', 'xRng60'],
            ['aClr60', 'xMag60', 'xBrd57', 'Shm59', 'xPal60', 'xEnc58'],
            ['xEnc59', 'xDru60', 'Wiz60', 'War59a', 'War59b', 'xShm60'],
            ['xWar59a', 'xShd60', 'xNec60', 'Rog60', 'Enc59', 'bClr60'],
            ['Shd60', 'Brd57']]

        random.seed(2)
        gb.build_groups(master_player_list)
        random.setstate(rand_state)

        generated_groups = []
        for group in gb.raid.groups:
            generated_groups.append([p.name for p in group.player_list])
        self.assertListEqual(expected_groups_2, generated_groups)
