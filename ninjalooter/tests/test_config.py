import collections

from ninjalooter import config
from ninjalooter.tests import base


class TestAllianceConfig(base.NLTestBase):
    def setUp(self):
        super().setUp()
        self._saved = {}
        for key in ("alliances", "extra_alliances", "default_alliance"):
            if config.CONF.has_option("default", key):
                self._saved[key] = config.CONF.get("default", key)
            else:
                self._saved[key] = None

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                if config.CONF.has_option("default", key):
                    config.CONF.remove_option("default", key)
            else:
                config.CONF.set("default", key, value)
        config.apply_alliance_config()
        super().tearDown()

    def test_shipped_text_round_trips(self):
        parsed = config.parse_alliances(config.DEFAULT_ALLIANCES_TEXT)
        self.assertEqual(config.DEFAULT_ALLIANCES_TEXT, config.format_alliances(parsed))
        self.assertEqual(["Good Guys", "Lineage", "Castle", "Kingdom"], list(parsed))
        self.assertIn("Ancient Blood", parsed["Castle"])

    def test_later_alliance_keeps_the_guild(self):
        base = config.parse_alliances("Castle:Castle,Ancient Blood")
        merged = config.merge_extra_alliances(base, "Ancient Blood:Ancient Blood")
        cleaned = config.effective_alliances(merged)

        self.assertEqual(["Castle"], cleaned["Castle"])
        self.assertEqual(["Ancient Blood"], cleaned["Ancient Blood"])

    def test_save_replaces_extra_alliances_with_one_list(self):
        config.CONF.set("default", "alliances", "Castle:Castle,Ancient Blood")
        config.CONF.set("default", "extra_alliances", "Ancient Blood:Ancient Blood")
        config.save_alliances(
            collections.OrderedDict(
                [
                    ("Castle", ["Castle"]),
                    ("Ancient Blood", ["Ancient Blood"]),
                ]
            ),
            persist=False,
        )

        self.assertFalse(config.CONF.has_option("default", "extra_alliances"))
        stored = config.CONF.get("default", "alliances")
        self.assertIn("Ancient Blood:Ancient Blood", stored)
        self.assertNotIn("Ancient Blood,", stored)
        self.assertEqual("Ancient Blood", config.ALLIANCE_MAP["Ancient Blood"])
        self.assertEqual("Castle", config.ALLIANCE_MAP["Castle"])

    def test_saving_the_shipped_list_clears_custom_settings(self):
        config.CONF.set("default", "alliances", "Castle:Castle")
        config.CONF.set("default", "extra_alliances", "Safe Space:Safe Space")
        config.save_alliances(config.shipped_alliances(), persist=False)

        self.assertFalse(config.CONF.has_option("default", "alliances"))
        self.assertFalse(config.CONF.has_option("default", "extra_alliances"))
        self.assertTrue(config.using_shipped_alliances())

    def test_reset_uses_the_version_list(self):
        config.CONF.set("default", "alliances", "Castle:Castle")
        config.CONF.set("default", "default_alliance", "Not A Real Alliance")
        config.reset_alliances(persist=False)

        self.assertFalse(config.CONF.has_option("default", "alliances"))
        self.assertTrue(config.using_shipped_alliances())
        self.assertEqual("Good Guys", config.DEFAULT_ALLIANCE)
        self.assertEqual("Good Guys", config.CONF.get("default", "default_alliance"))
