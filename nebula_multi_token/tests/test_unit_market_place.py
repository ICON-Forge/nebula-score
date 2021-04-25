from nebula_multi_token import NebulaMultiToken
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import *


class TestMarketPlace(ScoreTestCase):

    def setUp(self):
        super().setUp()

        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.score = self.get_score_instance(NebulaMultiToken, self.test_account1)

    def test_create_one_sell_order(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.score.create_sell_order(1, 100, 5)
    
    def test_list_sell_orders_one(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.score.create_sell_order(1, 100, 5)

        # List sell order
        self.assertEqual(self.score.list_sell_orders(1), {0: [100, 5, str(self.test_account1)]})
    
    def test_list_sell_orders_two(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.score.create_sell_order(1, 100, 5)
        self.score.create_sell_order(1, 120, 5)

        # List sell order
        self.assertEqual(self.score.list_sell_orders(1), {0: [100, 5, str(self.test_account1)], 
                                                          1: [120, 5,str(self.test_account1)]})