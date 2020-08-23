# pylint: disable=no-member,invalid-name,unused-argument,too-many-locals

import wx
import ObjectListView

from ninjalooter import logging
from ninjalooter import logparse
from ninjalooter import models
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    player_affiliations = None

    def __init__(self, parent=None, title="NinjaLooter EQ Loot Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(630, 630))
        self.player_affiliations = list()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Connect(-1, -1, models.EVT_DROP, self.OnDrop)
        self.Connect(-1, -1, models.EVT_BID, self.OnBid)
        self.Connect(-1, -1, models.EVT_WHO, self.OnWho)
        self.Connect(-1, -1, models.EVT_CLEAR_WHO, self.OnClearWho)
        # Notebook used to create a tabbed main interface
        notebook = wx.Notebook(self, style=wx.LEFT)

        #######################
        # Bidding Frame (Tab 1)
        #######################
        bidding_frame = wx.Window(notebook)
        bidding_main_box = wx.BoxSizer(wx.VERTICAL)

        label_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)

        # ----------------
        # Pending Loot Box
        # ----------------
        pending_label = wx.StaticText(
            bidding_frame, label="Pending Drops", style=wx.ALIGN_LEFT)
        pending_label.SetFont(label_font)
        bidding_main_box.Add(
            pending_label, flag=wx.LEFT | wx.TOP, border=10)
        pending_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            pending_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        utils.add_sample_data()  # TODO: remove sample data
        pending_list = ObjectListView.ObjectListView(
            bidding_frame, wx.ID_ANY,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        pending_box.Add(pending_list, flag=wx.EXPAND)
        self.pending_list = pending_list

        pending_list.SetColumns([
            ObjectListView.ColumnDefn("Report Time", "left", 160, "timestamp",
                                      fixedWidth=160),
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Class", "left", 90, "classes",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
        ])
        pending_list.SetObjects(utils.config.PENDING_AUCTIONS)
        pending_list.SetEmptyListMsg("No drops pending.")

        # Buttons
        pending_buttons_box = wx.BoxSizer(wx.VERTICAL)
        pending_box.Add(pending_buttons_box,
                        flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        pending_button_ignore = wx.Button(bidding_frame, label="Ignore")
        pending_button_dkp = wx.Button(bidding_frame, label="DKP Bid")
        pending_button_roll = wx.Button(bidding_frame, label="Roll")
        pending_buttonspacer = wx.StaticLine(bidding_frame)
        pending_button_wiki = wx.Button(bidding_frame, label="Wiki?")
        pending_buttons_box.Add(pending_button_ignore, flag=wx.TOP)
        pending_buttons_box.Add(pending_button_dkp, flag=wx.TOP, border=10)
        pending_buttons_box.Add(pending_button_roll, flag=wx.TOP, border=10)
        pending_buttons_box.Add(pending_buttonspacer, flag=wx.TOP, border=10)
        pending_buttons_box.Add(pending_button_wiki, flag=wx.TOP, border=10)

        pending_button_dkp.Bind(wx.EVT_BUTTON, self.StartAuctionDKP)
        pending_button_roll.Bind(wx.EVT_BUTTON, self.StartAuctionRandom)
        pending_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWiki)

        # ---------------
        # Active Loot Box
        # ---------------
        active_label = wx.StaticText(
            bidding_frame, label="Active Auctions", style=wx.ALIGN_LEFT)
        active_label.SetFont(label_font)
        bidding_main_box.Add(
            active_label, flag=wx.LEFT | wx.TOP, border=10)
        active_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            active_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        active_list = ObjectListView.ObjectListView(
            bidding_frame, wx.ID_ANY,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        active_box.Add(active_list, flag=wx.EXPAND)
        self.active_list = active_list

        active_list.SetColumns([
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Class", "left", 90, "classes",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Bid/Roll", "left", 70, "highest_number",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Winner", "left", 90, "highest_players",
                                      fixedWidth=90),
        ])
        active_list.SetObjects(list(utils.config.ACTIVE_AUCTIONS.values()))
        active_list.SetEmptyListMsg("No auctions pending.")

        # Buttons
        active_buttons_box = wx.BoxSizer(wx.VERTICAL)
        active_box.Add(active_buttons_box,
                       flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        active_button_undo = wx.Button(bidding_frame, label="Undo")
        active_buttonspacer = wx.StaticLine(bidding_frame)
        active_button_gettext = wx.Button(bidding_frame, label="Copy Bid")
        active_button_complete = wx.Button(bidding_frame, label="Complete")
        active_button_wiki = wx.Button(bidding_frame, label="Wiki?")
        active_buttons_box.Add(active_button_undo, flag=wx.TOP)
        active_buttons_box.Add(active_buttonspacer, flag=wx.TOP, border=10)
        active_buttons_box.Add(active_button_gettext, flag=wx.TOP, border=10)
        active_buttons_box.Add(active_button_complete, flag=wx.TOP, border=10)
        active_buttons_box.Add(active_button_wiki, flag=wx.TOP, border=10)

        active_button_undo.Bind(wx.EVT_BUTTON, self.UndoStart)
        active_button_gettext.Bind(wx.EVT_BUTTON, self.CopyBidText)
        active_button_complete.Bind(wx.EVT_BUTTON, self.CompleteAuction)
        active_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWiki)

        # -------------------
        # Historical Loot Box
        # -------------------
        history_label = wx.StaticText(
            bidding_frame, label="Historical Auctions", style=wx.ALIGN_LEFT)
        history_label.SetFont(label_font)
        bidding_main_box.Add(
            history_label, flag=wx.LEFT | wx.TOP, border=10)
        history_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            history_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        history_list = ObjectListView.ObjectListView(
            bidding_frame, wx.ID_ANY,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        history_box.Add(history_list, flag=wx.EXPAND)
        self.history_list = history_list

        history_list.SetColumns([
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Class", "left", 90, "classes",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Bid/Roll", "left", 70, "highest_number",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Winner", "left", 90, "highest_players",
                                      fixedWidth=90),
        ])
        history_list.SetObjects(
            list(utils.config.HISTORICAL_AUCTIONS.values()))
        history_list.SetEmptyListMsg("No auctions completed.")

        # Buttons
        history_buttons_box = wx.BoxSizer(wx.VERTICAL)
        history_box.Add(history_buttons_box,
                        flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        history_button_undo = wx.Button(bidding_frame, label="Undo")
        history_buttonspacer = wx.StaticLine(bidding_frame)
        history_button_gettext = wx.Button(bidding_frame, label="Copy Text")
        history_button_wiki = wx.Button(bidding_frame, label="Wiki?")
        history_buttons_box.Add(history_button_undo, flag=wx.TOP)
        history_buttons_box.Add(history_buttonspacer, flag=wx.TOP, border=10)
        history_buttons_box.Add(history_button_gettext, flag=wx.TOP, border=10)
        history_buttons_box.Add(history_button_wiki, flag=wx.TOP, border=10)

        history_button_undo.Bind(wx.EVT_BUTTON, self.UndoComplete)
        history_button_gettext.Bind(wx.EVT_BUTTON, self.CopyWinText)
        history_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWiki)

        # Finalize Tab
        bidding_frame.SetSizer(bidding_main_box)
        notebook.AddPage(bidding_frame, 'Bidding')

        ##########################
        # Population Frame (Tab 2)
        ##########################
        population_frame = wx.Window(notebook)
        population_main_box = wx.BoxSizer(wx.VERTICAL)

        population_label = wx.StaticText(
            population_frame, label="Population Count", style=wx.ALIGN_LEFT)
        population_label.SetFont(label_font)
        population_main_box.Add(
            population_label, flag=wx.LEFT | wx.TOP, border=10)
        population_box = wx.BoxSizer(wx.HORIZONTAL)
        population_main_box.Add(
            population_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=10)

        # List
        population_list = ObjectListView.GroupListView(
            population_frame, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(500, 630))
        population_box.Add(population_list, flag=wx.EXPAND | wx.ALL)
        self.population_list = population_list

        def popGroupKey(player):
            return utils.config.ALLIANCE_MAP.get(player.guild, "None")

        population_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Name", "left", 180, "name",
                groupKeyGetter=popGroupKey, fixedWidth=180),
            ObjectListView.ColumnDefn(
                "Class", "left", 90, "pclass",
                groupKeyGetter=popGroupKey, fixedWidth=90),
            ObjectListView.ColumnDefn(
                "Level", "left", 40, "level",
                groupKeyGetter=popGroupKey, fixedWidth=40),
            ObjectListView.ColumnDefn(
                "Guild", "left", 145, "guild",
                groupKeyGetter=popGroupKey, fixedWidth=145),
        ])
        population_list.SetObjects(self.player_affiliations)
        population_list.SetEmptyListMsg(
            "No player affiliation data loaded.\nPlease type `/who` ingame.")

        # Buttons / Adjustments
        population_buttons_box = wx.BoxSizer(wx.VERTICAL)
        population_box.Add(population_buttons_box,
                           flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        population_button_poptext = wx.Button(population_frame,
                                              label="Copy Pop")
        population_button_randtext = wx.Button(population_frame,
                                               label="Copy Random")
        population_buttons_box.Add(population_button_poptext,
                                   flag=wx.TOP, border=10)
        population_buttons_box.Add(population_button_randtext,
                                   flag=wx.TOP, border=10)

        population_button_poptext.Bind(wx.EVT_BUTTON, self.CopyPopText)
        population_button_randtext.Bind(wx.EVT_BUTTON, self.CopyPopRandom)

        # Finalize Tab
        population_frame.SetSizer(population_main_box)
        notebook.AddPage(population_frame, 'Population Rolls')

        ##############################
        # Attendance Log Frame (Tab 2)
        ##############################
        attendance_frame = wx.Window(notebook)
        attendance_main_box = wx.BoxSizer(wx.VERTICAL)

        # Finalize Tab
        attendance_frame.SetSizer(attendance_main_box)
        notebook.AddPage(attendance_frame, 'Attendance Logs')

        # self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)
        # self.SetSizer(notebook)
        self.Show(True)

        self.parser_thread = logparse.ParseThread(self)
        self.parser_thread.start()

    def OnClose(self, e: wx.Event):
        self.parser_thread.abort()
        dlg = wx.MessageDialog(
            self,
            "Do you really want to close this application?",
            "Confirm Exit", wx.OK | wx.CANCEL | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Destroy()

    def ShowWiki(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        utils.open_wiki_url(selected_object)

    def DialogDuplicate(self):
        dlg = wx.MessageDialog(
            self,
            "An item with this name is already pending auction.\n"
            "Please complete the existing auction before starting another.",
            "Duplicate Auction", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()

    def StartAuctionDKP(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        auc = utils.start_auction_dkp(selected_object)
        if not auc:
            self.DialogDuplicate()
            return
        self.pending_list.SetObjects(utils.config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(utils.config.ACTIVE_AUCTIONS.values()))
        self.active_list.SelectObject(auc)

    def StartAuctionRandom(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        auc = utils.start_auction_random(selected_object)
        if not auc:
            self.DialogDuplicate()
            return
        self.pending_list.SetObjects(utils.config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(utils.config.ACTIVE_AUCTIONS.values()))
        self.active_list.SelectObject(auc)

    def UndoStart(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        utils.config.PENDING_AUCTIONS.append(selected_object.item)
        utils.config.ACTIVE_AUCTIONS.pop(selected_object.item.name)
        self.pending_list.SetObjects(utils.config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(utils.config.ACTIVE_AUCTIONS.values()))
        self.pending_list.SelectObject(selected_object.item)

    def CompleteAuction(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        utils.config.HISTORICAL_AUCTIONS[selected_object.item.name] = (
            selected_object)
        utils.config.ACTIVE_AUCTIONS.pop(selected_object.item.name)
        self.active_list.SetObjects(
            list(utils.config.ACTIVE_AUCTIONS.values()))
        self.history_list.SetObjects(
            list(utils.config.HISTORICAL_AUCTIONS.values()))
        self.history_list.SelectObject(selected_object)

    def UndoComplete(self, e: wx.Event):
        selected_object = self.history_list.GetSelectedObject()
        if not selected_object:
            return
        utils.config.ACTIVE_AUCTIONS[selected_object.item.name] = (
            selected_object)
        utils.config.HISTORICAL_AUCTIONS.pop(selected_object.item.name)
        self.active_list.SetObjects(
            list(utils.config.ACTIVE_AUCTIONS.values()))
        self.history_list.SetObjects(
            list(utils.config.HISTORICAL_AUCTIONS.values()))
        self.active_list.SelectObject(selected_object)

    def CopyBidText(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        text = selected_object.bid_text()
        utils.to_clipboard(text)

    def CopyWinText(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        text = selected_object.win_text()
        utils.to_clipboard(text)

    def CopyPopText(self, e: wx.Event):  # pylint: disable=no-self-use
        poproll, _ = utils.generate_pop_roll()
        utils.to_clipboard(poproll)

    def CopyPopRandom(self, e: wx.Event):  # pylint: disable=no-self-use
        _, rolltext = utils.generate_pop_roll()
        utils.to_clipboard(rolltext)

    def OnDrop(self, e: models.DropEvent):
        selected_object = self.pending_list.GetSelectedObject()
        self.pending_list.SetObjects(utils.config.PENDING_AUCTIONS)
        if selected_object:
            self.pending_list.SelectObject(selected_object)

    def OnBid(self, e: models.BidEvent):
        self.active_list.RefreshObject(e.item)

    def OnWho(self, e: models.WhoEvent):
        player = models.Player(e.name, e.pclass, e.level, e.guild)
        self.player_affiliations.append(player)
        self.population_list.SetObjects(self.player_affiliations)

    def OnClearWho(self, e: models.ClearWhoEvent):
        self.player_affiliations.clear()
        self.population_list.SetObjects(self.player_affiliations)
