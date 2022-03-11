#!/usr/bin/python3

import os

from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.returnArticleDBConn(configOptions)

def main(remoteEsAddress):

    remoteEsConn = OSINTelastic.createESConn(remoteEsAddress)
    remoteEsClient = OSINTelastic.elasticDB(remoteEsConn, "osinter_articles")

    configOptions.logger.info("Downloading articles...")

    articles = remoteEsClient.searchArticles({"limit" : 10000})

    configOptions.logger.info(len(articles["articles"]))
    configOptions.logger.info(f"Downloaded {str(articles['result_number'])} articles.")
    configOptions.logger.info("Uploading articles")

    for article in articles["articles"]:
        if not esClient.existsInDB(article.url):
            esClient.saveArticle(article)

if __name__ == "__main__":
    main()
