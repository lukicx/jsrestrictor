import json
from config import WEB_HTTPS_PUBLIC_URL
from utils import make_driver, wait_result

def run_geo_case(load_jshelter):
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
        driver.execute_cdp_cmd(
            "Emulation.setGeolocationOverride",
            {
                "latitude": 50.1234,
                "longitude": 20.5678,
                "accuracy": 10,
            },
        )

        driver.get(WEB_HTTPS_PUBLIC_URL + "/geo")
        return wait_result(driver)
    finally:
        driver.quit()

def test_geo():
    unchanged_result = run_geo_case(False)
    jss_result = run_geo_case(True)

    print("Unchanged geolocation:", unchanged_result)
    print("JSS geolocation:", jss_result)

    assert not unchanged_result.startswith("Error:")
    assert unchanged_result not in ("Timeout", "Unsupported API")

    assert not jss_result.startswith("Error:")
    assert jss_result not in ("Timeout", "Unsupported API")

    unchanged_data = json.loads(unchanged_result)
    jss_data = json.loads(jss_result)

    assert unchanged_data["latitude"] != jss_data["latitude"]
    assert unchanged_data["longitude"] != jss_data["longitude"]
    assert unchanged_data["accuracy"] != jss_data["accuracy"]
    assert unchanged_data["timestamp"] != jss_data["timestamp"]

