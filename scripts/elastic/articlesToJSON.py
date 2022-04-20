#!/usr/bin/python3

import json

from OSINTmodules import *

from scripts import configOptions

esClient = OSINTelastic.returnArticleDBConn(configOptions)

def main(fileName):
    articles = esClient.searchDocuments({"limit" : 10000})

    articleDicts = []

    for article in articles["documents"]:
        articleDicts.append(article.as_dict())

    with open(fileName, "w") as exportFile:
        json.dump(articleDicts, exportFile)
