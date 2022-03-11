#!/usr/bin/python3

import json
from datetime import datetime

from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_CERT_PATH, configOptions.ELASTICSEARCH_ARTICLE_INDEX)

def main(fileName):
    with open(fileName, "r") as exportFile:
        articles = json.load(exportFile)

    for article in articles:
        for timeValue in ["publish_date", "inserted_at"]:
            article[timeValue] = datetime.strptime(article[timeValue], "%Y-%m-%dT%H:%M:%S%z")

        currentArticleObject = OSINTobjects.Article(**article)
        if not esClient.existsInDB(currentArticleObject.url):
            esClient.saveArticle(currentArticleObject)
