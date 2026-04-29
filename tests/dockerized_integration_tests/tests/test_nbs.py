import requests
import pytest
from config import WEB_HTTP_PUBLIC_URL, WEB_HTTP_LOCAL_URL, WEB_CONTROL_URL
from utils import make_driver, wait_result


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
        (False, WEB_HTTP_PUBLIC_URL + "/network", "?targetNetwork=public", "local loaded", True),

        #local -> local
        (False, WEB_HTTP_LOCAL_URL + "/network", "?targetNetwork=local", "local loaded", True),
    ],
)
def test_nbs(load_jshelter, page_url, url_suffix, expected_result, expect_logs):
    requests.post(f"{WEB_CONTROL_URL}/reset", timeout=2)

    driver = make_driver(load_jshelter, "firefox")
    try:
        driver.get(page_url + url_suffix)
        result = None
        result = wait_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/logs", timeout=2).json()

        print("Result:", result)
        print("Logs:", logs)

        assert result == expected_result, f"Expected {expected_result}, got {result}"
        if expect_logs:
            assert len(logs) >= 1
        else:
            assert len(logs) == 0
    finally:
        driver.quit()