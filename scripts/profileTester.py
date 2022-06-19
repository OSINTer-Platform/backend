#!/usr/bin/python3

import os
from time import sleep

from modules import *
from scripts.scrapeAndStore import scrapeUsingProfile, gatherArticleURLs
from scripts import configOptions

import elasticsearch


def main(profile, url=""):
    if url:
        articleURLCollection = {profile: [url]}
    else:
        articleURLCollection = gatherArticleURLs([profiles.getProfiles(profile)])

    articleIDs = scrapeUsingProfile(articleURLCollection[profile], profile)

    sleep(1)

    currentArticles = configOptions.esClient.queryDocuments(
        elastic.searchQuery(IDs=articleIDs)
    )

    for ID in articleIDs:
        os.system(f"firefox http://localhost:5000/renderMarkdownById/{ID}")

    for article in currentArticles["documents"]:
        os.system(f"firefox {article.url}")


if __name__ == "__main__":
    main()
