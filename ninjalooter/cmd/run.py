import wx

from ninjalooter.ui import window
from ninjalooter import utils


def run():
    utils.load_state()
    app = wx.App(False)
    window.MainWindow()
    app.MainLoop()


if __name__ == "__main__":
    run()
