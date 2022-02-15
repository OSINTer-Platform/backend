#!/usr/bin/python3

debugMessages = False

import os

from OSINTmodules.OSINTmisc import printDebug
from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_ARTICLE_INDEX)

def main():

    remoteEsAddress = input("Please enter the full URL (with read access) of the remote Elasticsearch cluster: ")

    remoteEsClient = OSINTelastic.elasticDB(remoteEsAddress, "osinter_articles")

    printDebug("Downloading articles...")

    articles = remoteEsClient.searchArticles({"limit" : 10000})

    printDebug(len(articles["articles"]))

    printDebug(f"Downloaded {str(articles['result_number'])} articles.")
    printDebug("Uploading articles")

    for article in articles["articles"]:
        if not esClient.existsInDB(article.url):
            esClient.saveArticle(article)

if __name__ == "__main__":
    main()
