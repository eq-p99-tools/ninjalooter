import contextlib
import os
import shutil
import sys
import tempfile
import threading
import traceback

from PySide6.QtWidgets import QApplication

from ninjalooter import autoupdate, config, extra_data, logger, utils
from ninjalooter.app_signals import signals
from ninjalooter.ui.theme import apply_app_theme
from ninjalooter.ui.window import MainWindow

LOG = logger.getLogger(__name__)


def _cleanup_update_temps():
    """Remove leftover ninjalooter_update_* dirs from previous auto-updates."""
    try:
        tmp = tempfile.gettempdir()
        for entry in os.scandir(tmp):
            if entry.is_dir() and entry.name.startswith("ninjalooter_update_"):
                with contextlib.suppress(OSError):
                    shutil.rmtree(entry.path)
    except Exception:
        pass


def run():
    app = QApplication(sys.argv)
    apply_app_theme(app, dark_mode=config.DARK_MODE)
    autoupdate.connect_updater_signals()
    _cleanup_update_temps()

    if getattr(sys, "frozen", False):
        try:
            autoupdate.check_update()
        except SystemExit:
            return
        except:  # noqa
            LOG.exception("Failed to automatically update. Continuing with old version.")

    extra_data.apply_custom_overrides()
    utils.load_state()

    window = MainWindow()
    window.show()
    threading.Thread(target=_load_sheet_overrides, name="min-dkp-sheet", daemon=True).start()
    sys.exit(app.exec())


def _load_sheet_overrides():
    """Fetch min-DKP overrides after the window is up so startup is not blocked."""
    try:
        extra_data.apply_sheet_overrides()
    except Exception:
        LOG.exception("Failed to fetch google sheet for overrides.")
        return
    signals.min_dkp_sheet_loaded.emit()


def main():
    try:
        run()
    except:  # noqa
        with open("nl-crash-log.txt", "w") as f:
            traceback.print_exc(file=f)
        raise


if __name__ == "__main__":
    main()
