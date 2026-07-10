from __future__ import annotations

from collections import defaultdict

from ninjalooter.models import Player

GUILDLESS_LABEL = "None"


def player_visible(player: Player, enabled_guilds: set[str]) -> bool:
    if player.guild:
        return player.guild in enabled_guilds
    return GUILDLESS_LABEL in enabled_guilds


def guilds_in_snapshot(snapshot: dict[str, Player]) -> set[str]:
    guilds: set[str] = set()
    for player in snapshot.values():
        if player.guild:
            guilds.add(player.guild)
        else:
            guilds.add(GUILDLESS_LABEL)
    return guilds


def group_players_by_class(
    snapshot: dict[str, Player], enabled_guilds: set[str]
) -> dict[str, list[Player]]:
    by_class: dict[str, list[Player]] = defaultdict(list)
    for player in snapshot.values():
        if player_visible(player, enabled_guilds):
            by_class[player.pclass or "Unknown"].append(player)
    return by_class


def total_filtered_count(by_class: dict[str, list[Player]]) -> int:
    return sum(len(players) for players in by_class.values())
