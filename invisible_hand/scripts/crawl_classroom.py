import sys
import errno
import os
import shutil
import atexit
from pathlib import Path

import click
from halo import Halo

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from ..config.github import config_crawl_classroom

spinner = Halo(stream=sys.stderr)

class Condition_logined:
    def __init__(self):
        pass

    def __call__(self, driver):
        try:
            # will throw an exception if target not found
            _ = driver.find_element_by_id("login_field")
            #print("I can still see login field")
            return False
        except:
            #print("no more login field found")
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


@click.command()
@click.argument('hw_title')
@click.argument('output')
@click.option('--login', default=config_crawl_classroom['login'], show_default=True)
@click.option('--passwd')
@click.option('--classroom_id', default=config_crawl_classroom['classroom_id'], show_default=True)
def crawl_classroom(hw_title, login, passwd, classroom_id, output):
    '''Get student homework submitted version from github classroom
        @output :filename to output your result
    '''
    spinner.start()
    if output is not None:
        if Path(output).exists():
            spinner.info(f'Overwrite existing file: {output}')

    spinner.text = "Initializing Chrome driver"
    # We can only use headless=False
    # Because I use my chrome extension helping my web crawling
    # but Google doesn't want to support Chrome extensions in headless mode
    # See https://bugs.chromium.org/p/chromium/issues/detail?id=706008#c5 for more information
    driver = createDriver(headless=False)
    atexit.register(lambda: driver.quit)

    # gh classroom assigment page
    spinner.text = "Opening GitHub Classroom"
    driver.get(
        BaseURL+"/classrooms/{}/assignments/{}"
        .format(classroom_id, hw_title)
    )

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
        spinner.text = "Loading page {}".format(page_loaded+1)
        spinner.start()
        wait_for_page_load(driver)
        page_loaded += 1
        spinner.succeed("Page {} loaded".format(page_loaded))
        soup = BeautifulSoup(driver.page_source, 'lxml')
        next_btn = soup.find("a", "next")

        li = soup.find_all("div", "assignment-repo-list-item")
        for i in li:
            user_id = i.find(
                "a", "assignment-repo-github-url").find("h3").contents[0]
            links_to_commit = i.find(
                "a", attrs={"aria-label": "View Submission"})

            if links_to_commit is not None:
                commit_url = links_to_commit['href']
                commit_hash = commit_url.rsplit('/', 1)[-1]
                submitted_str = "{}-{}:{}".format(
                    hw_title, user_id, commit_hash[0:7])
                submitted_infos.append(submitted_str)
                # print(submitted_str)
            else:
                not_submitted_list.append(f"{hw_title}-{user_id}")

        if next_btn == None:
            break
        driver.get(BaseURL + next_btn['href'])
    spinner.succeed("Success")

    ostream = sys.stdout
    if output is not None:
        ostream = open(output, 'w')
        atexit.register(lambda: ostream.close)

    for i in submitted_infos:
        print(i, end=' ', file=ostream)
    print('', file=ostream)

    if len(not_submitted_list) != 0:
        print("Students not submitted:", file=sys.stderr)
        print(not_submitted_list, file=sys.stderr)


def createDriver(headless=True) -> webdriver:

    options = Options()
    options.headless = headless
    options.add_argument("--window-size=1920,1200")
    options.add_extension("./chrome-ghclassroom-waiter.crx")

    cdriver_path = shutil.which("chromedriver")
    if cdriver_path is None:
        raise FileNotFoundError(
            errno.ENOENT, os.strerror(errno.ENOENT), "chromedriver")
    driver = webdriver.Chrome(options=options, executable_path=cdriver_path)
    return driver


def wait_for_page_load(driver):
    try:
        _ = WebDriverWait(driver, 30).until(
            # This id is generated by my chrome extension
            EC.presence_of_element_located(
                (By.ID, "chrome-extension-classroom-waiter-loaded"))
        )
    except:
        driver.close()
        raise("Timeout: cannot load assignment page")


if __name__ == "__main__":
    crawl_classroom()
