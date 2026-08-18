import threading
import time

import requests


URL = "http://127.0.0.1:8000/api/v1/screener/?min_roe=15"


def run_request(results, index, lock):
    start = time.perf_counter()

    try:
        response = requests.get(URL, timeout=10)
        elapsed = time.perf_counter() - start

        result = {
            "request": index,
            "status": response.status_code,
            "elapsed": elapsed,
            "success": response.ok,
            "count": response.json().get("count"),
            "error": None,
        }

    except Exception as exc:
        elapsed = time.perf_counter() - start

        result = {
            "request": index,
            "status": None,
            "elapsed": elapsed,
            "success": False,
            "count": None,
            "error": str(exc),
        }

    with lock:
        results.append(result)


def test_screener_10_concurrent_requests():
    results = []
    lock = threading.Lock()
    threads = []

    start = time.perf_counter()

    for index in range(1, 11):
        thread = threading.Thread(
            target=run_request,
            args=(results, index, lock),
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_elapsed = time.perf_counter() - start

    results.sort(key=lambda item: item["request"])

    print("\n=== Screener Load Test ===")

    for result in results:
        print(
            f"Request {result['request']}: "
            f"status={result['status']}, "
            f"time={result['elapsed']:.3f}s, "
            f"count={result['count']}, "
            f"success={result['success']}"
        )

    print(f"Total wall-clock time: {total_elapsed:.3f}s")

    assert len(results) == 10
    assert all(result["success"] for result in results)
    assert all(result["status"] == 200 for result in results)
    assert total_elapsed < 10