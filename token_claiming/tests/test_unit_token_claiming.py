from ..token_claiming import NebulaTokenClaiming
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from iconservice import *

class TestNebulaSpaceshipToken(ScoreTestCase):

    def setUp(self):
        super().setUp()

        self.mock_score_address = Address.from_string(f"cx{'1234'*10}")
        self.score = self.get_score_instance(NebulaTokenClaiming, self.test_account1)

    def test_initializes_roles(self):
        self.assertEqual(self.score._director.get(), self.test_account1)
        self.assertEqual(self.score._treasurer.get(), self.test_account1)
        self.assertEqual(self.score._operator.get(), self.test_account1)
        self.assertEqual(self.score._distributor.get(), self.test_account1)

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

    def test_assigns_operator(self):
        self.set_msg(self.test_account1)
        self.score.assign_operator(self.test_account2)

        self.assertEqual(self.score._operator.get(), self.test_account2)

    def test_throws_when_assigning_operator_without_correct_role(self):
        self.set_msg(self.test_account2)
        with self.assertRaises(IconScoreException) as e:
            self.score.assign_operator(self.test_account1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "You are not allowed to assign roles")

    def test_sets_whitelist_duration(self):
        self.set_msg(self.test_account1)
        self.score.set_whitelist_duration(60)

        self.assertEqual(self.score.get_whitelist_duration(), 60)

    def test_lists_token(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)

        expected = {
            "token_id": 1,
            "base_price": 100000000000000000
        }

        self.assertEqual(self.score.total_listed_token_count(), 1)
        self.assertEqual(self.score.get_token_listing(1), expected)

    def test_throws_when_listing_alrady_listed_token(self):
        self.set_msg(self.test_account1)
        # First listing does not throw
        self.score.list_token(1, 100000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.score.list_token(1, 100000000000000000)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is already listed")

    def test_delists_token(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)

        self.score.delist_token(1)

        self.assertEqual(self.score.total_listed_token_count(), 0)
        self.assertEqual(self.score.get_token_listing(1), {})

    def test_listing_again_after_delisting(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.delist_token(1)
        self.score.list_token(1, 100000000000000000)

        expected = {
            "token_id": 1,
            "base_price": 100000000000000000
        }

        self.assertEqual(self.score.total_listed_token_count(), 1)
        self.assertEqual(self.score.get_token_listing(1), expected)

    def test_whitelisting_token(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)

        record = {
            "token_id": 1,
            "base_price": 100000000000000000,
            "modified_price": 80000000000000000,
            "valid": True,
            "whitelist_expiration_time": self.score.now() + 60 * 60 * 100 * 100,
            "whitelist_time": self.score.now(),
        }

        record = self.score.get_whitelist_record(1, self.test_account2)

        self.assertEqual(record['token_id'], 1)
        self.assertEqual(record['base_price'], 100000000000000000)
        self.assertEqual(record['modified_price'], 80000000000000000)
        self.assertEqual(record['valid'], True)

    def test_get_whitelist_record_that_does_not_exist(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)

        self.assertEqual(self.score.get_whitelist_record(1, self.test_account2), {})

    def test_throws_when_adding_whitelist_record_for_unlisted_token(self):
        self.set_msg(self.test_account1)

        with self.assertRaises(IconScoreException) as e:
            self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Token is not listed")

    def test_throws_when_adding_whitelist_record_with_too_low_modified_price(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.score.add_whitelist_record(1, self.test_account2, 30000000000000000)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Modified price is too low")

    def test_claim_token(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)

        self.set_msg(self.test_account2, 80000000000000000)
        self.score.claim_token(1)

        self.assertEqual(self.score.total_listed_token_count(), 0)

    def test_throws_when_claiming_token_for_non_whitelisted_user(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account1, 80000000000000000)
            self.score.claim_token(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "This address is not whitelisted for token_id 1")

    def test_throws_when_claiming_token_with_wrong_amount(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, 90000000000000000)
            self.score.claim_token(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Whitelist record price does not match sent amount")

    def test_throws_when_claiming_token_with_zero_amount(self):
        self.set_msg(self.test_account1)
        self.score.list_token(1, 100000000000000000)
        self.score.add_whitelist_record(1, self.test_account2, 80000000000000000)

        with self.assertRaises(IconScoreException) as e:
            self.set_msg(self.test_account2, 0)
            self.score.claim_token(1)
        self.assertEqual(e.exception.code, 32)
        self.assertEqual(e.exception.message, "Sent ICX amount needs to be greater than 0")

