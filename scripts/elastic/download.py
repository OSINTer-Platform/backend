#!/usr/bin/python3

import os

from modules import *

from scripts import config_options


def main(remote_es_address):

    remote_es_conn = elastic.create_es_conn(remote_es_address)
    remote_es_client = elastic.ElasticDB(remote_es_conn, "osinter_articles")

    config_options.logger.info("Downloading articles...")

    articles = remote_es_client.query_documents(
        elastic.SearchQuery(limit=10_000, complete=False)
    )

    config_options.logger.info(len(articles["documents"]))
    config_options.logger.info(f"Downloaded {str(articles['result_number'])} articles.")
    config_options.logger.info("Uploading articles")

    for article in articles["documents"]:
        if not config_options.es_article_client.exists_in_db(article.url):
            config_options.es_article_client.save_document(article)
