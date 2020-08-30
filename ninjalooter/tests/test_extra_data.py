from ninjalooter import extra_data
from ninjalooter.tests import base
from ninjalooter import utils


class TestExtraData(base.NLTestBase):
    def test_sky_items_exist(self):
        items = set(utils.load_item_data())
        extra_items = set(map(lambda x: x.upper(),
                              extra_data.EXTRA_ITEM_DATA.keys()))
        self.assertEqual(set(), extra_items.difference(items))
