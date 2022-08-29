#!/usr/bin/python3

import json
from datetime import datetime

from modules import *

from scripts import config_options


def main(filename):
    with open(filename, "r") as import_file:
        articles = json.load(import_file)

    for article in articles:
        current_article_object = objects.FullArticle(**article)
        if not config_options.es_article_client.exists_in_db(
            current_article_object.url
        ):
            current_article_object.id = None
            config_options.es_article_client.save_document(current_article_object)
