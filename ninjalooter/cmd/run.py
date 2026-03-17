import sys
import traceback

import wx
import wx.html

from ninjalooter import autoupdate, extra_data, logger, utils
from ninjalooter.ui import window

LOG = logger.getLogger(__name__)


def run():
    app = wx.App(False)
    if getattr(sys, "frozen", False):
        try:
            autoupdate.check_update()
        except SystemExit:
            return
        except:  # noqa
            LOG.exception("Failed to automatically update. Continuing with old version.")

    try:
        extra_data.apply_sheet_overrides()
    except Exception as e:
        LOG.exception(f"Failed to fetch google sheet for overrides: {e}")
    extra_data.apply_custom_overrides()
    utils.load_state()
    window.MainWindow()
    app.MainLoop()


def main():
    try:
        run()
    except:  # noqa
        with open("nl-crash-log.txt", "w") as f:
            traceback.print_exc(file=f)
        raise


if __name__ == "__main__":
    main()
