# pylint: disable=no-member,invalid-name,unused-argument
import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import models


class AttendanceFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_WHO_HISTORY,
                                   self.OnWhoHistory)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)

        ##############################
        # Attendance Log Frame (Tab 3)
        ##############################
        attendance_main_box = wx.BoxSizer(wx.VERTICAL)

        # List
        attendance_list = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(600, 1080))
        attendance_main_box.Add(attendance_list, flag=wx.EXPAND | wx.ALL)
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

        # Finalize Tab
        self.SetSizer(attendance_main_box)
        parent.AddPage(self, 'Attendance Logs [WORK IN PROGRESS]')

    def OnWhoHistory(self, e: models.WhoHistoryEvent):
        self.attendance_list.SetObjects(config.WHO_LOG)

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
