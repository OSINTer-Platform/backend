#!/usr/bin/python3

import os

from modules import *

from scripts import config_options

import logging

logger = logging.getLogger("osinter")


def main(remote_es_address):

    remote_es_conn = elastic.create_es_conn(remote_es_address)
    remote_es_client = elastic.ElasticDB(remote_es_conn, "osinter_articles")

    logger.info("Downloading articles...")

    articles = remote_es_client.query_documents(
        elastic.SearchQuery(limit=10_000, complete=False)
    )

    logger.info(len(articles["documents"]))
    logger.info(f"Downloaded {str(articles['result_number'])} articles.")
    logger.info("Uploading articles")

    for article in articles["documents"]:
        if not config_options.es_article_client.exists_in_db(article.url):
            config_options.es_article_client.save_document(article)
