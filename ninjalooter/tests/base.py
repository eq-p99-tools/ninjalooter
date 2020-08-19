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
[Sun Aug 16 22:46:32 2020] Players Looking For Groups:
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
[Sun Aug 16 22:46:32 2020] [50 Monk] Peter (Human) <Venerate>
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Paul (Gnome) <Kingdom>
[Sun Aug 16 22:46:32 2020] [50 Bard] Mary (Half Elf) <Black Lotus>
[Sun Aug 16 22:46:32 2020] [50 Magician] Rad (Gnome) <Venerate>
[Sun Aug 16 22:46:32 2020] [50 Wizard] Dad (Erudite) <Venerate>
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Had (Dark Elf) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Necromancer] Mad (Gnome) <Kingdom>
[Sun Aug 16 22:46:32 2020] [ANONYMOUS] Bad  <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Shadow Knight] Tad (Troll) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Wizard] Gad (High Elf) <Venerate> LFG
[Sun Aug 16 22:46:32 2020] [50 Druid] Wad (Dark Elf) <Black Lotus> LFG
[Sun Aug 16 22:46:32 2020] [50 Wizard] Pad (Dark Elf) <Castle> LFG
[Sun Aug 16 22:46:32 2020] There are 24 players in Plane of Sky.
"""


class NLTestBase(unittest.TestCase):
    pass
