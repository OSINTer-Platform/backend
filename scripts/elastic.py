import os
import json
from datetime import datetime
from enum import Enum

from . import config_options
from modules.elastic import SearchQuery, ES_INDEX_CONFIGS
from modules.objects import FullArticle
from modules.files import convert_article_to_md

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient

import logging

logger = logging.getLogger("osinter")

import typer

app = typer.Typer()

class ESIndex(str, Enum):
    ELASTICSEARCH_TWEET_INDEX = "TWEET"
    ELASTICSEARCH_ARTICLE_INDEX = "ARTICLE"
    ELASTICSEARCH_USER_INDEX = "USER"

@app.command()
def reindex(index: ESIndex):
    index_name: str = config_options[index.name]
    index_config: dict[str, any] = ES_INDEX_CONFIGS[index.name]
    es_index_client = IndicesClient(config_options.es_conn)

    print(index_name)

    # es_index_client.delete(index = f"{index_name}-backup")



@app.command()
def articles_to_json(export_filename: str):
    articles = config_options.es_article_client.query_documents(
        SearchQuery(limit=0, complete=True)
    )

    article_dicts = []

    for article in articles["documents"]:
        article_dicts.append(article.dict())

    with open(export_filename, "w") as export_file:
        json.dump(article_dicts, export_file, default=str)


@app.command()
def json_to_articles(import_filename: str):
    with open(import_filename, "r") as import_file:
        articles = json.load(import_file)

    for article in articles:
        current_article_object = FullArticle(**article)
        if not config_options.es_article_client.exists_in_db(
            current_article_object.url
        ):
            current_article_object.id = None
            config_options.es_article_client.save_document(current_article_object)


@app.command()
def articles_to_md(destination: str):
    folder_path = os.path.join(destination, "MDArticles")

    try:
        os.mkdir(folder_path)
    except FileExistsError:
        pass

    logger.info("Downloading list of profiles...")
    profiles = list(config_options.es_article_client.get_unique_values())

    for profile in profiles:

        logger.info(f"Downloading list of articles for {profile}")

        articles = config_options.es_article_client.query_documents(
            SearchQuery(complete=True, limit=0, source_category=[profile])
        )["documents"]

        try:
            os.mkdir(os.path.join(folder_path, profile))
        except FileExistsError:
            pass

        logger.info(f"Converting {len(articles)} articles for {profile}")

        for article in articles:
            article_md = convert_article_to_md(article)

            with open(
                os.path.join(folder_path, profile, f"{article.id}.md"), "w"
            ) as article_file:
                article_file.write(article_md.getvalue())
