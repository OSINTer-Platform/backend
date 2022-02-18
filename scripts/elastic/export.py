#!/usr/bin/python3

import json

from OSINTmodules import *

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_ARTICLE_INDEX)

def main():
    articles = esClient.searchArticles({"limit" : 10000})

    articleDicts = []

    for article in articles["articles"]:
        articleDicts.append(article.as_dict())

    print(json.dumps(articleDicts))

if __name__ == "__main__":
    main()
