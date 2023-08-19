from enum import Enum
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, cast

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
from pydantic import Field
import typer

from modules.elastic import (
    ES_INDEX_CONFIGS,
    ElasticDB,
    SearchQuery,
)
from modules.files import convert_article_to_md
from modules.objects import BaseArticle, FullArticle

from . import config_options

logger = logging.getLogger("osinter")


app = typer.Typer()


class ESIndex(str, Enum):
    ELASTICSEARCH_ARTICLE_INDEX = "ARTICLE"


@app.command()
def reindex(index: ESIndex) -> None:
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
def articles_to_json(export_filename: str) -> None:
    logger.debug("Downloading articles")
    articles = config_options.es_article_client.query_documents(
        SearchQuery(limit=0, complete=True)
    )

    article_dicts = []

    logger.debug("Converting articles to json objects")

    for article in articles:
        article_dicts.append(article.model_dump(mode="json"))

    logger.debug("Writing articles to json file")

    with open(export_filename, "w") as export_file:
        json.dump(article_dicts, export_file, default=str)


class FullArticleNoTimezone(FullArticle):
    publish_date: datetime
    inserted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@app.command()
def add_timezone() -> None:
    customElasticDB = ElasticDB[BaseArticle | FullArticleNoTimezone](
        es_conn=config_options.es_conn,
        index_name=config_options.ELASTICSEARCH_ARTICLE_INDEX,
        unique_field="url",
        source_category="profile",
        weighted_search_fields=["title^5", "description^3", "content"],
        document_object_classes={"base" : BaseArticle, "full" : FullArticleNoTimezone},
        essential_fields=[
            "title",
            "description",
            "url",
            "image_url",
            "profile",
            "source",
            "publish_date",
            "inserted_at",
        ],
    )
    logger.debug("Downloading articles")
    articles = cast(list[FullArticleNoTimezone], customElasticDB.query_documents(SearchQuery(limit=0, complete=True)))

    logger.debug(f"Converting {len(articles)} articles")
    converted_articles: list[FullArticle] = []

    for article in articles:
        modified = False
        if article.publish_date.tzinfo is None:
            modified = True
            article.publish_date = article.publish_date.replace(tzinfo=timezone.utc)

        if article.inserted_at.tzinfo is None:
            modified = True
            article.inserted_at = article.inserted_at.replace(tzinfo=timezone.utc)

        if modified:
            converted_articles.append(article)

    logger.debug(f"Converted {len(converted_articles)} articles. Uploading changes")

    config_options.es_article_client.save_documents(converted_articles)


@app.command()
def json_to_articles(import_filename: str) -> None:
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
def articles_to_md(destination: str) -> None:
    folder_path = os.path.join(destination, "MDArticles")

    try:
        os.mkdir(folder_path)
    except FileExistsError:
        pass

    logger.info("Downloading list of profiles...")
    profiles = list(config_options.es_article_client.get_unique_values())

    for profile in profiles:
        logger.info(f"Downloading list of articles for {profile}")

        articles: list[FullArticle] = cast(
            list[FullArticle],
            config_options.es_article_client.query_documents(
                SearchQuery(complete=True, limit=0, source_category=set(profile))
            ),
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
