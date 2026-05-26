from __future__ import annotations

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from ninjalooter import autoupdate, logger, utils
from ninjalooter.ui.theme import semantic

LOG = logger.getLogger(__name__)

CHANGELOG_MAX_RELEASES = 15
_CHANGELOG_HEAD = "<style>h2 { font-size: 1.25em; }</style>"


def _changelog_body_style() -> str:
    return (
        f"background-color:{semantic.changelog_bg}; "
        f"color:{semantic.changelog_fg}; "
        "padding:12px; font-size:15px; line-height:1.5;"
    )


def _wrap_changelog_html(content: str) -> str:
    return f"{_CHANGELOG_HEAD}<body style=\"{_changelog_body_style()}\">{content}</body>"


def format_changelog_html(releases: list) -> str:
    """Render release dicts as styled HTML for QTextBrowser."""
    html = autoupdate.compile_changelog(releases)
    return _wrap_changelog_html(html)


class _ChangelogFetchThread(QThread):
    finished = Signal(object)

    def __init__(self, max_releases: int, parent=None):
        super().__init__(parent)
        self._max_releases = max_releases

    def run(self) -> None:
        try:
            releases = autoupdate.get_recent_releases(max_releases=self._max_releases)
            self.finished.emit(releases)
        except Exception as exc:
            self.finished.emit(exc)


class ChangelogFrame(QWidget):
    """Tab showing recent GitHub release notes."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._fetch_thread: _ChangelogFetchThread | None = None
        self._loaded = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(False)
        self._browser.anchorClicked.connect(self._open_url)
        layout.addWidget(self._browser)

        self._set_message("Open this tab to load release notes from GitHub.")

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._loaded and self._fetch_thread is None:
            self._load_releases()

    def _load_releases(self) -> None:
        self._set_message("Loading changelog…")
        self._fetch_thread = _ChangelogFetchThread(CHANGELOG_MAX_RELEASES, self)
        self._fetch_thread.finished.connect(self._on_fetch_finished)
        self._fetch_thread.start()

    def _on_fetch_finished(self, result) -> None:
        self._fetch_thread = None
        self._loaded = True

        if isinstance(result, Exception):
            LOG.exception("Failed to fetch changelog data from GitHub.")
            self._set_message(
                "Could not load release notes from GitHub.\n\n"
                f"{result}\n\n"
                "Check your network connection and try again later."
            )
            return

        if not result:
            self._set_message("No releases found.")
            return

        self._browser.setHtml(format_changelog_html(result))

    @staticmethod
    def _open_url(url) -> None:
        utils.open_generic_url(url.toString())

    def _set_message(self, text: str) -> None:
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        self._browser.setHtml(_wrap_changelog_html(escaped))
