import unittest
from unittest import mock

from ninjalooter import config
from ninjalooter import models

SAMPLE_ALLIANCES = {
    'BL': ('Black Lotus',),
    'Kingdom': ('Kingdom', 'Karens of Karana'),
    'Seal Team': ('Seal Team',),
    'VCR': ('Venerate', 'Castle', 'Reconstructed', 'Force of Will'),
}
SAMPLE_ALLIANCE_MAP = dict()
for alliance, guilds in SAMPLE_ALLIANCES.items():
    for guild in guilds:
        SAMPLE_ALLIANCE_MAP[guild] = alliance

SAMPLE_LAST_WHO_SNAPSHOT = {
    # 6 VC
    'Bill': models.Player('Bill', None, None, 'Reconstructed'),
    'Ted': models.Player('Ted', None, None, 'Castle'),
    'James': models.Player('James', None, None, 'Castle'),
    'John': models.Player('John', None, None, 'Venerate'),
    'Fred': models.Player('Fred', None, None, 'Venerate'),
    'Gail': models.Player('Gail', None, None, 'Venerate'),
    # 4 BL
    'Tim': models.Player('Tim', None, None, 'Black Lotus'),
    'Tom': models.Player('Tom', None, None, 'Black Lotus'),
    'Jim': models.Player('Jim', None, None, 'Black Lotus'),
    'Han': models.Player('Han', None, None, 'Black Lotus'),
    # 5 Kingdom
    'Joe': models.Player('Joe', None, None, 'Kingdom'),
    'Jill': models.Player('Jill', None, None, 'Kingdom'),
    'Peter': models.Player('Peter', None, None, 'Kingdom'),
    'Paul': models.Player('Paul', None, None, 'Kingdom'),
    'Mary': models.Player('Mary', None, None, 'Kingdom'),
    # 1 Daniel (but WHY?)
    'Dan': models.Player('Dan', None, None, 'Dial a Daniel'),
}

SAMPLE_ATTENDANCE_LOGS = """
[Sun Aug 16 22:46:32 2020] Players on EverQuest:
[Sun Aug 16 22:46:32 2020] ---------------------------
[Sun Aug 16 22:46:32 2020] [50 Warrior] Bill (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [50 Druid] Tom (Wood Elf) <Seal Team> LFG
[Sun Aug 16 22:46:32 2020] [50 Magician] Fred (Gnome) LFG
[Sun Aug 16 22:46:32 2020] [50 Necromancer] George (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [50 Cleric] Tim (Dark Elf) <Seal Team> LFG
[Sun Aug 16 22:46:32 2020]  AFK [49 Magician] Karen (Gnome) <Karens of Karana>
[Sun Aug 16 22:46:32 2020] [50 Wizard] Jim (Erudite) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Ron (Gnome) <Seal Team> LFG
[Sun Aug 16 22:46:32 2020] [50 Warrior] Gob (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Hob (Gnome) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [50 Rogue] Mob (Dark Elf) <Kingdom> LFG
[Sun Aug 16 22:46:32 2020] [49 Enchanter] Dob (Dark Elf) <Kingdom>
[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Peter (Human)
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Paul (Gnome) <Kingdom>
[Sun Aug 16 22:46:32 2020] [50 Bard] Mary (Half Elf) <Black Lotus>
[Sun Aug 16 22:46:32 2020] [50 Magician] Rad (Gnome) <Venerate>
[Sun Aug 16 22:46:32 2020] [50 Shadow Knight] Dad (Erudite) <Venerate>
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Had (Dark Elf) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Mad (Gnome) <Kingdom>
[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Bad  <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Shadow Knight] Tad (Troll) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Wizard] Loltest (High Elf) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Druid] Wad (Dark Elf) <Black Lotus> LFG
[Sun Aug 16 22:46:32 2020] [50 Wizard] Pad (Dark Elf) <Castle> LFG
[Sun Aug 16 22:46:32 2020]  <LINKDEAD>[60 Arch Mage] Ogey (Gnome) <Venerate>
[Sun Aug 16 22:46:32 2020] There are 25 players in Plane of Sky.
"""

SAMPLE_OOC_DROP = """
[Mon Aug 17 07:15:36 2020] Dob begins to walk faster.
[Mon Aug 17 07:15:39 2020] Peter says out of character, 'Belt of Iniquity, Copper Disc'
[Mon Aug 17 07:15:42 2020] Mary says, 'Hail, Paul'
[Mon Aug 17 07:15:58 2020] Paul says, 'lfg'
[Mon Aug 17 07:16:05 2020] Tim shouts, 'looted Miniature Sword'
"""  # noqa

SAMPLE_AUC_BID = """
[Sun Aug 16 17:41:25 2020] You auction, 'Belt of Iniquity 10 DKP MIN'
[Mon Aug 17 07:15:39 2020] Tad auctions, 'Belt of Iniquity 10'
[Mon Aug 17 07:15:39 2020] Paul auctions, 'Belt of Iniquity 15'
[Mon Aug 17 07:15:39 2020] Dad auctions, 'Belt of Iniquity 11'
[Mon Aug 17 07:15:39 2020] Tad auctions, 'Belt of Iniquity 16'
[Mon Aug 17 07:15:39 2020] Ron auctions, 'Belt of Iniquity 20'
[Mon Aug 17 07:15:39 2020] Pad auctions, 'Copper Disc 1'
"""

SAMPLE_KILL_TIMES = """
[Sun Aug 16 17:41:25 2020] an azarack has been slain by Peter!
[Sun Aug 16 17:42:44 2020] a shimmering meteor has been slain by Paul!
[Sun Aug 16 17:42:44 2020] a soul carrier has been slain by Mary!
"""

SAMPLE_FULL_TEST = SAMPLE_ATTENDANCE_LOGS + SAMPLE_OOC_DROP + SAMPLE_AUC_BID

SAMPLE_GSHEETS_TEXT = (
    'Era,Zone,Boss,Item,Minimum,Restrictions,Notes\r\n'
    'Classic,Permafrost,Lady Vox,White Wolf-hide Girdle,10,,\r\n'
    'Classic,Permafrost,Lady Vox,White Dragon Scales,100,,epic\r\n'
    'Test,Nowhere,Noone,My Item,,"BRD, CLR",no dkp min\r\n'
)
SAMPLE_GSHEETS_DATA = [
    {'Era': 'Classic',
     'Zone': 'Permafrost',
     'Boss': 'Lady Vox',
     'Item': 'White Wolf-hide Girdle',
     'Minimum': '10',
     'Restrictions': '',
     'Notes': ''},
    {'Era': 'Classic',
     'Zone': 'Permafrost',
     'Boss': 'Lady Vox',
     'Item': 'White Dragon Scales',
     'Minimum': '100',
     'Restrictions': '',
     'Notes': 'epic'},
    {'Era': 'Test',
     'Zone': 'Nowhere',
     'Boss': 'Noone',
     'Item': 'My Item',
     'Minimum': '',
     'Restrictions': 'BRD, CLR',
     'Notes': 'no dkp min'},
]
SAMPLE_GSHEETS_MINDKP_JSON = {
     'My Item': {'classes': ['BRD', 'CLR'], 'min_dkp': 1},
     'White Dragon Scales': {'min_dkp': 100},
     'White Wolf-hide Girdle': {'min_dkp': 10}
}


class NLTestBase(unittest.TestCase):
    def setUp(self) -> None:
        super(NLTestBase, self).setUp()
        config.AUDIO_ALERTS = False
        config.ALLIANCES = SAMPLE_ALLIANCES
        config.ALLIANCE_MAP = SAMPLE_ALLIANCE_MAP

        thread_patcher1 = mock.patch('threading.Timer')
        thread_patcher1.start()
        self.addCleanup(thread_patcher1.stop)

        self.mock_playsound = mock.Mock()
        sound_patcher = mock.patch('playsound.playsound', self.mock_playsound)
        sound_patcher.start()
        self.addCleanup(sound_patcher.stop)
