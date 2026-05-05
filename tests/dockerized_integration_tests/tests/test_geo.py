import json

import pytest
from config import WEB_HTTPS_PUBLIC_URL
from utils import make_driver, wait_result


GEO_CASES = [
    {"latitude": 49.1947382, "longitude": 16.6068291, "accuracy": 5},
    {"latitude": -33.8567844, "longitude": 151.2152967, "accuracy": 50},
    {"latitude": 64.1466014, "longitude": -21.9426354, "accuracy": 100},
]


def run_geo_case(load_jshelter, case):
    driver = make_driver(load_jshelter, "chrome")
    
    try:
        driver.execute_cdp_cmd(
            "Browser.setPermission",
            {
                "permission": {"name": "geolocation"},
                "setting": "granted",
                "origin": WEB_HTTPS_PUBLIC_URL,
            },
        )
        driver.execute_cdp_cmd("Emulation.setGeolocationOverride", case)
        driver.get(WEB_HTTPS_PUBLIC_URL + "/geo")
        return wait_result(driver)
    finally:
        driver.quit()

@pytest.mark.parametrize("case", GEO_CASES)
def test_geo(case):
    unchanged_result = run_geo_case(False, case)
    jss_result = run_geo_case(True, case)

    assert not unchanged_result.startswith("Error:")
    assert unchanged_result not in ("Timeout", "Unsupported API")

    assert not jss_result.startswith("Error:")
    assert jss_result not in ("Timeout", "Unsupported API")

    unchanged_data = json.loads(unchanged_result)
    jss_data = json.loads(jss_result)

    assert unchanged_data["latitude"] != jss_data["latitude"]
    assert unchanged_data["longitude"] != jss_data["longitude"]
    assert unchanged_data["accuracy"] != jss_data["accuracy"]

