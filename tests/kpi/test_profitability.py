import unittest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
)


class TestProfitabilityRatios(unittest.TestCase):

    def test_net_profit_margin(self):
        self.assertEqual(
            net_profit_margin(100, 1000),
            10.0,
        )

    def test_net_profit_margin_zero_sales(self):
        self.assertIsNone(
            net_profit_margin(100, 0)
        )

    def test_operating_profit_margin(self):
        self.assertEqual(
            operating_profit_margin(200, 1000),
            20.0,
        )

    def test_return_on_equity(self):
        self.assertAlmostEqual(
            return_on_equity(
                100,
                200,
                300,
            ),
            20.0,
        )

    def test_negative_equity(self):
        self.assertIsNone(
            return_on_equity(
                100,
                -500,
                100,
            )
        )

    def test_roce(self):
        self.assertAlmostEqual(
            return_on_capital_employed(
                100,
                200,
                300,
                500,
            ),
            10.0,
        )

    def test_roa(self):
        self.assertAlmostEqual(
            return_on_assets(
                100,
                1000,
            ),
            10.0,
        )

    def test_roa_zero_assets(self):
        self.assertIsNone(
            return_on_assets(
                100,
                0,
            )
        )


if __name__ == "__main__":
    unittest.main()