import collections
import os
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from ninjalooter import config
from ninjalooter.tests import base
from ninjalooter.ui.alliances_dialog import AlliancesDialog
from ninjalooter.ui.menu_bar import MenuBar

_app = QApplication.instance() or QApplication([])


def _close(widget):
    widget.deleteLater()
    QApplication.processEvents()


class TestAlliancesDialog(base.NLTestBase):
    def setUp(self):
        super().setUp()
        self._saved = {}
        for key in ("alliances", "extra_alliances", "default_alliance"):
            if config.CONF.has_option("default", key):
                self._saved[key] = config.CONF.get("default", key)
            else:
                self._saved[key] = None

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                if config.CONF.has_option("default", key):
                    config.CONF.remove_option("default", key)
            else:
                config.CONF.set("default", key, value)
        config.apply_alliance_config()
        super().tearDown()

    def test_moving_a_guild_explains_where_the_version_keeps_it(self):
        dialog = AlliancesDialog()
        self.addCleanup(_close, dialog)
        dialog._yours["Ancient Blood"] = ["Ancient Blood"]
        dialog._reload(select="Ancient Blood")

        self.assertIn("Custom alliances", dialog._summary.text())
        self.assertEqual(
            "Ancient Blood is inside Castle in this version.",
            dialog._hint.text(),
        )
        self.assertIn("Castle", [dialog._shipped_alliances.item(i).text() for i in range(dialog._shipped_alliances.count())])

    def test_adding_a_guild_moves_it_out_of_the_other_alliance(self):
        dialog = AlliancesDialog()
        self.addCleanup(_close, dialog)
        dialog._yours = collections.OrderedDict(
            [
                ("Castle", ["Castle", "Ancient Blood"]),
                ("Lineage", ["Lineage"]),
            ]
        )
        dialog._reload(select="Lineage")
        dialog._guild_edit.setText("Ancient Blood")
        dialog._add_guild()

        self.assertEqual(["Castle"], dialog._yours["Castle"])
        self.assertEqual(["Lineage", "Ancient Blood"], dialog._yours["Lineage"])
        self.assertEqual("Moved Ancient Blood out of Castle.", dialog._move_label.text())

    def test_save_writes_the_edited_list(self):
        dialog = AlliancesDialog()
        self.addCleanup(_close, dialog)
        dialog._yours = collections.OrderedDict([("Castle", ["Castle"]), ("Ancient Blood", ["Ancient Blood"])])
        with mock.patch("ninjalooter.config.write") as write:
            dialog._save()
        write.assert_called_once()
        self.assertEqual("Ancient Blood", config.ALLIANCE_MAP["Ancient Blood"])
        self.assertNotIn("Ancient Blood", config.ALLIANCES["Castle"])
        self.assertFalse(config.CONF.has_option("default", "extra_alliances"))

    def test_menu_lists_edit_and_rebuilt_alliances(self):
        parent = QWidget()
        bar = MenuBar(parent)
        self.addCleanup(_close, parent)
        self.addCleanup(_close, bar)
        config.ALLIANCES = collections.OrderedDict([("Only", ["Only"])])
        config.DEFAULT_ALLIANCE = "Only"
        bar._rebuild_alliance_actions()

        labels = [action.text() for action in bar._alliance_menu.actions() if not action.isSeparator()]
        self.assertEqual(["Only", "Edit Alliances..."], labels)
        self.assertTrue(bar._alliance_actions["Only"].isChecked())
