import json
import time
import pytest
import requests

from config import WEB_CONTROL_URL, WEB_HTTP_PUBLIC_URL
from utils import make_driver

RESULT_TIMEOUT = 15
BLOCK_THRESHOLD_MS = 1000

def wait_fpd_result(driver, timeout=RESULT_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        text = driver.find_element("id", "result").text.strip()
        if text != "idle":
            return json.loads(text)
        time.sleep(0.2)
    return {"first_blocked_ms": None, "total": 0, "blocked_count": 0}

def clear_state(driver):
    driver.get(f"{WEB_HTTP_PUBLIC_URL}/empty")
    driver.delete_all_cookies()
    driver.execute_script("""
        try { localStorage.clear(); } catch (e) {}
        try { sessionStorage.clear(); } catch (e) {}
        try {
            document.cookie.split(";").forEach(cookie => {
                const name = cookie.split("=")[0].trim();
                if (name) {
                    document.cookie = name + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
                }
            });
        } catch (e) {}
    """)

@pytest.mark.parametrize(
    "use_fpd_profile,do_fingerprinting,expect_blocked",
    [
        # no FPD, fingerprinting
        (False, True, False),
        # FPD + fingerprinting
        (True, True, True),
        # FPD + no fingerprinting
        (True, False, False),
    ],
    ids=[
        "no_fpd_with_fingerprinting",
        "fpd_with_fingerprinting",
        "fpd_without_fingerprinting",
    ],
)
def test_fpd(use_fpd_profile, do_fingerprinting, expect_blocked):
    requests.post(f"{WEB_CONTROL_URL}/fpd-reset", timeout=2)

    firefox_profile = "fpd" if use_fpd_profile else None
    driver = make_driver(False, "firefox", firefox_profile=firefox_profile)
    try:
        clear_state(driver)
        url = f"{WEB_HTTP_PUBLIC_URL}/fpd"
        if not do_fingerprinting:
            url += "?fingerprint=false"

        driver.get(url)
        result = wait_fpd_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/fpd-logs", timeout=2).json()

        if expect_blocked:
            assert result["blocked_count"] > 0, (
                f"Expected at least one blocked request."
                f"result={result}, logs={logs}"
            )

            assert result["first_blocked_ms"] is not None and result["first_blocked_ms"] <= BLOCK_THRESHOLD_MS, (
                f"Expected FPD to block within {BLOCK_THRESHOLD_MS} ms."
                f"result={result}, logs={logs}"
            )

            assert len(logs) < result["total"], (
                f"Expected not all requests to reach the server after FPD blocking."
                f"result={result}, logs={logs}"
            )
        else:
            assert result["first_blocked_ms"] is None, (
                f"Expected no blocking, but blocking was detected."
                f"result={result}, logs={logs}"
            )
            assert result["blocked_count"] == 0, (
                f"Expected no blocked requests. "
                f"result={result}, logs={logs}"
            )
            assert len(logs) > 0, (
                f"Expected uploads to reach the server, but logs were empty."
                f"result={result}, logs={logs}"
            )
    finally:
            driver.quit()