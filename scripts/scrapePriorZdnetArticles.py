#!/usr/bin/python3

# The profiles mapping the different websites are in json format
import json

import os

debugMessages = True

from OSINTmodules.OSINTprofiles import getProfiles
from OSINTmodules import *

from scripts.scrapeAndStore import scrapeUsingProfile

def main():
    zdnetProfile = json.loads(getProfiles("zdnet"))

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
        articleURLCollection = [ OSINTscraping.scrapeArticleURLs("https://www.zdnet.com/", "https://www.zdnet.com/topic/security/{}/".format(str(i)), zdnetProfile["source"]["scrapingTargets"], "zdnet")]

        OGTagCollection = OSINTtags.collectAllOGTags(articleURLCollection)["zdnet"]

        scrapeUsingProfile(OGTagCollection, "zdnet", articlePath="./ZDNetArticles/")

if __name__ == "__main__":
    main()
