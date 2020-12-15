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
        "http://localhost:8000/",               # homepage
        "http://localhost:8000/research",       # landing page
        "http://localhost:8000/about",          # content page
        "http://localhost:8000/people/staff",   # person list page
        "http://localhost:8000/projects",       # project list page
        "http://localhost:8000/events",         # event list page
        "http://localhost:8000/updates",        # blog post index
        # TODO project detail page
        # TODO event detail page
        # TODO profile page
        # TODO blog post
    ]


def run() -> None:
    """Take DOM snapshots of a set of URLs and upload to Percy."""
    browser = setup()

    # visit each URL, wait 10 seconds, then upload to Percy using page's title
    for url in get_urls():
        browser.get(url)
        browser.implicitly_wait(10)
        percySnapshot(browser=browser, name=browser.title)

    # shut down when finished
    browser.quit()


if __name__ == "__main__":
    run()
