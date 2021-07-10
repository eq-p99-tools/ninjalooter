# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import models


class KillTimesFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_KILL, self.OnKill)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)

        ###########################
        # Kill Timers Frame (Tab 4)
        ###########################
        killtimers_main_box = wx.BoxSizer(wx.VERTICAL)

        # List
        killtimers_list = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(600, 1080), useExpansionColumn=True)
        killtimers_main_box.Add(killtimers_list, flag=wx.EXPAND | wx.ALL)
        self.killtimers_list = killtimers_list

        def killtimerGroupKey(kill):
            group_key = kill.island()
            return group_key

        killtimers_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 180, "time",
                groupKeyGetter=killtimerGroupKey,
                groupKeyConverter='Island %s', fixedWidth=180),
            ObjectListView.ColumnDefn(
                "Mob", "left", 400, "name",
                groupKeyGetter=killtimerGroupKey,
                groupKeyConverter='Island %s', fixedWidth=400),
        ])
        killtimers_list.SetObjects(config.KILL_TIMERS)
        killtimers_list.SetEmptyListMsg(
            "No tracked mob deaths witnessed.")

        # Finalize Tab
        self.SetSizer(killtimers_main_box)
        parent.AddPage(self, 'Time of Death Tracking')

    def OnKill(self, e: models.KillEvent):
        self.killtimers_list.SetObjects(config.KILL_TIMERS)

    def OnClearApp(self, e: models.AppClearEvent):
        config.KILL_TIMERS.clear()
        self.killtimers_list.SetObjects(config.KILL_TIMERS)
        e.Skip()
