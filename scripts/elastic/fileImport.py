#!/usr/bin/python3

import json

from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_CERT_PATH, configOptions.ELASTICSEARCH_ARTICLE_INDEX)

def main(fileName):
    with open(fileName, "r") as exportFile:
        articles = json.load(exportFile)

    for article in articles:
        currentArticleObject = OSINTobjects.Article(**article)
        if not esClient.existsInDB(currentArticleObject.url):
            esClient.saveArticle(currentArticleObject)
