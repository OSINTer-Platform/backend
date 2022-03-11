#!/usr/bin/python3

import json

from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.returnArticleDBConn(configOptions)

def main(fileName):
    articles = esClient.searchArticles({"limit" : 10000})

    articleDicts = []

    for article in articles["articles"]:
        articleDicts.append(article.as_dict())

    with open(fileName, "w") as exportFile:
        json.dump(articleDicts, exportFile)

if __name__ == "__main__":
    main()
