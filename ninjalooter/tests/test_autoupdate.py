from unittest import mock

import semver
import wx

from ninjalooter import autoupdate
from ninjalooter import config
from ninjalooter.tests import base


class TestAutoUpdate(base.NLTestBase):
    def setUp(self) -> None:
        super(TestAutoUpdate, self).setUp()
        self.current_version = semver.VersionInfo.parse(config.VERSION)
        self.new_version = self.current_version.bump_patch()

    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    @mock.patch("wx.MessageDialog")
    @mock.patch("os.rename")
    @mock.patch("os.path.basename")
    @mock.patch("ninjalooter.autoupdate.download_and_unpack")
    @mock.patch("ninjalooter.autoupdate.get_release_from_github")
    def _check_update_new_version(
            self, mock_get_release, mock_download_and_unpack,
            mock_basename, mock_rename, mock_wx_message_dialog,
            mock_popen, mock_exit, exe_name, accept_update=True):

        if accept_update:
            (mock_wx_message_dialog.return_value.ShowModal.return_value
             ) = wx.ID_YES
        else:
            (mock_wx_message_dialog.return_value.ShowModal.return_value
             ) = wx.ID_CANCEL
        mock_get_release.return_value = (
            self.new_version,
            {'assets_url': 'https://some.url'}
        )

        mock_download_and_unpack.return_value = "/path/to/ninjalooter.exe"
        mock_basename.return_value = exe_name

        autoupdate.check_update()

        return (mock_wx_message_dialog, mock_rename, mock_popen, mock_exit,
                mock_download_and_unpack)

    def test_check_update_python_exe(self):
        (mock_wx_message_dialog, mock_rename, mock_popen, mock_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name="python.exe")

        mock_wx_message_dialog().ShowModal.assert_called_once_with()
        mock_popen.assert_called_once_with(
            [mock_download_and_unpack.return_value])
        mock_exit.assert_called_once_with()

    def test_check_update_versioned_exe(self):
        current_exe_name = f"ninjalooter-{config.VERSION}.exe"
        (mock_wx_message_dialog, mock_rename, mock_popen, mock_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name=current_exe_name)

        mock_wx_message_dialog().ShowModal.assert_called_once_with()
        mock_popen.assert_called_once_with(
            [mock_download_and_unpack.return_value])
        mock_exit.assert_called_once_with()

    def test_check_update_unversioned_exe(self):
        (mock_wx_message_dialog, mock_rename, mock_popen, mock_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name="ninjalooter.exe")

        mock_wx_message_dialog().ShowModal.assert_called_once_with()
        mock_popen.assert_called_once_with(["ninjalooter.exe"])
        mock_exit.assert_called_once_with()

    def test_check_update_user_declines(self):
        (mock_wx_message_dialog, mock_rename, mock_popen, mock_exit,
         mock_download_and_unpack,
         ) = self._check_update_new_version(exe_name="ninjalooter.exe",
                                            accept_update=False)

        mock_wx_message_dialog().ShowModal.assert_called_once_with()
        mock_download_and_unpack.assert_not_called()
        mock_popen.assert_not_called()
        mock_exit.assert_not_called()

    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    @mock.patch("wx.MessageDialog")
    @mock.patch("os.rename")
    @mock.patch("os.path.basename")
    @mock.patch("ninjalooter.autoupdate.download_and_unpack")
    @mock.patch("ninjalooter.autoupdate.get_release_from_github")
    def test_check_update_no_new_version(
            self, mock_get_release, mock_download_and_unpack,
            mock_basename, mock_rename, mock_wx_message_dialog,
            mock_popen, mock_exit):
        mock_wx_message_dialog.return_value.ShowModal.return_value = wx.ID_YES

        mock_get_release.return_value = (
            self.current_version,
            {'assets_url': 'https://some.url'}
        )

        mock_download_and_unpack.return_value = "/path/to/ninjalooter.exe"

        autoupdate.check_update()

        mock_wx_message_dialog().ShowModal.assert_not_called()
        mock_download_and_unpack.assert_not_called()
        mock_popen.assert_not_called()
        mock_exit.assert_not_called()

    @mock.patch("io.BytesIO")
    @mock.patch("wx.GenericProgressDialog")
    @mock.patch("zipfile.ZipFile")
    @mock.patch("ninjalooter.autoupdate.get")
    def test_download_and_unpack(
            self, mock_get, mock_zipfile, mock_wx_progress_dialog,
            mock_bytesio):
        mock_get().json.return_value = [
            {'content_type': 'application/x-zip-compressed',
             'browser_download_url': 'some_url'}]
        mock_get().headers.get.return_value = 10

        autoupdate.download_and_unpack("test_url")
