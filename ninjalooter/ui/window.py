# pylint: disable=no-member,invalid-name,unused-argument

import wx

from ninjalooter import logging
from ninjalooter import logparse
from ninjalooter.ui import attendance_frame
from ninjalooter.ui import bidding_frame
from ninjalooter.ui import killtimes_frame
from ninjalooter.ui import population_frame

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    player_affiliations = None

    def __init__(self, parent=None, title="NinjaLooter EQ Loot Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(725, 630))
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap("data/ninja_attack.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Notebook used to create a tabbed main interface
        notebook = wx.Notebook(self, style=wx.LEFT)

        # Bidding Frame
        bidding_frame.BiddingFrame(notebook)

        # Population Frame
        population_frame.PopulationFrame(notebook)

        # Attendance Frame
        attendance_frame.AttendanceFrame(notebook)

        # Kill Times Frame
        killtimes_frame.KillTimesFrame(notebook)

        self.Show(True)
        self.parser_thread = logparse.ParseThread(self)
        self.parser_thread.start()

    def OnClose(self, e: wx.Event):
        self.parser_thread.abort()
        dlg = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()
