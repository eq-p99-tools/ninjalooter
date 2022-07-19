# pylint: disable=no-member,invalid-name,unused-argument

import os.path
import sys

import markdown2
import ObjectListView
import semver
import wx
import wx.html

from ninjalooter import autoupdate
from ninjalooter import config
from ninjalooter import logger
from ninjalooter import logparse
from ninjalooter import overrides
from ninjalooter.ui import attendance_frame
from ninjalooter.ui import bidding_frame
from ninjalooter.ui import killtimes_frame
from ninjalooter.ui import menu_bar
from ninjalooter.ui import population_frame
from ninjalooter.ui import raidgroups_frame
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)
# Monkeypatch ObjectListView to fix a character encoding bug (PR upstream?)
# pylint: disable=protected-access
ObjectListView.ObjectListView._HandleTypingEvent = overrides._HandleTypingEvent


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        wx.adv.TaskBarIcon.__init__(self)
        self.frame = frame
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(os.path.join(
                config.PROJECT_DIR, "data", "icons", "ninja_attack.png"),
                      wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon, "NinjaLooter " + config.VERSION)
        self.alwaysontop_mi = None

    def CreatePopupMenu(self):
        menu = wx.Menu()

        self.alwaysontop_mi = wx.MenuItem(
            menu, wx.ID_ANY, 'Always On Top',
            kind=wx.ITEM_CHECK)
        menu.Append(self.alwaysontop_mi)
        self.alwaysontop_mi.Check(config.ALWAYS_ON_TOP)
        self.Bind(wx.EVT_MENU, self.OnAlwaysOnTop, self.alwaysontop_mi)

        exit_mi = wx.MenuItem(menu, wx.ID_EXIT, 'Quit')
        exit_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "exit.png"))
        exit_mi.SetBitmap(exit_bitmap)
        menu.Append(exit_mi)
        self.Bind(wx.EVT_MENU, self.frame.OnClose, exit_mi)

        return menu

    def OnAlwaysOnTop(self, e: wx.MenuEvent):
        config.ALWAYS_ON_TOP = self.alwaysontop_mi.IsChecked()
        self.frame.MenuBar.alwaysontop_mi.Check(config.ALWAYS_ON_TOP)
        config.CONF.set(
            'default', 'always_on_top', str(config.ALWAYS_ON_TOP))
        self.frame.UpdateAlwaysOnTop()
        config.write()


class MainWindow(wx.Frame):
    def __init__(self, parent=None, title="NinjaLooter EQ Raid Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(855, 800))
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(os.path.join(
                config.PROJECT_DIR, "data", "icons", "ninja_attack.png"),
                      wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set up menubar
        menu_bar.MenuBar(self)

        # Set up taskbar icon
        config.WX_TASKBAR_ICON = TaskBarIcon(self)

        # Notebook used to create a tabbed main interface
        notebook = wx.Notebook(self, style=wx.LEFT)

        # Bidding Frame
        self.bidding_frame = bidding_frame.BiddingFrame(notebook)

        # Attendance Frame
        self.attendance_frame = attendance_frame.AttendanceFrame(notebook)

        # Population Frame
        self.population_frame = population_frame.PopulationFrame(notebook)

        # Kill Times Frame
        self.killtimes_frame = killtimes_frame.KillTimesFrame(notebook)

        # Raid Groups Frame
        self.raidgroups_frame = raidgroups_frame.RaidGroupsFrame(notebook)

        self.Show(True)
        if config.ALWAYS_ON_TOP:
            self.SetWindowStyle(self.GetWindowStyle() | wx.STAY_ON_TOP)
        self.parser_thread = logparse.ParseThread(self)
        self.parser_thread.start()

        # Handle automatically switching characters
        if sys.platform == "win32":  # FileSystemWatcher is buggy on Linux/OSX
            self.watcher = wx.FileSystemWatcher()
            self.watcher.Bind(wx.EVT_FSWATCHER, self.OnFilesystemEvent)
            if os.path.isdir(config.LOG_DIRECTORY):
                self.watcher.Add(
                    config.LOG_DIRECTORY,
                    events=wx.FSW_EVENT_CREATE | wx.FSW_EVENT_MODIFY)
            config.WX_FILESYSTEM_WATCHER = self.watcher

        # Show Changelog on new version
        try:
            last_run = semver.VersionInfo.parse(config.LAST_RUN_VERSION)
            current = semver.VersionInfo.parse(config.VERSION)
            if current > last_run:
                ChangeLog(self)
        except (ValueError, TypeError):
            config.LAST_RUN_VERSION = config.VERSION
            config.CONF.set("default", "last_run_version", config.VERSION)
            config.write()

    def OnFilesystemEvent(self, e: wx.FileSystemWatcherEvent):
        if not config.AUTO_SWAP_LOGFILE:
            return
        logfile, name = utils.get_latest_logfile(config.LOG_DIRECTORY)
        if logfile != config.LATEST_LOGFILE:
            config.PLAYER_NAME = name
            config.LATEST_LOGFILE = logfile
            self.parser_thread.abort()
            self.parser_thread = logparse.ParseThread(self)
            self.parser_thread.start()

    def UpdateAlwaysOnTop(self):
        if config.ALWAYS_ON_TOP:
            self.SetWindowStyle(
                self.GetWindowStyle() | wx.STAY_ON_TOP)
        else:
            self.SetWindowStyle(
                self.GetWindowStyle() & ~wx.STAY_ON_TOP)

    def OnClose(self, e: wx.Event):
        if config.CONFIRM_EXIT:
            dlg = wx.MessageDialog(
                self,
                "Do you really want to close this application?",
                "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
        else:
            result = wx.ID_OK
        if result == wx.ID_OK:
            utils.clear_alerts()
            config.WX_TASKBAR_ICON.Destroy()
            self.parser_thread.abort()
            utils.store_state()
            self.Destroy()


class ChangeLog(wx.Frame):
    def __init__(self, parent=None):
        try:
            version, tag_data = autoupdate.get_release_from_github(
                config.VERSION)
        except Exception as e:  # noqa
            if isinstance(e, KeyError) and 'tag_name' in e.args:
                LOG.warning("This version is not yet released, no changelog "
                            "data to fetch.")
            else:
                LOG.exception("Failed to fetch changelog data from GitHub.")
            return
        title = f"Changelog for {version}"
        wx.Frame.__init__(self, parent, title=title, size=(600, 400))
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        self.changelog_data = markdown2.markdown(tag_data['body'])

        self.html_win = wx.html.HtmlWindow(self)
        self.html_win.SetPage(self.changelog_data)
        self.html_win.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OpenURL)
        if config.ALWAYS_ON_TOP:
            self.SetWindowStyle(
                self.GetWindowStyle() | wx.STAY_ON_TOP)
        self.html_win.SetBackgroundColour(wx.Colour("#eff7fa"))
        self.Show()

    @staticmethod
    def OpenURL(e: wx.html.EVT_HTML_LINK_CLICKED):
        url = e.GetLinkInfo().GetHref()
        utils.open_generic_url(url)

    def OnClose(self, e: wx.EVT_CLOSE):
        config.LAST_RUN_VERSION = config.VERSION
        config.CONF.set("default", "last_run_version", config.VERSION)
        config.write()
        self.Destroy()
