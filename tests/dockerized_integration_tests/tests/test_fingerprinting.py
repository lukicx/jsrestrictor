import pytest
from config import WEB_HTTP_PUBLIC_URL
from utils import make_driver, wait_result

def run_fingerprinting_case(load_jshelter, browser, test_case):
    driver = make_driver(load_jshelter, browser)
    try:
        driver.get(f"{WEB_HTTP_PUBLIC_URL}/fingerprinting?case={test_case}")
        return wait_result(driver)
    finally:
        driver.quit()


@pytest.mark.parametrize("browser", ["firefox", "chrome"])
@pytest.mark.parametrize("test_case", ["timer", "canvas", "webgl", "hardwareConcurrency"])
def test_fingerprinting(test_case, browser):
    unchanged_result = run_fingerprinting_case(False, browser, test_case)
    protected_result = run_fingerprinting_case(True, browser, test_case)

    assert unchanged_result != protected_result