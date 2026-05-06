import time
import requests
import pytest
from config import WEB_HTTP_PUBLIC_URL, WEB_HTTP_LOCAL_URL, WEB_CONTROL_URL
from utils import make_driver, wait_result

NBS_ACTIVATION_THRESHOLD_MS = 3000
NBS_ACTIVATION_TIMEOUT_MS = 5000
NBS_PROBE_INTERVAL_SECONDS = 0.1

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
        time.sleep(NBS_PROBE_INTERVAL_SECONDS)
    return None

@pytest.mark.parametrize(
    "load_jshelter,page_url,url_suffix,expected_result,expect_logs",
    [
        # public -> local
        # img
        (False, WEB_HTTP_PUBLIC_URL + "/network", "", "local loaded", True),
        (True, WEB_HTTP_PUBLIC_URL + "/network", "", "local blocked", False),
        # fetch
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=fetch", "local blocked", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=fetch", "local loaded", True),
        #script
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=script", "local blocked", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=script", "local loaded", True),
        #iframe
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=iframe", "local timeout", False),
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?requestType=iframe", "local loaded", True),

        #public -> public
        (True, WEB_HTTP_PUBLIC_URL + "/network", "?targetNetwork=public", "local loaded", True),

        #local -> local
        (True, WEB_HTTP_LOCAL_URL + "/network", "?targetNetwork=local", "local loaded", True),
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
            assert nbs_activation_ms <= NBS_ACTIVATION_THRESHOLD_MS, (
                f"NBS activated too late: {nbs_activation_ms}ms "
                f"(threshold {NBS_ACTIVATION_THRESHOLD_MS}ms)"
            )
            requests.post(f"{WEB_CONTROL_URL}/reset", timeout=2)

        driver.get(page_url + url_suffix)
        result = None
        result = wait_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/logs", timeout=2).json()

        if expect_logs:
            assert len(logs) >= 1
        else:
            assert len(logs) == 0
        assert result == expected_result
    finally:
        driver.quit()