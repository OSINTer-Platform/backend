#!/usr/bin/python3

import os
from pathlib import Path
import requests
import json

# For decompressing the geckodriver that comes compressed in the .tar.gz format when downloading it
import tarfile

import sqlite3

from modules import elastic
from scripts import config_options

import logging

logger = logging.getLogger("osinter")

# Mozilla will have an api endpoint giving a lot of information about the latest releases for the geckodriver, from which the url for the linux 64 bit has to be extracted
def extract_driver_url():
    driver_details = json.loads(
        requests.get(
            "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
        ).text
    )

    for platform_release in driver_details["assets"]:
        if platform_release["name"].endswith("linux64.tar.gz"):
            return platform_release["browser_download_url"]


# Downloading and extracting the .tar.gz file the geckodriver is stored in into the tools directory
def download_driver(driver_url):
    driver_contents = requests.get(driver_url, stream=True)
    with tarfile.open(fileobj=driver_contents.raw, mode="r|gz") as driver_file:
        driver_file.extractall(path=Path("./tools/"))


def main():

    logger.info("Downloading and extracting the geckodriver...")

    download_driver(extract_driver_url())

    logger.info("Configuring elasticsearch")
    elastic.configure_elasticsearch(config_options)


if __name__ == "__main__":
    main()
