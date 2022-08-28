#!/usr/bin/python3

import json
from datetime import datetime

from modules import *

from scripts import configOptions


def main(fileName):
    with open(fileName, "r") as exportFile:
        articles = json.load(exportFile)

    for article in articles:
        currentArticleObject = objects.FullArticle(**article)
        if not configOptions.esArticleClient.existsInDB(currentArticleObject.url):
            currentArticleObject.id = None
            configOptions.esArticleClient.saveDocument(currentArticleObject)
