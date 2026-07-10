from ninjalooter import constants
from ninjalooter import raid_overview
from ninjalooter.models import Player
from ninjalooter.tests import base


def _snapshot(*players: Player) -> dict[str, Player]:
    return {player.name: player for player in players}


class TestRaidOverviewLogic(base.NLTestBase):
    def test_total_filtered_count_sums_all_classes(self):
        snapshot = _snapshot(
            Player("Tano", constants.WARRIOR, 60, "Castle"),
            Player("Eran", constants.WARRIOR, 60, "Castle"),
            Player("Eldar", constants.CLERIC, 60, "Castle"),
            Player("Moryn", constants.CLERIC, 60, "Kingdom"),
        )
        enabled = {"Castle", "Kingdom"}
        by_class = raid_overview.group_players_by_class(snapshot, enabled)

        self.assertEqual(raid_overview.total_filtered_count(by_class), 4)
        self.assertEqual(len(by_class[constants.WARRIOR]), 2)
        self.assertEqual(len(by_class[constants.CLERIC]), 2)

    def test_guild_filter_excludes_unchecked_guilds(self):
        snapshot = _snapshot(
            Player("Tano", constants.WARRIOR, 60, "Castle"),
            Player("Moryn", constants.CLERIC, 60, "Kingdom"),
        )
        by_class = raid_overview.group_players_by_class(snapshot, {"Castle"})

        self.assertEqual(raid_overview.total_filtered_count(by_class), 1)
        self.assertEqual(len(by_class[constants.WARRIOR]), 1)
        self.assertNotIn(constants.CLERIC, by_class)

    def test_castle_only_example_from_bug_report(self):
        snapshot = _snapshot(
            Player("Tano", constants.WARRIOR, 60, "Castle"),
            Player("Eran", constants.WARRIOR, 60, "Castle"),
            Player("Nathan", constants.WARRIOR, 60, "Castle"),
            Player("Arthur", constants.WARRIOR, 60, "Castle"),
            Player("Eldar", constants.CLERIC, 60, "Castle"),
            Player("Moryn", constants.CLERIC, 60, "Castle"),
            Player("Belen", constants.CLERIC, 60, "Castle"),
            Player("Thora", constants.CLERIC, 60, "Castle"),
            Player("Alaric", constants.CLERIC, 60, "Castle"),
            Player("Isadora", constants.CLERIC, 60, "Castle"),
            Player("Septimus", constants.CLERIC, 60, "Castle"),
        )
        by_class = raid_overview.group_players_by_class(snapshot, {"Castle"})
        total = raid_overview.total_filtered_count(by_class)

        self.assertEqual(total, 11)
        self.assertEqual(len(by_class[constants.WARRIOR]), 4)
        self.assertEqual(len(by_class[constants.CLERIC]), 7)

    def test_guildless_players_use_none_label(self):
        snapshot = _snapshot(
            Player("Anon", constants.ROGUE, 60, ""),
            Player("Member", constants.WARRIOR, 60, "Castle"),
        )

        self.assertEqual(
            raid_overview.guilds_in_snapshot(snapshot),
            {"None", "Castle"},
        )

    def test_guildless_players_visible_when_none_enabled(self):
        snapshot = _snapshot(
            Player("Anon", constants.ROGUE, 60, ""),
            Player("Member", constants.WARRIOR, 60, "Castle"),
        )
        by_class = raid_overview.group_players_by_class(
            snapshot, {raid_overview.GUILDLESS_LABEL}
        )

        self.assertEqual(raid_overview.total_filtered_count(by_class), 1)
        self.assertEqual(len(by_class[constants.ROGUE]), 1)

    def test_guildless_players_hidden_when_none_disabled(self):
        snapshot = _snapshot(Player("Anon", constants.ROGUE, 60, ""))
        by_class = raid_overview.group_players_by_class(snapshot, {"Castle"})

        self.assertEqual(raid_overview.total_filtered_count(by_class), 0)

    def test_empty_snapshot_has_zero_total(self):
        by_class = raid_overview.group_players_by_class({}, {"Castle"})

        self.assertEqual(raid_overview.total_filtered_count(by_class), 0)
