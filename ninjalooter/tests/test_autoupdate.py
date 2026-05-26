from unittest import mock

import semver
from PySide6.QtWidgets import QMessageBox

from ninjalooter import autoupdate
from ninjalooter import config
from ninjalooter.tests import base


class TestAutoUpdate(base.NLTestBase):
    def setUp(self) -> None:
        super(TestAutoUpdate, self).setUp()
        self.current_version = semver.VersionInfo.parse(config.VERSION)
        self.new_version = self.current_version.bump_patch()

    @mock.patch("logging.shutdown")
    @mock.patch("os._exit")
    @mock.patch("subprocess.Popen")
    @mock.patch("PySide6.QtWidgets.QMessageBox.question")
    @mock.patch("os.rename")
    @mock.patch("os.path.basename")
    @mock.patch("ninjalooter.autoupdate.download_and_unpack")
    @mock.patch("ninjalooter.autoupdate.get_recent_releases")
    def _check_update_new_version(
            self, mock_get_releases, mock_download_and_unpack,
            mock_basename, mock_rename, mock_question,
            mock_popen, mock_os_exit, mock_logging_shutdown,
            exe_name, accept_update=True):

        if accept_update:
            mock_question.return_value = QMessageBox.StandardButton.Yes
        else:
            mock_question.return_value = QMessageBox.StandardButton.No

        releases = [{
            'version': self.new_version,
            'tag_name': f'v{self.new_version}',
            'name': f'v{self.new_version}',
            'body': '',
            'published_at': '',
            'assets_url': 'https://some.url',
            'prerelease': False,
        }]
        mock_get_releases.return_value = releases

        mock_download_and_unpack.return_value = "/path/to/ninjalooter.exe"
        mock_basename.return_value = exe_name

        autoupdate._on_releases_fetched_main_thread(releases, False)

        return (mock_question, mock_rename, mock_popen, mock_os_exit,
                mock_download_and_unpack)

    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    def test_check_update_python_exe(self, mock_active_window):
        (mock_question, mock_rename, mock_popen, mock_os_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name="python.exe")

        mock_question.assert_called_once()
        mock_download_and_unpack.assert_called_once()

    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    def test_check_update_versioned_exe(self, mock_active_window):
        current_exe_name = f"ninjalooter-{config.VERSION}.exe"
        (mock_question, mock_rename, mock_popen, mock_os_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name=current_exe_name)

        mock_question.assert_called_once()
        mock_download_and_unpack.assert_called_once()

    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    def test_check_update_user_declines(self, mock_active_window):
        (mock_question, mock_rename, mock_popen, mock_os_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name="ninjalooter.exe",
                                            accept_update=False)

        mock_question.assert_called_once()
        mock_download_and_unpack.assert_not_called()
        mock_popen.assert_not_called()
        mock_os_exit.assert_not_called()

    @mock.patch("PySide6.QtWidgets.QMessageBox.information")
    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    @mock.patch("ninjalooter.autoupdate.get_recent_releases")
    def test_check_update_no_new_version(
            self, mock_get_releases, mock_active_window,
            mock_information):
        releases = [{
            'version': self.current_version,
            'tag_name': f'v{self.current_version}',
            'name': f'v{self.current_version}',
            'body': '',
            'published_at': '',
            'assets_url': 'https://some.url',
            'prerelease': False,
        }]
        mock_get_releases.return_value = releases

        autoupdate._on_releases_fetched_main_thread(releases, True)

        mock_information.assert_called_once()

    @mock.patch("PySide6.QtWidgets.QMessageBox.information")
    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    def test_check_update_no_releases(self, mock_active_window,
                                      mock_information):
        autoupdate._on_releases_fetched_main_thread([], True)
        mock_information.assert_called_once()

    @mock.patch("PySide6.QtWidgets.QMessageBox.information")
    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow",
                return_value=None)
    def test_check_update_no_releases_silent(self, mock_active_window,
                                             mock_information):
        autoupdate._on_releases_fetched_main_thread([], False)
        mock_information.assert_not_called()

    @mock.patch("ninjalooter.autoupdate.get")
    def test_get_recent_releases(self, mock_get):
        mock_get.return_value.raise_for_status = mock.Mock()
        mock_get.return_value.json.return_value = [
            {
                'tag_name': 'v1.2.3',
                'name': 'Release 1.2.3',
                'body': 'Some changes',
                'published_at': '2024-01-01',
                'assets_url': 'https://api.github.com/repos/test/releases/1/assets',
                'prerelease': False,
            },
            {
                'tag_name': 'v1.2.2',
                'name': 'Release 1.2.2',
                'body': 'Older changes',
                'published_at': '2023-12-01',
                'assets_url': 'https://api.github.com/repos/test/releases/2/assets',
                'prerelease': False,
            },
        ]

        releases = autoupdate.get_recent_releases(max_releases=10)

        self.assertEqual(2, len(releases))
        self.assertEqual(semver.VersionInfo.parse("1.2.3"), releases[0]['version'])
        self.assertEqual(semver.VersionInfo.parse("1.2.2"), releases[1]['version'])
        self.assertEqual('Some changes', releases[0]['body'])

    @mock.patch("ninjalooter.autoupdate.get")
    def test_get_recent_releases_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")

        releases = autoupdate.get_recent_releases()

        self.assertEqual([], releases)

    def test_is_upgrade_available_stable_over_rc_console_build(self):
        local = semver.VersionInfo.parse("1.18.0-rc11+console")
        remote = semver.VersionInfo.parse("1.18.0")
        self.assertTrue(autoupdate.is_upgrade_available(remote, local))

    def test_is_upgrade_available_equal_rc_ignores_build_metadata(self):
        local = semver.VersionInfo.parse("1.18.0-rc11+console")
        remote = semver.VersionInfo.parse("1.18.0-rc11")
        self.assertFalse(autoupdate.is_upgrade_available(remote, local))

    def test_find_newest_upgrade_prefers_stable_over_matching_rc_tag(self):
        current = semver.VersionInfo.parse("1.18.0-rc11+console")
        releases = [
            {"version": semver.VersionInfo.parse("1.18.0-rc11")},
            {"version": semver.VersionInfo.parse("1.18.0")},
        ]
        self.assertEqual(
            semver.VersionInfo.parse("1.18.0"),
            autoupdate.find_newest_upgrade(releases, current),
        )

    def test_find_newest_upgrade_none_when_only_equal_rc(self):
        current = semver.VersionInfo.parse("1.18.0-rc11+console")
        releases = [{"version": semver.VersionInfo.parse("1.18.0-rc11")}]
        self.assertIsNone(autoupdate.find_newest_upgrade(releases, current))

    @mock.patch("logging.shutdown")
    @mock.patch("os._exit")
    @mock.patch("subprocess.Popen")
    @mock.patch("PySide6.QtWidgets.QMessageBox.question")
    @mock.patch("os.rename")
    @mock.patch("os.path.basename")
    @mock.patch("ninjalooter.autoupdate.download_and_unpack")
    @mock.patch.object(config, "VERSION", "1.18.0-rc11+console")
    @mock.patch("PySide6.QtWidgets.QApplication.activeWindow", return_value=None)
    def test_check_update_stable_from_rc_console_build(
        self,
        mock_active_window,
        mock_download_and_unpack,
        mock_basename,
        mock_rename,
        mock_question,
        mock_popen,
        mock_os_exit,
        mock_logging_shutdown,
    ):
        mock_question.return_value = QMessageBox.StandardButton.Yes
        mock_download_and_unpack.return_value = "ninjalooter.exe"
        mock_basename.return_value = "ninjalooter.exe"

        releases = [
            {
                "version": semver.VersionInfo.parse("1.18.0-rc11"),
                "tag_name": "1.18.0-rc11",
                "name": "1.18.0-rc11",
                "body": "",
                "published_at": "",
                "assets_url": "https://example.com/assets",
                "prerelease": True,
            },
            {
                "version": semver.VersionInfo.parse("1.18.0"),
                "tag_name": "1.18.0",
                "name": "1.18.0",
                "body": "",
                "published_at": "",
                "assets_url": "https://example.com/assets",
                "prerelease": False,
            },
        ]

        autoupdate._on_releases_fetched_main_thread(releases, False)

        mock_question.assert_called_once()
