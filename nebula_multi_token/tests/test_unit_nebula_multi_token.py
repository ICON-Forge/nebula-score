from nebula_multi_token import NebulaMultiToken
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import *


class TestNebulaMultiToken(ScoreTestCase):

    def setUp(self):
        super().setUp()

        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.score = self.get_score_instance(NebulaMultiToken, self.test_account1)

    def test_initializes_roles(self):
        self.assertEqual(self.score._director.get(), self.test_account1)
        self.assertEqual(self.score._treasurer.get(), self.test_account1)
        self.assertEqual(self.score._minter.get(), self.test_account1)

    def test_assigns_treasurer(self):
        self.set_msg(self.test_account1)
        self.score.assign_treasurer(self.test_account2)

        self.assertEqual(self.score._treasurer.get(), self.test_account2)

    def test_throws_when_assigning_treasurer_without_correct_role(self):
        self.set_msg(self.test_account2)
        with self.assertRaises(IconScoreException) as e:
            self.score.assign_treasurer(self.test_account1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to assign roles")

    def test_assigns_minter(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        self.assertEqual(self.score._minter.get(), self.test_account2)

    def test_throws_when_assigning_minter_without_correct_role(self):
        self.set_msg(self.test_account2)
        with self.assertRaises(IconScoreException) as e:
            self.score.assign_minter(self.test_account1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to assign roles")

    def test_mints_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 10)
        self.assertEqual(self.score.totalSupply(), 1)
        self.assertEqual(self.score.totalSupplyPerToken(1), 10)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 1)
    
    def test_increments_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 11, 5, "1.json")
        self.score.mint_to(self.test_account1, 12, 5, "2.json")

        self.assertEqual(self.score.totalSupply(), 2)

    def test_decrements_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 11, 10, "1.json")
        self.score.burn(11, 9)

        self.assertEqual(self.score.totalSupplyPerToken(11), 1)
    
    def test_no_balance_of_token(self):
        self.set_msg(self.test_account1)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 0)

    def test_throws_when_minting_without_correct_role(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.mint(1, 10, "1.json")
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to mint tokens")

    def test_transfers_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.score.transfer(self.test_account2, 1, 5)

        #self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 5)
        self.assertEqual(self.score.balanceOf(self.test_account2, 1), 5)

    # def test_approves_token_transfer(self):
    #     self.set_msg(self.test_account1)
    #     self.score.mint(1, 10, "1.json")
    #     self.score.approve(self.test_account2, 1)

    #     self.assertEqual(self.score.getApproved(1), self.test_account2)

    def test_transfers_token_from_another_account(self):
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.score.transferFrom(self.test_account1, self.test_account2, 1, 6)

        # TODO self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 4)
        self.assertEqual(self.score.balanceOf(self.test_account2, 1), 6)
    
    def test_gets_token_balance(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 1, 10, "1.json")
        self.score.mint_to(self.test_account2, 2, 10, "2.json")
        self.score.mint_to(self.test_account1, 3, 10, "3.json")
        self.score.mint_to(self.test_account2, 4, 10, "4.json")
        self.score.mint_to(self.test_account1, 5, 10, "5.json")

        self.assertEqual(self.score.balanceOfTokenClasses(self.test_account1), 3)
        self.assertEqual(self.score.balanceOfTokenClasses(self.test_account2), 2)

    def test_burns_token_partly(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 1, 10, "1.json")
        token_supply = self.score.totalSupplyPerToken(1)
        self.score.burn(1, 5)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 5)
        self.assertEqual(self.score.totalSupplyPerToken(1), 5)

    def test_burns_token_all_for_user(self):
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.score.mint(2, 10, "2.json")
        token_supply = self.score.totalSupplyPerToken(1)
        self.score.burn(1, 10)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 0)
        self.assertEqual(self.score.totalSupplyPerToken(1), 0)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 2)
        self.assertEqual(self.score.balanceOfTokenClasses(self.test_account1), 1)

    def test_burns_received_token(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account2, 1, 10, "1.json")
        self.score.mint_to(self.test_account2, 2, 10, "2.json")

        self.set_msg(self.test_account2)
        self.score.transfer(self.test_account1, 1, 10)
        self.score.transfer(self.test_account1, 2, 10)

        self.set_msg(self.test_account1)
        token_supply = self.score.totalSupplyPerToken(1)
        self.score.burn(1, 5)

        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 5)
        self.assertEqual(self.score.balanceOf(self.test_account1, 2), 10)
        self.assertEqual(self.score.totalSupplyPerToken(1), 5)
        self.assertEqual(self.score.totalSupplyPerToken(2), 10)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 1)
        self.assertEqual(self.score.balanceOfTokenClasses(self.test_account1), 2)

        self.score.burn(1, 5)
        self.assertEqual(self.score.balanceOf(self.test_account1, 1), 0)
        self.assertEqual(self.score.balanceOf(self.test_account1, 2), 10)
        self.assertEqual(self.score.totalSupplyPerToken(1), 0)
        self.assertEqual(self.score.totalSupplyPerToken(2), 10)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 2)
        self.assertEqual(self.score.balanceOfTokenClasses(self.test_account1), 1)

    
    def test_throws_burns_transfered_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(1, 10, "1.json")
        self.score.mint(2, 10, "2.json")
        self.score.transfer(self.test_account2, 1, 10)
        with self.assertRaises(IconScoreException) as e:
            self.score.burn(1, 10)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "The token balance is not correct.")        

    def test_throws_when_burning_without_correct_role(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.burn(1, 5)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to burn tokens")

    def test_throws_when_transferring_without_permission(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 1, 10, "1.json")
        self.score.mint_to(self.test_account2, 2, 10, "2.json")
        with self.assertRaises(IconScoreException) as e:
            self.score.transferFrom(self.test_account2, self.test_account1, 1, 5)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You don't have permission to transfer this NFT")

    def test_gets_token_URI(self):
        self.set_msg(self.test_account1)
        self.score.set_metadata_base_URL("http://www.projectnebula.app/api/metadata/")
        self.score.mint_to(self.test_account1, 1, 10, "1.json")

        self.assertEqual(self.score.tokenURI(1), "http://www.projectnebula.app/api/metadata/1.json")

    # # TODO
    # def test_gets_correct_token_of_owner_by_index(self):
    #     self.set_msg(self.test_account1)
    #     self.score.mint(self.test_account1, 1, 10, "1.json")
    #     self.score.mint(self.test_account2, 2, 10, "2.json")
    #     self.score.mint(self.test_account1, 3, 10, "3.json")
    #     self.score.mint(self.test_account2, 4, 10, "4.json")
    #     self.score.mint(self.test_account1, 5, 10, "5.json")

    #     self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 1)
    #     self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 3)
    #     self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 3), 5)
    #     self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 1), 2)
    #     self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 2), 4)

    def test_pauses_contract(self):
        self.set_msg(self.test_account1)
        self.score.pause_contract()

        self.assertEqual(self.score._is_paused.get(), True)

    def test_throws_when_pausing_contract_while_already_paused(self):
        self.set_msg(self.test_account1)
        self.score._is_paused.set(True)
        with self.assertRaises(IconScoreException) as e:
            self.score.pause_contract()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is already paused")

    def test_throws_when_unpausing_contract_while_already_unpaused(self):
        self.set_msg(self.test_account1)
        with self.assertRaises(IconScoreException) as e:
            self.score.unpause_contract()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is already unpaused")

    def test_restricts_token_sale(self):
        self.set_msg(self.test_account1)
        self.score.restrict_sale()

        self.assertEqual(self.score._is_restricted_sale.get(), True)

    def test_throws_when_restricting_sale_while_already_restricted(self):
        self.set_msg(self.test_account1)
        self.score._is_restricted_sale.set(True)
        with self.assertRaises(IconScoreException) as e:
            self.score.restrict_sale()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token sale is already restricted")

    def test_throws_when_unrestricting_sale_while_already_unrestricted(self):
        self.set_msg(self.test_account1)
        with self.assertRaises(IconScoreException) as e:
            self.score.unrestrict_sale()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token sale is already without restrictions")

    def test_gets_owned_tokens(self):
        self.set_msg(self.test_account1)
        self.score.mint_to(self.test_account1, 1, 10, "1.json")
        self.score.mint_to(self.test_account1, 2, 10, "2.json")
        expectedAccount1Tokens = [1, 2]
        expectedAccount2Tokens = []

        self.assertEqual(self.score.owned_tokens(self.test_account1), expectedAccount1Tokens)
        self.assertEqual(self.score.owned_tokens(self.test_account2), expectedAccount2Tokens)
    
    def test_calculate_seller_fee(self):
        self.set_msg(self.test_account1)
        self.score.set_seller_fee(2500)

        price = 100
        fee = self.score._calculate_seller_fee(price)

        self.assertEqual(fee, 2.5)

    def test_gets_seller_fee(self):
        self.set_msg(self.test_account1)
        self.score.set_seller_fee(2500)

        self.assertEqual(self.score.seller_fee(), 2500)
