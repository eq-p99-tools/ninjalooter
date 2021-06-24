# pylint: disable=no-member,invalid-name,unused-argument

import os.path

import wx

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import logparse
from ninjalooter import models
from ninjalooter.ui import bidding_frame
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


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
            utils.PROJECT_DIR, "data", "icons", "gear.png"))
        set_log_mi.SetBitmap(set_log_bitmap)
        file_menu.Append(set_log_mi)
        self.Bind(wx.EVT_MENU, self.OnConfigure, set_log_mi)

        self.alwaysontop_mi = wx.MenuItem(
            file_menu, wx.ID_ANY, '&Always On Top',
            kind=wx.ITEM_CHECK)
        file_menu.Append(self.alwaysontop_mi)
        self.alwaysontop_mi.Check(config.ALWAYS_ON_TOP)
        self.Bind(wx.EVT_MENU, self.OnAlwaysOnTop, self.alwaysontop_mi)

        file_menu.AppendSeparator()

        export_mi = wx.MenuItem(
            file_menu, wx.ID_FLOPPY, '&Export to Excel\tCtrl+E')
        export_bitmap = wx.Bitmap(os.path.join(
            utils.PROJECT_DIR, "data", "icons", "export.png"))
        export_mi.SetBitmap(export_bitmap)
        file_menu.Append(export_mi)
        self.Bind(wx.EVT_MENU, self.OnExportExcel, export_mi)

        export_mi = wx.MenuItem(
            file_menu, wx.ID_FLOPPY, '&Export to EQDKPlus\tCtrl+P')
        export_bitmap = wx.Bitmap(os.path.join(
            utils.PROJECT_DIR, "data", "icons", "export.png"))
        export_mi.SetBitmap(export_bitmap)
        file_menu.Append(export_mi)
        self.Bind(wx.EVT_MENU, self.OnExportEQDKP, export_mi)

        clear_mi = wx.MenuItem(file_menu, wx.ID_NEW, '&Clear Data')
        clear_bitmap = wx.Bitmap(os.path.join(
            utils.PROJECT_DIR, "data", "icons", "clear.png"))
        clear_mi.SetBitmap(clear_bitmap)
        file_menu.Append(clear_mi)
        self.Bind(wx.EVT_MENU, self.OnClearApp, clear_mi)

        file_menu.AppendSeparator()

        exit_mi = wx.MenuItem(file_menu, wx.ID_EXIT, '&Quit\tCtrl+W')
        exit_bitmap = wx.Bitmap(os.path.join(
            utils.PROJECT_DIR, "data", "icons", "exit.png"))
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

        alliance_menu = wx.Menu()
        for alliance in config.ALLIANCES:
            alliance_item = wx.MenuItem(
                alliance_menu, wx.ID_ANY, alliance, kind=wx.ITEM_RADIO)
            alliance_menu.Append(alliance_item)
            if config.DEFAULT_ALLIANCE == alliance:
                alliance_item.Check()
            self.Bind(wx.EVT_MENU, self.OnSetAlliance, alliance_item)
        bidding_menu.AppendSubMenu(alliance_menu, '&Alliance')

        self.restrict_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, '&Restrict to Alliance',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.restrict_mi)
        self.restrict_mi.Check(config.RESTRICT_BIDS)
        self.Bind(wx.EVT_MENU, self.OnRestrict, self.restrict_mi)

        self.nodrop_only_mi = wx.MenuItem(
            bidding_menu, wx.ID_ANY, '&Ignore Droppable Items',
            kind=wx.ITEM_CHECK)
        bidding_menu.Append(self.nodrop_only_mi)
        self.nodrop_only_mi.Check(config.NODROP_ONLY)
        self.Bind(wx.EVT_MENU, self.OnNodropOnly, self.nodrop_only_mi)

        self.Append(bidding_menu, '&Bidding')

        parent.SetMenuBar(self)

    def OnSetAlliance(self, e: wx.MenuEvent):
        menu_item = [mi for mi in e.EventObject.MenuItems if mi.Id == e.Id][0]
        config.DEFAULT_ALLIANCE = menu_item.ItemLabel
        config.CONF.set(
            'default', 'default_alliance', config.DEFAULT_ALLIANCE)
        config.write()

    def OnConfigure(self, e: wx.MenuEvent):
        existing_logdir = config.LOG_DIRECTORY
        if not os.path.isdir(existing_logdir):
            existing_logdir = os.path.dirname(existing_logdir)
        openFileDialog = wx.DirDialog(
            self.Parent, "Select Log Directory", existing_logdir,
            wx.DD_DIR_MUST_EXIST)

        result = openFileDialog.ShowModal()
        selected = openFileDialog.GetPath()
        openFileDialog.Destroy()
        if result == wx.ID_OK:
            LOG.info("Selected log directory: %s", selected)
            config.LOG_DIRECTORY = selected
            config.CONF.set('default', 'logdir', selected)
            config.write()
            self.Parent.parser_thread.abort()
            self.Parent.parser_thread = logparse.ParseThread(self.Parent)
            self.Parent.parser_thread.start()

    def OnExportExcel(self, e: wx.MenuEvent):
        LOG.info("Exporting to Excel format.")
        saveFileDialog = wx.FileDialog(
            self.Parent, "Export to Excel", "", "",
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
            self.Parent, "Export to EQDKP", "", "",
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
            wx.PostEvent(self.Parent, models.AppClearEvent())

    def OnRestrict(self, e: wx.MenuEvent):
        config.RESTRICT_BIDS = self.restrict_mi.IsChecked()
        config.CONF.set(
            'default', 'restrict_bids', str(config.RESTRICT_BIDS))
        config.write()

    def OnNodropOnly(self, e: wx.MenuEvent):
        config.NODROP_ONLY = self.nodrop_only_mi.IsChecked()
        config.CONF.set(
            'default', 'nodrop_only', str(config.NODROP_ONLY))
        config.write()

    def OnAlwaysOnTop(self, e: wx.MenuEvent):
        config.ALWAYS_ON_TOP = self.alwaysontop_mi.IsChecked()
        config.CONF.set(
            'default', 'always_on_top', str(config.ALWAYS_ON_TOP))
        if config.ALWAYS_ON_TOP:
            self._parent.SetWindowStyle(
                self._parent.GetWindowStyle() | wx.STAY_ON_TOP)
        else:
            self._parent.SetWindowStyle(
                self._parent.GetWindowStyle() & ~wx.STAY_ON_TOP)
        config.write()

    def OnShowIgnored(self, e: wx.MenuEvent):
        bidding_frame.IgnoredItemsWindow(parent=self.Parent)
