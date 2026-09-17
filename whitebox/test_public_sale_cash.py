import unittest

from whitebox.versions import v239_public_scenario_c06 as c06


class PublicSaleCashTests(unittest.TestCase):
    def setUp(self):
        self.previous = c06.SALE_CASH_FACTOR
        self.previous_committed = c06.COMMITTED_WORK_SALE_CASH_FACTOR

    def tearDown(self):
        c06.SALE_CASH_FACTOR = self.previous
        c06.COMMITTED_WORK_SALE_CASH_FACTOR = self.previous_committed

    def test_default_preserves_the_existing_candidate(self):
        c06.SALE_CASH_FACTOR = 0.85
        self.assertEqual(c06._sale_cash_credit(1000), 850)

    def test_engine_exact_ledger_credits_the_full_quote(self):
        c06.SALE_CASH_FACTOR = 1.0
        self.assertEqual(c06._sale_cash_credit(1000), 1000)

    def test_negative_projection_never_creates_cash(self):
        c06.SALE_CASH_FACTOR = 1.0
        self.assertEqual(c06._sale_cash_credit(-10), 0)

    def test_committed_ledger_releases_only_the_factor_difference(self):
        c06.SALE_CASH_FACTOR = 0.85
        c06.COMMITTED_WORK_SALE_CASH_FACTOR = 1.0
        self.assertEqual(
            c06._release_committed_sale_cash(850, 1000),
            1000,
        )

    def test_default_committed_ledger_is_action_equivalent(self):
        c06.SALE_CASH_FACTOR = 0.85
        c06.COMMITTED_WORK_SALE_CASH_FACTOR = 0.85
        self.assertEqual(
            c06._release_committed_sale_cash(850, 1000),
            850,
        )


if __name__ == "__main__":
    unittest.main()
