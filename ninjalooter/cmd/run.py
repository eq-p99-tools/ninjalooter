import sys
import traceback

from PySide6.QtWidgets import QApplication

from ninjalooter import autoupdate, config, extra_data, logger, utils
from ninjalooter.ui.theme import apply_app_theme
from ninjalooter.ui.window import MainWindow

LOG = logger.getLogger(__name__)


def run():
    app = QApplication(sys.argv)
    apply_app_theme(app, dark_mode=config.DARK_MODE)
    autoupdate.connect_updater_signals()

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

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


def main():
    try:
        run()
    except:  # noqa
        with open("nl-crash-log.txt", "w") as f:
            traceback.print_exc(file=f)
        raise


if __name__ == "__main__":
    main()
