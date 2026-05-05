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

XYZ_READINGS = {
    "accelerometer": {"x": 18.7, "y": -22.4, "z": 15.8},
    "gyroscope": {"x": 8.5, "y": -7.7, "z": 9.8},
    "gravity": {"x": 5.7,  "y": -6.3,  "z": 4.5},
    "linearAcceleration": {"x": 12.3, "y": -9.8, "z": 14.5},
}

ORIENTATION_READINGS = {
    "absoluteOrientation": {
        "x": 0.2,
        "y": 0.4,
        "z": 0.4,
        "w": 0.8,
    },
    "relativeOrientation": {
        "x": 0.6,
        "y": 0.0,
        "z": 0.0,
        "w": 0.8,
    },
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
                        "x": ORIENTATION_READINGS[sensor_type]["x"],
                        "y": ORIENTATION_READINGS[sensor_type]["y"],
                        "z": ORIENTATION_READINGS[sensor_type]["z"],
                        "w": ORIENTATION_READINGS[sensor_type]["w"],
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
                        "x": XYZ_READINGS[sensor_type]["x"],
                        "y": XYZ_READINGS[sensor_type]["y"],
                        "z": XYZ_READINGS[sensor_type]["z"],
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

    print("Unchanged:", unchanged_result)
    print("JSS:", jss_result)

    assert not unchanged_result.startswith("Error:")
    assert unchanged_result not in ("Timeout", "Unsupported API")

    assert not jss_result.startswith("Error:")
    assert jss_result not in ("Timeout", "Unsupported API")

    unchanged_data = json.loads(unchanged_result)
    jss_data = json.loads(jss_result)

    assert unchanged_data != jss_data

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