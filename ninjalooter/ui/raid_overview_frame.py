# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx
import wx.lib.scrolledpanel as scrolled

from ninjalooter import config
from ninjalooter import constants
from ninjalooter import models


class RaidOverviewFrame(scrolled.ScrolledPanel):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)
        parent.GetParent().Connect(-1, -1, models.EVT_SHOW_RAID_OVERVIEW,
                                   self.OnCalcRaidOverview)
        parent.GetParent().Connect(-1, -1, models.EVT_WHO_END,
                                   self.OnLastWho)

        #############################
        # Raid Overview Frame (Tab 6)
        #############################
        self.raid_overview_main_box = wx.WrapSizer()
        self.label_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)

        # Add a box for guild filter checkboxes
        self.guild_cb_outer_box = wx.BoxSizer(wx.VERTICAL)
        self.guild_cb_inner_box = wx.WrapSizer()
        self.guild_cb_outer_box.Add(self.guild_cb_inner_box)
        self.raid_overview_main_box.Add(
            self.guild_cb_outer_box, flag=wx.TOP | wx.LEFT, border=10)

        # Set up boxes for each class
        self.class_olv_objects = {}
        for pclass in sorted(constants.ALL_CLASSES):
            group_box = wx.BoxSizer(wx.VERTICAL)
            group_type_label = wx.StaticText(
                self, label=pclass)
            group_type_label.SetFont(self.label_font)
            group_box.Add(group_type_label)
            group_list = ObjectListView.ObjectListView(
                self, wx.ID_ANY, size=wx.Size(262, 142),
                style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=True)
            group_list.SetEmptyListMsg(f"No {pclass}s")
            group_list.SetColumns([
                ObjectListView.ColumnDefn("Player", "left", 114, "name",
                                          fixedWidth=114),
                ObjectListView.ColumnDefn("Lvl", "left", 30, "level",
                                          fixedWidth=30),
                ObjectListView.ColumnDefn("Guild", "left", 100, "sortguild",
                                          fixedWidth=100),
            ])
            group_list.SetFilter(
                ObjectListView.Filter.Predicate(self._guild_filter))
            group_box.Add(group_list)
            self.class_olv_objects[pclass] = group_list, group_type_label
            self.raid_overview_main_box.Add(
                group_box, flag=wx.TOP | wx.LEFT, border=8)

        # Finalize Tab
        self.SetSizer(self.raid_overview_main_box)
        parent.AddPage(self, 'Raid Overview')

        # Fix scrolling
        self.SetupScrolling(scroll_x=False)
        self.Bind(wx.EVT_SIZE, self.onSize)

        # Initialize data
        self._guilds_enabled = set()
        self._who_log = config.LAST_WHO_SNAPSHOT
        self._recalc_lists()

    def onSize(self, e: wx.EVT_SIZE):
        size = self.GetSize()
        vsize = self.GetVirtualSize()

        self.guild_cb_outer_box.SetMinSize((size[0] - 25, 0))
        self.SetVirtualSize((size[0], vsize[1]))

        if e:
            e.Skip()

    def OnLastWho(self, e: models.WhoEndEvent):
        print("Calc raid overview")
        self._who_log = config.LAST_WHO_SNAPSHOT
        self._recalc_lists()
        e.Skip()

    def OnCalcRaidOverview(self, e: models.ShowRaidOverviewEvent):
        print("Calc raid overview")
        self._who_log = e.wholog.log
        self._recalc_lists()
        self.GetParent().SetSelection(5)
        e.Skip()

    def _recalc_lists(self):
        guilds = set()
        self._cached_class_rosters = {pclass: [] for pclass in constants.ALL_CLASSES}
        for player in self._who_log.values():
            if player.pclass in self._cached_class_rosters:
                self._cached_class_rosters[player.pclass].append(player)
                if player.guild:
                    guilds.add(player.guild)
                else:
                    guilds.add("None")

        self.guild_cb_inner_box.Clear(True)

        self._guilds_enabled.clear()
        for guild in sorted(guilds):
            guild_cb = wx.CheckBox(self, label=str(guild))
            if config.RAID_OVERVIEW_GUILDS_ENABLED_CACHE.get(guild, True):
                guild_cb.SetValue(True)
                self._guilds_enabled.add(guild)
            guild_cb.Bind(wx.EVT_CHECKBOX, self._filter_checkbox_event)
            if not self.guild_cb_inner_box.GetItemCount() == 0:
                self.guild_cb_inner_box.Add(
                    wx.StaticLine(self, style=wx.LI_VERTICAL, size=(2, 16)),
                    flag=wx.ALL, border=6
                )
            self.guild_cb_inner_box.Add(
                guild_cb, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=6)
        self.onSize(None)  # Trigger a resize to handle initialization

        self._refresh_list_items()

    def _refresh_list_items(self):
        total = 0
        for pclass, listview in self.class_olv_objects.items():
            listview[0].SetObjects(self._cached_class_rosters[pclass])
            listview[0].SortBy(1, False)
            class_count = len(listview[0].GetFilteredObjects())
            listview[1].SetLabel(f"{pclass} ({class_count})")
            total += class_count

    def _guild_filter(self, obj):
        if obj.guild in self._guilds_enabled:
            return True
        elif not obj.guild and "None" in self._guilds_enabled:
            return True
        return False

    def _filter_checkbox_event(self, e: wx.EVT_CHECKBOX):
        checkbox = e.GetEventObject()
        config.RAID_OVERVIEW_GUILDS_ENABLED_CACHE[
            checkbox.GetLabel()] = checkbox.IsChecked()

        self._guilds_enabled.clear()
        for cb_window in self.guild_cb_inner_box.GetChildren():
            checkbox = cb_window.GetWindow()
            if hasattr(checkbox, "IsChecked") and checkbox.IsChecked():
                self._guilds_enabled.add(checkbox.GetLabel())

        self._refresh_list_items()

        e.Skip()

    def OnClearApp(self, e: models.AppClearEvent):
        for pclass, listview in self.class_olv_objects.items():
            listview[0].ClearAll()
        e.Skip()
