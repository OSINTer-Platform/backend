#!/usr/bin/python3

# Used for loading the profile
import json

# Used for reading from file
from pathlib import Path

import os

from bs4 import BeautifulSoup as bs
from markdownify import MarkdownConverter

from modules import *
from scripts import configOptions

from datetime import datetime, timezone

from searchtweets import load_credentials

from pydantic import ValidationError


class customMD(MarkdownConverter):
    def convert_figure(self, el, text, convert_as_inline):
        self.process_tag(el, False, children_only=True)
        return text + "\n\n"


# Function for gathering list of URLs for articles from newssite
def gatherArticleURLs(profiles):

    articleURLs = {}

    for profile in profiles:

        configOptions.logger.debug(
            f'Gathering URLs for the "{profile["source"]["profileName"]}" profile.'
        )

        try:
            # For those were the RSS feed is useful, that will be used
            if profile["source"]["retrivalMethod"] == "rss":
                configOptions.logger.debug("Using RSS for gathering links.\n")
                articleURLs[
                    profile["source"]["profileName"]
                ] = scraping.RSSArticleURLs(
                    profile["source"]["newsPath"], profile["source"]["profileName"]
                )

            # For basically everything else scraping will be used
            elif profile["source"]["retrivalMethod"] == "scraping":
                configOptions.logger.debug("Using scraping for gathering links.\n")
                articleURLs[
                    profile["source"]["profileName"]
                ] = scraping.scrapeArticleURLs(
                    profile["source"]["address"],
                    profile["source"]["newsPath"],
                    profile["source"]["scrapingTargets"],
                    profile["source"]["profileName"],
                )

        except Exception as e:
            configOptions.logger.exception(
                f'Problem with gathering URLs for the "{profile["source"]["profileName"]}" profile. Skipping for now.'
            )

    return articleURLs


def handleSingleArticle(URL, currentProfile):

    # Scrape the whole article source based on how the profile says
    scrapingTypes = currentProfile["scraping"]["type"].split(";")
    articleSource = scraping.scrapePageDynamic(URL, scrapingTypes)
    articleSoup = bs(articleSource, "html.parser")

    articleMetaInformation = extract.extractMetaInformation(
        articleSoup,
        currentProfile["scraping"]["meta"],
        currentProfile["source"]["address"],
    )

    currentArticle = objects.FullArticle(
        url=URL,
        profile=currentProfile["source"]["profileName"],
        source=currentProfile["source"]["name"],
        **articleMetaInformation,
    )

    articleText, articleClearText = extract.extractArticleContent(
        currentProfile["scraping"]["content"], articleSoup
    )

    articleClearText = text.cleanText(articleClearText)

    currentArticle.content = articleClearText
    currentArticle.formatted_content = customMD(heading_style="closed_atx").convert(
        articleText
    )

    # Generate the tags
    currentArticle.tags["automatic"] = text.generateTags(
        text.tokenizeText(articleClearText)
    )
    currentArticle.tags["interresting"] = text.locateObjectsOfInterrest(
        articleClearText
    )
    currentArticle.tags["manual"] = {}

    if os.path.isdir(Path("./tools/keywords/")):
        for file in os.listdir(Path("./tools/keywords/")):
            currentTags = text.locateKeywords(
                misc.decodeKeywordsFile(Path(f"./tools/keywords/{file}")),
                articleClearText,
            )
            if currentTags != []:
                currentArticle.tags["manual"][file] = currentTags

    currentArticle.inserted_at = datetime.now(timezone.utc)

    return configOptions.esArticleClient.saveDocument(currentArticle)


def scrapeUsingProfile(articleURLList, profileName):
    if not articleURLList:
        return []

    configOptions.logger.info(
        f'Scraping {len(articleURLList)} articles using the "{profileName}" profile.'
    )

    # Loading the profile for the current website
    currentProfile = profiles.getProfiles(profileName)

    articleIDs = []

    for i, URL in enumerate(articleURLList):
        configOptions.logger.debug(
            f'Scraped article number {i + 1} with the types "{currentProfile["scraping"]["type"]}" and following url: {URL}.'
        )
        try:
            articleIDs.append(handleSingleArticle(URL, currentProfile))
        except ValidationError as e:
            configOptions.logger.error(f'Encountered problem with article with URL "{URL}", skipping for now. Error: {e}')


    return articleIDs


def scrapeArticles():
    configOptions.logger.debug("Scraping articles from frontpages and RSS feeds")
    articleURLCollection = gatherArticleURLs(profiles.getProfiles())

    configOptions.logger.debug(
        "Removing those articles that have already been stored in the database"
    )

    filteredArticleURLCollection = {}

    for articleSource in articleURLCollection:
        filteredArticleURLCollection[
            articleSource
        ] = configOptions.esArticleClient.filterDocumentList(
            articleURLCollection[articleSource]
        )

    numberOfArticleAfterFilter = sum(
        [
            len(filteredArticleURLCollection[profileName])
            for profileName in filteredArticleURLCollection
        ]
    )

    if numberOfArticleAfterFilter == 0:
        configOptions.logger.info(
            "All articles seems to have already been stored, exiting."
        )
        return
    else:
        configOptions.logger.info(
            "Found {} articles left to scrape, will begin that process now".format(
                str(numberOfArticleAfterFilter)
            )
        )

    # Looping through the list of articles from specific news site in the list of all articles from all sites
    for profileName in filteredArticleURLCollection:
        scrapeUsingProfile(filteredArticleURLCollection[profileName], profileName)


def getTweets(majorAuthorList, credentials, chunckSize=10):
    chunckedAuthorList = [
        majorAuthorList[i : i + chunckSize]
        for i in range(0, len(majorAuthorList), chunckSize)
    ]

    tweets = []

    for authorList in chunckedAuthorList:
        configOptions.logger.debug(
            f"Scraping tweets for these authors: {' '.join(authorList)}"
        )
        try:
            lastID = configOptions.esTweetClient.getLastDocument(authorList).twitter_id
            tweetData = twitter.gatherTweetData(credentials, authorList, lastID)
        except AttributeError:
            configOptions.logger.debug("These are the first tweets by these authors.")
            tweetData = twitter.gatherTweetData(credentials, authorList)

        if tweetData:
            configOptions.logger.debug("Converting twitter data to python objects.")
            for tweet in twitter.processTweetData(tweetData):
                tweets.append(objects.FullTweet(**tweet))
        else:
            configOptions.logger.debug("No tweets was found.")
            return []

    return tweets


def scrapeTweets(authorListPath=Path("./tools/twitter_authors")):
    configOptions.logger.debug("Trying to load twitter credentials and authorlist.")
    if os.path.isfile(authorListPath) and os.path.isfile(
        configOptions.TWITTER_CREDENTIAL_PATH
    ):
        credentials = load_credentials(
            configOptions.TWITTER_CREDENTIAL_PATH,
            yaml_key="search_tweets_v2",
            env_overwrite=False,
        )

        authorList = []

        with open(authorListPath, "r") as f:
            for line in f.readlines():
                # Splitting by # to allow for comments
                authorList.append(line.split("#")[0].strip())

        configOptions.logger.debug(
            "Succesfully loaded twitter credentials and authorlist."
        )

        tweetIDs = []

        tweetList = getTweets(authorList, credentials)

        configOptions.logger.debug("Saving the tweets.\n")
        for tweet in tweetList:
            tweetIDs.append(configOptions.esTweetClient.saveDocument(tweet))

        return tweetIDs
    else:
        configOptions.logger.debug(
            "Couldn't load twitter credentials and authorlist.\n"
        )
        return None


def main():

    for scrapingFunction in [scrapeTweets, scrapeArticles]:
        try:
            configOptions.logger.info(
                f'Running the "{scrapingFunction.__name__}" function.'
            )
            scrapingFunction()

        except Exception as e:
            configOptions.logger.critical(
                f'Critical error prevented running the "{scrapingFunction.__name__}".',
                exc_info=True,
            )


if __name__ == "__main__":
    main()
