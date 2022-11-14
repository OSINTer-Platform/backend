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
    backup_name: str = f"{index_name}_backup"

    index_config: dict[str, any] = ES_INDEX_CONFIGS[index.name]
    es_index_client = IndicesClient(config_options.es_conn)

    # Create empty backup index
    es_index_client.delete(index=backup_name, ignore=[404])
    original_index_config = es_index_client.get_mapping(index=index_name)[index_name]["mappings"]
    es_index_client.create(index=backup_name, mappings=original_index_config)

    config_options.es_conn.reindex(dest={"index" : backup_name}, source={"index" : index_name})
    es_index_client.delete(index = index_name)

    # Migrate backup index to original index
    es_index_client.create(index = index_name, mappings=index_config)

    try:
        logger.debug("Attempting to reindex backup into new main index")
        config_options.es_conn.reindex(dest={"index" : index_name}, source={"index" : backup_name})
    except:
        logger.critical("Error when reindexing, attempting to recover original index from backup")

        try:
            es_index_client.delete(index = index_name)
            es_index_client.create(index = index_name, mappings=original_index_config)
            config_options.es_conn.reindex(dest={"index" : index_name}, source={"index" : backup_name})
        except:
            logger.critical(f'Error when attempting to recovering original index from backup, please manually recover "{index_name}" from the backup "{backup_name}"')

        raise




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
        local_articles: dict[str, any] = json.load(import_file)

    remote_article_urls: list[str] = [ article.url for article in config_options.es_article_client.query_all_documents()["documents"] ]


    new_articles: list[FullArticle] = []

    for article in local_articles:
        if article["url"] not in remote_article_urls:
            current_article_object = FullArticle(**article)
            current_article_object.id = None
            new_articles.append(current_article_object)


    saved_count: int = config_options.es_article_client.save_document(new_articles)



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
