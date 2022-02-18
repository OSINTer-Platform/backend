#!/usr/bin/python3

import os
from time import sleep

from OSINTmodules import *
from scripts.scrapeAndStore import scrapeUsingProfile

import elasticsearch

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_ARTICLE_INDEX)


def main(profile, url=""):
    if url:
        articleURLCollection = {profile : [url]}
    else:
        articleURLCollection = OSINTscraping.gatherArticleURLs([OSINTprofiles.getProfiles(profile)])

    articleIDs = scrapeUsingProfile(articleURLCollection[profile], profile)

    sleep(1)

    currentArticles = esClient.searchArticles({"IDs" : articleIDs})

    for ID in articleIDs:
        os.system(f"firefox http://localhost:5000/renderMarkdownById/{ID}")

    for article in currentArticles["articles"]:
        os.system(f"firefox {article.url}")




if __name__ == "__main__":
    main()
