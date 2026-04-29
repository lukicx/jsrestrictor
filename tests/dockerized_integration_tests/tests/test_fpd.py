import json
import time
import pytest
import requests

from config import WEB_CONTROL_URL, WEB_HTTP_PUBLIC_URL
from utils import make_driver

RESULT_TIMEOUT = 10

def get_logged_steps(logs):
    return [entry["payload"]["step"] for entry in logs]

def wait_fpd_result(driver, timeout=RESULT_TIMEOUT):
    end = time.time() + timeout
    while time.time() < end:
        text = driver.find_element("id", "result").text.strip()
        if text != "idle":
            return json.loads(text)
        time.sleep(0.2)
    return {"request": "blocked"}


@pytest.mark.parametrize(
    "use_fpd_profile,do_fingerprinting,expected_request,expect_logs",
    [
        # Baseline, no FPD, no fingerprinting
        (False, True, "loaded", True),
        # FPD + fingerprinting
        (True, True, "blocked", False),
        # FPD + no fingerprinting
        (True, False, "loaded", True),
    ],
)
def test_fpd(use_fpd_profile, do_fingerprinting, expected_request, expect_logs):
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

    print("FPD profile:", use_fpd_profile)
    print("Fingerprinting:", do_fingerprinting)
    print("Result:", result)
    print("Logs:", logs)

    assert result["request"] == expected_request
    if expect_logs:
        assert get_logged_steps(logs) == ["fingerprint-upload"]
    else:
        assert get_logged_steps(logs) == []