import atexit
import shutil
import sys
from pathlib import Path
from typing import Optional

import requests
import typer
from bs4 import BeautifulSoup
from halo import Halo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from invisible_hand.config import app_context
from invisible_hand.ensures import ensure_config_exists
from invisible_hand.errors import ERR_CHROME_DRIVER_NOT_INSTALLED

spinner = Halo(stream=sys.stderr)

# must reside in root folder
# change the extension version for newer versions
EXTENSION_FILE_VERSION = ""
EXTENSION_FILE = "chrome-ghclassroom-waiter{EXTENSION_FILE_VERSION}.crx"


def cache_extension_path() -> Path:
    """ Download and cache chrome extension from github
    """
    extension_path: Path = app_context.config_manager.base_folder / EXTENSION_FILE
    url: str = f"https://github.com/ianre657/invisible-hand/raw/master/{EXTENSION_FILE}"
    if not extension_path.exists():
        response = requests.get(url, allow_redirects=True)
        print(response.json)
        if response.status_code == 200:
            open(extension_path, "wb").write(response.content)
        else:
            raise RuntimeError("Cannot download file from {url}")
    return extension_path


class Condition_logined:
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            # will throw an exception if target not found
            _ = driver.find_element_by_id("login_field")
            # print("I can still see login field")
            return False
        except:
            # print("no more login field found")
            return True


# TODO:
#  - error handling
#     - deadline is not due
#
#  - show progress
#     - how many repos in the page that are not loaded
#  - show progress bar in each page
#
#  - report statistics
#     - how many repos
#     - how many students have submitted their hw
#     - how many students didn't submitted their hw and their info


BaseURL = "https://classroom.github.com"


def crawl_classroom(
    hw_title=typer.Argument(..., help="homework submission to crawl"),
    output: str = typer.Argument(..., help="filename to output your result"),
    classroom_id: Optional[str] = typer.Option(None, show_default=True),
    login: Optional[str] = typer.Option(None),
    passwd: Optional[str] = typer.Option(
        default=None, help="password for your github classroom"
    ),
):
    """Get student's submissions from Github Classroom
    """
    ensure_config_exists()

    def fallback(val, fallback_value):
        return val if val else fallback_value

    # Handle default value manually because we'll change our config after app starts up
    classroom_id: str = fallback(
        classroom_id, app_context.config.crawl_classroom.classroom_id
    )
    login: str = fallback(login, app_context.config.crawl_classroom.login)

    spinner.start()
    if output is not None:
        if Path(output).exists():
            spinner.info(f"Overwrite existing file: {output}")

    spinner.text = "Initializing Chrome driver"
    # We can only use headless=False
    # Because I use my chrome extension helping my web crawling
    # but Google doesn't want to support Chrome extensions in headless mode
    # See https://bugs.chromium.org/p/chromium/issues/detail?id=706008#c5 for more information
    driver = createDriver(headless=False)
    atexit.register(lambda: driver.quit)

    # gh classroom assigment page
    spinner.text = "Opening GitHub Classroom"
    driver.get(BaseURL + "/classrooms/{}/assignments/{}".format(classroom_id, hw_title))

    # user id
    input_id = driver.find_element_by_id("login_field")
    input_id.send_keys(login)

    # user password
    input_passwd = driver.find_element_by_id("password")
    spinner.text = "Login..."

    if passwd is not None:
        input_passwd.send_keys(passwd)
        driver.find_element_by_name("commit").click()
        try:
            _ = WebDriverWait(driver, 0).until(Condition_logined())
            spinner.text = "Login to GitHub Classroom"
            spinner.succeed()
        except:
            spinner.fail("Invalid password")
            sys.exit(1)

    try:
        logined = Condition_logined()
        _ = WebDriverWait(driver, 20).until(logined)
    except:
        spinner.fail("Browser timed out")
        sys.exit(1)

    # check if error
    submitted_infos = []
    not_submitted_list = []
    page_loaded = 0
    while True:
        spinner.text = "Loading page {}".format(page_loaded + 1)
        spinner.start()
        wait_for_page_load(driver)
        page_loaded += 1
        spinner.succeed("Page {} loaded".format(page_loaded))
        soup = BeautifulSoup(driver.page_source, "lxml")
        next_btn = soup.find("a", "next")

        li = soup.find_all("div", "assignment-repo-list-item")
        for i in li:
            user_id = i.find("a", "assignment-repo-github-url").find("h3").contents[0]
            links_to_commit = i.find("a", attrs={"aria-label": "View Submission"})

            if links_to_commit is not None:
                commit_url = links_to_commit["href"]
                commit_hash = commit_url.rsplit("/", 1)[-1]
                submitted_str = "{}-{}:{}".format(hw_title, user_id, commit_hash[0:7])
                submitted_infos.append(submitted_str)
                # print(submitted_str)
            else:
                not_submitted_list.append(f"{hw_title}-{user_id}")

        if next_btn == None:
            break
        driver.get(BaseURL + next_btn["href"])
    spinner.succeed("Success")

    ostream = sys.stdout
    if output is not None:
        ostream = open(output, "w")
        atexit.register(lambda: ostream.close)

    for i in submitted_infos:
        print(i, end=" ", file=ostream)
    print("", file=ostream)

    if len(not_submitted_list) != 0:
        print("Students not submitted:", file=sys.stderr)
        print(not_submitted_list, file=sys.stderr)


def createDriver(headless=True) -> webdriver:

    options = Options()
    options.headless = headless
    options.add_argument("--window-size=1920,1200")

    options.add_extension(cache_extension_path())

    cdriver_path = shutil.which("chromedriver")
    if cdriver_path is None:
        raise ERR_CHROME_DRIVER_NOT_INSTALLED
    driver = webdriver.Chrome(options=options, executable_path=cdriver_path)
    return driver


def wait_for_page_load(driver):
    try:
        _ = WebDriverWait(driver, 30).until(
            # This id is generated by my chrome extension
            EC.presence_of_element_located(
                (By.ID, "chrome-extension-classroom-waiter-loaded")
            )
        )
    except:
        driver.close()
        raise ("Timeout: cannot load assignment page")


if __name__ == "__main__":
    crawl_classroom()
