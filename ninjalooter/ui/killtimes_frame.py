# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import extra_data
from ninjalooter import models


class KillTimesFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_KILL, self.OnKill)

        ###########################
        # Kill Timers Frame (Tab 4)
        ###########################
        killtimers_main_box = wx.BoxSizer(wx.VERTICAL)

        # List
        killtimers_list = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(600, 630))
        killtimers_main_box.Add(killtimers_list, flag=wx.EXPAND | wx.ALL)
        self.killtimers_list = killtimers_list

        def killtimerGroupKey(kill):
            group_key = extra_data.TIMER_MOBS.get(kill.name, "Other")
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
