"""Auto-updater using GitHub releases API with background thread + Qt signals."""

import contextlib
import functools
import io
import json
import logging
import os
import subprocess
import sys
import threading
import zipfile

import markdown2
import requests
import semver
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from ninjalooter import config
from ninjalooter.changelog_prefix import get_changelog_prefix, strip_changelog_prefix

LOG = logging.getLogger(__name__)

GITHUB_API_LATEST_RELEASE_URL = "https://api.github.com/repos/rm-you/ninjalooter/releases/latest"
GITHUB_API_TAGGED_RELEASE_URL = "https://api.github.com/repos/rm-you/ninjalooter/releases/tags/{tag}"
GITHUB_API_RELEASES_URL = "https://api.github.com/repos/rm-you/ninjalooter/releases?per_page={max_releases}"

REQUEST_TIMEOUT = (5, 15)

_auth = None
if os.path.exists("github_auth.json"):
    try:
        with open("github_auth.json") as gha:
            auth_data = json.load(gha)
        _auth = requests.auth.HTTPBasicAuth(auth_data["username"], auth_data["key"])
    except (json.JSONDecodeError, KeyError, OSError) as e:
        LOG.warning("Failed to load github_auth.json: %s", e)

get = functools.partial(requests.get, auth=_auth, timeout=REQUEST_TIMEOUT)

STABLE_EXE_NAME = "ninjalooter.exe"


class UpdaterBridge(QObject):
    """Marshals updater thread results to the Qt GUI thread."""

    releases_ready = Signal(list, bool)
    fetch_failed = Signal(str)


_updater_bridge_instance: UpdaterBridge | None = None
_updater_signals_connected = False


def init_updater_bridge() -> UpdaterBridge | None:
    """Create the updater bridge on the GUI thread (call after QApplication exists)."""
    global _updater_bridge_instance
    app = QApplication.instance()
    if app is None:
        return None
    if _updater_bridge_instance is None:
        _updater_bridge_instance = UpdaterBridge(app)
    return _updater_bridge_instance


def _get_updater_bridge() -> UpdaterBridge | None:
    return _updater_bridge_instance


def connect_updater_signals():
    """Connect updater bridge signals to main-thread handlers (call after QApplication exists)."""
    global _updater_signals_connected
    b = init_updater_bridge()
    if b is None or _updater_signals_connected:
        return
    b.releases_ready.connect(_on_releases_fetched_main_thread)
    b.fetch_failed.connect(_show_update_error_main_thread)
    _updater_signals_connected = True


def parse_release_version(tag_name: str) -> semver.VersionInfo:
    """Parse a GitHub release tag into a semver VersionInfo."""
    return semver.VersionInfo.parse(tag_name.lstrip("v"))


def is_upgrade_available(remote: semver.VersionInfo, local: semver.VersionInfo) -> bool:
    """True when remote is a semver upgrade over local (e.g. 1.18.0 over 1.18.0-rc11+console)."""
    return remote > local


def visible_releases_for(releases: list, current: semver.VersionInfo) -> list:
    """Releases the user may upgrade to, based on their running version."""
    if current.prerelease is not None:
        return releases
    return [r for r in releases if not r["prerelease"]]


def find_newest_upgrade(releases: list, current: semver.VersionInfo) -> semver.VersionInfo | None:
    """Highest release strictly newer than current (releases should be semver-sorted desc)."""
    for release in releases:
        candidate = release["version"]
        if is_upgrade_available(candidate, current):
            return candidate
    return None


def get_recent_releases(max_releases=10):
    """Fetch the most recent releases from GitHub (excludes drafts)."""
    try:
        resp = get(GITHUB_API_RELEASES_URL.format(max_releases=max_releases))
        resp.raise_for_status()
        releases_data = resp.json()
        releases = []
        for release in releases_data:
            if release.get("draft", False):
                continue
            version = parse_release_version(release["tag_name"])
            releases.append(
                {
                    "version": version,
                    "tag_name": release["tag_name"],
                    "name": release.get("name", release["tag_name"]),
                    "body": release.get("body", ""),
                    "published_at": release.get("published_at", ""),
                    "assets_url": release.get("assets_url", ""),
                    "prerelease": release.get("prerelease", False),
                }
            )
        releases.sort(key=lambda x: x["version"], reverse=True)
        return releases
    except Exception:
        LOG.exception("Failed to fetch recent releases")
        return []


def compile_changelog(releases):
    """Compile release notes into HTML."""
    changelog = get_changelog_prefix() + "\n\n"
    for release in releases:
        version_str = f"v{release['version']}"
        changelog += f"## {version_str}\n"
        body = strip_changelog_prefix(release["body"])
        if body:
            for raw_line in body.split("\n"):
                stripped = raw_line.strip()
                if not stripped:
                    continue
                if stripped.startswith(("#", "-", "*")):
                    changelog += f"{stripped}\n"
                else:
                    changelog += f"- {stripped}\n"
        else:
            changelog += f"- Release {version_str}\n"
        changelog += "\n"
    return markdown2.markdown(changelog)


def download_and_unpack(url: str):
    """Download and unpack the update zip file."""
    resp = get(url)
    resp.raise_for_status()
    asset_data = resp.json()
    ZIP_CONTENT_TYPES = {"application/x-zip-compressed", "application/zip", "application/octet-stream"}
    zip_url = None
    for asset in asset_data:
        if asset["content_type"] in ZIP_CONTENT_TYPES or asset.get("name", "").endswith(".zip"):
            zip_url = asset["browser_download_url"]
            break
    if zip_url:
        LOG.info("Downloading update from %s", zip_url)
        zip_data = get(zip_url, stream=True)
        zip_data.raise_for_status()
        size = int(zip_data.headers.get("content-length", 0))
        chunk_size = max(size // 100, 8192)
        progress_max = max(size, 1)
        parent = QApplication.activeWindow()
        pd = QProgressDialog("Downloading update, please wait...", "Cancel", 0, progress_max, parent)
        pd.setWindowTitle("Downloading Update")
        pd.setWindowModality(Qt.WindowModality.ApplicationModal)
        pd.setMinimumDuration(0)
        pd.setValue(0)
        with io.BytesIO() as bio:
            downloaded = 0
            cancelled = False
            for data in zip_data.iter_content(chunk_size=chunk_size):
                bio.write(data)
                downloaded += len(data)
                pd.setValue(min(downloaded, progress_max))
                QApplication.processEvents()
                if pd.wasCanceled():
                    cancelled = True
                    break
            pd.close()
            if cancelled:
                return None
            with zipfile.ZipFile(bio) as zip_file:
                for member in zip_file.namelist():
                    if os.path.isabs(member) or ".." in member.split("/"):
                        LOG.error("Zip contains unsafe path: %s", member)
                        return None
                exe_name = zip_file.namelist()[0]
                zip_file.extractall()
            return exe_name
    LOG.info("Failed to download update, no zip found.")
    return None


def _prompt_and_apply_update(releases, latest_version):
    """Show the update prompt and apply the update if accepted."""
    parent = QApplication.activeWindow()
    result = QMessageBox.question(
        parent,
        "Update Available",
        "A new update is available. Would you like to update?\n\n"
        f"Your version: {config.VERSION}\n"
        f"New version: {latest_version}",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if result != QMessageBox.StandardButton.Yes:
        return

    assets_url = next((r.get("assets_url") for r in releases if r["version"] == latest_version), None)
    if not assets_url:
        LOG.error("No assets_url for version %s", latest_version)
        _show_update_error_main_thread(
            f"Could not locate download assets for version {latest_version}.\n\n"
            "Try downloading the update manually from GitHub."
        )
        return

    app_dir = os.path.dirname(os.path.abspath(sys.executable))
    original_cwd = os.getcwd()
    try:
        os.chdir(app_dir)
    except OSError as e:
        LOG.exception("Cannot chdir to application directory: %s", app_dir)
        _show_update_error_main_thread(f"Cannot access application directory:\n{app_dir}\n\n{e}")
        return

    current_exe = os.path.basename(sys.executable)
    is_packaged = not current_exe.lower().startswith("python")
    backed_up = False
    backup_name = f"ninjalooter-{config.VERSION}.exe"

    try:
        if is_packaged and current_exe.lower() == STABLE_EXE_NAME.lower():
            try:
                if os.path.exists(backup_name):
                    os.remove(backup_name)
                os.rename(current_exe, backup_name)
                backed_up = True
            except OSError as e:
                LOG.exception("Failed to backup current exe before update")
                _show_update_error_main_thread(f"Failed to prepare for update: {e}")
                return

        newest_exe = download_and_unpack(assets_url)
        if not newest_exe:
            LOG.error("Failed to download update.")
            if backed_up:
                with contextlib.suppress(OSError):
                    os.rename(backup_name, STABLE_EXE_NAME)
            _show_update_error_main_thread("Failed to download update. Continuing with existing version.")
            return

        LOG.info("Downloaded new version: %s", newest_exe)

        if is_packaged and current_exe.lower() == STABLE_EXE_NAME.lower():
            if newest_exe.lower() != STABLE_EXE_NAME.lower():
                try:
                    if os.path.exists(STABLE_EXE_NAME):
                        os.remove(STABLE_EXE_NAME)
                    os.rename(newest_exe, STABLE_EXE_NAME)
                except OSError as rename_err:
                    LOG.error("Failed to rename new exe: %s", rename_err)
                    _show_update_error_main_thread(
                        f"Failed to rename update files: {rename_err}\n\n"
                        f"The new version was downloaded as '{newest_exe}'. "
                        "You can rename it manually and restart."
                    )
                    return
            launch_exe = STABLE_EXE_NAME
        elif is_packaged:
            launch_exe = newest_exe
        else:
            launch_exe = newest_exe

        logging.shutdown()
        with subprocess.Popen([os.path.join(app_dir, launch_exe)]):
            os._exit(0)
    except Exception as e:
        LOG.exception("Unexpected error during update apply")
        _show_update_error_main_thread(f"Update failed unexpectedly:\n\n{e}")
        os.chdir(original_cwd)


def _on_releases_fetched_main_thread(releases, notify_no_update):
    """Handle fetched releases on the main (UI) thread."""
    if not releases:
        LOG.info("No releases found.")
        if notify_no_update:
            parent = QApplication.activeWindow()
            QMessageBox.information(
                parent,
                "Update Check",
                f"Version: {config.VERSION}\n\nCould not retrieve release information.",
            )
        return

    current_version = semver.VersionInfo.parse(config.VERSION)
    visible_releases = visible_releases_for(releases, current_version)

    if not visible_releases:
        if notify_no_update:
            parent = QApplication.activeWindow()
            QMessageBox.information(
                parent,
                "No Update Available",
                f"Version: {config.VERSION}\n\nYou are running the latest version.",
            )
        return

    newest_upgrade = find_newest_upgrade(visible_releases, current_version)
    if newest_upgrade is not None:
        LOG.info("Update available: %s", newest_upgrade)
        _prompt_and_apply_update(releases, newest_upgrade)
    else:
        LOG.info("No update available.")
        if notify_no_update:
            parent = QApplication.activeWindow()
            QMessageBox.information(
                parent,
                "No Update Available",
                f"Version: {config.VERSION}\n\nYou are running the latest version.",
            )


def check_update(notify_no_update=False):
    """Check for updates in a background thread.

    Network I/O runs off the main thread so the UI stays responsive.
    All dialogs and UI updates are marshaled back via Qt signals.
    """

    def _background():
        try:
            LOG.info("Checking for update. Current version: %s", config.VERSION)
            releases = get_recent_releases(10)
            b = _get_updater_bridge()
            if b:
                b.releases_ready.emit(releases, notify_no_update)
            else:
                LOG.warning("Updater bridge not initialized; update check result dropped")
        except Exception as e:
            LOG.exception("Failed to check for update")
            if notify_no_update:
                eb = _get_updater_bridge()
                if eb:
                    eb.fetch_failed.emit(str(e))
                else:
                    LOG.warning("Updater bridge not initialized; update error not shown")

    thread = threading.Thread(target=_background, daemon=True)
    thread.start()


def _show_update_error_main_thread(message: str):
    """Show an update error dialog on the main thread."""
    parent = QApplication.activeWindow()
    QMessageBox.critical(parent, "Update Error", f"Failed to check for updates:\n\n{message}")
