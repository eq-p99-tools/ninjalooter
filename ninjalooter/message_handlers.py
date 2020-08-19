from ninjalooter import config


def handle_who(match):
    if not match:
        # No match was made, probably junk
        return
    name = match.group("name")
    guild = match.group("guild")
    pclass = match.group("class")
    if name not in config.PLAYER_AFFILIATIONS:
        config.PLAYER_AFFILIATIONS[name] = guild
    elif guild is not None or (guild is None and pclass != "ANONYMOUS"):
        config.PLAYER_AFFILIATIONS[name] = guild


def handle_ooc(match):
    if not match:
        # No match was made, probably junk
        return tuple()
    name = match.group("name")
    text = match.group("text")
    guild = config.PLAYER_AFFILIATIONS.get(name)
    if guild and guild not in config.ALLIANCE_MAP:
        # Some other guild is talking, discard line
        return tuple()

    # Handle text to return a list of items linked
    found_items = config.TREE.search_all(text)
    item_names = tuple(item[0] for item in found_items)
    for item in item_names:
        config.PENDING_AUCTIONS.append(item)
    return item_names


def handle_auc(match) -> bool:
    if not match:
        # No match was made, probably junk
        return False
    name = match.group("name")
    guild = config.PLAYER_AFFILIATIONS.get(name)
    text = match.group("text")
    bid = match.group("bid")

    found_items = tuple(config.TREE.search_all(text))
    if not found_items:
        # No item found in auction
        return False
    found_items = tuple(found_items)
    if len(found_items) > 1:
        # Can't bid on two items at once
        return False
    item, _ = found_items[0]

    if guild not in config.ALLIANCE_MAP:
        # Player is not in the alliance
        return False
    if item not in config.ACTIVE_AUCTIONS:
        # Item is not currently up for bid
        return False
    return config.ACTIVE_AUCTIONS[item].add(bid, name)
