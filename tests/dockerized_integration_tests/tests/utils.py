import time
import base64
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import requests

from config import SELENIUM_FIREFOX_URL, JSHELTER_FIREFOX_PATH, SELENIUM_CHROME_URL

JSHELTER__STARTUP_DELAY = 1

def install_firefox_addon(driver, addon_path):
    with open(addon_path, "rb") as file:
        addon_b64 = base64.b64encode(file.read()).decode("ascii")

    response = requests.post(
        f"{SELENIUM_FIREFOX_URL.rstrip('/')}/session/{driver.session_id}/moz/addon/install",
        json={"addon": addon_b64, "temporary": True},
        timeout=30,
    )

    if not response.ok:
        raise RuntimeError(f"Failed to install addon: {response.status_code} {response.text}")


def make_driver(load_jshelter, browser, firefox_profile=None, firefox_lna_allow=False, firefox_lna_block=False):
    if browser == "chrome":
        opts = ChromeOptions()
        opts.page_load_strategy = "eager"
        opts.set_capability("acceptInsecureCerts", True)
        opts.add_argument("--enable-features=PrivateNetworkAccessPermissionPrompt")
        opts.add_argument("--enable-blink-features=PrivateNetworkAccessPermissionPrompt")
        opts.add_argument("--use-angle=swiftshader")
        
        if load_jshelter:
            opts.add_argument(f"--user-data-dir=/tmp/chrome-profiles/jshelter")

        return webdriver.Remote(
            command_executor=SELENIUM_CHROME_URL,
            options=opts,
        )
    opts = FirefoxOptions()
    opts.page_load_strategy = "eager"
    opts.set_preference("xpinstall.signatures.required", False)

    if firefox_lna_allow:
        opts.set_preference("network.lna.enabled", True)
        opts.set_preference("network.lna.blocking", False)
        opts.set_preference("security.mixed_content.block_active_content", False)
        opts.set_preference("security.mixed_content.upgrade_display_content", False)
    elif firefox_lna_block:
        opts.set_preference("network.lna.enabled", True)
        opts.set_preference("network.lna.blocking", True)
        opts.set_preference("security.mixed_content.block_active_content", False)
        opts.set_preference("security.mixed_content.upgrade_display_content", False)

    if firefox_profile:
        opts.add_argument("-profile")
        opts.add_argument(f"/tmp/firefox-profiles/{firefox_profile}")

    driver = webdriver.Remote(
        command_executor=SELENIUM_FIREFOX_URL,
        options=opts,
    )

    if firefox_profile is None and load_jshelter:
        install_firefox_addon(driver, JSHELTER_FIREFOX_PATH)
        time.sleep(JSHELTER__STARTUP_DELAY)
    return driver

def is_result_ready(driver):
    text = driver.find_element(By.ID, "result").text.strip()
    return text != "idle"

def wait_result(driver, timeout=10):
    WebDriverWait(driver, timeout).until(is_result_ready)
    return driver.find_element(By.ID, "result").text.strip()
