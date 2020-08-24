import unittest

SAMPLE_PLAYER_AFFILIATIONS = {
    # 6 VCR
    'Bill': 'Reconstructed',
    'Ted': 'Castle',
    'James': 'Castle',
    'John': 'Venerate',
    'Fred': 'Venerate',
    'Gail': 'Venerate',
    # 4 BL
    'Tim': 'Black Lotus',
    'Tom': 'Black Lotus',
    'Jim': 'Black Lotus',
    'Han': 'Black Lotus',
    # 5 Kingdom
    'Joe': 'Kingdom',
    'Jill': 'Kingdom',
    'Peter': 'Kingdom',
    'Paul': 'Kingdom',
    'Mary': 'Kingdom',
    # 1 Daniel (but WHY?)
    'Dan': 'Dial a Daniel',
}

SAMPLE_WHO_LOG = """
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
[Sun Aug 16 22:46:32 2020] There are 24 players in Plane of Sky.
"""

SAMPLE_OOC_DROP = """
[Mon Aug 17 07:15:36 2020] Dob begins to walk faster.
[Mon Aug 17 07:15:39 2020] Peter says out of character, 'Belt of Iniquity'
[Mon Aug 17 07:15:42 2020] Mary says, 'Hail, Paul'
[Mon Aug 17 07:15:58 2020] Paul says, 'lfg'
[Mon Aug 17 07:16:05 2020] Tim shouts, 'looted Miniature Sword'
"""

SAMPLE_AUC_BID = """
[Sun Aug 16 17:41:25 2020] You auction, 'Belt of Iniquity 10 DKP MIN'
[Mon Aug 17 07:15:39 2020] Tad auctions, 'Belt of Iniquity 10'
[Mon Aug 17 07:15:39 2020] Paul auctions, 'Belt of Iniquity 15'
[Mon Aug 17 07:15:39 2020] Dad auctions, 'Belt of Iniquity 11'
[Mon Aug 17 07:15:39 2020] Tad auctions, 'Belt of Iniquity 16'
[Mon Aug 17 07:15:39 2020] Ron auctions, 'Belt of Iniquity 20'
[Mon Aug 17 07:15:39 2020] Pad auctions, 'Copper Disc 1'
"""

SAMPLE_FULL_TEST = SAMPLE_WHO_LOG + SAMPLE_OOC_DROP + SAMPLE_AUC_BID


class NLTestBase(unittest.TestCase):
    pass
