import sys

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

profile = sys.argv[1]

opts = Options()
opts.set_capability("acceptInsecureCerts", True)
opts.add_argument("-profile")
opts.add_argument(f"/tmp/firefox-profiles/{profile}")

driver = webdriver.Remote(
    command_executor="http://selenium-firefox:4444/wd/hub",
    options=opts,
)

try:
    driver.get("https://addons.mozilla.org/en-US/firefox/addon/javascript-restrictor/?utm_source=addons.mozilla.org&utm_medium=referral&utm_content=search")
    print("Open Firefox noVNC at: http://localhost:7900/")
    input("Install JShelter, set Fingerprint Detector behavior to 'Limited Blocking', then press Enter here to close Firefox..")
finally:
    driver.quit()