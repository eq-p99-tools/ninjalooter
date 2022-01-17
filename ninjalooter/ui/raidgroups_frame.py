# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import models
from ninjalooter import raidgroups


class RaidGroupsFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)
        parent.GetParent().Connect(-1, -1, models.EVT_CALC_RAIDGROUPS,
                                   self.OnCalcRaidGroups)

        config.RAID_GROUPS = raidgroups.GroupBuilder()

        ###########################
        # Raid Groups Frame (Tab 5)
        ###########################
        self.raidgroups_main_box = wx.WrapSizer()
        self.label_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)

        self.no_groups_text = wx.StaticText(
            self,
            label="No raid groups have been calculated.\n\n"
                  "Please select an entry from the Attendance Logs "
                  "panel to use for group calculation.")
        self.no_groups_text.SetFont(self.label_font)
        self.raidgroups_main_box.Add(self.no_groups_text,
                                     flag=wx.TOP | wx.LEFT, border=10)

        # Finalize Tab
        self.SetSizer(self.raidgroups_main_box)
        parent.AddPage(self, 'Raid Groups')

    def OnCalcRaidGroups(self, e: models.CalcRaidGroupsEvent):
        print("Calc raidgroups")
        self.no_groups_text.Hide()
        self.raidgroups_main_box.Clear()
        for group in config.RAID_GROUPS.raid.groups:
            group_box = wx.BoxSizer(wx.VERTICAL)
            group_type_label = wx.StaticText(
                self, label="%s Group" % group.group_type)
            group_type_label.SetFont(self.label_font)
            group_box.Add(group_type_label)
            group_list = ObjectListView.ObjectListView(
                self, wx.ID_ANY, size=wx.Size(250, 142),
                style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
            group_list.SetColumns([
                ObjectListView.ColumnDefn("Player", "left", 110, "name",
                                          fixedWidth=110),
                ObjectListView.ColumnDefn("Class", "left", 80, "pclass",
                                          fixedWidth=80),
                ObjectListView.ColumnDefn("Level", "left", 60, "level",
                                          fixedWidth=60),
            ])
            group_list.SetObjects(group.player_list)
            group_box.Add(group_list)
            self.raidgroups_main_box.Add(
                group_box, flag=wx.TOP | wx.LEFT, border=10)
        self.raidgroups_main_box.Layout()
        self.Parent.SetSelection(4)
        e.Skip()

    def OnClearApp(self, e: models.AppClearEvent):
        config.RAID_GROUPS = raidgroups.GroupBuilder()
        self.raidgroups_main_box.Clear()
        self.no_groups_text.Show()
        e.Skip()
