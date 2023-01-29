from enum import Enum
import json
import logging
import os
from typing import Any

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
import typer

from modules.elastic import ES_INDEX_CONFIGS, SearchQuery
from modules.files import convert_article_to_md
from modules.objects import FullArticle

from . import config_options

logger = logging.getLogger("osinter")


app = typer.Typer()


class ESIndex(str, Enum):
    ELASTICSEARCH_TWEET_INDEX = "TWEET"
    ELASTICSEARCH_ARTICLE_INDEX = "ARTICLE"
    ELASTICSEARCH_USER_INDEX = "USER"


@app.command()
def reindex(index: ESIndex):
    index_name: str = config_options[index.name]
    backup_name: str = f"{index_name}_backup"

    index_config: dict[str, Any] = ES_INDEX_CONFIGS[index.name]
    es_index_client = IndicesClient(config_options.es_conn)

    logger.debug("Creating empty backup index")

    try:
        es_index_client.delete(index=backup_name)
    except BadRequestError as e:
        if e.status_code != 404:
            raise e

    original_index_config = es_index_client.get_mapping(index=index_name)[index_name][
        "mappings"
    ]
    es_index_client.create(index=backup_name, mappings=original_index_config)

    logger.debug("Copying main index to backup index")
    config_options.es_conn.reindex(
        dest={"index": backup_name}, source={"index": index_name}
    )

    logger.debug("Emptying main index and updating index mappings")
    es_index_client.delete(index=index_name)
    es_index_client.create(index=index_name, mappings=index_config)

    try:
        logger.debug("Attempting to reindex backup into new main index")
        config_options.es_conn.reindex(
            dest={"index": index_name}, source={"index": backup_name}
        )
    except:
        logger.critical(
            "Error when reindexing, attempting to recover original index from backup"
        )

        try:
            logger.debug("Emptying main index and reverting to old mappings")
            es_index_client.delete(index=index_name)
            es_index_client.create(index=index_name, mappings=original_index_config)

            logger.debug("Attempting to recover original index contents from backup")
            config_options.es_conn.reindex(
                dest={"index": index_name}, source={"index": backup_name}
            )
        except:
            logger.critical(
                f'Error when attempting to recovering original index from backup, please manually recover "{index_name}" from the backup "{backup_name}"'
            )

        raise


@app.command()
def articles_to_json(export_filename: str):
    logger.debug("Downloading articles")
    articles = config_options.es_article_client.query_documents(
        SearchQuery(limit=0, complete=True)
    )

    article_dicts = []

    logger.debug("Converting articles to json objects")

    for article in articles:
        article_dicts.append(article.dict())

    logger.debug("Writing articles to json file")

    with open(export_filename, "w") as export_file:
        json.dump(article_dicts, export_file, default=str)


@app.command()
def json_to_articles(import_filename: str):
    logger.debug("Loading articles from file")

    with open(import_filename, "r") as import_file:
        local_articles: list[dict[str, Any]] = json.load(import_file)

    logger.debug(
        "Downloading list of articles from remote DB for removal of already stored articles"
    )
    remote_article_urls: list[str] = [
        article_url
        for article in config_options.es_article_client.query_all_documents()
        if (article_url := getattr(article, "url", None))
    ]

    logger.debug("Removing articles that's already stored in DB")

    new_articles: list[FullArticle] = []

    for article in local_articles:
        if article["url"] not in remote_article_urls:
            current_article_object = FullArticle(**article)
            current_article_object.id = None
            new_articles.append(current_article_object)

    logger.debug(f"Saving {len(new_articles)} new articles")

    saved_count: int = config_options.es_article_client.save_documents(new_articles)

    logger.info(f"Saved {saved_count} new articles")


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
        )

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
