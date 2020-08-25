from ..nebula_planet_token import NebulaPlanetToken
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import *

class TestNebulaPlanetToken(ScoreTestCase):

    def setUp(self):
        super().setUp()

        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.score = self.get_score_instance(NebulaPlanetToken, self.test_account1)

    def test_initialize_roles(self):
        self.assertEqual(self.score._director.get(), self.test_account1)
        self.assertEqual(self.score._treasurer.get(), self.test_account1)
        self.assertEqual(self.score._minter.get(), self.test_account1)

    def test_assignTreasurer(self):
        self.set_msg(self.test_account1)
        self.score.assignTreasurer(self.test_account2)

        self.assertEqual(self.score._treasurer.get(), self.test_account2)

    def test_error_assignTreasurer(self):
        self.set_msg(self.test_account2)
        with self.assertRaises(IconScoreException) as e:
            self.score.assignTreasurer(self.test_account1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to assign roles")

    def test_assignMinter(self):
        self.set_msg(self.test_account1)
        self.score.assignMinter(self.test_account2)

        self.assertEqual(self.score._minter.get(), self.test_account2)

    def test_error_assignMinter(self):
        self.set_msg(self.test_account2)
        with self.assertRaises(IconScoreException) as e:
            self.score.assignMinter(self.test_account1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to assign roles")

    def test_get_name(self):
        self.assertEqual("NebulaPlanetToken", self.score.name())

    def test_get_symbol(self):
        self.assertEqual("NPT", self.score.symbol())

    def test_set_mint(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")

        self.assertEqual(self.score.ownerOf(1), self.test_account1)
        self.assertEqual(self.score.balanceOf(self.test_account1), 1)

    def test_error_mint(self):
        self.set_msg(self.test_account1)
        self.score.assignMinter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to mint tokens")

    def test_set_transfer(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.transfer(self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_set_approve(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.approve(self.test_account2, 1)

        self.assertEqual(self.score.getApproved(1), self.test_account2)

    def test_set_transferFrom(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.transferFrom(self.test_account1, self.test_account2, 1)

        self.assertEqual(self.score.ownerOf(1), self.test_account2)
        self.assertEqual(0, self.score.balanceOf(self.test_account1))
        self.assertEqual(1, self.score.balanceOf(self.test_account2))

    def test_get_balanceOf(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account2, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.mint(self.test_account2, 4, "http://www.example.com/4")
        self.score.mint(self.test_account1, 5, "http://www.example.com/5")

        self.assertEqual(self.score.balanceOf(self.test_account1), 3)
        self.assertEqual(self.score.balanceOf(self.test_account2), 2)

    def test_set_burn(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.burn(1)
        with self.assertRaises(IconScoreException) as e:
            self.score.ownerOf(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Invalid _tokenId. NFT is burned")
        self.assertEqual(self.score.balanceOf(self.test_account1), 0)

    def test_error_burn(self):
        self.set_msg(self.test_account1)
        self.score.assignMinter(self.test_account2)

        with self.assertRaises(IconScoreException) as e:
            self.score.burn(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to burn tokens")

    def test_error_transfer(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account2, 2, "http://www.example.com/2")
        with self.assertRaises(IconScoreException) as e:
            self.score.transferFrom(self.test_account1, self.test_account2, 2)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You don't have permission to transfer this NFT")

    def test_error_ownerOf(self):
        with self.assertRaises(IconScoreException) as e:
            self.score.ownerOf(2)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Invalid _tokenId. NFT is not minted")

    def test_get_tokenURI(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")

        self.assertEqual(self.score.tokenURI(1), "http://www.example.com/1")

    def test_get_tokenOfOwnerByIndex(self):
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

    def test_get_tokenOfOwnerByIndex_after_burn(self):
        self.set_msg(self.test_account1)
        self.score.assignMinter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account1, 2, "http://www.example.com/2")
        self.score.mint(self.test_account1, 3, "http://www.example.com/3")
        self.score.burn(1)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 2)

    def test_error_tokenOfOwnerByIndex(self):
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 5), 0)

    def test_get_ownedTokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 1, "http://www.example.com/1")
        self.score.mint(self.test_account1, 2, "http://www.example.com/2")
        expectedAccount1Tokens = [1, 2]
        expectedAccount2Tokens = []

        self.assertEqual(self.score.ownedTokens(self.test_account1), expectedAccount1Tokens)
        self.assertEqual(self.score.ownedTokens(self.test_account2), expectedAccount2Tokens)

    def test_get_findTokenIndexByTokenId(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")

        self.assertEqual(self.score._findTokenIndexByTokenId(self.test_account1, 12), 2)

    def test_emptyResult_findTokenIndexByTokenId(self):
        self.assertEqual(self.score._findTokenIndexByTokenId(self.test_account1, 99), 0)

    def test_get_ownerTokenIndex(self):
        self.set_msg(self.test_account1)
        self.score._setOwnerTokenIndex(self.test_account1, 1, 11)
        self.score._setOwnerTokenIndex(self.test_account1, 2, 12)

        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 12)

    def test_ownerTokenIndex_mint_and_burn(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.mint(self.test_account1, 14, "http://www.example.com/4")
        self.score._burn(self.test_account1, 12)

        self.assertEqual(self.score._ownedTokenCount[self.test_account1], 3)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 2), 14)
        self.assertEqual(self.score.tokenOfOwnerByIndex(self.test_account1, 3), 13)

    def test_ownerTokenIndex_transfer(self):
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

    def test_incrementTotalSupply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")

        self.assertEqual(self.score.totalSupply(), 2)

    def test_decrementTotalSupply(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.burn(11)

        self.assertEqual(self.score.totalSupply(), 0)

    def test_token_indexes(self):
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
        self.assertEqual(self.score._getTokenIndexByTokenId(11), 1)
        self.assertEqual(self.score._getTokenIndexByTokenId(12), 0)
        self.assertEqual(self.score._getTokenIndexByTokenId(13), 3)
        self.assertEqual(self.score._getTokenIndexByTokenId(14), 2)

    def test_listToken(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account2, 12, "http://www.example.com/1")
        self.score.mint(self.test_account1, 13, "http://www.example.com/2")
        self.score.listToken(11, 100000000000000000)
        self.score.listToken(13, 300000000000000000)
        self.set_msg(self.test_account2)
        self.score.listToken(12, 200000000000000000)

        self.assertEqual(self.score.totalListedTokenCount(), 3)
        self.assertEqual(self.score.getTokenPrice(11), 100000000000000000)
        self.assertEqual(self.score.getTokenPrice(12), 200000000000000000)
        self.assertEqual(self.score.getTokenPrice(13), 300000000000000000)
        self.assertEqual(self.score.getListedTokenByIndex(1), 11)
        self.assertEqual(self.score.getListedTokenByIndex(2), 13)
        self.assertEqual(self.score.getListedTokenByIndex(3), 12)
        self.assertEqual(self.score._getOwnerListedTokenIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score._getOwnerListedTokenIndex(self.test_account2, 1), 12)
        self.assertEqual(self.score._getOwnerListedTokenIndex(self.test_account1, 2), 13)

    def test_get_listedTokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.listToken(11, 100000000000000000)
        self.score.listToken(12, 200000000000000000)
        self.score.listToken(13, 300000000000000000)

        listedTokens = self.score.listedTokens()

        expectedTokens = {11: 100000000000000000, 12: 200000000000000000, 13: 300000000000000000}

        self.assertEqual(listedTokens, expectedTokens)

    def test_get_listedTokens_over_max_iteration(self):
        self.set_msg(self.test_account1)
        self.score.MAX_ITERATION_LOOP = 2
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.listToken(11, 100000000000000000)
        self.score.listToken(12, 200000000000000000)
        self.score.listToken(13, 300000000000000000)

        listedTokens = self.score.listedTokens()
        expectedTokens = {11: 100000000000000000, 12: 200000000000000000}
        offsetTokens = self.score.listedTokens(2)
        expectedOffsetTokens = {13: 300000000000000000}

        self.assertEqual(listedTokens, expectedTokens)
        self.assertEqual(offsetTokens, expectedOffsetTokens)

    def test_get_ownerListedTokens(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account2, 13, "http://www.example.com/3")
        self.score.mint(self.test_account2, 14, "http://www.example.com/4")
        self.score.listToken(11, 100000000000000000)
        self.score.listToken(12, 200000000000000000)
        self.set_msg(self.test_account2)
        self.score.listToken(13, 300000000000000000)
        self.score.listToken(14, 400000000000000000)

        firstAccountTokens = self.score.listedTokensByOwner(self.test_account1)
        firstAccountExpectedTokens = {11: 100000000000000000, 12: 200000000000000000}
        secondAccountTokens = self.score.listedTokensByOwner(self.test_account2)
        secondAccountExpectedTokens = {13: 300000000000000000, 14: 400000000000000000}

        self.assertEqual(firstAccountTokens, firstAccountExpectedTokens)
        self.assertEqual(secondAccountTokens, secondAccountExpectedTokens)

    def test_delistToken(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account1, 12, "http://www.example.com/2")
        self.score.mint(self.test_account1, 13, "http://www.example.com/3")
        self.score.mint(self.test_account1, 14, "http://www.example.com/4")
        self.score.listToken(11, 100000000000000000)
        self.score.listToken(12, 200000000000000000)
        self.score.listToken(13, 300000000000000000)
        self.score.listToken(14, 400000000000000000)

        self.score.delistToken(12)

        listedTokens = self.score.listedTokens()
        expectedTokens = {11: 100000000000000000, 13: 300000000000000000, 14: 400000000000000000}

        self.assertEqual(listedTokens, expectedTokens)
        self.assertEqual(self.score.getListedTokenByIndex(1), 11)
        self.assertEqual(self.score.getListedTokenByIndex(2), 14)
        self.assertEqual(self.score.getListedTokenByIndex(3), 13)
        self.assertEqual(self.score.totalListedTokenCount(), 3)

    def test_error_delistToken(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.score.delistToken(11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not listed")

    def test_clearOwnerTokenListing(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.mint(self.test_account2, 12, "http://www.example.com/2")
        self.score.mint(self.test_account2, 13, "http://www.example.com/3")
        self.score.mint(self.test_account2, 14, "http://www.example.com/4")
        self.score.mint(self.test_account2, 15, "http://www.example.com/5")
        self.score.listToken(11, 100000000000000000)

        self.set_msg(self.test_account2)
        self.score.listToken(12, 200000000000000000)
        self.score.listToken(13, 300000000000000000)
        self.score.listToken(14, 400000000000000000)
        self.score.listToken(15, 500000000000000000)

        self.score.delistToken(13)

        self.assertEqual(self.score.totalListedTokenCount(), 4)
        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account1), 1)
        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account2), 3)
        self.assertEqual(self.score.getListedTokenOfOwnerByIndex(self.test_account1, 1), 11)
        self.assertEqual(self.score.getListedTokenOfOwnerByIndex(self.test_account2, 1), 12)
        self.assertEqual(self.score.getListedTokenOfOwnerByIndex(self.test_account2, 2), 15)
        self.assertEqual(self.score.getListedTokenOfOwnerByIndex(self.test_account2, 3), 14)

    def test_purchaseToken(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        tokenPrice = 5000000000000000000
        self.score.listToken(11, tokenPrice)

        self.set_msg(self.test_account2, tokenPrice)
        self.score.purchaseToken(11)

        self.assertEqual(self.score.icx.get_balance(self.test_account2), 1000000000000000000000 - tokenPrice)
        self.assertEqual(self.score.balanceOf(self.test_account1), 0)
        self.assertEqual(self.score.balanceOf(self.test_account2), 1)
        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account1), 0)
        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account2), 0)
        self.assertEqual(self.score.getTokenPrice(11), 0)

        self.assertEqual(self.score.totalListedTokenCount(), 0)

    def test_listedTokenCountByOwner_after_burn(self):
        self.set_msg(self.test_account1)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        tokenPrice = 5000000000000000000
        self.score.listToken(11, tokenPrice)

        self.score.assignMinter(self.test_account2)
        self.set_msg(self.test_account2)
        self.score.burn(11)

        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account1), 0)
        self.assertEqual(self.score.listedTokenCountByOwner(self.test_account2), 0)

    def test_pauseContract(self):
        self.set_msg(self.test_account1)
        self.score.pauseContract()

        self.assertEqual(self.score._isPaused.get(), True)

    def test_error_unpauseContract(self):
        self.set_msg(self.test_account1)
        with self.assertRaises(IconScoreException) as e:
            self.score.unpauseContract()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is already unpaused")

    def test_error_pauseContract(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        with self.assertRaises(IconScoreException) as e:
            self.score.pauseContract()
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is already paused")

    def test_error_transfer_when_isPaused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account2, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.transfer(self.test_account1, 11)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_transfer_when_isPaused_and_minter(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.transfer(self.test_account2, 11)

        self.assertEqual(self.score.ownerOf(11), self.test_account2)

    def test_listToken_when_isPaused_and_minter(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        self.score.listToken(11, 100)

        self.assertEqual(self.score.getTokenPrice(11), 100)

    def test_error_list_when_isPaused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account2, 11, "http://www.example.com/1")
        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2)
            self.score.listToken(11, 100)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Contract is currently paused")

    def test_purchaseToken_when_isPaused(self):
        self.set_msg(self.test_account1)
        self.score._isPaused.set(True)
        self.score.mint(self.test_account1, 11, "http://www.example.com/1")
        tokenPrice = 5000000000000000000
        self.score.listToken(11, tokenPrice)

        self.set_msg(self.test_account2, tokenPrice)
        self.score.purchaseToken(11)

        self.assertEqual(self.score.ownerOf(11), self.test_account2)





































