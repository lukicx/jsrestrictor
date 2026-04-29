import sys

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

profile = sys.argv[1]

opts = Options()
opts.set_capability("acceptInsecureCerts", True)
opts.add_argument(f"--user-data-dir=/tmp/chrome-profiles/{profile}")

driver = webdriver.Remote(
    command_executor="http://selenium-chrome:4444/wd/hub",
    options=opts,
)

try:
    driver.get("https://chromewebstore.google.com/detail/jshelter/ammoloihpcbognfddfjcljgembpibcmb")
    print("Open Chrome noVNC at: http://localhost:7901/")
    input("Install JShelter, enable 'Allow User Scripts' in the extension details, then press Enter here to close Chrome..")
finally:
    driver.quit()