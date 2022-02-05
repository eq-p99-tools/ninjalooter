import wx

from ninjalooter import autoupdate
from ninjalooter import extra_data
from ninjalooter import logger
from ninjalooter.ui import window
from ninjalooter import utils

LOG = logger.getLogger(__name__)


def run():
    app = wx.App(False)
    try:
        autoupdate.check_update()
    except SystemExit:
        return
    except:  # noqa
        LOG.exception(
            "Failed to automatically update. Continuing with old version.")

    extra_data.apply_sheet_overrides()
    extra_data.apply_custom_overrides()
    utils.load_state()
    window.MainWindow()
    app.MainLoop()


if __name__ == "__main__":
    run()
