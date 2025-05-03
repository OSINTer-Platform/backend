import logging
import os
import time
import re
from typing import Any, cast

from fake_useragent import UserAgent

from bs4 import BeautifulSoup, element
import feedparser  # type: ignore
import requests
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from modules.profiles import Profile

logger = logging.getLogger("osinter")


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
    ua = UserAgent(os="Windows", platforms="desktop", min_version=120.0)
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    }

    page_source: requests.models.Response = requests.get(url, headers=headers)

    if page_source.status_code != 200:
        logger.error(f"Status code {page_source.status_code}, skipping URL {url}")
        return None

    return BeautifulSoup(page_source.content, "html.parser")


def scrape_article_urls(
    profile: Profile,
    max_url_count: int,
    web_soups: list[BeautifulSoup] | None = None,
    news_paths: list[str] | None = None,
) -> list[str]:
    def extract_links(soup: BeautifulSoup) -> list[str]:
        # Getting a soup for the website
        if profile.source.scraping_targets.container_list:
            outer_container = soup.select_one(
                profile.source.scraping_targets.container_list
            )
            if (outer_container) is None:
                raise Exception(
                    f"Error when scraping the specific container on front-page from {profile.source.profile_name}"
                )
        else:
            outer_container = soup

        inner_containers: list[element.Tag] = outer_container.select(
            profile.source.scraping_targets.link_containers
        )

        link_elements: list[element.Tag] = []

        if not profile.source.scraping_targets.links:
            link_elements = inner_containers
        else:
            for container in inner_containers:
                link_element = container.select_one(
                    profile.source.scraping_targets.links
                )

                if link_element:
                    link_elements.append(link_element)

        raw_article_urls: list[str] = [
            url
            for link in link_elements[:max_url_count]
            if isinstance((url := link.get("href")), str)
        ]

        return [cat_url(profile.source.address, url) for url in raw_article_urls]

    if not web_soups:
        news_paths = news_paths if news_paths else profile.source.news_paths
        scraped_soups = [scrape_web_soup(url) for url in news_paths]

        if None in scraped_soups:
            raise Exception(
                f"Error when scraping article urls from {profile.source.profile_name}"
            )

        web_soups = cast(list[BeautifulSoup], scraped_soups)

    links = [extract_links(soup) for soup in web_soups]

    # Flatten and remove duplicates
    return list({item for sublist in links for item in sublist})


# Function for scraping a list of recent articles using the url to a RSS feed
def get_article_urls_from_rss(
    rss_urls: list[str],
    max_url_count: int,
) -> list[str]:
    def parse_feed(url: str) -> list[Any]:
        # Parse the whole RSS feed
        rss_feed = feedparser.parse(url)
        return [entry.id for entry in rss_feed.entries[:max_url_count]]

    links = [parse_feed(url) for url in rss_urls]
    return [item for sublist in links for item in sublist]


def scrape_page_dynamic(
    page_url: str,
    js_injections: list[str] | None,
    load_time: int = 3,
    headless: bool = True,
) -> str:
    # Setting the options for running the browser driver headlessly so it doesn't pop up when running the script
    driver_options = Options()
    if headless:
        driver_options.add_argument("-headless")

    # Setup the webdriver with options
    with webdriver.Firefox(
        options=driver_options,
    ) as driver:
        # Actually scraping the page
        driver.get(page_url)

        # Sleeping a pre-specified time to let the driver actually render the page properly
        time.sleep(load_time)

        if js_injections:
            for injection_name in js_injections:
                with open(
                    os.path.normcase(f"./profiles/js_injections/{injection_name}.js")
                ) as f:
                    js_script: str = f.read()

                driver.execute_script(js_script)

                while driver.execute_script("return document.osinterReady") == False:
                    time.sleep(1)

        # Getting the source code for the page
        return cast(str, driver.page_source)
