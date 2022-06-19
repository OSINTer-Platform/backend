#!/usr/bin/python3

import json

from modules import *

from scripts import configOptions


def main(fileName):
    articles = configOptions.esArticleClient.queryDocuments(
        elastic.searchQuery(limit=10_000, complete=True)
    )

    articleDicts = []

    for article in articles["documents"]:
        articleDicts.append(article.dict())

    with open(fileName, "w") as exportFile:
        json.dump(articleDicts, exportFile, default=str)
