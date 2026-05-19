"""Central signal hub replacing wx.PostEvent / wx.CallAfter for cross-thread communication.

Qt signals with default (auto/queued) connections are thread-safe and will
automatically marshal calls to the receiver's thread — no CallAfter needed.
"""

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    # Log-driven events (emitted from message_handlers via ParseThread)
    drop = Signal()
    bid = Signal(object)  # Auction item
    who = Signal(str, str, int, str)  # name, pclass, level, guild
    clear_who = Signal()
    who_history = Signal()
    who_end = Signal()
    kill = Signal()
    creditt = Signal()
    gratss = Signal()

    # UI-driven events
    calc_raid_groups = Signal()
    show_raid_overview = Signal(object)  # WhoLog
    app_clear = Signal()
    app_reload = Signal()
    ignore = Signal()

    # Auction lifecycle (replaces direct widget manipulation)
    auction_started = Signal()
    auction_completed = Signal()

    # Misc
    title_changed = Signal(str)
    alert = Signal(str, str, int)  # title, message, msec
    alliance_changed = Signal(str)  # alliance name


signals = AppSignals()
