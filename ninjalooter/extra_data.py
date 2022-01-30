# pylint: disable=too-many-lines
import json
import pydicti

from ninjalooter import config
from ninjalooter import constants
from ninjalooter import logger

LOG = logger.getLogger(__name__)

TIMER_MOBS = {
    "a thunder spirit": 1,
    "a thunder spirit princess": 1,
    "an azarack": 2,
    "a gorgalask": 3,
    "a crystalline cloud": 3,
    "a gust of wind": 3,
    "a shimmering meteor": 3,
    "an avenging gazer": 3,
    "heart harpie": 3,
    "a watchful guard": 3,
    "a spirited harpie": 3,
    "Gorgalosk": 3,
    "a soul carrier": 4,
    "an essence harvester": 4,
    "Keeper of Souls": 4,
    "a spiroc vanquisher": 5,
    "The Spiroc Guardian": 5,
    "The Spiroc Lord": 5,
    "Bzzazzt": 6,
    "Bazzzazzt": 6,
    "Bizazzt": 6,
    "Bzzzt": 6,
    "Bazzt Zzzt": 6,
    "a heartsbane drake": 7,
    "a fatestealer drake": 7,
    "a windrider drake": 7,
    "a greater sphinx": 7,
    "undine spirit": 7,
    "Sister of the Spire": 7,
    "Eye of Veeshan": 8,
    "Noble Dojorn": 1.5,
    "a blade storm": 1.5,
    "Overseer of Air": 4,
    "the Hand of Veeshan": 8,
}

CLASS_TITLES = {
    # Bard
    "Minstrel": constants.BARD,
    "Troubadour": constants.BARD,
    "Virtuoso": constants.BARD,
    # Cleric
    "Vicar": constants.CLERIC,
    "Templar": constants.CLERIC,
    "High Priest": constants.CLERIC,
    # Druid
    "Wanderer": constants.DRUID,
    "Preserver": constants.DRUID,
    "Hierophant": constants.DRUID,
    # Enchanter
    "Illusionist": constants.ENCHANTER,
    "Beguiler": constants.ENCHANTER,
    "Phantasmist": constants.ENCHANTER,
    # Magician
    "Elementalist": constants.MAGICIAN,
    "Conjurer": constants.MAGICIAN,
    "Arch Mage": constants.MAGICIAN,
    # Monk
    "Disciple": constants.MONK,
    "Master": constants.MONK,
    "Grandmaster": constants.MONK,
    # Necromancer
    "Heretic": constants.NECROMANCER,
    "Defiler": constants.NECROMANCER,
    "Warlock": constants.NECROMANCER,
    # Paladin
    "Cavalier": constants.PALADIN,
    "Knight": constants.PALADIN,
    "Crusader": constants.PALADIN,
    # Ranger
    "Pathfinder": constants.RANGER,
    "Outrider": constants.RANGER,
    "Warder": constants.RANGER,
    # Rogue
    "Rake": constants.ROGUE,
    "Blackguard": constants.ROGUE,
    "Assassin": constants.ROGUE,
    # Shadow Knight
    "Reaver": constants.SHADOW_KNIGHT,
    "Revenant": constants.SHADOW_KNIGHT,
    "Grave Lord": constants.SHADOW_KNIGHT,
    # Shaman
    "Mystic": constants.SHAMAN,
    "Luminary": constants.SHAMAN,
    "Oracle": constants.SHAMAN,
    # Warrior
    "Champion": constants.WARRIOR,
    "Myrmidon": constants.WARRIOR,
    "Warlord": constants.WARRIOR,
    # Wizard
    "Channeler": constants.WIZARD,
    "Evoker": constants.WIZARD,
    "Sorcerer": constants.WIZARD,
}

EXTRA_ITEM_DATA = pydicti.Dicti({
    ############################
    # Plane of Sky Quest Items #
    ############################
    "Ochre Tessera": {
        "classes": ["BRD", "CLR"],
        "nodrop": False,
        # "min_dkp": 1,
    },
    "Songbird Statuette": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Light Woolen Mask": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Platinum Disc": {
        "classes": ["BRD", "SHM"],
        "nodrop": False,
    },
    "Music Box": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Light Woolen Mantle": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Phosphoric Globe": {
        "classes": ["BRD", "SHM"],
        "nodrop": False,
    },
    "Shimmering Diamond": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Crude Wooden Flute": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Imp Statuette": {
        "classes": ["BRD", "NEC"],
        "nodrop": False,
    },
    "Dull Stone": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Amulet of Woven Hair": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Saffron Spiroc Feather": {
        "classes": ["BRD", "CLR"],
        "nodrop": False,
    },
    "Adamantium Bands": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Glowing Diamond": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Efreeti War Horn": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Manna Nectar": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Nebulous Emerald": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Nebulous Diamond": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Efreeti War Spear": {
        "classes": ["BRD"],
        "nodrop": False,
    },
    "Sky Emerald": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Silver Hoop": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Gold Disc": {
        "classes": ["CLR", "MNK"],
        "nodrop": False,
    },
    "Dark Wood": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Small Shield": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Adumbrate Globe": {
        "classes": ["CLR", "MNK"],
        "nodrop": False,
    },
    "Faintly Glowing Diamond": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Shiny Pauldrons": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Spiroc Statuette": {
        "classes": ["CLR", "MNK"],
        "nodrop": False,
    },
    "Spiroc Healing Totem": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Silvered Spiroc Necklace": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Glowing Sapphire": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Djinni Aura": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Efreeti Mace": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Shimmering Topaz": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Mithril Bands": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "Efreeti Standard": {
        "classes": ["CLR"],
        "nodrop": False,
    },
    "Azure Tessera": {
        "classes": ["DRU", "WIZ"],
        "nodrop": False,
    },
    "Black Face Paint": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Worn Leather Mask": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Copper Disc": {
        "classes": ["DRU", "SHD"],
        "nodrop": False,
    },
    "Nature Walker's Sky Emerald": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Mantle of Woven Grass": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Diaphanous Globe": {
        "classes": ["DRU", "PAL", "SHD"],
        "nodrop": False,
    },
    "Hardened Clay": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Spiroc Battle Staff": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Efreeti Statuette": {
        "classes": ["DRU", "WIZ"],
        "nodrop": False,
    },
    "Wilder's Girdle": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Divine Honeycomb": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "White-tipped Spiroc Feather": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Ethereal Ruby": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Spiroc Elder's Totem": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Acidic Venom": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Lush Nectar": {
        "classes": ["DRU", "WIZ"],
        "nodrop": False,
    },
    "Fire Sky Ruby": {
        "classes": ["DRU-wt3", "SHM-wt12"],
        "nodrop": False,
    },
    "Storm Sky Opal": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Efreeti Scimitar": {
        "classes": ["DRU"],
        "nodrop": False,
    },
    "Crimson Tessera": {
        "classes": ["ENC", "MAG"],
        "nodrop": False,
    },
    "Darkstone Emerald": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Finely Woven Cloth Cord": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Silver Disc": {
        "classes": ["ENC", "NEC"],
        "nodrop": False,
    },
    "Bluish Stone": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Light Cloth Mantle": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Rugous Globe": {
        "classes": ["ENC", "NEC"],
        "nodrop": False,
    },
    "Sky Pearl": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Silken Mask": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Harpy Statuette": {
        "classes": ["ENC", "MAG"],
        "nodrop": False,
    },
    "Black Nebulous Sapphire": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Adamantium Earring": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Carmine Spiroc Feather": {
        "classes": ["ENC", "MAG"],
        "nodrop": False,
    },
    "Ganoric Poison": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Glowing Necklace": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Sweet Nectar": {
        "classes": ["ENC", "MAG"],
        "nodrop": False,
    },
    "Black Sky Diamond": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Large Sky Sapphire": {
        "classes": ["ENC", "WIZ"],
        "nodrop": True,
    },
    "Efreeti Wind Staff": {
        "classes": ["ENC"],
        "nodrop": False,
    },
    "Ethereal Sapphire": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Feathered Cape": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Iron Disc": {
        "classes": ["MAG", "WIZ"],
        "nodrop": False,
    },
    "Gem of Empowerment": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Ceramic Mask": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Hyaline Globe": {
        "classes": ["MAG", "WIZ"],
        "nodrop": False,
    },
    "Ivory Pendant": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Golden Coffer": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Finely Woven Cloth Amice": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Large Diamond": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Blood Sky Amethyst": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Golden Efreeti Ring": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Sphinx Crown": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Hazy Opal": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Efreeti Magi Staff": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Crown of Elemental Mastery": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Large Opal": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Djinni Stave": {
        "classes": ["MAG"],
        "nodrop": False,
    },
    "Verdant Tessera": {
        "classes": ["MNK", "NEC"],
        "nodrop": False,
    },
    "Finely Woven Gold Mesh": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Silken Strands": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Tiny Ruby": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Cracked Leather Eyepatch": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Shimmering Opal": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Dove Slippers": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Spiroc Talon": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Silken Wrap": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "White Spiroc Feather": {
        "classes": ["MNK", "NEC"],
        "nodrop": False,
    },
    "Ethereal Amethyst": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Brass Knuckles": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Nebulous Sapphire": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Aged Nectar": {
        "classes": ["MNK", "NEC"],
        "nodrop": False,
    },
    "Writ of Quellious": {
        "classes": ["MNK"],
        "nodrop": False,
    },
    "Tear of Quellious": {
        "classes": ["MNK"],
        "nodrop": True,
    },

    "Ebon Shard": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Griffon's Beak": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Spiroc Feathers": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Black Silk Cape": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Djinni Blood": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Fine Cloth Raiment": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Obsidian Amulet": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Pulsating Ruby": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Nebulous Ruby": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Ring of Veeshan": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Gorgon Head": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Glowing Black Pearl": {
        "classes": ["NEC"],
        "nodrop": False,
    },
    "Efreeti Great Staff": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Silvery Girdle": {
        "classes": ["PAL"],
        "nodrop": False,
    },
    "Ivory Sky Diamond": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Griffon Statuette": {
        "classes": ["PAL", "SHD"],
        "nodrop": False,
    },
    "Spiroc Peace Totem": {
        "classes": ["PAL"],
        "nodrop": False,
    },
    "Bixie Sword Blade": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Dark Spiroc Feather": {
        "classes": ["PAL", "SHD"],
        "nodrop": False,
    },
    "Ethereal Topaz": {
        "classes": ["PAL"],
        "nodrop": False,
    },
    "Sphinx Claw": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Dulcet Nectar": {
        "classes": ["PAL", "SHD"],
        "nodrop": False,
    },
    "Golden Hilt": {
        "classes": ["PAL"],
        "nodrop": False,
    },
    "Large Sky Diamond": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Efreeti Zweihander": {
        "classes": ["PAL"],
        "nodrop": False,
    },
    "Auburn Tessera": {
        "classes": ["RNG", "SHM"],
        "nodrop": False,
    },
    "Ysgaril Root": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Griffon Talon": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Mithril Disc": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Harpy Tongue": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Fine Velvet Cloak": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Gridelin Globe": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Dragon-hide Mantle": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Spiroc Earth Totem": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Djinni Statuette": {
        "classes": ["RNG", "SHM"],
        "nodrop": False,
    },
    "Spiroc Thunder Totem": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "White Gold Earring": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Emerald Spiroc Feather": {
        "classes": ["RNG", "SHM"],
        "nodrop": False,
    },
    "Bitter Honey": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Circlet of Brambles": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Efreeti Long Sword": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Thickened Nectar": {
        "classes": ["RNG", "SHM"],
        "nodrop": False,
    },
    "Sphinx Tallow": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Shimmering Pearl": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Efreeti War Bow": {
        "classes": ["RNG"],
        "nodrop": False,
    },
    "Ivory Tessera": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Gem of Invigoration": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Inlaid Choker": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Bronze Disc": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Red Face Paint": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Jester's Mask": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Pearlescent Globe": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Black Griffon Feather": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Spiroc Sky Totem": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Pegasus Statuette": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Prismatic Sphere": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Fine Wool Cloak": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Mottled Spiroc Feather": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Cracked Leather Belt": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Sphinxian Circlet": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Honeyed Nectar": {
        "classes": ["ROG", "WAR"],
        "nodrop": False,
    },
    "Bixie Stinger": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Lightning Rod": {
        "classes": ["ROG"],
        "nodrop": False,
    },
    "Bloodsky Sapphire": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Ebon Tessera": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Sphinx Eye Opal": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Finely Crafted Amulet": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Small Sapphire": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Silvery Ring": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Dried Leather": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Finely Woven Cloth Belt": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Blood Sky Emerald": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Rusted Pauldrons": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Obsidian Shard": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Efreeti War Shield": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Jar of Honey": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Sphinxian Ring": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Fae Pauldrons": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Large Sky Pearl": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Bloodstained Hilt": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Blood Sky Ruby": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Efreeti War Axe": {
        "classes": ["SHD"],
        "nodrop": False,
    },
    "Drake Fang": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Leather Cord": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Ethereal Amber": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Shimmering Amber": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Ceremonial Belt": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Sphinx Hide": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Light Damask Mantle": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Wooden Bands": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Corrosive Venom": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Efreeti War Club": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Bixie Essence": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    # The p99 wiki has this item using a backtick? Likely inaccurate?
    "Spiritualist's Ring": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    # Adding both because I don't know what it REALLY is in-game...
    "Spiritualist`s Ring": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Symbol of Veeshan": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Efreeti War Maul": {
        "classes": ["SHM"],
        "nodrop": False,
    },
    "Small Ruby": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Azure Ring": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Small Pick": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Stone Amulet": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Silver Mesh": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Spiroc Air Totem": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Spiroc Wind Totem": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Wind Tablet": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Efreeti Belt": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Virulent Poison": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Djinni War Blade": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Bottled Djinni": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Ethereal Emerald": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Efreeti Battle Axe": {
        "classes": ["WAR"],
        "nodrop": False,
    },
    "Augmentor's Gem": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Grey Damask Cloak": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "Ethereal Opal": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Woven Skull Cap": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "Sky Topaz": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "High Quality Raiment": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "Mithril Air Ring": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Box of Winds": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "White-Tipped Spiroc Feather": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Pulsating Sapphire": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Amethyst Amulet": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "Copper Air Band": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    "Efreeti War Staff": {
        "classes": ["WIZ"],
        "nodrop": False,
    },
    #####################
    # NOT QUEST RELATED #
    #####################
    "Belt of Concordance": {
        "classes": ["BRD"],
        "nodrop": True,
    },
    "Belt of Contention": {
        "classes": ["WAR"],
        "nodrop": True,
    },
    "Belt of Iniquity": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Belt of the Pine": {
        "classes": ["RNG"],
        "nodrop": True,
    },
    "Belt of Tranquility": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Belt of Transience": {
        "classes": ["ROG"],
        "nodrop": True,
    },
    "Belt of Virtue": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Blade of Abrogation": {
        "classes": ["SHD"],
        "nodrop": True,
    },
    "Bracelet of Cessation": {
        "classes": ["NEC"],
        "nodrop": True,
    },
    "Bracelet of Distortion": {
        "classes": ["WIZ"],
        "nodrop": True,
    },
    "Bracelet of Exertion": {
        "classes": ["MAG"],
        "nodrop": True,
    },
    "Bracelet of Quiescence": {
        "classes": ["ENC"],
        "nodrop": True,
    },
    "Stein of Flowing Ichor": {
        "classes": ["SHM"],
        "nodrop": True,
    },
    "Symbol of Marr": {
        "classes": ["PAL"],
        "nodrop": True,
    },
    "Treant Tear": {
        "classes": ["DRU"],
        "nodrop": True,
    },
    "Weight of the Gods": {
        "classes": ["CLR"],
        "nodrop": True,
    },
    "White Satin Gloves": {
        "classes": ["ALL"],
        "nodrop": True,
    },
    "Whitened Treant Fists": {
        "classes": ["MNK"],
        "nodrop": True,
    },
    "Spiroc Wingblade": {
        "classes": ["WAR", "RNG"],
        "nodrop": True,
    },
})

if config.MIN_DKP_SHEET_URL:
    from ninjalooter import utils
    data = utils.fetch_google_sheet_data(config.MIN_DKP_SHEET_URL)
    if data:
        mindkp_data = utils.translate_sheet_csv_to_mindkp_json(data)
        EXTRA_ITEM_DATA.update(mindkp_data)

try:
    with open('item_data.json') as extra_item_data:
        OVERRIDE_EXTRA_ITEM_DATA = pydicti.Dicti(json.load(extra_item_data))
    EXTRA_ITEM_DATA.update(OVERRIDE_EXTRA_ITEM_DATA)
except FileNotFoundError:
    pass
