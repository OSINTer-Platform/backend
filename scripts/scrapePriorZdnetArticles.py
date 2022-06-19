#!/usr/bin/python3

# The profiles mapping the different websites are in json format
import json

import os

from modules.profiles import getProfiles
from modules import *

from scripts.scrapeAndStore import scrapeUsingProfile
from scripts import configOptions


def main():
    elastic.configureElasticsearch(
        configOptions.ELASTICSEARCH_URL,
        configOptions.ELASTICSEARCH_CERT_PATH,
        "osinter_zdnet",
    )

    zdnetProfile = getProfiles("zdnet")

    if os.path.isfile("./progress.txt"):
        with open("./progress.txt", "r") as file:
            progressCounter = int(file.read())
    else:
        progressCounter = 0

    for i in range(progressCounter, 3301):
        print(i)
        with open("./progress.txt", "w") as file:
            file.write(str(i))
        configOptions.logger.info("Scraping page {}.".format(str(i)))
        articleURLList = scraping.scrapeArticleURLs(
            "https://www.zdnet.com/",
            "https://www.zdnet.com/topic/security/{}/".format(str(i)),
            zdnetProfile["source"]["scrapingTargets"],
            "zdnet",
        )

        scrapeUsingProfile(articleURLList, "zdnet")


if __name__ == "__main__":
    main()
