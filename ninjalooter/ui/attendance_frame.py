# pylint: disable=no-member,invalid-name,unused-argument,duplicate-code
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
            size=wx.Size(680, 600))
        attendance_box.Add(attendance_list, flag=wx.EXPAND | wx.ALL)
        attendance_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowAttendanceDetail)
        attendance_list.Bind(wx.EVT_RIGHT_DCLICK, self.OnMarkRaidtick)
        self.attendance_list = attendance_list

        attendance_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Time", "left", 140, "time",
                fixedWidth=140),
            ObjectListView.ColumnDefn(
                "Name", "left", 140, "tick_name",
                fixedWidth=140),
            ObjectListView.ColumnDefn(
                "RT", "left", 25, "raidtick_display",
                fixedWidth=25),
            ObjectListView.ColumnDefn(
                "Populations", "left", 357, "populations",
                fixedWidth=357),
        ])
        attendance_list.SetObjects(config.ATTENDANCE_LOGS)
        attendance_list.SetEmptyListMsg(
            "No who log history.\nPlease type `/who` ingame.")
        attendance_list.SetToolTip(
            "Double left-click an attendance record to edit it in a detailed "
            "view.\n"
            "Double right-click an attendance record to toggle its RaidTick "
            "status.")

        # Attendance / Raidtick Buttons
        attendance_buttons_box = wx.BoxSizer(wx.VERTICAL)
        attendance_box.Add(attendance_buttons_box,
                           flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)
        attendance_button_raidtick = wx.CheckBox(
            pane_1, label="Show RaidTicks Only")
        attendance_buttons_box.Add(attendance_button_raidtick,
                                   flag=wx.ALL, border=6)
        attendance_button_raidtick.Bind(wx.EVT_CHECKBOX, self.OnRaidtickOnly)
        self.attendance_button_raidtick = attendance_button_raidtick
        attendance_button_raidtick.SetValue(config.SHOW_RAIDTICK_ONLY)
        if config.SHOW_RAIDTICK_ONLY:
            self.OnRaidtickOnly(None)

        attendance_toggle_raidtick = wx.Button(
            pane_1, label="Toggle RaidTick", size=(140, 22))
        attendance_toggle_raidtick.Bind(wx.EVT_BUTTON, self.OnMarkRaidtick)
        attendance_buttons_box.Add(
            attendance_toggle_raidtick, border=5, flag=wx.ALL)

        attendance_use_raidgroups = wx.Button(
            pane_1, label="Calculate Raid Groups", size=(140, 22))
        attendance_use_raidgroups.Bind(wx.EVT_BUTTON, self.OnCalcRaidGroups)
        attendance_buttons_box.Add(
            attendance_use_raidgroups, border=5, flag=wx.ALL)

        # Creditt Log
        creditt_box = wx.BoxSizer(wx.HORIZONTAL)
        creditt_list = ObjectListView.ObjectListView(
            pane_2, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(680, 200))
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
        creditt_button_ignore = wx.Button(
            pane_2, label="Ignore Creditt", size=(140, 22))
        creditt_buttons_box.Add(creditt_button_ignore)
        creditt_button_ignore.Bind(wx.EVT_BUTTON, self.OnIgnoreCreditt)

        # Gratss Log
        gratss_box = wx.BoxSizer(wx.HORIZONTAL)
        gratss_list = ObjectListView.ObjectListView(
            pane_3, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(680, 200))
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
        gratss_button_ignore = wx.Button(
            pane_3, label="Ignore Gratss", size=(140, 22))
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
        self.RefreshList()
        config.write()

    def RefreshList(self):
        if config.SHOW_RAIDTICK_ONLY:
            # Filter to raidtick only
            raidticks = [x for x in config.ATTENDANCE_LOGS if x.raidtick]
            self.attendance_list.SetObjects(raidticks)
        else:
            self.attendance_list.SetObjects(config.ATTENDANCE_LOGS)

    def OnCalcRaidGroups(self, e: wx.Event):
        selected_tick = self.attendance_list.GetSelectedObject()
        if selected_tick:
            config.RAID_GROUPS.build_groups(list(selected_tick.log.values()))
            wx.PostEvent(self.GetGrandParent(), models.CalcRaidGroupsEvent())
        print("raidgroups")

    def OnWhoHistory(self, e: models.WhoHistoryEvent):
        if self.attendance_button_raidtick.GetValue():
            # Filter to raidtick only
            raidticks = [x for x in config.ATTENDANCE_LOGS if x.raidtick]
            self.attendance_list.SetObjects(raidticks)
        else:
            self.attendance_list.SetObjects(config.ATTENDANCE_LOGS)

    def OnCreditt(self, e: models.CredittEvent):
        self.creditt_list.SetObjects(config.CREDITT_LOG)

    def OnGratss(self, e: models.GratssEvent):
        self.gratss_list.SetObjects(config.GRATSS_LOG)

    def OnClearApp(self, e: models.AppClearEvent):
        config.ATTENDANCE_LOGS.clear()
        config.CREDITT_LOG.clear()
        config.GRATSS_LOG.clear()
        self.attendance_list.SetObjects(config.ATTENDANCE_LOGS)
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

    def OnMarkRaidtick(self, e: wx.EVT_RIGHT_DCLICK):
        selected_object = self.attendance_list.GetSelectedObject()
        if not selected_object:
            return
        selected_object.raidtick = not selected_object.raidtick
        self.OnRaidtickOnly(e)
        self.attendance_list.SelectObject(selected_object)
        utils.store_state()


class AttendanceDetailWindow(wx.Frame):
    def __init__(self, item, parent=None, title="Attendance Record"):
        wx.Frame.__init__(self, parent, title=title, size=(510, 800))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.item = item

        main_box = wx.BoxSizer(wx.VERTICAL)
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        main_box.Add(button_box, border=5)

        add_button = wx.Button(self, label="Add Player")
        add_button.Bind(wx.EVT_BUTTON, self.OnAddPlayer)
        button_box.Add(add_button, border=5, flag=wx.ALL)

        remove_button = wx.Button(self, label="Remove Player")
        remove_button.Bind(wx.EVT_BUTTON, self.OnRemovePlayer)
        button_box.Add(remove_button, border=5, flag=wx.ALL)

        self.name_textbox = wx.TextCtrl(self, id=wx.ID_ANY, size=(130, 22),
                                        value=item.tick_name or "")
        if self.item.zone:
            self.name_textbox.SetHint(f"{self.item.zone}?")
        else:
            self.name_textbox.SetHint("Tick Name?")
        button_box.Add(self.name_textbox, flag=wx.TOP | wx.LEFT, border=6)

        raidtick_checkbox = wx.CheckBox(self, label="Raidtick")
        raidtick_checkbox.SetValue(item.raidtick)
        bs = wx.SizerFlags().Border(wx.LEFT, 5).CenterVertical()
        button_box.Add(raidtick_checkbox, bs)
        self.raidtick_checkbox = raidtick_checkbox

        attendance_record = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(405, 1080), useExpansionColumn=True)
        attendance_record.CopyObjectsToClipboard = self.CopyObjectsToClipboard
        main_box.Add(attendance_record, flag=wx.EXPAND | wx.ALL)
        self.attendance_record = attendance_record

        def attendanceGroupKey(player):
            return config.ALLIANCE_MAP.get(player.guild, "No Alliance")

        attendance_record.SetColumns([
            ObjectListView.ColumnDefn(
                "Name", "left", 160, "name",
                groupKeyGetter=attendanceGroupKey, fixedWidth=160),
            ObjectListView.ColumnDefn(
                "Guild", "left", 140, "sortguild",
                groupKeyGetter=attendanceGroupKey, fixedWidth=140),
            ObjectListView.ColumnDefn(
                "Level", "left", 40, "level",
                groupKeyGetter=attendanceGroupKey, fixedWidth=40),
            ObjectListView.ColumnDefn(
                "Class", "left", 110, "sortclass",
                groupKeyGetter=attendanceGroupKey, fixedWidth=110),
        ])
        attendance_list = list(item.log.values())
        attendance_record.SetObjects(attendance_list)
        attendance_record.AlwaysShowScrollbars(False, True)

        self.SetSizer(main_box)
        if config.ALWAYS_ON_TOP:
            self.SetWindowStyle(
                self.GetWindowStyle() | wx.STAY_ON_TOP)
        self.Show()

    def CopyObjectsToClipboard(self, objects):
        """
        Put a textual representation of the given objects onto the clipboard.

        Custom version of the copy text from a tick line:

        [Sun Jul 17 10:22:15 2022] [ANONYMOUS] Player <Guild> {## Class}
        """
        if objects is None or len(objects) == 0:
            return

        # Get all the values of the given rows into multi-list
        rows = self.attendance_record._GetValuesAsMultiList(objects)

        # Make a text version of the values
        lines = [
            (f"[{self.item.eqtime()}] [ANONYMOUS] "
             f"{x[0]} <{x[1]}> {{{x[2]} {x[3]}}}") for x in rows]
        txt = "\n".join(lines) + "\n"

        # Make a html version on Windows
        try:
            lines = ["<td>" + "</td><td>".join(x) + "</td>" for x in rows]
            html = "<table><tr>" + "</tr><tr>".join(lines) + "</tr></table>"
            self.attendance_record._PutTextAndHtmlToClipboard(txt, html)
        except ImportError:
            cb = wx.Clipboard()
            if cb.Open():
                cb.SetData(wx.TextDataObject(txt))
                cb.Flush()
                cb.Close()

    def OnRemovePlayer(self, e: wx.EVT_BUTTON):
        selected_player = self.attendance_record.GetSelectedObject()
        if not selected_player:
            return

        self.item.log.pop(selected_player.name)
        self.attendance_record.RemoveObject(selected_player)
        self.Update()
        utils.store_state()

    def OnAddPlayer(self, e: wx.EVT_BUTTON):
        name_dialog = wx.TextEntryDialog(self, "Player name:", "Add Player")
        result = name_dialog.ShowModal()
        player_name = name_dialog.GetValue().capitalize()
        name_dialog.Destroy()
        if result != wx.ID_OK or not player_name:
            return

        player_guild = config.ALLIANCES[config.DEFAULT_ALLIANCE][0]
        player_record = models.Player(player_name, None, None, player_guild)
        if player_name in config.PLAYER_DB:
            player_record = config.PLAYER_DB[player_name]

        self.item.log[player_name] = player_record
        self.attendance_record.AddObject(player_record)
        self.attendance_record.Update()
        utils.store_state()

    def OnClose(self, e: wx.EVT_CLOSE):
        self.item.raidtick = self.raidtick_checkbox.IsChecked()
        self.item.tick_name = self.name_textbox.GetValue()
        self.GetParent().RefreshList()
        utils.store_state()
        self.Destroy()
