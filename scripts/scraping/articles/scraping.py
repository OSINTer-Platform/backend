import logging
import os
import random
import time
import re
from typing import Any, cast

from bs4 import BeautifulSoup, element
import feedparser  # type: ignore
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger("osinter")

# Used for simulating an actual browser when scraping for OGTags, stolen from here
browser_headers_list = [
    # Firefox 77 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    },
    # Chrome 83 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    },
    # Chrome 83 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
    },
]


def check_if_valid_url(url: str) -> bool:
    if re.match(r"https?:\/\/.*\..*", url):
        return True
    else:
        return False


# Function for intellegently adding the domain to a relative path on website depending on if the domain is already there
def cat_url(root_url: str, relative_path: str) -> str:
    if check_if_valid_url(relative_path):
        return relative_path
    else:
        return root_url[:-1] + relative_path


# Simple function for scraping static page and converting it to a soup
def scrape_web_soup(url: str) -> BeautifulSoup | None:
    current_headers: dict[str, str] = random.choice(browser_headers_list)
    page_source: requests.models.Response = requests.get(url, headers=current_headers)

    if page_source.status_code != 200:
        logger.error(f"Status code {page_source.status_code}, skipping URL {url}")
        return None

    return BeautifulSoup(page_source.content, "html.parser")


def scrape_article_urls(
    root_url: str,
    front_page_url: str,
    scraping_targets: dict[str, Any],
    profile_name: str,
    max_url_count: int = 10,
    web_soup: BeautifulSoup | None = None,
) -> list[str]:
    if not web_soup:
        web_soup = scrape_web_soup(front_page_url)

    if web_soup is None:
        raise Exception(f"Error when scraping article urls from {profile_name}")

    # Getting a soup for the website
    if scraping_targets["container_list"] != []:
        if (
            outer_container := web_soup.select_one(scraping_targets["container_list"])
        ) is None:
            raise Exception(
                f"Error when scraping the specific container on front-page from {profile_name}"
            )
    else:
        outer_container = web_soup

    inner_containers: list[element.Tag] = outer_container.select(
        scraping_targets["link_containers"]
    )

    link_elements: list[element.Tag] = []

    if not scraping_targets["links"]:
        link_elements = inner_containers
    else:
        for container in inner_containers:
            link_element = container.select_one(scraping_targets["links"])

            if link_element:
                link_elements.append(link_element)

    raw_article_urls: list[str] = [
        url
        for link in link_elements[:max_url_count]
        if isinstance((url := link.get("href")), str)
    ]

    return [cat_url(root_url, url) for url in raw_article_urls]


# Function for scraping a list of recent articles using the url to a RSS feed
def get_article_urls_from_rss(
    rss_url: str,
    max_url_count: int = 10,
) -> list[str]:
    # Parse the whole RSS feed
    rss_feed = feedparser.parse(rss_url)

    return [entry.id for entry in rss_feed.entries[:max_url_count]]


def scrape_page_dynamic(
    page_url: str, scraping_types: list[str], load_time: int = 3, headless: bool = True
) -> str:
    # Setting the options for running the browser driver headlessly so it doesn't pop up when running the script
    driver_options = Options()
    if headless:
        driver_options.add_argument("-headless")  # type: ignore

    # Setup the webdriver with options
    with webdriver.Firefox(
        options=driver_options,
    ) as driver:
        # Actually scraping the page
        driver.get(page_url)

        # Sleeping a pre-specified time to let the driver actually render the page properly
        time.sleep(load_time)

        for scraping_type in scraping_types:
            current_type = scraping_type.split(":")
            if current_type[0] == "JS":
                with open(
                    os.path.normcase(f"./profiles/js_injections/{current_type[1]}.js")
                ) as f:
                    js_script: str = f.read()

                driver.execute_script(js_script)

                while driver.execute_script("return document.osinterReady") == False:
                    time.sleep(1)

        # Getting the source code for the page
        return cast(str, driver.page_source)
