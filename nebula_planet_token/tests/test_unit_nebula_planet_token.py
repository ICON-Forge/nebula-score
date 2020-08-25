from ..nebula_planet_token import NebulaPlanetToken
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import *


class TestNebulaPlanetToken(ScoreTestCase):

    def setUp(self):
        super().setUp()

        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.score = self.get_score_instance(NebulaPlanetToken, self.test_account1)

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

    def test_gets_name(self):
        self.assertEqual("NebulaPlanetToken", self.score.name())

    def test_gets_test_symbol(self):
        self.assertEqual("NPT", self.score.symbol())

    def test_mints_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")

        self.assertEqual(self.score.ownerOf(1), self.test_account1)
        self.assertEqual(self.score.balanceOf(self.test_account1), 1)

    def test_throws_when_minting_without_correct_role(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to mint tokens")

    def test_transfers_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.transfer(self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_approves_token_transfer(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.approve(self.test_account2, 1)

        self.assertEqual(self.score.getApproved(1), self.test_account2)

    def test_transfers_token_from_another_account(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.transferFrom(self.test_account1, self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_gets_token_balance(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account2, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.mint(self.test_account2, 4, "http://www.example.com/4")
        self.score.mint(self.test_account1, 5, "http://www.example.com/5")

        self.assertEqual(self.score.balanceOf(self.test_account1), 3)
        self.assertEqual(self.score.balanceOf(self.test_account2), 2)

    def test_burns_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.burn(1)
        with self.assertRaises(IconScoreException) as e:
            self.score.ownerOf(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Invalid _tokenId. NFT is burned")
        self.assertEqual(self.score.balanceOf(self.test_account1), 0)

    def test_throws_when_burning_without_correct_role(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.burn(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to burn tokens")

    def test_throws_when_transferring_without_permission(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account2, 2, "http://www.example.com/2")
        with self.assertRaises(IconScoreException) as e:
            self.score.transferFrom(self.test_account1, self.test_account2, 2)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You don't have permission to transfer this NFT")

    def test_throws_when_checking_owner_of_unminted_token(self):
        with self.assertRaises(IconScoreException) as e:
            self.score.ownerOf(2)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Invalid _tokenId. NFT is not minted")

    def test_gets_token_URI(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")

        self.assertEqual(self.score.tokenURI(1), "http://www.example.com/1")

    def test_gets_correct_token_of_owner_by_index(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account2, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.mint(self.test_account2, 4, "http://www.example.com/4")
        self.score.mint(self.test_account1, 5, "http://www.example.com/5")

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 1)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 3), 5)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 1), 2)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 2), 4)

    def test_gets_correct_token_of_owner_by_index_after_burning(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account1, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.burn(1)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 2)

    def test_gets_correct_token_of_owner_by_index_after_transferring(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.transfer(self.test_account2, 1)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 0)

    def test_gets_correct_token_of_owner_by_index_after_transferring_from_another_account(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.mint(self.test_account2, 14, "http://www.example.com/4")
        self.score.transferFrom(self.test_account1, self.test_account2, 12)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 13)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 1), 14)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 2), 12)

    def test_gets_correct_token_by_index_after_burning(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.mint(self.test_account1, 14, "http://www.example.com/4")
        self.score.burn(12)

        self.assertEqual(self.score.tokenByIndex(1), 11)
        self.assertEqual(self.score.tokenByIndex(2), 14)
        self.assertEqual(self.score.tokenByIndex(3), 13)
        self.assertEqual(self.score.tokenByIndex(4), 0)
        self.assertEqual(self.score._get_token_index_by_token_id(11), 1)
        self.assertEqual(self.score._get_token_index_by_token_id(12), 0)
        self.assertEqual(self.score._get_token_index_by_token_id(13), 3)
        self.assertEqual(self.score._get_token_index_by_token_id(14), 2)

    def test_gets_no_tokens_by_index_after_burning_all(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account1, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.burn(1)
        self.score.burn(3)
        self.score.burn(2)

        self.assertEqual(self.score.tokenByIndex(1), 0)
        self.assertEqual(self.score.tokenByIndex(2), 0)
        self.assertEqual(self.score.tokenByIndex(3), 0)

    def test_gets_owned_tokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account1, 2, "http://www.example.com/2")
        expectedAccount1Tokens = [1, 2]
        expectedAccount2Tokens = []

        self.assertEqual(self.score.owned_tokens(self.test_account1), expectedAccount1Tokens)
        self.assertEqual(self.score.owned_tokens(self.test_account2), expectedAccount2Tokens)

    def test_gets_token_using_token_index(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")

        self.assertEqual(self.score._find_token_index_by_token_id(self.test_account1, 12), 2)

    def test_gets_no_token_when_using_nonexistent_index(self):
        self.assertEqual(self.score._find_token_index_by_token_id(self.test_account1, 99), 0)

    def test_increments_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")

        self.assertEqual(self.score.totalSupply(), 2)

    def test_decrements_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.burn(11)

        self.assertEqual(self.score.totalSupply(), 0)

    def test_lists_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account2, 12, "http://www.example.com/1")
        self.score.mint(self.test_account1, 13, "http://www.example.com/2")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(13, 300000000000000000)
        self.set_msg(self.test_account2)
        self.score.list_token(12, 200000000000000000)

        self.assertEqual(self.score.total_listed_token_count(), 3)
        self.assertEqual(self.score.get_token_price(11), 100000000000000000)
        self.assertEqual(self.score.get_token_price(12), 200000000000000000)
        self.assertEqual(self.score.get_token_price(13), 300000000000000000)
        self.assertEqual(self.score.get_listed_token_by_index(1), 11)
        self.assertEqual(self.score.get_listed_token_by_index(2), 13)
        self.assertEqual(self.score.get_listed_token_by_index(3), 12)
        self.assertEqual(self.score._get_owner_listed_token_index(self.test_account1, 1), 11)
        self.assertEqual(self.score._get_owner_listed_token_index(self.test_account2, 1), 12)
        self.assertEqual(self.score._get_owner_listed_token_index(self.test_account1, 2), 13)

    def test_gets_listed_tokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)

        listed_tokens = self.score.listed_tokens()

        expected_tokens = {11: 100000000000000000, 12: 200000000000000000, 13: 300000000000000000}

        self.assertEqual(listed_tokens, expected_tokens)

    def test_gets_listed_tokens_with_offset(self):
        self.set_msg(self.test_account1)
        self.score._MAX_ITERATION_LOOP = 2
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)

        listed_tokens = self.score.listed_tokens()
        expected_tokens = {11: 100000000000000000, 12: 200000000000000000}
        offeset_tokens = self.score.listed_tokens(2)
        expected_offset_tokens = {13: 300000000000000000}

        self.assertEqual(listed_tokens, expected_tokens)
        self.assertEqual(offeset_tokens, expected_offset_tokens)

    def test_gets_listed_tokens_of_owner(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account2, 13, "http://www.example.com/3")
        self.score.mint(self.test_account2, 14, "http://www.example.com/4")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.set_msg(self.test_account2)
        self.score.list_token(13, 300000000000000000)
        self.score.list_token(14, 400000000000000000)

        first_account_tokens = self.score.listed_tokens_by_owner(self.test_account1)
        first_account_expected_tokens = {11: 100000000000000000, 12: 200000000000000000}
        second_account_tokens = self.score.listed_tokens_by_owner(self.test_account2)
        second_account_expected_tokens = {13: 300000000000000000, 14: 400000000000000000}

        self.assertEqual(first_account_tokens, first_account_expected_tokens)
        self.assertEqual(second_account_tokens, second_account_expected_tokens)

    def test_delists_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.mint(self.test_account1, 14, "http://www.example.com/4")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)
        self.score.list_token(14, 400000000000000000)

        self.score.delist_token(12)

        listed_tokens = self.score.listed_tokens()
        expected_tokens = {11: 100000000000000000, 13: 300000000000000000, 14: 400000000000000000}

        self.assertEqual(listed_tokens, expected_tokens)
        self.assertEqual(self.score.get_listed_token_by_index(1), 11)
        self.assertEqual(self.score.get_listed_token_by_index(2), 14)
        self.assertEqual(self.score.get_listed_token_by_index(3), 13)
        self.assertEqual(self.score.total_listed_token_count(), 3)

    def test_throws_when_delisting_an_unlisted_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.score.delist_token(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not listed")

    def test_delists_token_and_keeps_correct_indexes(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account2, 12, "http://www.example.com/2")
        self.score.mint(self.test_account2, 13, "http://www.example.com/3")
        self.score.mint(self.test_account2, 14, "http://www.example.com/4")
        self.score.mint(self.test_account2, 15, "http://www.example.com/5")
        self.score.list_token(11, 100000000000000000)

        self.set_msg(self.test_account2)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)
        self.score.list_token(14, 400000000000000000)
        self.score.list_token(15, 500000000000000000)

        self.score.delist_token(13)

        self.assertEqual(self.score.total_listed_token_count(), 4)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account1), 1)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account2), 3)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 1), 11)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 1), 12)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 2), 15)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 3), 14)

    def test_purchases_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        token_price = 5000000000000000000
        self.score.list_token(11, token_price)

        self.set_msg(self.test_account2, token_price)
        self.score.purchase_token(11)

        self.assertEqual(self.score.icx.get_balance(self.test_account2), 1000000000000000000000 - token_price)
        self.assertEqual(self.score.balanceOf(self.test_account1), 0)
        self.assertEqual(self.score.balanceOf(self.test_account2), 1)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account1), 0)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account2), 0)
        self.assertEqual(self.score.get_token_price(11), 0)

        self.assertEqual(self.score.total_listed_token_count(), 0)

    def test_gets_number_of_listed_tokens_of_owner(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        token_price = 5000000000000000000
        self.score.list_token(11, token_price)

        self.score.assign_minter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.burn(11)

        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account1), 0)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account2), 0)
        self.assertEqual(self.score.get_listed_token_by_index(1), 0)

    def test_pauses_contract(self):
        self.set_msg(self.test_account1)
        self.score.pause_contract()

        self.assertEqual(self.score._isPaused.get(), True)

    def test_throws_when_pausing_contract_while_already_paused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
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

    def test_throws_when_transferring_token_while_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account2, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.transfer(self.test_account1, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_transfers_token_when_contract_is_paused_but_has_correct_role(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.transfer(self.test_account2, 11)

        self.assertEqual(self.score.ownerOf(11), self.test_account2)

    def test_lists_token_when_contract_is_paused_but_has_correct_role(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.list_token(11, 100)

        self.assertEqual(self.score.get_token_price(11), 100)

    def test_throws_when_listing_token_while_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account2, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.list_token(11, 100)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_purchases_token_when_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        token_price = 5000000000000000000
        self.score.list_token(11, token_price)

        self.set_msg(self.test_account2, token_price)
        self.score.purchase_token(11)

        self.assertEqual(self.score.ownerOf(11), self.test_account2)
