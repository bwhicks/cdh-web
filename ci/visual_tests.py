#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Execute visual regression tests against a running django server."""

# much of this code was adapted from the following example:
# https://github.com/percy/example-percy-python-selenium/blob/master/tests/todo.py

from typing import Iterable

from percy import percySnapshot
from selenium import webdriver

__author__ = "CDH @ Princeton"
__email__ = "cdh-info@princeton.edu"

# viewport widths at which to take a snapshot of a page
DEVICE_WIDTHS = [375, 768, 1280]


def setup() -> webdriver.Chrome:
    """Initialize and return a browser driver to use for taking snapshots."""
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def get_urls() -> Iterable[str]:
    """Get the set of URLs to execute visual regression testing against."""
    # TODO make this smarter; maybe crawl the top-level sitemap?
    return [
        "http://localhost:8000/",
        "http://localhost:8000/about",
        "http://localhost:8000/grants",
        "http://localhost:8000/people/staff",
        "http://localhost:8000/people/meredith-martin/"
        "http://localhost:8000/projects",
        "http://localhost:8000/projects/princeton-prosody-archive/"
        "http://localhost:8000/events",
        "http://localhost:8000/events/2018/03/dataviz-2/"
        "http://localhost:8000/updates",
        "http://localhost:8000/updates/2018/08/28/bridging-dh-oss/"
    ]


def run() -> None:
    """Take DOM snapshots of a set of URLs and upload to Percy."""
    browser = setup()

    # visit each URL, wait 10 seconds, then upload to Percy
    for url in get_urls():
        browser.get(url)
        browser.implicitly_wait(10)
        percySnapshot(browser=browser, name=browser.title,
                      widths=DEVICE_WIDTHS)

    # shut down when finished
    browser.quit()


if __name__ == "__main__":
    run()
