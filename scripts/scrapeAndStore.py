#!/usr/bin/python3

# Used for loading the profile
import json

# Used for reading from file
from pathlib import Path

import os

from bs4 import BeautifulSoup as bs
from markdownify import markdownify

debugMessages = True

from OSINTmodules.OSINTmisc import printDebug
from OSINTmodules import *

import dateutil.parser as dateParser
from datetime import datetime, timezone

esAddress = os.environ.get('ELASTICSEARCH_URL') or "http://localhost:9200"
esClient = OSINTelastic.elasticDB(esAddress, "osinter_articles")

def handleSingleArticle(URL, currentProfile):

    printDebug("\n", False)

    # Scrape the whole article source based on how the profile says
    scrapingTypes = currentProfile['scraping']['type'].split(";")
    printDebug(f"Scraping: {URL} using the types {str(scrapingTypes)}")
    articleSource = OSINTscraping.scrapePageDynamic(URL, scrapingTypes)
    articleSoup = bs(articleSource, "html.parser")


    printDebug("Extracting the details")
    articleMetaInformation = OSINTextract.extractMetaInformation(articleSoup, currentProfile['scraping']['meta'])

    if articleMetaInformation["publish_date"]:
        tzinfos = {"UTC": 0}
        articleMetaInformation["publish_date"] = dateParser.parse(articleMetaInformation["publish_date"], tzinfos=tzinfos)
    else:
        articleMetaInformation["publish_date"] = datetime.now(timezone.utc).astimezone()


    currentArticle = OSINTobjects.Article(url = URL, profile = currentProfile["source"]["profileName"], source = currentProfile["source"]["name"], **articleMetaInformation)

    printDebug("Extracting the content")
    articleText, articleClearText = OSINTextract.extractArticleContent(currentProfile['scraping']['content'], articleSoup)

    articleClearText = OSINTtext.cleanText(articleClearText)

    currentArticle.content = articleClearText
    currentArticle.formatted_content = markdownify(articleText)

    printDebug("Generating tags and extracting objects of interrest")
    # Generate the tags
    currentArticle.tags["automatic"] = OSINTtext.generateTags(OSINTtext.tokenizeText(articleClearText))
    currentArticle.tags["interresting"] = OSINTtext.locateObjectsOfInterrest(articleClearText)
    currentArticle.tags["manual"] = {}

    if os.path.isdir(Path("./tools/keywords/")):
        for file in os.listdir(Path("./tools/keywords/")):
            currentTags = OSINTtext.locateKeywords(OSINTmisc.decodeKeywordsFile(Path(f"./tools/keywords/{file}")), articleClearText)
            if currentTags != []:
                currentArticle.tags["manual"][file]  = currentTags

    printDebug("Setting the inserted_at date.")
    currentArticle.inserted_at = datetime.now(timezone.utc).astimezone()

    printDebug("Saving the article")
    return esClient.saveArticle(currentArticle)

def scrapeUsingProfile(articleURLList, profileName):
    printDebug("\n", False)
    printDebug("Scraping using this profile: " + profileName)

    # Loading the profile for the current website
    currentProfile = OSINTprofiles.getProfiles(profileName)

    articleIDs = []

    for URL in articleURLList:
        articleIDs.append(handleSingleArticle(URL, currentProfile))

    return articleIDs

def main():

    printDebug("Scraping articles from frontpages and RSS feeds")
    articleURLCollection = OSINTscraping.gatherArticleURLs(OSINTprofiles.getProfiles())

    printDebug("Removing those articles that have already been stored in the database")
    filteredArticleURLCollection = esClient.filterArticleURLList(articleURLCollection)

    numberOfArticleAfterFilter = sum ([ len(filteredArticleURLCollection[profileName]) for profileName in filteredArticleURLCollection ])

    if numberOfArticleAfterFilter == 0:
        printDebug("All articles seems to have already been stored, exiting.")
        return
    else:
        printDebug("Found {} articles left to scrape, will begin that process now".format(str(numberOfArticleAfterFilter)))

    # Looping through the list of articles from specific news site in the list of all articles from all sites
    for profileName in filteredArticleURLCollection:
        scrapeUsingProfile(filteredArticleURLCollection[profileName], profileName)

    printDebug("\n---\n", False)

if __name__ == "__main__":
    main()
