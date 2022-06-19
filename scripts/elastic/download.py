#!/usr/bin/python3

import os

from modules import *

from scripts import configOptions


def main(remoteEsAddress):

    remoteEsConn = elastic.createESConn(remoteEsAddress)
    remoteEsClient = elastic.elasticDB(remoteEsConn, "osinter_articles")

    configOptions.logger.info("Downloading articles...")

    articles = remoteEsClient.queryDocuments(
        elastic.searchQuery(limit=10_000, complete=False)
    )

    configOptions.logger.info(len(articles["documents"]))
    configOptions.logger.info(f"Downloaded {str(articles['result_number'])} articles.")
    configOptions.logger.info("Uploading articles")

    for article in articles["documents"]:
        if not configOptions.esArticleClient.existsInDB(article.url):
            configOptions.esArticleClient.saveDocument(article)
