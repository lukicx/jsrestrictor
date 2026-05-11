import json
import time
import pytest
import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import WEB_CONTROL_URL, WEB_HTTP_PUBLIC_URL
from utils import make_driver

RESULT_TIMEOUT = 15
FRAME_TIMEOUT = 10
BLOCK_THRESHOLD_MS = 1000

def wait_fpd_result(driver):
    end = time.time() + RESULT_TIMEOUT
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

def assert_fpd_result(result, logs, expect_blocked):
    if expect_blocked:
        assert result["blocked_count"] > 0, (
            f"Expected at least one blocked request."
            f"result={result}, logs={logs}"
        )

        assert (
            result["first_blocked_ms"] is not None
            and result["first_blocked_ms"] <= BLOCK_THRESHOLD_MS
        ), (
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
            f"Expected no blocked requests."
            f"result={result}, logs={logs}"
        )

        assert len(logs) > 0, (
            f"Expected uploads to reach the server, but logs were empty."
            f"result={result}, logs={logs}"
        )


@pytest.mark.parametrize(
    "use_fpd_profile,do_fingerprinting,expect_blocked",
    [
        (False, True, False),
        (True, True, True),
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

        assert_fpd_result(result, logs, expect_blocked)
    finally:
        driver.quit()


def run_fpd_frame_test(path, depth, do_fingerprinting, expect_blocked):
    requests.post(f"{WEB_CONTROL_URL}/fpd-reset", timeout=2)

    driver = make_driver(False, "firefox", firefox_profile="fpd")
    try:
        clear_state(driver)

        url = f"{WEB_HTTP_PUBLIC_URL}{path}?depth={depth}"
        if not do_fingerprinting:
            url += "&fingerprint=false"

        driver.get(url)

        for _ in range(depth):
            WebDriverWait(driver, FRAME_TIMEOUT).until(
                EC.frame_to_be_available_and_switch_to_it((By.ID, "fpd-frame"))
        )
        WebDriverWait(driver, FRAME_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, "result"))
        )


        result = wait_fpd_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/fpd-logs", timeout=2).json()

        assert_fpd_result(result, logs, expect_blocked)
    finally:
        driver.quit()

@pytest.mark.parametrize("depth", [1, 9], ids=["depth_1", "depth_9"])
@pytest.mark.parametrize(
    "do_fingerprinting,expect_blocked",
    [
        (True, True),
        (False, False),
    ],
    ids=[
        "with_fingerprinting",
        "without_fingerprinting",
    ],
)
def test_fpd_nested_iframes(depth, do_fingerprinting, expect_blocked):
    run_fpd_frame_test(
        "/fpd-iframe",
        depth,
        do_fingerprinting,
        expect_blocked,
    )


@pytest.mark.parametrize("depth", [1, 9], ids=["depth_1", "depth_9"])
@pytest.mark.parametrize(
    "do_fingerprinting,expect_blocked",
    [
        (True, True),
        (False, False),
    ],
    ids=[
        "with_fingerprinting",
        "without_fingerprinting",
    ],
)
def test_fpd_nested_iframes_docwrite(depth, do_fingerprinting, expect_blocked):
    run_fpd_frame_test(
        "/fpd-iframe-docwrite",
        depth,
        do_fingerprinting,
        expect_blocked,
    )