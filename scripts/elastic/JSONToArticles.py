#!/usr/bin/python3

import json
from datetime import datetime

from OSINTmodules import *

from scripts import configOptions


def main(fileName):
    with open(fileName, "r") as exportFile:
        articles = json.load(exportFile)

    for article in articles:
        currentArticleObject = OSINTobjects.FullArticle(**article)
        if not configOptions.esArticleClient.existsInDB(currentArticleObject.url):
            configOptions.esArticleClient.saveDocument(currentArticleObject)
