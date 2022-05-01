#!/usr/bin/python3

import os
from time import sleep

from OSINTmodules import *
from scripts.scrapeAndStore import scrapeUsingProfile, gatherArticleURLs
from scripts import configOptions

import elasticsearch

def main(profile, url=""):
    if url:
        articleURLCollection = {profile : [url]}
    else:
        articleURLCollection = gatherArticleURLs([OSINTprofiles.getProfiles(profile)])

    articleIDs = scrapeUsingProfile(articleURLCollection[profile], profile)

    sleep(1)

    currentArticles = configOptions.esClient.queryDocuments(OSINTelastic.searchQuery(IDs = articleIDs))

    for ID in articleIDs:
        os.system(f"firefox http://localhost:5000/renderMarkdownById/{ID}")

    for article in currentArticles["documents"]:
        os.system(f"firefox {article.url}")




if __name__ == "__main__":
    main()
