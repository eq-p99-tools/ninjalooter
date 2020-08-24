import wx

from ninjalooter.ui import window


def run():
    app = wx.App(False)
    window.MainWindow()
    app.MainLoop()


if __name__ == "__main__":
    run()
