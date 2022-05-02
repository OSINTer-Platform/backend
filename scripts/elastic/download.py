#!/usr/bin/python3

import os

from OSINTmodules import *

from scripts import configOptions

def main(remoteEsAddress):

    remoteEsConn = OSINTelastic.createESConn(remoteEsAddress)
    remoteEsClient = OSINTelastic.elasticDB(remoteEsConn, "osinter_articles")

    configOptions.logger.info("Downloading articles...")

    articles = remoteEsClient.queryDocuments(OSINTelastic.searchQuery(limit = 10_000, complete = False))

    configOptions.logger.info(len(articles["documents"]))
    configOptions.logger.info(f"Downloaded {str(articles['result_number'])} articles.")
    configOptions.logger.info("Uploading articles")

    for article in articles["documents"]:
        if not configOptions.esArticleClient.existsInDB(article.url):
            configOptions.esArticleClient.saveDocument(article)
