from ninjalooter import logparse
from ninjalooter.tests import base
from ninjalooter import utils

SAMPLE_OOC = (
    "[Mon Aug 17 00:04:45 2020] "
    "Calcium says out of character, "
    "'Shiny Pauldrons Belt of Iniquity'")


class TestLogparse(base.NLTestBase):
    def setUp(self) -> None:
        super(TestLogparse, self).setUp()
        utils.setup_aho()

    def test_match_line(self):
        match = logparse.match_line(SAMPLE_OOC)
        items = tuple(match)
        self.assertEqual(2, len(items))
        self.assertIn('Shiny Pauldrons'.upper(), items)
        self.assertIn('Belt of Iniquity'.upper(), items)
