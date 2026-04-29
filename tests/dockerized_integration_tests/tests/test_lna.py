import requests
import pytest
from config import WEB_CONTROL_URL, WEB_HTTPS_PUBLIC_URL
from utils import make_driver, wait_result


@pytest.mark.parametrize(
    "request_type,expected_results,access",
    [
        ("fetch", {"local blocked", "local timeout"}, "block"),
        ("script", {"local blocked", "local timeout"}, "block"),
        ("iframe", {"local blocked", "local timeout"}, "block"),
        ("fetch", {"local loaded"}, "allow"),
    ],
)
def test_lna(request_type, expected_results, access):
    requests.post(f"{WEB_CONTROL_URL}/reset", timeout=2)

    driver = make_driver(False, "chrome")
    try:
        if access == "allow":
            driver.execute_cdp_cmd(
                "Browser.setPermission",
                {
                    "permission": {"name": "local-network"},
                    "setting": "granted",
                    "origin": WEB_HTTPS_PUBLIC_URL,
                },
            )
        url_suffix = f"?requestType={request_type}"
        driver.get(WEB_HTTPS_PUBLIC_URL + "/network"+ url_suffix)
        result = wait_result(driver)
        logs = requests.get(f"{WEB_CONTROL_URL}/logs", timeout=2).json()

        print("Access type:", access)
        print("Request type:", request_type)
        print("Expected results:", expected_results)
        print("Result:", result)
        print("Logs:", logs)

        assert result in expected_results

        if access == "block":
            assert len(logs) == 0
        else:
            assert len(logs) >= 1


    finally:
        driver.quit()
