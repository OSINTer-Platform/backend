#!/usr/bin/python3

# The profiles mapping the different websites are in json format
import json

debugMessages = True

from OSINTmodules.OSINTprofiles import getProfiles
from OSINTmodules import *

from scripts.scrapeAndStore import scrapeUsingProfile

def main():
    zdnetProfile = json.loads(getProfiles("zdnet"))

    for i in range(0, 3301):
        OSINTmisc.printDebug("Scraping page {}.".format(str(i)))
        articleURLCollection = [ OSINTscraping.scrapeArticleURLs("https://www.zdnet.com/", "https://www.zdnet.com/topic/security/{}/".format(str(i)), zdnetProfile["source"]["scrapingTargets"], "zdnet")]

        OGTagCollection = OSINTtags.collectAllOGTags(articleURLCollection)["zdnet"]

        scrapeUsingProfile(OGTagCollection, "zdnet", articlePath="./ZDNetArticles")

if __name__ == "__main__":
    main()
