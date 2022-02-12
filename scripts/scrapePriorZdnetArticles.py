#!/usr/bin/python3

# The profiles mapping the different websites are in json format
import json

import os

debugMessages = True

from OSINTmodules.OSINTprofiles import getProfiles
from OSINTmodules import *

from scripts.scrapeAndStore import scrapeUsingProfile

def main():
    OSINTmisc.printDebug("Configuring elasticsearch")
    esAddress = os.environ.get('ELASTICSEARCH_URL') or "http://localhost:9200"
    OSINTelastic.configureElasticsearch(esAddress, "osinter_zdnet")

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
        OSINTmisc.printDebug("Scraping page {}.".format(str(i)))
        articleURLList = OSINTscraping.scrapeArticleURLs("https://www.zdnet.com/", "https://www.zdnet.com/topic/security/{}/".format(str(i)), zdnetProfile["source"]["scrapingTargets"], "zdnet")

        scrapeUsingProfile(articleURLList, "zdnet")

if __name__ == "__main__":
    main()
