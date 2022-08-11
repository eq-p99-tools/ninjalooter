# pylint: disable=no-member,invalid-name,unused-argument
# pylint: disable=too-many-instance-attributes

import datetime
import os.path

import wx
import wx.adv

from ninjalooter import config
from ninjalooter import logger
from ninjalooter import logparse
from ninjalooter import logreplay
from ninjalooter import models
from ninjalooter.ui import bidding_frame
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logger.getLogger(__name__)


class MenuBar(wx.MenuBar):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._parent = parent

        #############
        # File Menu #
        #############
        file_menu = wx.Menu()

        set_log_mi = wx.MenuItem(file_menu, wx.ID_FIND, '&Set Log Directory')
        set_log_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "gear.png"))
        set_log_mi.SetBitmap(set_log_bitmap)
        file_menu.Append(set_log_mi)
        self.Bind(wx.EVT_MENU, self.OnConfigure, set_log_mi)

        self.autoswap_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Auto-Switch Characters',
            kind=wx.ITEM_CHECK)
        file_menu.Append(self.autoswap_mi)
        self.autoswap_mi.Check(config.AUTO_SWAP_LOGFILE)
        self.Bind(wx.EVT_MENU, self.OnAutoSwapLogfile, self.autoswap_mi)

        self.alwaysontop_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, '&Always On Top',
            kind=wx.ITEM_CHECK)
        file_menu.Append(self.alwaysontop_mi)
        self.alwaysontop_mi.Check(config.ALWAYS_ON_TOP)
        self.Bind(wx.EVT_MENU, self.OnAlwaysOnTop, self.alwaysontop_mi)

        self.confirm_exit_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Confirm Exit',
            kind=wx.ITEM_CHECK)
        file_menu.Append(self.confirm_exit_mi)
        self.confirm_exit_mi.Check(config.CONFIRM_EXIT)
        self.Bind(wx.EVT_MENU, self.ConfirmExit, self.confirm_exit_mi)

        file_menu.AppendSeparator()

        self.export_tz_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, 'Export in Eastern Time',
            kind=wx.ITEM_CHECK)
        file_menu.Append(self.export_tz_mi)
        self.export_tz_mi.Check(config.EXPORT_TIME_IN_EASTERN)
        self.Bind(wx.EVT_MENU, self.OnExportTimezone, self.export_tz_mi)

        export_excel_mi = wx.MenuItem(
            file_menu, wx.ID_FLOPPY, '&Export to Excel\tCtrl+E')
        export_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "excel.png"))
        export_excel_mi.SetBitmap(export_bitmap)
        file_menu.Append(export_excel_mi)
        export_excel_mi.Enable(config.ALLOW_EXCEL_EXPORT)
        self.Bind(wx.EVT_MENU, self.OnExportExcel, export_excel_mi)

        export_dkp_mi = wx.MenuItem(
            file_menu, wx.ID_CONVERT, '&Export to EQDKPlus\tCtrl+P')
        export_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "export.png"))
        export_dkp_mi.SetBitmap(export_bitmap)
        file_menu.Append(export_dkp_mi)
        self.Bind(wx.EVT_MENU, self.OnExportEQDKP, export_dkp_mi)

        file_menu.AppendSeparator()

        replay_mi = wx.MenuItem(file_menu, wx.ID_OPEN, '&Replay Log File')
        replay_mi.Enable(False)
        replay_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "reload.png"))
        replay_mi.SetBitmap(replay_bitmap)
        file_menu.Append(replay_mi)
        self.Bind(wx.EVT_MENU, self.OnReplayLog, replay_mi)

        clear_mi = wx.MenuItem(file_menu, wx.ID_NEW, '&Clear Data')
        clear_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "clear.png"))
        clear_mi.SetBitmap(clear_bitmap)
        file_menu.Append(clear_mi)
        self.Bind(wx.EVT_MENU, self.OnClearApp, clear_mi)

        file_menu.AppendSeparator()

        exit_mi = wx.MenuItem(file_menu, wx.ID_EXIT, '&Quit\tCtrl+W')
        exit_bitmap = wx.Bitmap(os.path.join(
            config.PROJECT_DIR, "data", "icons", "exit.png"))
        exit_mi.SetBitmap(exit_bitmap)
        file_menu.Append(exit_mi)
        self.Bind(wx.EVT_MENU, parent.OnClose, exit_mi)

        self.Append(file_menu, '&File')

        ################
        # Bidding Menu #
        ################
        bidding_menu = wx.Menu()

        show_ignored_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, '&Show Ignored Items...')
        bidding_menu.Append(show_ignored_mi)
        self.Bind(wx.EVT_MENU, self.OnShowIgnored, show_ignored_mi)

        bidding_menu.AppendSeparator()

        self.alliance_menu = wx.Menu()
        for alliance in config.ALLIANCES:
            alliance_item = wx.MenuItem(
                self.alliance_menu, wx.ID_ANY, alliance, kind=wx.ITEM_RADIO)
            self.alliance_menu.Append(alliance_item)
            if config.DEFAULT_ALLIANCE == alliance:
                alliance_item.Check()
            self.Bind(wx.EVT_MENU, self.OnSetAlliance, alliance_item)
        bidding_menu.AppendSubMenu(self.alliance_menu, '&Alliance')

        drop_chan_menu = wx.Menu()
        for channel in config.DROP_CHANNEL_OPTIONS:
            channel_item = wx.MenuItem(
                drop_chan_menu, wx.ID_ANY, channel, kind=wx.ITEM_CHECK)
            drop_chan_menu.Append(channel_item)
            if config.DROP_CHANNEL_OPTIONS[channel] in config.MATCH_DROP:
                channel_item.Check()
            self.Bind(wx.EVT_MENU, self.OnSetDropChannel, channel_item)
        bidding_menu.AppendSubMenu(drop_chan_menu, '&Drop Channels')

        bid_chan_menu = wx.Menu()
        for channel in config.BID_CHANNEL_OPTIONS:
            channel_item = wx.MenuItem(
                bid_chan_menu, wx.ID_ANY, channel, kind=wx.ITEM_CHECK)
            bid_chan_menu.Append(channel_item)
            if config.BID_CHANNEL_OPTIONS[channel] in config.MATCH_BID:
                channel_item.Check()
            self.Bind(wx.EVT_MENU, self.OnSetBidChannel, channel_item)
        bidding_menu.AppendSubMenu(bid_chan_menu, '&Bid Channels')

        self.restrict_bids_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, 'Restrict Bids to Alliance',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.restrict_bids_mi)
        self.restrict_bids_mi.Check(config.RESTRICT_BIDS)
        self.Bind(wx.EVT_MENU, self.OnRestrictBids, self.restrict_bids_mi)

        self.restrict_exports_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, '&Restrict Export to Alliance',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.restrict_exports_mi)
        self.restrict_exports_mi.Check(config.RESTRICT_EXPORT)
        self.Bind(wx.EVT_MENU, self.OnRestrictExport, self.restrict_exports_mi)

        self.nodrop_only_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, '&Ignore Droppable Items',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.nodrop_only_mi)
        self.nodrop_only_mi.Check(config.NODROP_ONLY)
        self.Bind(wx.EVT_MENU, self.OnNodropOnly, self.nodrop_only_mi)

        self.tick_before_loot_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, 'Tick Before Loot (Quake Mode)',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.tick_before_loot_mi)
        self.tick_before_loot_mi.Check(config.TICK_BEFORE_LOOT)
        self.Bind(wx.EVT_MENU, self.OnTickBeforeLoot, self.tick_before_loot_mi)

        self.remember_guild_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, 'Remember &Guild Affiliations',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.remember_guild_mi)
        self.remember_guild_mi.Check(config.REMEMBER_GUILD_AFFILIATION)
        self.Bind(wx.EVT_MENU, self.OnRememberGuild, self.remember_guild_mi)

        bidding_menu.AppendSeparator()

        self.audio_alerts_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, 'Use &Audio Alerts',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.audio_alerts_mi)
        self.audio_alerts_mi.Check(config.AUDIO_ALERTS)
        self.Bind(wx.EVT_MENU, self.OnAudioAlerts, self.audio_alerts_mi)

        self.text_alerts_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, 'Use &Text Alerts',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.text_alerts_mi)
        self.text_alerts_mi.Check(config.TEXT_ALERTS)
        self.Bind(wx.EVT_MENU, self.OnTextAlerts, self.text_alerts_mi)

        self.Append(bidding_menu, '&Bidding')

        parent.SetMenuBar(self)

    def OnReplayLog(self, e: wx.MenuEvent):
        LOG.info("Attempting to replay an eqlog...")
        openFileDialog = wx.FileDialog(
            self.GetParent(), "Open EQ Logfile", "D:\\EverQuest\\Logs\\", "",
            "EQ Logfile (eqlog_*.txt)|eqlog_*.txt", wx.FD_OPEN)

        result = openFileDialog.ShowModal()
        filename = openFileDialog.GetPath()
        openFileDialog.Destroy()
        if result != wx.ID_OK:
            return
        config.PLAYER_NAME = utils.get_character_name_from_logfile(filename)

        # Load the lines from the logfile
        with open(filename, 'r') as logfile:
            loglines = logfile.readlines()

        # Get the timestamp bounds
        try:
            first_time = utils.get_first_timestamp(loglines)
            last_time = utils.get_first_timestamp(reversed(loglines))
            LOG.info("%s -> %s", first_time, last_time)
            if not first_time and last_time:
                raise ValueError()
        except (TypeError, ValueError):
            LOG.exception("Failed to find a first/last timestamp")
            self.DialogParseFail()
            return

        time_select_dialog = wx.Dialog(
            self.GetParent(), title="Select Time Bounds")
        time_select_main_box = wx.BoxSizer(wx.VERTICAL)

        # Time Bounds
        time_select_bounds_box = wx.GridBagSizer(3, 2)
        bold_font = wx.Font(10, wx.DEFAULT, wx.DEFAULT, wx.BOLD)
        from_label = wx.StaticText(time_select_dialog, label="From")
        from_label.SetFont(bold_font)
        date_chooser_from = wx.adv.DatePickerCtrl(time_select_dialog)
        date_chooser_from.SetValue(first_time)
        date_chooser_from.SetRange(first_time, last_time)
        time_chooser_from = wx.adv.TimePickerCtrl(time_select_dialog)
        time_chooser_from.SetValue(first_time)
        to_label = wx.StaticText(time_select_dialog, label="To")
        to_label.SetFont(bold_font)
        date_chooser_to = wx.adv.DatePickerCtrl(time_select_dialog)
        date_chooser_to.SetValue(last_time)
        date_chooser_to.SetRange(first_time, last_time)
        time_chooser_to = wx.adv.TimePickerCtrl(time_select_dialog)
        time_chooser_to.SetValue(last_time)
        time_select_bounds_box.Add(
            from_label, pos=(0, 0), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        time_select_bounds_box.Add(
            date_chooser_from, pos=(0, 1), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALL)
        time_select_bounds_box.Add(
            time_chooser_from, pos=(0, 2), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALL)
        time_select_bounds_box.Add(
            to_label, pos=(1, 0), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL | wx.ALL)
        time_select_bounds_box.Add(
            date_chooser_to, pos=(1, 1), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALL)
        time_select_bounds_box.Add(
            time_chooser_to, pos=(1, 2), border=2,
            flag=wx.ALIGN_RIGHT | wx.ALL)

        # Buttons
        time_select_buttons_box = time_select_dialog.CreateButtonSizer(
            wx.OK | wx.CANCEL)

        time_select_main_box.Add(time_select_bounds_box, border=10,
                                 flag=wx.ALL | wx.EXPAND)
        time_select_main_box.Add(time_select_buttons_box, border=10,
                                 flag=wx.BOTTOM | wx.RIGHT | wx.EXPAND)
        time_select_dialog.SetSizer(time_select_main_box)
        time_select_dialog.Fit()

        # Show the modal
        if time_select_dialog.ShowModal() != wx.ID_OK:
            time_select_dialog.Destroy()
            return

        time_select_dialog.Destroy()

        fd, ft = date_chooser_from.GetValue(), time_chooser_from.GetValue()
        fdt = datetime.datetime(*map(int, fd.FormatISODate().split('-')),
                                *map(int, ft.FormatISOTime().split(':')))
        td, tt = date_chooser_to.GetValue(), time_chooser_to.GetValue()
        tdt = datetime.datetime(*map(int, td.FormatISODate().split('-')),
                                *map(int, tt.FormatISOTime().split(':')))
        first_index = utils.find_timestamp(loglines, fdt)
        last_index = utils.find_timestamp(loglines, tdt)
        if first_index is None or last_index is None:
            # can't parse those times
            LOG.error(
                "Couldn't find the first (%s) or last (%s) log line index.",
                first_index, last_index
            )
            self.DialogParseFail()
            return
        LOG.debug("Times: %s -> %s", fdt, tdt)
        LOG.debug("First line: %s", loglines[first_index])
        LOG.debug("Last line: %s", loglines[max(last_index - 1, 0)])
        picked_lines = loglines[first_index:last_index]
        total_picked_lines = len(picked_lines)
        parse_progress_dialog = wx.GenericProgressDialog(
            title="Parsing Logs...",
            message="Please wait while your logfile is parsed.",
            maximum=total_picked_lines,
            parent=self.GetParent(),
            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_CAN_ABORT |
                  wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME
        )

        logreplay.replay_logs(picked_lines, parse_progress_dialog)
        self.GetParent().bidding_frame.OnHideRot(None)
        parse_progress_dialog.Destroy()

    def DialogParseFail(self):
        dlg = wx.MessageDialog(
            self,
            "Failed to parse the selected file.\n"
            "Are you certain it is a valid EverQuest log file?",
            "Log Parse Error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    @staticmethod
    def OnSetAlliance(e: wx.MenuEvent):
        menu_item = [mi for mi in e.EventObject.MenuItems if mi.Id == e.Id][0]
        config.DEFAULT_ALLIANCE = menu_item.ItemLabel
        config.CONF.set(
            'default', 'default_alliance', config.DEFAULT_ALLIANCE)
        config.write()

    @staticmethod
    def OnSetDropChannel(e: wx.MenuEvent):
        selected_channels = [
            mi.ItemLabel
            for mi in e.EventObject.MenuItems
            if mi.IsChecked()
        ]
        config.MATCH_DROP = [
            config.DROP_CHANNEL_OPTIONS[chan]
            for chan in selected_channels
        ]
        logparse.reset_matchers()
        config.CONF.set('default', 'drop_channels',
                        ','.join(selected_channels))
        config.write()

    @staticmethod
    def OnSetBidChannel(e: wx.MenuEvent):
        selected_channels = [
            mi.ItemLabel
            for mi in e.EventObject.MenuItems
            if mi.IsChecked()
        ]
        config.MATCH_BID = [
            config.BID_CHANNEL_OPTIONS[chan]
            for chan in selected_channels
        ]
        logparse.reset_matchers()
        config.CONF.set('default', 'bid_channels',
                        ','.join(selected_channels))
        config.write()

    def OnConfigure(self, e: wx.MenuEvent):
        existing_logdir = config.LOG_DIRECTORY
        if not os.path.isdir(existing_logdir):
            existing_logdir = os.path.dirname(existing_logdir)
        openFileDialog = wx.DirDialog(
            self.GetParent(), "Select Log Directory", existing_logdir,
            wx.DD_DIR_MUST_EXIST)

        result = openFileDialog.ShowModal()
        selected = openFileDialog.GetPath()
        openFileDialog.Destroy()
        if result == wx.ID_OK:
            LOG.info("Selected log directory: %s", selected)
            config.LOG_DIRECTORY = selected
            config.CONF.set('default', 'logdir', selected)
            config.write()
            self.GetParent().parser_thread.abort()
            self.GetParent().parser_thread = logparse.ParseThread(
                self.GetParent())
            self.GetParent().parser_thread.start()
            if config.WX_FILESYSTEM_WATCHER is not None:
                config.WX_FILESYSTEM_WATCHER.RemoveAll()
                config.WX_FILESYSTEM_WATCHER.Add(
                    config.LOG_DIRECTORY,
                    events=wx.FSW_EVENT_CREATE | wx.FSW_EVENT_MODIFY)

    def OnExportTimezone(self, e: wx.MenuEvent):
        config.EXPORT_TIME_IN_EASTERN = self.export_tz_mi.IsChecked()
        config.CONF.set(
            'default', 'export_time_in_eastern',
            str(config.EXPORT_TIME_IN_EASTERN))
        config.write()

    def OnExportExcel(self, e: wx.MenuEvent):
        LOG.info("Exporting to Excel format.")
        saveFileDialog = wx.FileDialog(
            self.GetParent(), "Export to Excel", "", "",
            "Excel Spreadsheet (*.xlsx)|*.xlsx", wx.FD_SAVE)

        result = saveFileDialog.ShowModal()
        filename = saveFileDialog.GetPath()
        if not filename.endswith(".xlsx"):
            filename = filename + ".xlsx"
        saveFileDialog.Destroy()
        if result == wx.ID_OK:
            result = utils.export_to_excel(filename)
            if not result:
                dlg = wx.MessageDialog(
                    self,
                    "Failed to export data. The most common cause of this\n"
                    "error is attempting to export to a file that is still "
                    "open\nin Excel.",
                    "Failed to Export", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                dlg = wx.MessageDialog(
                    self,
                    "Successfully exported data to:\n%s" % filename,
                    "Export Complete", wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

    def OnExportEQDKP(self, e: wx.MenuEvent):
        LOG.info("Exporting to EQDKPlus format.")
        saveFileDialog = wx.FileDialog(
            self.GetParent(), "Export to EQDKPlus", "", "",
            "Excel Spreadsheet (*.xlsx)|*.xlsx", wx.FD_SAVE)

        result = saveFileDialog.ShowModal()
        filename = saveFileDialog.GetPath()
        if not filename.endswith(".xlsx"):
            filename = filename + ".xlsx"
        saveFileDialog.Destroy()
        if result == wx.ID_OK:
            result = utils.export_to_eqdkp(filename)
            if not result:
                dlg = wx.MessageDialog(
                    self,
                    "Failed to export data. The most common cause of this\n"
                    "error is attempting to export to a file that is still "
                    "open\nin Excel.",
                    "Failed to Export", wx.OK | wx.ICON_ERROR)
                dlg.ShowModal()
                dlg.Destroy()
            else:
                dlg = wx.MessageDialog(
                    self,
                    "Successfully exported data to:\n%s" % filename,
                    "Export Complete", wx.OK | wx.ICON_INFORMATION)
                dlg.ShowModal()
                dlg.Destroy()

    def OnClearApp(self, e: wx.MenuEvent):
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to clear all data?",
            "Confirm Clear", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            utils.store_state(backup=True)
            wx.PostEvent(self.GetParent(), models.AppClearEvent())
            utils.clear_alerts()

    def OnRestrictBids(self, e: wx.MenuEvent):
        config.RESTRICT_BIDS = self.restrict_bids_mi.IsChecked()
        config.CONF.set(
            'default', 'restrict_bids', str(config.RESTRICT_BIDS))
        config.write()

    def OnRestrictExport(self, e: wx.MenuEvent):
        config.RESTRICT_EXPORT = self.restrict_exports_mi.IsChecked()
        config.CONF.set(
            'default', 'restrict_export', str(config.RESTRICT_EXPORT))
        config.write()

    def OnNodropOnly(self, e: wx.MenuEvent):
        config.NODROP_ONLY = self.nodrop_only_mi.IsChecked()
        config.CONF.set(
            'default', 'nodrop_only', str(config.NODROP_ONLY))
        config.write()

    def OnTickBeforeLoot(self, e: wx.MenuEvent):
        config.TICK_BEFORE_LOOT = self.tick_before_loot_mi.IsChecked()
        config.CONF.set(
            'default', 'tick_before_loot', str(config.TICK_BEFORE_LOOT))
        config.write()

    def OnRememberGuild(self, e: wx.MenuEvent):
        config.REMEMBER_GUILD_AFFILIATION = self.remember_guild_mi.IsChecked()
        config.CONF.set(
            'default', 'remember_guild_affiliation',
            str(config.REMEMBER_GUILD_AFFILIATION))
        config.write()

    def OnAudioAlerts(self, e: wx.MenuEvent):
        config.AUDIO_ALERTS = self.audio_alerts_mi.IsChecked()
        config.CONF.set(
            'alerts', 'audio_enabled', str(config.AUDIO_ALERTS))
        config.write()

    def OnTextAlerts(self, e: wx.MenuEvent):
        config.TEXT_ALERTS = self.text_alerts_mi.IsChecked()
        config.CONF.set(
            'alerts', 'text_enabled', str(config.TEXT_ALERTS))
        config.write()

    def OnAlwaysOnTop(self, e: wx.MenuEvent):
        config.ALWAYS_ON_TOP = self.alwaysontop_mi.IsChecked()
        config.CONF.set(
            'default', 'always_on_top', str(config.ALWAYS_ON_TOP))
        self.GetParent().UpdateAlwaysOnTop()
        config.write()

    def ConfirmExit(self, e: wx.MenuEvent):
        config.CONFIRM_EXIT = self.confirm_exit_mi.IsChecked()
        config.CONF.set(
            'default', 'confirm_exit', str(config.CONFIRM_EXIT))
        config.write()

    def OnAutoSwapLogfile(self, e: wx.MenuEvent):
        config.AUTO_SWAP_LOGFILE = self.autoswap_mi.IsChecked()
        config.CONF.set(
            'default', 'auto_swap_logfile', str(config.AUTO_SWAP_LOGFILE))
        config.write()

    def OnShowIgnored(self, e: wx.MenuEvent):
        bidding_frame.IgnoredItemsWindow(parent=self.GetParent())
