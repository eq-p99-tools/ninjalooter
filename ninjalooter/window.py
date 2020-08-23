# pylint: disable=no-member,invalid-name,unused-argument,too-many-locals
import math

import wx
import ObjectListView

from ninjalooter import config
from ninjalooter import logging
from ninjalooter import logparse
from ninjalooter import models
from ninjalooter import utils

# This is the app logger, not related to EQ logs
LOG = logging.getLogger(__name__)


class MainWindow(wx.Frame):
    player_affiliations = None

    def __init__(self, parent=None, title="NinjaLooter EQ Loot Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(725, 630))
        icon = wx.Icon()
        icon.CopyFromBitmap(
            wx.Bitmap("data/ninja_attack.ico", wx.BITMAP_TYPE_ANY))
        self.SetIcon(icon)

        self.player_affiliations = list()
        self.pop_adjustments = dict()
        self.pop_preview = list()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Connect(-1, -1, models.EVT_DROP, self.OnDrop)
        self.Connect(-1, -1, models.EVT_BID, self.OnBid)
        self.Connect(-1, -1, models.EVT_WHO, self.OnWho)
        self.Connect(-1, -1, models.EVT_CLEAR_WHO, self.OnClearWho)
        self.Connect(-1, -1, models.EVT_WHO_HISTORY, self.OnWhoHistory)
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
            bidding_frame, wx.ID_ANY, size=wx.Size(600, 154),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        pending_box.Add(pending_list, flag=wx.EXPAND)
        self.pending_list = pending_list

        pending_list.SetColumns([
            ObjectListView.ColumnDefn("Report Time", "left", 160, "timestamp",
                                      fixedWidth=160),
            ObjectListView.ColumnDefn("Reporter", "left", 90, "reporter",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Classes", "left", 95, "classes",
                                      fixedWidth=95),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
        ])
        pending_list.SetObjects(config.PENDING_AUCTIONS)
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

        pending_button_ignore.Bind(wx.EVT_BUTTON, self.IgnorePending)
        pending_button_dkp.Bind(wx.EVT_BUTTON, self.PickAuctionDKP)
        pending_button_roll.Bind(wx.EVT_BUTTON, self.StartAuctionRandom)
        pending_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWikiPending)

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
            bidding_frame, wx.ID_ANY, size=wx.Size(600, 154),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        active_box.Add(active_list, flag=wx.EXPAND)
        active_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowActiveDetail)
        self.active_list = active_list

        active_list.SetColumns([
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Classes", "left", 95, "classes",
                                      fixedWidth=95),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Rand/Min", "left", 90, "get_target_min",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Bid/Roll", "left", 70, "highest_number",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Winner", "left", 90, "highest_players",
                                      fixedWidth=90),
        ])
        active_list.SetObjects(list(config.ACTIVE_AUCTIONS.values()))
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
        active_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWikiActive)

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
            bidding_frame, wx.ID_ANY, size=wx.Size(600, 154),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL, sortable=False)
        history_box.Add(history_list, flag=wx.EXPAND)
        history_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowHistoryDetail)
        self.history_list = history_list

        history_list.SetColumns([
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Classes", "left", 95, "classes",
                                      fixedWidth=95),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Rand/Min", "left", 90, "get_target_min",
                                      fixedWidth=90),
            ObjectListView.ColumnDefn("Bid/Roll", "left", 70, "highest_number",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Winner", "left", 90, "highest_players",
                                      fixedWidth=90),
        ])
        history_list.SetObjects(
            list(config.HISTORICAL_AUCTIONS.values()))
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
        history_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWikiHistory)

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
            size=wx.Size(500, 1080))
        population_box.Add(population_list, flag=wx.EXPAND | wx.ALL)
        self.population_list = population_list

        def popGroupKey(player):
            group_key = config.ALLIANCE_MAP.get(player.guild, "None")
            if player.guild in ('Seal Team',):
                group_key = 'Seal Team'
            return group_key

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
                "Guild", "left", 160, "guild",
                groupKeyGetter=popGroupKey, fixedWidth=160),
        ])
        population_list.SetObjects(self.player_affiliations)
        population_list.SetEmptyListMsg(
            "No player affiliation data loaded.\nPlease type `/who` ingame.")

        # Buttons / Adjustments
        population_buttons_box = wx.BoxSizer(wx.VERTICAL)
        population_box.Add(population_buttons_box,
                           flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        # Autogenerate adjustments for each Alliance
        adj_alliance_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)
        adj_alliance_header = wx.StaticText(
            population_frame, label="Adjustments")
        adj_alliance_header.SetFont(adj_alliance_font)
        population_buttons_box.Add(adj_alliance_header,
                                   flag=wx.BOTTOM, border=10)
        for alliance in config.ALLIANCES:
            adj_alliance_box = wx.GridBagSizer(1, 2)
            adj_alliance_label = wx.StaticText(
                population_frame, label=alliance, size=(100, 20),
                style=wx.ALIGN_RIGHT)
            adj_alliance_label.SetFont(adj_alliance_font)
            adj_alliance_spinner = wx.SpinCtrl(population_frame, value='0')
            adj_alliance_spinner.SetRange(-1000, 1000)  # Why limit things? :D
            adj_alliance_spinner.Bind(wx.EVT_SPINCTRL, self.ResetPopPreview)
            self.pop_adjustments[alliance] = adj_alliance_spinner
            adj_alliance_box.Add(adj_alliance_label, pos=(0, 0),
                                 flag=wx.RIGHT | wx.TOP, border=3)
            adj_alliance_box.Add(adj_alliance_spinner, pos=(0, 1),
                                 flag=wx.LEFT, border=7)
            population_buttons_box.Add(adj_alliance_box,
                                       flag=wx.BOTTOM | wx.EXPAND, border=10)

        # Small Pop-List Display
        population_preview_list = ObjectListView.ObjectListView(
            population_frame, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
            size=wx.Size(120, 140))
        population_buttons_box.Add(population_preview_list,
                                   flag=wx.EXPAND | wx.ALL)
        self.population_preview_list = population_preview_list

        population_preview_list.SetColumns([
            ObjectListView.ColumnDefn(
                "Alliance", "left", 125, "alliance", fixedWidth=125),
            ObjectListView.ColumnDefn(
                "Pop", "left", 40, "population", fixedWidth=40),
        ])
        population_preview_list.SetObjects(self.pop_preview)
        population_preview_list.SetEmptyListMsg(
            "No pop data found.")

        population_button_half = wx.Button(population_frame, label="Halve")
        population_button_reset = wx.Button(population_frame, label="Reset")
        population_box_half_reset = wx.BoxSizer(wx.HORIZONTAL)
        population_box_half_reset.Add(population_button_half,
                                      flag=wx.LEFT, border=5)
        population_box_half_reset.Add(population_button_reset,
                                      flag=wx.LEFT, border=10)

        population_button_poptext = wx.Button(population_frame,
                                              label="Copy Populations",
                                              size=(160, 23))
        population_button_randtext = wx.Button(population_frame,
                                               label="Copy Roll Text",
                                               size=(160, 23))
        population_buttons_box.Add(population_box_half_reset,
                                   flag=wx.TOP | wx.BOTTOM, border=10)
        population_buttons_box.Add(population_button_poptext,
                                   flag=wx.LEFT | wx.BOTTOM, border=5)
        population_buttons_box.Add(population_button_randtext,
                                   flag=wx.LEFT | wx.TOP, border=5)

        population_button_half.Bind(wx.EVT_BUTTON, self.RecalcPopPreview)
        population_button_reset.Bind(wx.EVT_BUTTON, self.ResetPopPreview)
        population_button_poptext.Bind(wx.EVT_BUTTON, self.CopyPopText)
        population_button_randtext.Bind(wx.EVT_BUTTON, self.CopyPopRandom)

        # Finalize Tab
        population_frame.SetSizer(population_main_box)
        notebook.AddPage(population_frame, 'Population Rolls')

        ##############################
        # Attendance Log Frame (Tab 3)
        ##############################
        attendance_frame = wx.Window(notebook)
        attendance_main_box = wx.BoxSizer(wx.VERTICAL)

        # List
        attendance_list = ObjectListView.GroupListView(
            attendance_frame, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(600, 630))
        attendance_main_box.Add(attendance_list, flag=wx.EXPAND | wx.ALL)
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
        attendance_frame.SetSizer(attendance_main_box)
        notebook.AddPage(attendance_frame,
                         'Attendance Logs [WORK IN PROGRESS]')

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

    def ResetPopPreview(self, e: wx.Event):
        pops = utils.get_pop_numbers(extras=self._get_spinner_pops())
        self.pop_preview.clear()
        for alliance, pop in pops.items():
            pop_obj = models.PopulationPreview(alliance, str(pop))
            self.pop_preview.append(pop_obj)
        selected_index = self.population_preview_list.GetFirstSelected()
        self.population_preview_list.SetObjects(self.pop_preview)
        if selected_index >= 0:
            self.population_preview_list.Select(selected_index)

    def RecalcPopPreview(self, e: wx.Event):
        selected_object = self.population_preview_list.GetSelectedObject()
        if not selected_object:
            return
        sel_pop = int(selected_object.population)
        selected_object.population = str(math.ceil(sel_pop / 2))
        self.population_preview_list.RefreshObject(selected_object)

    def ShowWikiPending(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        utils.open_wiki_url(selected_object)

    def ShowWikiActive(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        utils.open_wiki_url(selected_object.item)

    def ShowWikiHistory(self, e: wx.Event):
        selected_object = self.history_list.GetSelectedObject()
        if not selected_object:
            return
        utils.open_wiki_url(selected_object.item)

    def DialogDuplicate(self):
        dlg = wx.MessageDialog(
            self,
            "An item with this name is already pending auction.\n"
            "Please complete the existing auction before starting another.",
            "Duplicate Auction", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()

    def IgnorePending(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        utils.ignore_pending_item(selected_object)
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)

    def PickAuctionDKP(self, e: wx.Event):
        class MyPopupMenu(wx.Menu):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent
                for alliance in config.ALLIANCES:
                    mi = wx.MenuItem(self, wx.NewId(), alliance)
                    self.Append(mi)
                    self.Bind(wx.EVT_MENU, parent.StartAuctionDKP, mi)

        self.PopupMenu(MyPopupMenu(self), e.EventObject.GetPosition())

    def StartAuctionDKP(self, e: wx.Event):
        menu_item = [mi for mi in e.EventObject.MenuItems if mi.Id == e.Id][0]
        alliance = menu_item.ItemLabel
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        auc = utils.start_auction_dkp(selected_object, alliance)
        if not auc:
            self.DialogDuplicate()
            return
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(config.ACTIVE_AUCTIONS.values()))
        self.active_list.SelectObject(auc)

    def StartAuctionRandom(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        if not selected_object:
            return
        auc = utils.start_auction_random(selected_object)
        if not auc:
            self.DialogDuplicate()
            return
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(config.ACTIVE_AUCTIONS.values()))
        self.active_list.SelectObject(auc)

    def UndoStart(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        config.PENDING_AUCTIONS.append(selected_object.item)
        config.ACTIVE_AUCTIONS.pop(selected_object.item.uuid)
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        self.active_list.SetObjects(
            list(config.ACTIVE_AUCTIONS.values()))
        self.pending_list.SelectObject(selected_object.item)

    def CompleteAuction(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        config.HISTORICAL_AUCTIONS[selected_object.item.uuid] = (
            selected_object)
        config.ACTIVE_AUCTIONS.pop(selected_object.item.uuid)
        self.active_list.SetObjects(
            list(config.ACTIVE_AUCTIONS.values()))
        self.history_list.SetObjects(
            list(config.HISTORICAL_AUCTIONS.values()))
        self.history_list.SelectObject(selected_object)

    def UndoComplete(self, e: wx.Event):
        selected_object = self.history_list.GetSelectedObject()
        if not selected_object:
            return
        config.ACTIVE_AUCTIONS[selected_object.item.uuid] = (
            selected_object)
        config.HISTORICAL_AUCTIONS.pop(selected_object.item.uuid)
        self.active_list.SetObjects(
            list(config.ACTIVE_AUCTIONS.values()))
        self.history_list.SetObjects(
            list(config.HISTORICAL_AUCTIONS.values()))
        self.active_list.SelectObject(selected_object)

    def CopyBidText(self, e: wx.Event):
        selected_object = self.active_list.GetSelectedObject()
        if not selected_object:
            return
        text = selected_object.bid_text()
        utils.to_clipboard(text)

    def CopyWinText(self, e: wx.Event):
        selected_object = self.history_list.GetSelectedObject()
        if not selected_object:
            return
        text = selected_object.win_text()
        utils.to_clipboard(text)

    def _get_spinner_pops(self):
        return {
            alliance: spinner.GetValue()
            for alliance, spinner in self.pop_adjustments.items()
        }

    def CopyPopText(self, e: wx.Event):  # pylint: disable=no-self-use
        pop_dict = {pop.alliance: int(pop.population)
                    for pop in self.pop_preview}
        poproll, _ = utils.generate_pop_roll(source={}, extras=pop_dict)
        utils.to_clipboard(poproll)

    def CopyPopRandom(self, e: wx.Event):  # pylint: disable=no-self-use
        _, rolltext = utils.generate_pop_roll(extras=self._get_spinner_pops())
        utils.to_clipboard(rolltext)

    def OnDrop(self, e: models.DropEvent):
        selected_object = self.pending_list.GetSelectedObject()
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        if selected_object:
            self.pending_list.SelectObject(selected_object)

    def OnBid(self, e: models.BidEvent):
        self.active_list.RefreshObject(e.item)

    def OnWho(self, e: models.WhoEvent):
        player = models.Player(e.name, e.pclass, e.level, e.guild)
        self.player_affiliations.append(player)
        self.population_list.SetObjects(self.player_affiliations)
        self.ResetPopPreview(e)

    def OnClearWho(self, e: models.ClearWhoEvent):
        self.player_affiliations.clear()
        self.population_list.SetObjects(self.player_affiliations)

    def OnWhoHistory(self, e: models.WhoHistoryEvent):
        self.attendance_list.SetObjects(config.WHO_LOG)

    def ShowHistoryDetail(self, e: wx.EVT_LEFT_DCLICK):
        return self.ShowItemDetail(self.history_list)

    def ShowActiveDetail(self, e: wx.EVT_LEFT_DCLICK):
        return self.ShowItemDetail(self.active_list)

    def ShowItemDetail(self, listbox: ObjectListView.ObjectListView):
        selected_object = listbox.GetSelectedObject()
        if not selected_object:
            return
        ItemDetailWindow(selected_object, parent=self, title="Item Detail")


class ItemDetailWindow(wx.Frame):
    def __init__(self, item, parent=None, title="NinjaLooter EQ Loot Manager"):
        wx.Frame.__init__(self, parent, title=title, size=(400, 400))
        main_box = wx.BoxSizer(wx.HORIZONTAL)

        text_area = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY,
                                size=wx.Size(400, 400))
        data = getattr(item, 'rolls', getattr(item, 'bids', ""))
        bids_or_rolls = [
            "{}: {}".format(number, players)
            for number, players in data.items()]
        text_area.SetValue('\n'.join(bids_or_rolls))
        main_box.Add(text_area)

        self.SetSizer(main_box)
        self.Show()
