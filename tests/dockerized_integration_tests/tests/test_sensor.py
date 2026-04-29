import pytest
from config import WEB_HTTPS_PUBLIC_URL
from utils import make_driver, wait_result
import json

CDP_PERMISSIONS = {
    "accelerometer": ["accelerometer"],
    "gyroscope": ["gyroscope"],
    "gravity": ["accelerometer"],
    "linearAcceleration": ["accelerometer"],
    "relativeOrientation": ["accelerometer", "gyroscope"],
    "absoluteOrientation": ["accelerometer", "gyroscope", "magnetometer"],
}

CDP_TYPE = {
    "accelerometer": "accelerometer",
    "gyroscope": "gyroscope",
    "gravity": "gravity",
    "linearAcceleration": "linear-acceleration",
    "absoluteOrientation": "absolute-orientation",
    "relativeOrientation": "relative-orientation",
}

def setup_driver(driver, sensor_type):
    for permission in CDP_PERMISSIONS[sensor_type]:
        driver.execute_cdp_cmd(
                "Browser.setPermission",
                {
                    "permission": {"name": permission},
                    "setting": "granted",
                    "origin": WEB_HTTPS_PUBLIC_URL,
                },
            )

    driver.execute_cdp_cmd(
        "Emulation.setFocusEmulationEnabled",
        {
            "enabled": True
        },
    )
    driver.execute_cdp_cmd(
        "Emulation.setSensorOverrideEnabled",
        {
            "enabled": True,
            "type": CDP_TYPE[sensor_type],
        },
    )
    if sensor_type in ["absoluteOrientation", "relativeOrientation"]:
        driver.execute_cdp_cmd(
            "Emulation.setSensorOverrideReadings",
            {
                "type": CDP_TYPE[sensor_type],
                "reading": {
                    "quaternion": {
                        "x": 0,
                        "y": 0,
                        "z": 0,
                        "w": 1,
                    }
                },
            },
        )
    else:
        driver.execute_cdp_cmd(
            "Emulation.setSensorOverrideReadings",
            {
                "type": CDP_TYPE[sensor_type],
                "reading": {
                    "xyz": {
                        "x": 1.23,
                        "y": 4.56,
                        "z": 7.89,
                    }
                },
            },
        )

def run_sensor_case(load_jshelter, sensor_type):
    driver = make_driver(load_jshelter, "chrome")
    try:
        setup_driver(driver, sensor_type)
        driver.get(WEB_HTTPS_PUBLIC_URL + f"/sensor?sensorType={sensor_type}")
        return wait_result(driver)
    finally:
        driver.quit()

@pytest.mark.parametrize("sensor_type", [
    "accelerometer", "gyroscope", "gravity", "linearAcceleration", 
    "absoluteOrientation", "relativeOrientation"
    ])
def test_sensor(sensor_type):
    unchanged_result = run_sensor_case(False, sensor_type)
    jss_result = run_sensor_case(True, sensor_type)

    print("Sensor:", sensor_type)
    print("Unchanged:", unchanged_result)
    print("JSS:", jss_result)

    assert not unchanged_result.startswith("Error:")
    assert unchanged_result not in ("Timeout", "Unsupported API")

    assert not jss_result.startswith("Error:")
    assert jss_result not in ("Timeout", "Unsupported API")

    unchanged_data = json.loads(unchanged_result)
    jss_data = json.loads(jss_result)

    if sensor_type in ["absoluteOrientation", "relativeOrientation"]:
        assert unchanged_data["x"] != jss_data["x"]
        assert unchanged_data["y"] != jss_data["y"]
        assert unchanged_data["z"] != jss_data["z"]
        assert unchanged_data["w"] != jss_data["w"]
    else:
        assert unchanged_data["x"] != jss_data["x"]
        assert unchanged_data["y"] != jss_data["y"]
        assert unchanged_data["z"] != jss_data["z"]

@pytest.mark.parametrize("sensor_type", ["absoluteOrientation", "relativeOrientation", "accelerometer", "gravity", "linearAcceleration", "gyroscope"])
def test_sensor_refresh_same_result(sensor_type):
    driver = make_driver(True, "chrome")
    try:
        setup_driver(driver, sensor_type)
        driver.get(WEB_HTTPS_PUBLIC_URL + f"/sensor?sensorType={sensor_type}")
        first_result = wait_result(driver)

        assert first_result not in ("Timeout", "Unsupported API")
        assert not first_result.startswith("Error:")

        driver.refresh()
        second_result = wait_result(driver)

        assert second_result not in ("Timeout", "Unsupported API")
        assert not second_result.startswith("Error:")


        assert first_result == second_result
    finally:
        driver.quit()