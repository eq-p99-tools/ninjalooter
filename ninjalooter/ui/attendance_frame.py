# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx
import wx.lib.splitter

from ninjalooter import config
from ninjalooter import models
from ninjalooter import utils


class AttendanceFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_WHO_HISTORY,
                                   self.OnWhoHistory)
        parent.GetParent().Connect(-1, -1, models.EVT_CREDITT,
                                   self.OnCreditt)
        parent.GetParent().Connect(-1, -1, models.EVT_GRATSS,
                                   self.OnGratss)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)

        ##############################
        # Attendance Log Frame (Tab 2)
        ##############################
        attendance_main_box = wx.BoxSizer(wx.VERTICAL)
        attendance_splitter = wx.lib.splitter.MultiSplitterWindow(
            self, wx.ID_ANY, style=wx.SP_3D | wx.SP_BORDER)
        attendance_splitter.SetOrientation(wx.VERTICAL)
        pane_1 = wx.Panel(attendance_splitter, wx.ID_ANY)
        pane_2 = wx.Panel(attendance_splitter, wx.ID_ANY)
        pane_3 = wx.Panel(attendance_splitter, wx.ID_ANY)

        # Attendance / Raidtick List
        attendance_box = wx.BoxSizer(wx.HORIZONTAL)
        attendance_list = ObjectListView.ObjectListView(
            pane_1, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(650, 600))
        attendance_box.Add(attendance_list, flag=wx.EXPAND | wx.ALL)
        attendance_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowAttendanceDetail)
        self.attendance_list = attendance_list

        attendance_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 180, "time",
                fixedWidth=180),
            ObjectListView.ColumnDefn(
                "RT", "left", 25, "raidtick_display",
                fixedWidth=25),
            ObjectListView.ColumnDefn(
                "Populations", "left", 425, "populations",
                fixedWidth=425),
        ])
        attendance_list.SetObjects(config.WHO_LOG)
        attendance_list.SetEmptyListMsg(
            "No who log history.\nPlease type `/who` ingame.")

        # Attendance / Raidtick Buttons
        attendance_buttons_box = wx.BoxSizer(wx.VERTICAL)
        attendance_box.Add(attendance_buttons_box,
                           flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)
        attendance_button_raidtick = wx.CheckBox(pane_1, label="Raidtick Only")
        attendance_buttons_box.Add(attendance_button_raidtick)
        attendance_button_raidtick.Bind(wx.EVT_CHECKBOX, self.OnRaidtickOnly)
        self.attendance_button_raidtick = attendance_button_raidtick
        attendance_button_raidtick.SetValue(config.SHOW_RAIDTICK_ONLY)
        if config.SHOW_RAIDTICK_ONLY:
            self.OnRaidtickOnly(None)

        # Creditt Log
        creditt_box = wx.BoxSizer(wx.HORIZONTAL)
        creditt_list = ObjectListView.ObjectListView(
            pane_2, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(650, 200))
        creditt_box.Add(creditt_list, flag=wx.EXPAND | wx.ALL)
        # creditt_list.Bind(wx.EVT_LEFT_DCLICK, self.OnEditCreditt)
        self.creditt_list = creditt_list

        creditt_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 160, "time",
                fixedWidth=160),
            ObjectListView.ColumnDefn(
                "From", "left", 120, "user",
                fixedWidth=120),
            ObjectListView.ColumnDefn(
                "Message", "left", 350, "message",
                fixedWidth=350),
        ])
        creditt_list.SetObjects(config.CREDITT_LOG)
        creditt_list.SetEmptyListMsg("No creditt messages received.")

        # Creditt Buttons
        creditt_buttons_box = wx.BoxSizer(wx.VERTICAL)
        creditt_box.Add(creditt_buttons_box,
                        flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)
        creditt_button_ignore = wx.Button(pane_2, label="Ignore Creditt")
        creditt_buttons_box.Add(creditt_button_ignore)
        creditt_button_ignore.Bind(wx.EVT_BUTTON, self.OnIgnoreCreditt)

        # Gratss Log
        gratss_box = wx.BoxSizer(wx.HORIZONTAL)
        gratss_list = ObjectListView.ObjectListView(
            pane_3, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(650, 200))
        gratss_box.Add(gratss_list, flag=wx.EXPAND | wx.ALL)
        # gratss_list.Bind(wx.EVT_LEFT_DCLICK, self.OnEditGratss)
        self.gratss_list = gratss_list

        gratss_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 160, "time",
                fixedWidth=160),
            ObjectListView.ColumnDefn(
                "From", "left", 120, "user",
                fixedWidth=120),
            ObjectListView.ColumnDefn(
                "Message", "left", 350, "message",
                fixedWidth=350),
        ])
        gratss_list.SetObjects(config.GRATSS_LOG)
        gratss_list.SetEmptyListMsg("No gratss messages received.")

        # Gratss Buttons
        gratss_buttons_box = wx.BoxSizer(wx.VERTICAL)
        gratss_box.Add(gratss_buttons_box,
                       flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)
        gratss_button_ignore = wx.Button(pane_3, label="Ignore Gratss")
        gratss_buttons_box.Add(gratss_button_ignore)
        gratss_button_ignore.Bind(wx.EVT_BUTTON, self.OnIgnoreGratss)

        # Set up Splitter
        pane_1.SetSizer(attendance_box)
        pane_2.SetSizer(creditt_box)
        pane_3.SetSizer(gratss_box)
        attendance_splitter.AppendWindow(pane_1)
        attendance_splitter.AppendWindow(pane_2)
        attendance_splitter.AppendWindow(pane_3)
        attendance_main_box.Add(attendance_splitter, 1, wx.EXPAND, 0)

        # Finalize Tab
        self.SetSizer(attendance_main_box)
        attendance_main_box.Fit(self)
        attendance_splitter.SetMinimumPaneSize(80)
        attendance_splitter.SetSashPosition(0, config.CREDITT_SASH_POS)
        attendance_splitter.SetSashPosition(1, config.GRATSS_SASH_POS)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged,
                  source=attendance_splitter)
        parent.AddPage(self, 'Attendance Logs')

    @staticmethod
    def OnSashChanged(e: wx.lib.splitter.MultiSplitterEvent):
        index, new_pos = e.GetSashIdx(), e.GetSashPosition()
        if index == 0:
            config.CREDITT_SASH_POS = new_pos
        elif index == 1:
            config.GRATSS_SASH_POS = new_pos

    def OnIgnoreCreditt(self, e: wx.Event):
        selected_object = self.creditt_list.GetSelectedObject()
        selected_index = self.creditt_list.GetFirstSelected()
        if not selected_object:
            return
        config.CREDITT_LOG.remove(selected_object)
        self.creditt_list.SetObjects(config.CREDITT_LOG)
        item_count = self.creditt_list.GetItemCount()
        if item_count > 0:
            self.creditt_list.Select(min(selected_index, item_count - 1))
        utils.store_state()

    def OnIgnoreGratss(self, e: wx.Event):
        selected_object = self.gratss_list.GetSelectedObject()
        selected_index = self.gratss_list.GetFirstSelected()
        if not selected_object:
            return
        config.GRATSS_LOG.remove(selected_object)
        self.gratss_list.SetObjects(config.GRATSS_LOG)
        item_count = self.gratss_list.GetItemCount()
        if item_count > 0:
            self.gratss_list.Select(min(selected_index, item_count - 1))
        utils.store_state()

    def OnRaidtickOnly(self, e: wx.Event):
        config.SHOW_RAIDTICK_ONLY = self.attendance_button_raidtick.IsChecked()
        config.CONF.set(
            'default', 'raidtick_filter', str(config.SHOW_RAIDTICK_ONLY))
        if config.SHOW_RAIDTICK_ONLY:
            # Filter to raidtick only
            raidticks = [x for x in config.WHO_LOG if x.raidtick]
            self.attendance_list.SetObjects(raidticks)
        else:
            self.attendance_list.SetObjects(config.WHO_LOG)
        config.write()

    def OnWhoHistory(self, e: models.WhoHistoryEvent):
        if self.attendance_button_raidtick.GetValue():
            # Filter to raidtick only
            raidticks = [x for x in config.WHO_LOG if x.raidtick]
            self.attendance_list.SetObjects(raidticks)
        else:
            self.attendance_list.SetObjects(config.WHO_LOG)

    def OnCreditt(self, e: models.CredittEvent):
        self.creditt_list.SetObjects(config.CREDITT_LOG)

    def OnGratss(self, e: models.GratssEvent):
        self.gratss_list.SetObjects(config.GRATSS_LOG)

    def OnClearApp(self, e: models.AppClearEvent):
        config.WHO_LOG.clear()
        config.CREDITT_LOG.clear()
        config.GRATSS_LOG.clear()
        self.attendance_list.SetObjects(config.WHO_LOG)
        self.creditt_list.SetObjects(config.CREDITT_LOG)
        self.gratss_list.SetObjects(config.GRATSS_LOG)
        e.Skip()

    def ShowAttendanceDetail(self, e: wx.EVT_LEFT_DCLICK):
        selected_object = self.attendance_list.GetSelectedObject()
        if not selected_object:
            return
        AttendanceDetailWindow(
            selected_object, parent=self,
            title="Attendance Record: {}".format(selected_object.time))


class AttendanceDetailWindow(wx.Frame):
    def __init__(self, item, parent=None, title="Attendance Record"):
        wx.Frame.__init__(self, parent, title=title, size=(420, 800))
        self.item = item

        main_box = wx.BoxSizer(wx.VERTICAL)

        raidtick_checkbox = wx.CheckBox(self, label="Raidtick")
        raidtick_checkbox.SetValue(item.raidtick)
        raidtick_checkbox.Bind(wx.EVT_CHECKBOX, self.OnRaidtickCheck)
        main_box.Add(raidtick_checkbox, border=10)
        self.raidtick_checkbox = raidtick_checkbox

        attendance_record = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(405, 1080), useExpansionColumn=True)
        main_box.Add(attendance_record, flag=wx.EXPAND | wx.ALL)

        def attendanceGroupKey(player):
            return config.ALLIANCE_MAP.get(player.guild, "None")

        attendance_record.SetColumns([
            ObjectListView.ColumnDefn(
                "Name", "left", 180, "name",
                groupKeyGetter=attendanceGroupKey, fixedWidth=180),
            ObjectListView.ColumnDefn(
                "Guild", "left", 180, "guild",
                groupKeyGetter=attendanceGroupKey, fixedWidth=180),
        ])
        attendance_list = [models.Player(name, None, None, guild)
                           for name, guild in item.log.items()]
        attendance_record.SetObjects(attendance_list)
        attendance_record.AlwaysShowScrollbars(False, True)

        self.SetSizer(main_box)
        self.Show()

    def OnRaidtickCheck(self, e: wx.EVT_CHECKBOX):
        self.item.raidtick = self.raidtick_checkbox.IsChecked()
        self.GetParent().OnRaidtickOnly(e)
