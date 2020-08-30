# pylint: disable=no-member,invalid-name,unused-argument
# pylint: disable=too-many-locals,too-many-statements
import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import models
from ninjalooter import utils


class BiddingFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_DROP, self.OnDrop)
        parent.GetParent().Connect(-1, -1, models.EVT_BID, self.OnBid)
        parent.GetParent().Connect(-1, -1, models.EVT_APP_CLEAR,
                                   self.OnClearApp)
        #######################
        # Bidding Frame (Tab 1)
        #######################
        # bidding_frame = wx.Window(notebook)
        bidding_main_box = wx.BoxSizer(wx.VERTICAL)
        label_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)

        # ----------------
        # Pending Loot Box
        # ----------------
        pending_label = wx.StaticText(
            self, label="Pending Drops", style=wx.ALIGN_LEFT)
        pending_label.SetFont(label_font)
        bidding_main_box.Add(
            pending_label, flag=wx.LEFT | wx.TOP, border=10)
        pending_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            pending_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        pending_list = ObjectListView.ObjectListView(
            self, wx.ID_ANY, size=wx.Size(600, 180),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        pending_box.Add(pending_list, flag=wx.EXPAND)
        pending_list.Bind(wx.EVT_LEFT_DCLICK, self.OnIgnorePending)
        self.pending_list = pending_list

        pending_list.SetColumns([
            ObjectListView.ColumnDefn("Report Time", "left", 160, "timestamp",
                                      fixedWidth=160),
            ObjectListView.ColumnDefn("Reporter", "left", 80, "reporter",
                                      fixedWidth=80),
            ObjectListView.ColumnDefn("Item", "left", 178, "name",
                                      fixedWidth=178),
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

        pending_button_ignore = wx.Button(self, label="Ignore")
        pending_button_dkp = wx.Button(self, label="DKP Bid")
        pending_button_roll = wx.Button(self, label="Roll")
        # pending_buttonspacer = wx.StaticLine(self)
        pending_button_wiki = wx.Button(self, label="Wiki?")
        pending_buttons_box.Add(pending_button_ignore, flag=wx.TOP)
        pending_buttons_box.Add(pending_button_dkp, flag=wx.TOP, border=10)
        pending_buttons_box.Add(pending_button_roll, flag=wx.TOP, border=10)
        # pending_buttons_box.Add(pending_buttonspacer, flag=wx.TOP, border=10)
        pending_buttons_box.Add(pending_button_wiki, flag=wx.TOP, border=10)
        min_dkp_font = wx.Font(10, wx.DEFAULT, wx.DEFAULT, wx.BOLD)
        min_dkp_label = wx.StaticText(
            self, label="Min DKP")
        min_dkp_label.SetFont(min_dkp_font)
        min_dkp_spinner = wx.SpinCtrl(self, value=str(config.MIN_DKP))
        min_dkp_spinner.SetRange(0, 1000)
        min_dkp_spinner.Bind(wx.EVT_SPINCTRL, self.OnMinDkpSpin)
        self.min_dkp_spinner = min_dkp_spinner
        pending_buttons_box.Add(min_dkp_label,
                                flag=wx.TOP | wx.LEFT, border=10)
        pending_buttons_box.Add(min_dkp_spinner, flag=wx.LEFT, border=10)

        pending_button_ignore.Bind(wx.EVT_BUTTON, self.OnIgnorePending)
        pending_button_dkp.Bind(wx.EVT_BUTTON, self.PickAuctionDKP)
        pending_button_roll.Bind(wx.EVT_BUTTON, self.StartAuctionRandom)
        pending_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWikiPending)

        # ---------------
        # Active Loot Box
        # ---------------
        active_label = wx.StaticText(
            self, label="Active Auctions", style=wx.ALIGN_LEFT)
        active_label.SetFont(label_font)
        bidding_main_box.Add(
            active_label, flag=wx.LEFT | wx.TOP, border=10)
        active_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            active_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        active_list = ObjectListView.ObjectListView(
            self, wx.ID_ANY, size=wx.Size(600, 154),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
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
            ObjectListView.ColumnDefn("Leading", "left", 90, "highest_players",
                                      fixedWidth=90),
        ])
        active_list.SetObjects(list(config.ACTIVE_AUCTIONS.values()))
        active_list.SetEmptyListMsg("No auctions pending.")

        # Buttons
        active_buttons_box = wx.BoxSizer(wx.VERTICAL)
        active_box.Add(active_buttons_box,
                       flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        active_button_undo = wx.Button(self, label="Undo")
        active_buttonspacer = wx.StaticLine(self)
        active_button_gettext = wx.Button(self, label="Copy Bid")
        active_button_complete = wx.Button(self, label="Complete")
        active_button_wiki = wx.Button(self, label="Wiki?")
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
            self, label="Historical Auctions", style=wx.ALIGN_LEFT)
        history_label.SetFont(label_font)
        bidding_main_box.Add(
            history_label, flag=wx.LEFT | wx.TOP, border=10)
        history_box = wx.BoxSizer(wx.HORIZONTAL)
        bidding_main_box.Add(
            history_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        # List
        history_list = ObjectListView.ObjectListView(
            self, wx.ID_ANY, size=wx.Size(600, 1000),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        history_box.Add(history_list, flag=wx.EXPAND | wx.BOTTOM, border=10)
        history_list.Bind(wx.EVT_LEFT_DCLICK, self.ShowHistoryDetail)
        self.history_list = history_list

        history_list.SetColumns([
            ObjectListView.ColumnDefn("Item", "left", 180, "name",
                                      fixedWidth=180),
            ObjectListView.ColumnDefn("Classes", "left", 95, "classes",
                                      fixedWidth=95),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
            ObjectListView.ColumnDefn("Rand/Min", "left", 65, "get_target_min",
                                      fixedWidth=65),
            ObjectListView.ColumnDefn("Bid/Roll", "left", 65, "highest_number",
                                      fixedWidth=65),
            ObjectListView.ColumnDefn("Winner", "left", 108, "highest_players",
                                      fixedWidth=108),
        ])
        history_list.SetObjects(
            list(config.HISTORICAL_AUCTIONS.values()))
        history_list.SetEmptyListMsg("No auctions completed.")

        # Buttons
        history_buttons_box = wx.BoxSizer(wx.VERTICAL)
        history_box.Add(history_buttons_box,
                        flag=wx.EXPAND | wx.TOP | wx.LEFT, border=10)

        history_button_undo = wx.Button(self, label="Undo")
        history_buttonspacer = wx.StaticLine(self)
        history_button_gettext = wx.Button(self, label="Copy Text")
        history_button_wiki = wx.Button(self, label="Wiki?")
        history_buttons_box.Add(history_button_undo, flag=wx.TOP)
        history_buttons_box.Add(history_buttonspacer, flag=wx.TOP, border=10)
        history_buttons_box.Add(history_button_gettext, flag=wx.TOP, border=10)
        history_buttons_box.Add(history_button_wiki, flag=wx.TOP, border=10)

        history_button_undo.Bind(wx.EVT_BUTTON, self.UndoComplete)
        history_button_gettext.Bind(wx.EVT_BUTTON, self.CopyWinText)
        history_button_wiki.Bind(wx.EVT_BUTTON, self.ShowWikiHistory)

        # Finalize Tab
        self.SetSizer(bidding_main_box)
        parent.AddPage(self, 'Bidding')

    def OnIgnorePending(self, e: wx.Event):
        selected_object = self.pending_list.GetSelectedObject()
        selected_index = self.pending_list.GetFirstSelected()
        if not selected_object:
            return
        utils.ignore_pending_item(selected_object)
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        item_count = self.pending_list.GetItemCount()
        if item_count > 0:
            self.pending_list.Select(min(selected_index, item_count - 1))
        utils.store_state()
        wx.PostEvent(self.Parent.Parent, models.IgnoreEvent())

    def DialogDuplicate(self):
        dlg = wx.MessageDialog(
            self,
            "An item with this name is already pending auction.\n"
            "Please complete the existing auction before starting another.",
            "Duplicate Auction", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

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
        utils.store_state()

    def OnMinDkpSpin(self, e: wx.SpinEvent):
        min_dkp = self.min_dkp_spinner.GetValue()
        config.MIN_DKP = min_dkp
        config.CONF.set(
            'default', 'min_dkp', str(min_dkp))
        config.write()

    def PickAuctionDKP(self, e: wx.Event):
        class MyPopupMenu(wx.Menu):
            def __init__(self, parent):
                super().__init__()
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
        self.CopyBidText(e)
        utils.store_state()

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
        self.CopyBidText(e)
        utils.store_state()

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
        self.CopyWinText(e)
        utils.store_state()

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
        utils.store_state()

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

    def ShowHistoryDetail(self, e: wx.EVT_LEFT_DCLICK):
        return self.ShowItemDetail(self.history_list)

    def ShowActiveDetail(self, e: wx.EVT_LEFT_DCLICK):
        return self.ShowItemDetail(self.active_list)

    def OnDrop(self, e: models.DropEvent):
        selected_object = self.pending_list.GetSelectedObject()
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        if selected_object:
            self.pending_list.SelectObject(selected_object)

    def OnBid(self, e: models.BidEvent):
        self.active_list.RefreshObject(e.item)

    def OnClearApp(self, e: models.AppClearEvent):
        config.PENDING_AUCTIONS.clear()
        config.ACTIVE_AUCTIONS.clear()
        config.HISTORICAL_AUCTIONS.clear()
        config.IGNORED_AUCTIONS.clear()
        self.pending_list.SetObjects(config.PENDING_AUCTIONS)
        self.active_list.SetObjects(list(config.ACTIVE_AUCTIONS.values()))
        self.history_list.SetObjects(list(config.HISTORICAL_AUCTIONS.values()))
        e.Skip()

    def ShowItemDetail(self, listbox: ObjectListView.ObjectListView):
        selected_object = listbox.GetSelectedObject()
        if not selected_object:
            return
        ItemDetailWindow(selected_object, listbox, parent=self)


class ItemDetailWindow(wx.Frame):
    def __init__(self, item: models.Auction,
                 listbox: ObjectListView.ObjectListView,
                 parent=None, title="Item Detail"):
        wx.Frame.__init__(self, parent, title=title, size=(400, 400))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.item = item
        self.listbox = listbox
        main_box = wx.BoxSizer(wx.HORIZONTAL)

        text_area = wx.TextCtrl(self, style=wx.TE_MULTILINE,
                                size=wx.Size(400, 400))
        data = getattr(item, 'rolls', getattr(item, 'bids', dict()))
        bids_or_rolls = [
            "{}: {}".format(number, players)
            for number, players in data.items()]
        text_area.SetValue('\n'.join(bids_or_rolls))
        main_box.Add(text_area)
        self.bid_data = text_area

        self.SetSizer(main_box)
        self.Show()

    def OnClose(self, e: wx.Event):
        text_data = self.bid_data.GetValue()
        bid_data = {}
        data = getattr(self.item, 'rolls', getattr(self.item, 'bids', dict()))
        try:
            for line in text_data.split('\n'):
                if not line:
                    continue
                if isinstance(self.item, models.RandomAuction):
                    bidder, bid = line.split(":")
                    bid_data[bidder.strip()] = int(bid)
                else:
                    bid, bidder = line.split(":")
                    bid_data[int(bid)] = bidder.strip()
            data.clear()
            data.update(bid_data)
            self.listbox.RefreshObject(self.item)
        except Exception:
            pass
        self.Destroy()


class IgnoredItemsWindow(wx.Frame):
    def __init__(self, parent=None,
                 title="Ignored Auctions (Double Click to Restore)"):
        wx.Frame.__init__(self, parent, title=title, size=(616, 600))
        self.Parent.Connect(-1, -1, models.EVT_IGNORE, self.OnRefresh)
        main_box = wx.BoxSizer(wx.HORIZONTAL)

        ignored_list = ObjectListView.ObjectListView(
            self, wx.ID_ANY, size=wx.Size(600, 1080),
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
        main_box.Add(ignored_list, flag=wx.EXPAND)

        ignored_list.SetColumns([
            ObjectListView.ColumnDefn("Report Time", "left", 160, "timestamp",
                                      fixedWidth=160),
            ObjectListView.ColumnDefn("Reporter", "left", 80, "reporter",
                                      fixedWidth=80),
            ObjectListView.ColumnDefn("Item", "left", 178, "name",
                                      fixedWidth=178),
            ObjectListView.ColumnDefn("Classes", "left", 95, "classes",
                                      fixedWidth=95),
            ObjectListView.ColumnDefn("Droppable", "center", 70, "droppable",
                                      fixedWidth=70),
        ])
        ignored_list.SetObjects(config.IGNORED_AUCTIONS)
        ignored_list.SetEmptyListMsg("No drops ignored.")
        ignored_list.Bind(wx.EVT_LEFT_DCLICK, self.OnRestoreIgnored)
        self.ignored_list = ignored_list

        self.SetSizer(main_box)
        self.Show()

    def OnRefresh(self, e: models.IgnoreEvent):
        self.ignored_list.SetObjects(config.IGNORED_AUCTIONS)

    def OnRestoreIgnored(self, e: wx.EVT_LEFT_DCLICK):
        item = self.ignored_list.GetSelectedObject()
        config.IGNORED_AUCTIONS.remove(item)
        config.PENDING_AUCTIONS.append(item)
        self.ignored_list.SetObjects(config.IGNORED_AUCTIONS)
        wx.PostEvent(self.Parent, models.DropEvent())
