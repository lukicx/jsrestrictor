import json
import time
import pytest
import requests

from config import WEB_CONTROL_URL, WEB_HTTP_PUBLIC_URL
from utils import make_driver

RESULT_TIMEOUT = 15
BLOCK_THRESHOLD_MS = 700

def get_logged_steps(logs):
    return [entry["payload"]["step"] for entry in logs]

def wait_fpd_result(driver, timeout=RESULT_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        text = driver.find_element("id", "result").text.strip()
        if text != "idle":
            return json.loads(text)
        time.sleep(0.2)
    return {"first_blocked_ms": None, "total": 0, "blocked_count": 0}


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
)
def test_fpd(use_fpd_profile, do_fingerprinting, expect_blocked):
    requests.post(f"{WEB_CONTROL_URL}/fpd-reset", timeout=2)

    firefox_profile = "fpd" if use_fpd_profile else None
    driver = make_driver(False, "firefox", firefox_profile=firefox_profile)
    try:
        url = f"{WEB_HTTP_PUBLIC_URL}/fpd"
        if not do_fingerprinting:
            url += "?fingerprint=false"

        driver.get(url)
        result = wait_fpd_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/fpd-logs", timeout=2).json()
    finally:
        driver.quit()
        
    if expect_blocked:
        assert result["first_blocked_ms"] <= BLOCK_THRESHOLD_MS
        assert result["blocked_count"] > 0
    else:
        assert result["blocked_count"] == 0
        assert len(logs) > 0
