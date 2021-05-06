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


    def test_cancel_sell_order(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.score.create_sell_order(1, 100, 5)

        # List sell order
        self.assertEqual(self.score.list_sell_orders(1), {0: [100, 5, str(self.test_account1)]})

        self.assertEqual(self.score.list_own_sell_orders(), {0: [1, 100, 5]})

        self.score.cancel_own_sell_order(1, 0)

    
    def test_purchase_sell_order(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.score.create_sell_order(1, 100, 5)
        # List sell order
        self.assertEqual(self.score.list_sell_orders(1), {0: [100, 5, str(self.test_account1)]})

        self.assertEqual(self.score.list_own_sell_orders(), {0: [1, 100, 5]})

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        self.set_msg(self.test_account2, 100)
        self.score.purchase_token(1, 0)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 5)
        self.assertEqual(self.score.balanceOf(self.test_account2, 1), 5)

        record = self.score.get_sale_record(1)

        self.assertEqual(self.score._records_count(), 1)
        self.assertEqual(record['token_id'], 1)
        self.assertEqual(record['type'], 'sale_success')
        self.assertEqual(record['seller'], self.test_account1)
        self.assertEqual(record['start_time'], 0)
        self.assertEqual(record['end_time'], self.score.now())
        self.assertEqual(record['starting_price'], 100)
        self.assertEqual(record['final_price'], 100)
        self.assertEqual(record['buyer'], self.test_account2)
        self.assertEqual(record['number_tokens'], 5)


    def test_purchase_buy_order(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create buy order
        self.set_msg(self.test_account2, 100)
        self.score.create_buy_order(1, 100, 5)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)
        self.assertEqual(self.score.balanceOf(self.test_account2, 1), 0)

    def test_cancel_buy_order(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create buy order
        self.set_msg(self.test_account2, 100)
        self.score.create_buy_order(1, 100, 5)

        self.assertEqual(self.get_balance(self.test_account2), 999999999999999999900)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)
        self.assertEqual(self.score.balanceOf(self.test_account2, 1), 0)

        self.score.cancel_own_buy_order(1, 0)

        self.assertEqual(self.get_balance(self.test_account2), 1000000000000000000000)
    
    def test_list_buy_orders_one(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create buy order
        self.set_msg(self.test_account2, 100)
        self.score.create_buy_order(1, 100, 5)

        # List sell order
        self.assertEqual(self.score.list_buy_orders(1), {0: [100, 5, str(self.test_account2)]})
    
    def test_list_buy_orders_two(self):
        # Mint Tokens
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)

        # Create sell order
        self.set_msg(self.test_account2, 100)
        self.score.create_buy_order(1, 100, 5)
        self.set_msg(self.test_account2, 65)
        self.score.create_buy_order(1, 65, 3)


        # List sell order
        self.assertEqual(self.score.list_buy_orders(1), {0: [100, 5, str(self.test_account2)], 
                                                          1: [65, 3,str(self.test_account2)]})



