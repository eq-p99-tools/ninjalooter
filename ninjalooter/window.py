import wx


class MainWindow(wx.Frame):
    def __init__(self, parent=None, title="Hello"):
        wx.Frame.__init__(self, parent, title=title, size=(200, 100))
        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        self.Show(True)
