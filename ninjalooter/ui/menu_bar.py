# pylint: disable=no-member,invalid-name,unused-argument

import os.path

import wx

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import models
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class MenuBar(wx.MenuBar):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        file_menu = wx.Menu()

        set_log_mi = wx.MenuItem(file_menu, wx.ID_FIND, '&Set Log Directory')
        set_log_bitmap = wx.Bitmap(os.path.join("data", "icons", "gear.png"))
        set_log_mi.SetBitmap(set_log_bitmap)
        file_menu.Append(set_log_mi)
        self.Bind(wx.EVT_MENU, self.OnConfigure, set_log_mi)

        export_mi = wx.MenuItem(
            file_menu, wx.ID_FLOPPY, '&Export to Excel\tCtrl+E')
        export_bitmap = wx.Bitmap(os.path.join("data", "icons", "export.png"))
        export_mi.SetBitmap(export_bitmap)
        export_mi.Enable(False)
        file_menu.Append(export_mi)
        self.Bind(wx.EVT_MENU, self.OnExport, export_mi)

        clear_mi = wx.MenuItem(file_menu, wx.ID_NEW, '&Clear Data')
        clear_bitmap = wx.Bitmap(os.path.join("data", "icons", "clear.png"))
        clear_mi.SetBitmap(clear_bitmap)
        clear_mi.Enable(False)
        file_menu.AppendItem(clear_mi)
        self.Bind(wx.EVT_MENU, self.OnClear, clear_mi)

        exit_mi = wx.MenuItem(file_menu, wx.ID_EXIT, '&Quit\tCtrl+W')
        exit_bitmap = wx.Bitmap(os.path.join("data", "icons", "exit.png"))
        exit_mi.SetBitmap(exit_bitmap)
        file_menu.Append(exit_mi)
        self.Bind(wx.EVT_MENU, parent.OnClose, exit_mi)

        self.Append(file_menu, '&File')
        parent.SetMenuBar(self)

    def OnConfigure(self, e: wx.Event):
        existing_logdir = config.LOG_DIRECTORY
        if not os.path.isdir(existing_logdir):
            existing_logdir = os.path.dirname(existing_logdir)
        openFileDialog = wx.DirDialog(
            self.parent, "Select Log Directory", existing_logdir,
            wx.DD_DIR_MUST_EXIST)

        result = openFileDialog.ShowModal()
        selected = openFileDialog.GetPath()
        openFileDialog.Destroy()
        if result == wx.ID_OK:
            LOG.info("Selected log directory: %s", selected)
            config.LOG_DIRECTORY = selected
            config.CONF.set('default', 'logdir', selected)
            config.write()

    def OnExport(self, e: wx.Event):
        LOG.info("Exporting to Excel format.")
        saveFileDialog = wx.FileDialog(
            self.parent, "Export to Excel", "", "",
            "Excel files (*.xls, *.xlsx)|*.xlsx?", wx.FD_SAVE)

        result = saveFileDialog.ShowModal()
        filename = saveFileDialog.GetPath()
        saveFileDialog.Destroy()
        if result == wx.ID_OK:
            utils.export_to_excel(filename)

    def OnClear(self, e: wx.Event):
        wx.PostEvent(self.parent, models.AppClearEvent())
