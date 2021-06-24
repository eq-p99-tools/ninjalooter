# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx

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
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)

        ##############################
        # Attendance Log Frame (Tab 3)
        ##############################
        attendance_main_box = wx.BoxSizer(wx.VERTICAL)
        attendance_splitter = wx.SplitterWindow(
            self, wx.ID_ANY, style=wx.SP_3D | wx.SP_BORDER)
        pane_1 = wx.Panel(attendance_splitter, wx.ID_ANY)
        pane_2 = wx.Panel(attendance_splitter, wx.ID_ANY)

        # Attendance / Raidtick List
        attendance_box = wx.BoxSizer(wx.HORIZONTAL)
        attendance_list = ObjectListView.GroupListView(
            pane_1, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(622, 600))
        attendance_box.Add(attendance_list, flag=wx.EXPAND | wx.ALL)
        attendance_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowAttendanceDetail)
        self.attendance_list = attendance_list

        attendance_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 180, "time",
                fixedWidth=180),
            ObjectListView.ColumnDefn(
                "Populations", "left", 400, "populations",
                fixedWidth=400),
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
            size=wx.Size(622, 200))
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
                "Message", "left", 322, "message",
                fixedWidth=322),
        ])
        creditt_list.SetObjects(config.CREDITT_LOG)
        creditt_list.SetEmptyListMsg("No creditt/gratss messages received.")

        # Creditt Buttons
        creditt_buttons_box = wx.BoxSizer(wx.VERTICAL)
        creditt_box.Add(creditt_buttons_box,
                        flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)
        creditt_button_ignore = wx.Button(pane_2, label="Ignore Creditt")
        creditt_buttons_box.Add(creditt_button_ignore)
        creditt_button_ignore.Bind(wx.EVT_BUTTON, self.OnIgnoreCreditt)

        # Set up Splitter
        pane_1.SetSizer(attendance_box)
        pane_2.SetSizer(creditt_box)
        attendance_splitter.SplitHorizontally(pane_1, pane_2)
        attendance_main_box.Add(attendance_splitter, 1, wx.EXPAND, 0)

        # Finalize Tab
        self.SetSizer(attendance_main_box)
        attendance_main_box.Fit(self)
        attendance_splitter.SetSashPosition(500)
        parent.AddPage(self, 'Attendance Logs [WORK IN PROGRESS]')

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

    def OnClearApp(self, e: models.AppClearEvent):
        config.WHO_LOG.clear()
        self.attendance_list.SetObjects(config.WHO_LOG)
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
        main_box = wx.BoxSizer(wx.HORIZONTAL)

        attendance_record = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(405, 1080))
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
