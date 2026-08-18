import time

from streamlit.testing.v1 import AppTest


TICKERS = ["TCS", "RELIANCE", "INFY", "HDFCBANK", "ICICIBANK"]
PROFILE_PAGE = "src/dashboard/pages/02_profile.py"

MAX_LOAD_TIME = 3.0


def test_company_profile_load_time():
    results = []

    for ticker in TICKERS:
        start = time.perf_counter()

        at = AppTest.from_file(PROFILE_PAGE).run()

        assert not at.exception, (
            f"Company Profile failed to load for {ticker}: "
            f"{at.exception}"
        )

        # Locate the company selector and select the requested ticker.
        selectors = at.selectbox

        assert len(selectors) > 0, (
            f"Company selector not found for {ticker}"
        )

        selector = selectors[0]

        options = list(selector.options)

        matching_options = [
            option
            for option in options
            if str(option).upper() == ticker.upper()
            or ticker.upper() in str(option).upper()
        ]

        assert matching_options, (
            f"Ticker {ticker} not found in Company Profile selector"
        )

        selector.select(matching_options[0])
        at.run()

        elapsed = time.perf_counter() - start
        results.append((ticker, elapsed))

        print(
            f"\nCompany Profile - {ticker}: "
            f"{elapsed:.3f}s"
        )

        assert not at.exception, (
            f"Company Profile failed after selecting {ticker}: "
            f"{at.exception}"
        )

        assert elapsed < MAX_LOAD_TIME, (
            f"Company Profile for {ticker} took "
            f"{elapsed:.3f}s (target < {MAX_LOAD_TIME:.1f}s)"
        )

    print("\n=== Company Profile Performance ===")

    for ticker, elapsed in results:
        print(f"{ticker}: {elapsed:.3f}s")

    print(
        f"Maximum load time: "
        f"{max(time_taken for _, time_taken in results):.3f}s"
    )

