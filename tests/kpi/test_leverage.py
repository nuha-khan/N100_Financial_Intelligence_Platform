import unittest

from src.analytics.ratios import (
    debt_to_equity,
    high_leverage_flag,
    interest_coverage_ratio,
    icr_label,
    icr_warning_flag,
    net_debt,
    asset_turnover,
)


class TestLeverageRatios(unittest.TestCase):

    def test_debt_to_equity(self):
        self.assertEqual(
            debt_to_equity(
                100,
                200,
                300,
            ),
            0.2,
        )

    def test_debt_free(self):
        self.assertEqual(
            debt_to_equity(
                0,
                200,
                300,
            ),
            0,
        )

    def test_negative_equity(self):
        self.assertIsNone(
            debt_to_equity(
                100,
                -200,
                100,
            )
        )

    def test_high_leverage_flag(self):
        self.assertTrue(
            high_leverage_flag(
                6,
                "Industrials",
            )
        )

    def test_interest_coverage(self):
        self.assertEqual(
            interest_coverage_ratio(
                100,
                20,
                10,
            ),
            12.0,
        )

    def test_interest_zero(self):
        self.assertIsNone(
            interest_coverage_ratio(
                100,
                20,
                0,
            )
        )

    def test_icr_label(self):
        self.assertEqual(
            icr_label(None),
            "Debt Free",
        )

    def test_icr_warning(self):
        self.assertTrue(
            icr_warning_flag(1.2)
        )

    def test_net_debt(self):
        self.assertEqual(
            net_debt(
                500,
                100,
            ),
            400,
        )

    def test_asset_turnover(self):
        self.assertEqual(
            asset_turnover(
                1000,
                500,
            ),
            2.0,
        )


if __name__ == "__main__":
    unittest.main()