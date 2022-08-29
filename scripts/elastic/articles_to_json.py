#!/usr/bin/python3

import json

from modules import *

from scripts import config_options


def main(filename):
    articles = config_options.es_article_client.query_documents(
        elastic.SearchQuery(limit=10_000, complete=True)
    )

    article_dics = []

    for article in articles["documents"]:
        article_dics.append(article.dict())

    with open(filename, "w") as export_file:
        json.dump(article_dics, export_file, default=str)
