# pylint: disable=no-member,invalid-name,unused-argument

import os.path

import ObjectListView
import wx

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


class MainWindow(wx.Frame):
    def __init__(self, parent=None, title="NinjaLooter EQ Loot Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(850, 800))
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap(os.path.join(
                utils.PROJECT_DIR, "data", "icons", "ninja_attack.png"),
                      wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Set up menubar
        menu_bar.MenuBar(self)

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

    def OnClose(self, e: wx.Event):
        dlg = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.parser_thread.abort()
            utils.store_state()
            self.Destroy()
