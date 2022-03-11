#!/usr/bin/python3

# Used for loading the profile
import json

# Used for reading from file
from pathlib import Path

import os

from bs4 import BeautifulSoup as bs
from markdownify import MarkdownConverter

from OSINTmodules import *

from datetime import datetime, timezone

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.returnArticleDBConn(configOptions)

class customMD(MarkdownConverter):
    def convert_figure(self, el, text, convert_as_inline):
        self.process_tag(el, False, children_only=True)
        return text + "\n\n"

def handleSingleArticle(URL, currentProfile):

    # Scrape the whole article source based on how the profile says
    scrapingTypes = currentProfile['scraping']['type'].split(";")
    configOptions.logger.info(f"Scraping: {URL} using the types {str(scrapingTypes)}")
    articleSource = OSINTscraping.scrapePageDynamic(URL, scrapingTypes)
    articleSoup = bs(articleSource, "html.parser")


    articleMetaInformation = OSINTextract.extractMetaInformation(articleSoup, currentProfile['scraping']['meta'], currentProfile['source']['address'])

    currentArticle = OSINTobjects.Article(url = URL, profile = currentProfile["source"]["profileName"], source = currentProfile["source"]["name"], **articleMetaInformation)

    articleText, articleClearText = OSINTextract.extractArticleContent(currentProfile['scraping']['content'], articleSoup)

    articleClearText = OSINTtext.cleanText(articleClearText)

    currentArticle.content = articleClearText
    currentArticle.formatted_content = customMD(heading_style="closed_atx").convert(articleText)

    # Generate the tags
    currentArticle.tags["automatic"] = OSINTtext.generateTags(OSINTtext.tokenizeText(articleClearText))
    currentArticle.tags["interresting"] = OSINTtext.locateObjectsOfInterrest(articleClearText)
    currentArticle.tags["manual"] = {}

    if os.path.isdir(Path("./tools/keywords/")):
        for file in os.listdir(Path("./tools/keywords/")):
            currentTags = OSINTtext.locateKeywords(OSINTmisc.decodeKeywordsFile(Path(f"./tools/keywords/{file}")), articleClearText)
            if currentTags != []:
                currentArticle.tags["manual"][file]  = currentTags

    currentArticle.inserted_at = datetime.now(timezone.utc)

    return esClient.saveArticle(currentArticle)

def scrapeUsingProfile(articleURLList, profileName):
    if not articleURLList:
        return []

    configOptions.logger.info("Scraping using this profile: " + profileName)

    # Loading the profile for the current website
    currentProfile = OSINTprofiles.getProfiles(profileName)

    articleIDs = []

    for URL in articleURLList:
        articleIDs.append(handleSingleArticle(URL, currentProfile))

    return articleIDs

def main():

    configOptions.logger.info("Scraping articles from frontpages and RSS feeds")
    articleURLCollection = OSINTscraping.gatherArticleURLs(OSINTprofiles.getProfiles())

    configOptions.logger.info("Removing those articles that have already been stored in the database")
    filteredArticleURLCollection = esClient.filterArticleURLList(articleURLCollection)

    numberOfArticleAfterFilter = sum ([ len(filteredArticleURLCollection[profileName]) for profileName in filteredArticleURLCollection ])

    if numberOfArticleAfterFilter == 0:
        configOptions.logger.info("All articles seems to have already been stored, exiting.")
        return
    else:
        configOptions.logger.info("Found {} articles left to scrape, will begin that process now".format(str(numberOfArticleAfterFilter)))

    # Looping through the list of articles from specific news site in the list of all articles from all sites
    for profileName in filteredArticleURLCollection:
        scrapeUsingProfile(filteredArticleURLCollection[profileName], profileName)

if __name__ == "__main__":
    main()
