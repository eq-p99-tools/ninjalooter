# pylint: disable=no-member,invalid-name,unused-argument
# pylint: disable=too-many-locals,too-many-statements
import math

import ObjectListView
import wx

from ninjalooter import config
from ninjalooter import models
from ninjalooter import utils


class PopulationFrame(wx.Window):
    def __init__(self, parent: wx.Notebook, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        parent.GetParent().Connect(-1, -1, models.EVT_WHO,
                                   self.OnWho)
        parent.GetParent().Connect(-1, -1, models.EVT_CLEAR_WHO,
                                   self.OnClearWho)
        parent.GetParent().Connect(-1, -1, models.EVT_WHO_END,
                                   self.ResetPopPreview)
        self.player_affiliations = config.WX_PLAYER_AFFILIATIONS or list()
        config.WX_PLAYER_AFFILIATIONS = self.player_affiliations
        self.pop_adjustments = dict()
        self.pop_preview = list()

        ##########################
        # Population Frame (Tab 2)
        ##########################
        label_font = wx.Font(11, wx.DEFAULT, wx.DEFAULT, wx.BOLD)
        population_main_box = wx.BoxSizer(wx.VERTICAL)

        population_label = wx.StaticText(
            self, label="Population Count", style=wx.ALIGN_LEFT)
        population_label.SetFont(label_font)
        population_main_box.Add(
            population_label, flag=wx.LEFT | wx.TOP, border=10)
        population_box = wx.BoxSizer(wx.HORIZONTAL)
        population_main_box.Add(
            population_box, flag=wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=10)

        # List
        population_list = ObjectListView.GroupListView(
            self, wx.ID_ANY, style=wx.LC_REPORT,
            size=wx.Size(500, 1200))
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
                "Guild", "left", 148, "guild",
                groupKeyGetter=popGroupKey, fixedWidth=148),
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
            self, label="Adjustments:")
        adj_alliance_header.SetFont(adj_alliance_font)
        population_buttons_box.Add(adj_alliance_header,
                                   flag=wx.BOTTOM, border=10)
        for alliance in config.ALLIANCES:
            adj_alliance_box = wx.GridBagSizer(1, 2)
            adj_alliance_label = wx.StaticText(
                self, label=alliance, size=(100, 20),
                style=wx.ALIGN_RIGHT)
            adj_alliance_label.SetFont(adj_alliance_font)
            adj_alliance_spinner = wx.SpinCtrl(self, value='0')
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
            self, wx.ID_ANY, style=wx.LC_REPORT | wx.LC_SINGLE_SEL,
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

        population_button_half = wx.Button(self, label="Halve")
        population_button_reset = wx.Button(self, label="Reset")
        population_box_half_reset = wx.BoxSizer(wx.HORIZONTAL)
        population_box_half_reset.Add(population_button_half,
                                      flag=wx.LEFT, border=5)
        population_box_half_reset.Add(population_button_reset,
                                      flag=wx.LEFT, border=10)

        population_button_poptext = wx.Button(self,
                                              label="Copy Populations",
                                              size=(160, 23))
        population_button_randtext = wx.Button(self,
                                               label="Copy Roll Text",
                                               size=(160, 23))
        population_buttons_box.Add(population_box_half_reset,
                                   flag=wx.TOP | wx.BOTTOM, border=10)
        population_buttons_box.Add(population_button_poptext,
                                   flag=wx.LEFT | wx.BOTTOM, border=5)
        population_buttons_box.Add(population_button_randtext,
                                   flag=wx.LEFT | wx.TOP, border=5)

        population_button_half.Bind(wx.EVT_BUTTON, self.HalvePopPreview)
        population_button_reset.Bind(wx.EVT_BUTTON, self.ResetPopPreview)
        population_button_poptext.Bind(wx.EVT_BUTTON, self.CopyPopText)
        population_button_randtext.Bind(wx.EVT_BUTTON, self.CopyPopRandom)
        self.ResetPopPreview(None)

        # Finalize Tab
        self.SetSizer(population_main_box)
        parent.AddPage(self, 'Population Rolls')

    def _get_spinner_pops(self):
        return {
            alliance: spinner.GetValue()
            for alliance, spinner in self.pop_adjustments.items()
        }

    def OnClearWho(self, e: models.ClearWhoEvent):
        self.player_affiliations.clear()
        self.population_list.SetObjects(self.player_affiliations)

    def OnWho(self, e: models.WhoEvent):
        player = models.Player(e.name, e.pclass, e.level, e.guild)
        self.player_affiliations.append(player)
        self.population_list.SetObjects(self.player_affiliations)

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
        # self.CopyPopText(e)

    def HalvePopPreview(self, e: wx.Event):
        selected_object = self.population_preview_list.GetSelectedObject()
        if not selected_object:
            return
        sel_pop = int(selected_object.population)
        selected_object.population = str(math.ceil(sel_pop / 2))
        self.population_preview_list.RefreshObject(selected_object)
        self.CopyPopText(e)

    def CopyPopText(self, e: wx.Event):  # pylint: disable=no-self-use
        pop_dict = {pop.alliance: int(pop.population)
                    for pop in self.pop_preview}
        poproll, _ = utils.generate_pop_roll(source={}, extras=pop_dict)
        utils.to_clipboard(poproll)

    def CopyPopRandom(self, e: wx.Event):  # pylint: disable=no-self-use
        pop_dict = {pop.alliance: int(pop.population)
                    for pop in self.pop_preview}
        _, rolltext = utils.generate_pop_roll(source={}, extras=pop_dict)
        utils.to_clipboard(rolltext)
