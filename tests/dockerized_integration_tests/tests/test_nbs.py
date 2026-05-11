import time
import requests
import pytest
from config import WEB_HTTP_PUBLIC_URL, WEB_HTTP_LOCAL_URL, WEB_CONTROL_URL
from utils import make_driver, wait_result

NBS_ACTIVATION_TIMEOUT_MS = 5000
NBS_PROBE_INTERVAL = 0.1

def wait_for_nbs(driver):
    driver.get(WEB_HTTP_PUBLIC_URL + "/")

    start = time.time()
    end = start + (NBS_ACTIVATION_TIMEOUT_MS / 1000)

    while time.time() < end:
        blocked = driver.execute_async_script("""
            const callback = arguments[arguments.length - 1];
            const img = new Image();
            let done = false;

            img.onload = () => {
                if (!done) {
                    done = true;
                    callback(false);
                }
            };
            img.onerror = () => {
                if (!done) {
                    done = true;
                    callback(true);
                }
            };
            setTimeout(() => {
                if (!done) {
                    done = true;
                    callback(true);
                }
            }, 800);
            img.src = "http://10.255.0.10:5000/img?probe=true&ts=" + Date.now();
        """)

        if blocked:
            return int((time.time() - start) * 1000)
        time.sleep(NBS_PROBE_INTERVAL)
    return None

@pytest.mark.parametrize(
    "load_jshelter,page_url,url_suffix,expected_result,expect_logs",
    [
        (False, WEB_HTTP_PUBLIC_URL + "/network", "", "local loaded", True),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "", "local blocked", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=fetch", "local loaded", True),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=fetch", "local blocked", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=script", "local loaded", True),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=script", "local blocked", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=iframe", "local loaded", True),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=iframe", "local timeout", False),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?targetNetwork=public", "local loaded", True),
        (True, WEB_HTTP_LOCAL_URL + "/network", "?targetNetwork=local", "local loaded", True),
    ],
    ids=[
        "no-jshelter-img-public-to-local",
        "jshelter-img-public-to-local",
        "no-jshelter-fetch-public-to-local",
        "jshelter-fetch-public-to-local",
        "no-jshelter-script-public-to-local",
        "jshelter-script-public-to-local",
        "no-jshelter-iframe-public-to-local",
        "jshelter-iframe-public-to-local",
        "jshelter-img-public-to-public",
        "jshelter-img-local-to-local",
    ],
)
def test_nbs(load_jshelter, page_url, url_suffix, expected_result, expect_logs):
    requests.post(f"{WEB_CONTROL_URL}/reset", timeout=2)

    driver = make_driver(load_jshelter, "firefox")
    try:
        if load_jshelter:
            nbs_activation_ms = wait_for_nbs(driver)
            assert nbs_activation_ms is not None, (
                f"NBS did not activate within {NBS_ACTIVATION_TIMEOUT_MS}ms"
            )
            requests.post(f"{WEB_CONTROL_URL}/reset", timeout=2)

        driver.get(page_url + url_suffix)
        result = None
        result = wait_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/logs", timeout=2).json()

        if expect_logs:
            assert logs, f"Expected logs, got none"
        else:
            assert not logs, f"Expected no logs, got {len(logs)}"
        assert result == expected_result, f"Expected {expected_result}, got {result}"
    finally:
        driver.quit()