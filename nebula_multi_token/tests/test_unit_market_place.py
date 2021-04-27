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

    def test_list_sell_orders_multiple_users(self):
        # Mint Tokens User 1
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)
        self.score.mint(2, 20, "2.json")

        # Transfer Token
        self.score.transfer(self.test_account2, 2, 15)

        self.assertEqual(self.score.balanceOf(self.test_account1, 2), 5)
        self.assertEqual(self.score.balanceOf(self.test_account2, 2), 15)       

        # Create first sell order user 1
        self.score.create_sell_order(1, 100, 5)

        # Create first sell order user 2
        self.set_msg(self.test_account2)
        self.score.create_sell_order(2, 250, 15)

        # Create second sell order user 1
        self.set_msg(self.test_account1)
        self.score.create_sell_order(1, 120, 5)
        self.score.create_sell_order(2, 60, 5)

        # List sell order
        self.assertEqual(self.score.list_sell_orders(1), {0: [100, 5, str(self.test_account1)], 
                                                          1: [120, 5,str(self.test_account1)]})
        
        self.assertEqual(self.score.list_sell_orders(2), {0: [250, 15, str(self.test_account2)],
                                                          1: [60, 5, str(self.test_account1)]})
    
    def test_list_own_sell_orders(self):
        # Mint Tokens User 1
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)
        self.score.mint(2, 20, "2.json")

        # Transfer Token
        self.score.transfer(self.test_account2, 2, 15)

        self.assertEqual(self.score.balanceOf(self.test_account1, 2), 5)
        self.assertEqual(self.score.balanceOf(self.test_account2, 2), 15)       

        # Create first sell order user 1
        self.score.create_sell_order(1, 100, 5)

        # Create first sell order user 2
        self.set_msg(self.test_account2)
        self.score.create_sell_order(2, 250, 15)

        # Create second sell order user 1
        self.set_msg(self.test_account1)
        self.score.create_sell_order(1, 120, 5)
        self.score.create_sell_order(2, 60, 5)

        # List sell order
        self.assertEqual(self.score.list_own_sell_orders(), {0: [1, 100, 5], 
                                                          1: [1, 120, 5],
                                                          2: [2, 60, 5]})
        
        self.set_msg(self.test_account2)
        self.assertEqual(self.score.list_own_sell_orders(), {0: [2, 250, 15]})

