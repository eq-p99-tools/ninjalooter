import io
import functools
import json
import os
import subprocess
import sys
import zipfile

import requests
import semver
import wx

from ninjalooter.config import VERSION
from ninjalooter import logger

LOG = logger.getLogger(__name__)
GITHUB_API_LATEST_RELEASE_URL = (
    "https://api.github.com/repos/rm-you/ninjalooter/releases/latest")

if os.path.exists("github_auth.json"):
    with open("github_auth.json") as gha:
        auth_data = json.load(gha)
    get = functools.partial(requests.get, auth=requests.auth.HTTPBasicAuth(
        auth_data['username'], auth_data['key']))
else:
    get = requests.get


def get_newest_release_from_github():
    latest = get(GITHUB_API_LATEST_RELEASE_URL).json()
    latest_version = semver.VersionInfo.parse(latest['tag_name'])
    assets_url = latest['assets_url']
    return latest_version, assets_url


def download_and_unpack(url):
    # pylint: disable=no-member
    asset_data = get(url).json()
    zip_url = None
    for asset in asset_data:
        if asset['content_type'] == 'application/x-zip-compressed':
            zip_url = asset['browser_download_url']
            break
    if zip_url:
        zip_data = get(zip_url, stream=True)
        size = int(zip_data.headers.get('content-length', 0))
        pd = wx.GenericProgressDialog(
            title="Downloading Update",
            message="Downloading update, please wait...",
            maximum=size,
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT |
                  wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        )
        with io.BytesIO() as bio:
            downloaded = 0
            cancelled = False
            for data in zip_data.iter_content(chunk_size=int(size/100)):
                bio.write(data)
                downloaded += len(data)
                pd.Update(downloaded)
                if pd.WasCancelled():
                    cancelled = True
                    break
            pd.Destroy()
            if cancelled:
                return None
            with zipfile.ZipFile(bio) as zip_file:
                exe_name = zip_file.namelist()[0]
                zip_file.extractall()
            return exe_name
    return None


def check_update():
    # pylint: disable=no-member
    current_version = semver.VersionInfo.parse(VERSION)
    newest_version, newest_url = get_newest_release_from_github()
    if newest_version > current_version:
        au_win = wx.MessageDialog(
            None,
            "A new update is available. Would you like to update?\n\n"
            f"Your version: {current_version}\n"
            f"New version: {newest_version}",
            "Update Available", wx.YES | wx.NO | wx.ICON_QUESTION)
        result = au_win.ShowModal()
        au_win.Destroy()
        if result == wx.ID_YES:
            newest_exe = download_and_unpack(newest_url)
            if newest_exe:
                current_exe = os.path.basename(sys.executable).lower()
                if not current_exe.startswith("python"):
                    if current_exe == f"ninjalooter-{current_version}.exe":
                        pass
                    else:
                        os.rename(current_exe,
                                  f"ninjalooter-{current_version}.exe")
                        os.rename(newest_exe, "ninjalooter.exe")
                        newest_exe = "ninjalooter.exe"
                with subprocess.Popen([newest_exe]):
                    sys.exit()
            else:
                dlg = wx.MessageDialog(
                    None,
                    "Failed to update. Continuing with existing version.",
                    "Update Error", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
