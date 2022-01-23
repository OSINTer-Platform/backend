#!/usr/bin/python3

import os
from time import sleep

from OSINTmodules import *
from scripts.scrapeAndStore import scrapeUsingProfile

import elasticsearch

esAddress = os.environ.get('ELASTICSEARCH_URL') or "http://localhost:9200"
esClient = OSINTelastic.elasticDB(esAddress, "osinter_articles")


def main():
    profile = input("Which profile do you want to test? ")

    url = input("Enter specific URL or leave blank for scraping 10 urls by itself: ")

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
