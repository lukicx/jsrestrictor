import time
import base64
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import requests

from config import SELENIUM_FIREFOX_URL, JSHELTER_FIREFOX_PATH, SELENIUM_CHROME_URL

def install_firefox_addon(driver, addon_path):
    with open(addon_path, "rb") as f:
        addon_b64 = base64.b64encode(f.read()).decode("ascii")

    response = requests.post(
        f"{SELENIUM_FIREFOX_URL.rstrip('/')}/session/{driver.session_id}/moz/addon/install",
        json={"addon": addon_b64, "temporary": True},
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(f"Failed to install addon: {response.status_code} {response.text}")


def make_driver(load_jshelter, browser, firefox_profile=None):
    if browser == "chrome":
        opts = ChromeOptions()
        opts.page_load_strategy = "eager"
        opts.set_capability("acceptInsecureCerts", True)
        opts.add_argument("--enable-features=PrivateNetworkAccessPermissionPrompt")
        opts.add_argument("--enable-blink-features=PrivateNetworkAccessPermissionPrompt")
        opts.add_argument("--use-angle=swiftshader")
        

        if load_jshelter:
            profile = "jshelter"
        else:
            profile = "clean"
        opts.add_argument(f"--user-data-dir=/tmp/chrome-profiles/{profile}")


        return webdriver.Remote(
            command_executor=SELENIUM_CHROME_URL,
            options=opts,
        )
    print("Firefox profile:", firefox_profile)
    opts = FirefoxOptions()
    opts.page_load_strategy = "eager"
    opts.set_preference("xpinstall.signatures.required", False)

    if firefox_profile:
        opts.add_argument("-profile")
        opts.add_argument(f"/tmp/firefox-profiles/{firefox_profile}")

    driver = webdriver.Remote(
        command_executor=SELENIUM_FIREFOX_URL,
        options=opts,
    )

    if firefox_profile is None and load_jshelter:
        install_firefox_addon(driver, JSHELTER_FIREFOX_PATH)
        time.sleep(1)
    return driver

def is_result_ready(driver):
    text = driver.find_element(By.ID, "result").text.strip()
    return text != "idle"

def wait_result(driver, timeout=10):
    WebDriverWait(driver, timeout).until(is_result_ready)
    return driver.find_element(By.ID, "result").text.strip()
