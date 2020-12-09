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
        self.score.mint(self.test_account1, 1, "1.json")

        self.assertEqual(self.score.ownerOf(1), self.test_account1)
        self.assertEqual(self.score.balanceOf(self.test_account1), 1)

    def test_throws_when_minting_without_correct_role(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.mint(self.test_account1, 1, "1.json")
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to mint tokens")

    def test_transfers_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.transfer(self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_approves_token_transfer(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.approve(self.test_account2, 1)

        self.assertEqual(self.score.getApproved(1), self.test_account2)

    def test_transfers_token_from_another_account(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.transferFrom(self.test_account1, self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_gets_token_balance(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account2, 2, "2.json")
        self.score.mint(self.test_account1, 3, "3.json")
        self.score.mint(self.test_account2, 4, "4.json")
        self.score.mint(self.test_account1, 5, "5.json")

        self.assertEqual(self.score.balanceOf(self.test_account1), 3)
        self.assertEqual(self.score.balanceOf(self.test_account2), 2)

    def test_burns_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
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
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account2, 2, "2.json")
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
        self.score.set_metadata_base_URL("http://www.projectnebula.app/api/metadata/")
        self.score.mint(self.test_account1, 1, "1.json")

        self.assertEqual(self.score.tokenURI(1), "http://www.projectnebula.app/api/metadata/1.json")

    def test_gets_correct_token_of_owner_by_index(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account2, 2, "2.json")
        self.score.mint(self.test_account1, 3, "3.json")
        self.score.mint(self.test_account2, 4, "4.json")
        self.score.mint(self.test_account1, 5, "5.json")

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 1)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 3), 5)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 1), 2)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 2), 4)

    def test_gets_correct_token_of_owner_by_index_after_burning(self):
        self.set_msg(self.test_account1)
        self.score.assign_minter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account1, 2, "2.json")
        self.score.mint(self.test_account1, 3, "3.json")
        self.score.burn(1)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 2)

    def test_gets_correct_token_of_owner_by_index_after_transferring(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.transfer(self.test_account2, 1)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 0)

    def test_gets_correct_token_of_owner_by_index_after_transferring_from_another_account(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
        self.score.mint(self.test_account2, 14, "4.json")
        self.score.transferFrom(self.test_account1, self.test_account2, 12)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 13)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 1), 14)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account2, 2), 12)

    def test_gets_correct_token_by_index_after_burning(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
        self.score.mint(self.test_account1, 14, "4.json")
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
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account1, 2, "2.json")
        self.score.mint(self.test_account1, 3, "3.json")
        self.score.burn(1)
        self.score.burn(3)
        self.score.burn(2)

        self.assertEqual(self.score.tokenByIndex(1), 0)
        self.assertEqual(self.score.tokenByIndex(2), 0)
        self.assertEqual(self.score.tokenByIndex(3), 0)

    def test_gets_owned_tokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "1.json")
        self.score.mint(self.test_account1, 2, "2.json")
        expectedAccount1Tokens = [1, 2]
        expectedAccount2Tokens = []

        self.assertEqual(self.score.owned_tokens(self.test_account1), expectedAccount1Tokens)
        self.assertEqual(self.score.owned_tokens(self.test_account2), expectedAccount2Tokens)

    def test_gets_token_using_token_index(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")

        self.assertEqual(self.score._find_token_index_by_token_id(self.test_account1, 12), 2)

    def test_gets_no_token_when_using_nonexistent_index(self):
        self.assertEqual(self.score._find_token_index_by_token_id(self.test_account1, 99), 0)

    def test_increments_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")

        self.assertEqual(self.score.totalSupply(), 2)

    def test_decrements_total_supply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.burn(11)

        self.assertEqual(self.score.totalSupply(), 0)

    def test_lists_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account2, 12, "1.json")
        self.score.mint(self.test_account1, 13, "2.json")
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
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 1), 11)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 1), 12)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 2), 13)

    def test_gets_listed_tokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)

        listed_tokens = self.score.listed_tokens()

        expected_tokens = {11: 100000000000000000, 12: 200000000000000000, 13: 300000000000000000}

        self.assertEqual(listed_tokens, expected_tokens)

    def test_gets_listed_tokens_with_offset(self):
        self.set_msg(self.test_account1)
        self.score._MAX_ITERATION_LOOP = 2
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
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
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account2, 13, "3.json")
        self.score.mint(self.test_account2, 14, "4.json")
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
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
        self.score.mint(self.test_account1, 14, "4.json")
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
        self.score.mint(self.test_account1, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            self.score.delist_token(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not listed")

    def test_throws_when_delisting_an_auctioned_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 300000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.delist_token(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is on auction and can't be delisted")


    def test_delists_token_and_keeps_correct_indexes(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account1, 12, "2.json")
        self.score.mint(self.test_account1, 13, "3.json")
        self.score.mint(self.test_account2, 14, "4.json")
        self.score.mint(self.test_account2, 15, "5.json")
        self.score.mint(self.test_account2, 16, "6.json")
        self.score.list_token(11, 100000000000000000)
        self.score.list_token(12, 200000000000000000)
        self.score.list_token(13, 300000000000000000)

        self.set_msg(self.test_account2)
        self.score.list_token(14, 400000000000000000)
        self.score.list_token(15, 500000000000000000)
        self.score.list_token(16, 600000000000000000)

        self.score.delist_token(15)

        self.set_msg(self.test_account1)

        self.score.delist_token(12)

        self.assertEqual(self.score.total_listed_token_count(), 4)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account1), 2)
        self.assertEqual(self.score.listed_token_count_by_owner(self.test_account2), 2)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 1), 11)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 2), 13)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 1), 14)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 2), 16)

        self.assertEqual(self.score._get_listed_token_index_by_token_id(11), 1)
        self.assertEqual(self.score._get_listed_token_index_by_token_id(13), 3)
        self.assertEqual(self.score._get_listed_token_index_by_token_id(14), 4)
        self.assertEqual(self.score._get_listed_token_index_by_token_id(16), 2)

    def test_purchase_token(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
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
        self.score.mint(self.test_account1, 11, "1.json")
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

    def test_throws_when_transferring_token_while_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._is_paused.set(True)
        self.score.mint(self.test_account2, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.transfer(self.test_account1, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_lists_token_when_contract_is_paused_but_has_correct_role(self):
        self.set_msg(self.test_account1)
        self.score._is_paused.set(True)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.list_token(11, 100)

        self.assertEqual(self.score.get_token_price(11), 100)

    def test_throws_when_listing_token_while_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._is_paused.set(True)
        self.score.mint(self.test_account2, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.list_token(11, 100)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_throws_when_purchasing_token_while_contract_is_paused(self):
        self.set_msg(self.test_account1)
        self.score._is_paused.set(True)
        self.score.mint(self.test_account1, 11, "1.json")
        token_price = 5000000000000000000
        self.score.list_token(11, token_price)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, token_price)
            self.score.purchase_token(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

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

    def test_throws_when_listing_token_while_sale_is_restricted(self):
        self.set_msg(self.test_account1)
        self.score._is_restricted_sale.set(True)
        self.score.mint(self.test_account2, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.list_token(11, 100)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Listing tokens is currently disabled")

    def test_throws_when_approving_token_while_sale_is_restricted(self):
        self.set_msg(self.test_account1)
        self.score._is_restricted_sale.set(True)
        self.score.mint(self.test_account2, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.approve(self.test_account1, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Approving tokens is currently disabled")

    def test_lists_token_when_sale_is_restricted_but_has_correct_role(self):
        self.set_msg(self.test_account1)
        self.score._is_restricted_sale.set(True)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.list_token(11, 100)

        self.assertEqual(self.score.get_token_price(11), 100)

    def test_purchase_token_throws_when_sent_amount_is_zero(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        with self.assertRaises(IconScoreException) as e:
            token_price = 0
            self.set_msg(self.test_account2, token_price)
            self.score.purchase_token(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Sent ICX amount needs to be greater than 0")

    def test_create_auction(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.mint(self.test_account2, 12, "1.json")
        self.score.mint(self.test_account1, 13, "2.json")
        self.score.list_token(11, 100000000000000000)
        self.score.create_auction(13, 300000000000000000, 24)
        self.set_msg(self.test_account2)
        self.score.list_token(12, 200000000000000000)

        self.assertEqual(self.score.total_listed_token_count(), 3)
        self.assertEqual(self.score.get_token_price(11), 100000000000000000)
        self.assertEqual(self.score.get_token_price(12), 200000000000000000)
        self.assertEqual(self.score.get_token_price(13), -1)
        self.assertEqual(self.score.get_listed_token_by_index(1), 11)
        self.assertEqual(self.score.get_listed_token_by_index(2), 13)
        self.assertEqual(self.score.get_listed_token_by_index(3), 12)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 1), 11)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account2, 1), 12)
        self.assertEqual(self.score.get_listed_token_of_owner_by_index(self.test_account1, 2), 13)

    def test_create_auction_throws_when_token_already_listed(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "11")
        self.score.list_token(11, 100000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.score.create_auction(11, 300000000000000000, 24)

        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is already listed")

    def test_create_auction_throws_when_token_already_on_auction(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "11")
        self.score.create_auction(11, 500000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.create_auction(11, 300000000000000000, 24)

        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is already auctioned")

    def test_create_auction_throws_when_duration_is_too_long(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "11")

        with self.assertRaises(IconScoreException) as e:
            self.score.create_auction(11, 300000000000000000, 337) # Two weeks + 1 hour

        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Auction duration can not be longer than two weeks")

    def test_get_auction_info(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        duration = 24
        self.score.create_auction(11, 300000000000000000, duration)

        result = self.score.get_auction_info(11)
        end_time = result['start_time'] + duration * 3600 * 1000 * 1000

        self.assertEqual(result['current_bid'], 0)
        self.assertEqual(result['highest_bidder'], None)
        self.assertEqual(result['starting_price'], 300000000000000000)
        self.assertEqual(result['end_time'], end_time)

    def test_get_auction_info_throws_when_no_listing(self):
        self.set_msg(self.test_account1)

        with self.assertRaises(IconScoreException) as e:
            self.score.get_auction_info(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not on auction")

    def test_get_auction_info_throws_when_token_is_listed_but_not_auctioned(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.list_token(11, 100000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.score.get_auction_info(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not on auction")

    def test_place_bid(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        token_price = 5000000000000000000
        self.score.create_auction(11, token_price, 24)

        self.set_msg(self.test_account2, token_price)
        self.score.place_bid(11)

        result = self.score.get_auction_info(11)
        self.assertEqual(result['current_bid'], token_price)
        self.assertEqual(result['highest_bidder'], self.test_account2)

    def test_place_bid_throws_when_amount_is_less_than_minimum_bid(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, 3000000000000000000)
            self.score.place_bid(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Your bid 3.0 is lower than minimum bid amount 5.0")

    def test_place_bid_throws_when_token_is_listed_with_fixed_price(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.list_token(11, 5000000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, 5000000000000000000)
            self.score.place_bid(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not on auction")

    def test_place_bid_throws_when_token_is_not_listed(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, 5000000000000000000)
            self.score.place_bid(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not on auction")

    def test_transfer_throws_when_token_is_on_auction(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.transfer(self.test_account2, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is currently on auction")

    def test_transfer_from_throws_when_token_is_on_auction(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.transferFrom(self.test_account1, self.test_account2, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is currently on auction")

    def test_return_unsold_item_throws_when_status_is_active(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.return_unsold_item(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Auction needs to have status: unsold. Current status: active")

    def test_claim_auctioned_item_throws_when_status_is_active(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.score.claim_auctioned_item(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Auction needs to have status: unclaimed. Current status: active")

    def test_cancel_auction(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 300000000000000000, 24)

        self.assertEqual(self.score.total_listed_token_count(), 1)

        self.score.cancel_auction(11)

        self.assertEqual(self.score.total_listed_token_count(), 0)

    def test_cancel_auction_throws_when_bid_has_been_made(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        self.set_msg(self.test_account2, 5000000000000000000)
        self.score.place_bid(11)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account1)
            self.score.cancel_auction(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Bid has already been made. Auction cannot be cancelled.")

    def test_cancel_auction_throws_when_caller_is_not_token_owner(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.create_auction(11, 5000000000000000000, 24)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.cancel_auction(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You do not own this NFT")

    def test_cancel_auction_throws_when_token_is_listed(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        self.score.list_token(11, 5000000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.score.cancel_auction(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not on auction")

    def test_place_bid_extend_time(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "1.json")
        token_price = 5000000000000000000
        self.score.create_auction(11, token_price, 1)

        result = self.score.get_auction_info(11)
        print(result['end_time'])

        self.set_msg(self.test_account2, token_price)
        self.score.place_bid(11)

        result = self.score.get_auction_info(11)
        print(result['end_time'])

        self.assertEqual(result['current_bid'], token_price)
        self.assertEqual(result['highest_bidder'], self.test_account2)
