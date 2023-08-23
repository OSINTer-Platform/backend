from enum import Enum
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
from pydantic import Field, ValidationError

import typer
from rich import print_json

from modules.elastic import (
    ES_INDEX_CONFIGS,
    ArticleSearchQuery,
    ElasticDB,
)
from modules.files import article_to_md
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
        ArticleSearchQuery(limit=0), True
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
    customElasticDB = ElasticDB[BaseArticle, FullArticleNoTimezone, ArticleSearchQuery](
        es_conn=config_options.es_conn,
        index_name=config_options.ELASTICSEARCH_ARTICLE_INDEX,
        unique_field="url",
        document_object_classes={
            "base": BaseArticle,
            "full": FullArticleNoTimezone,
            "search_query": ArticleSearchQuery,
        },
    )
    logger.debug("Downloading articles")
    articles = customElasticDB.query_documents(ArticleSearchQuery(limit=0), True)

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
def clean_up() -> None:
    def get_binary_user_input(prompt: str) -> bool:
        user_input: str = ""
        while True:
            user_input = input(f"{prompt} [y/n]: ").lower()

            if user_input in ["y", "n"]:
                break

            print("Wrong answer")
        return user_input == "y"

    def modify_doc(doc: dict[str, Any]) -> None | FullArticle:
        try:
            validated_doc = FullArticle.model_validate(doc["_source"])
            validated_doc.id = doc["_id"]
            return validated_doc
        except ValidationError as e:
            if get_binary_user_input(
                "The document cannot validate. Do you want to try and fix it?"
            ):
                print("\n\nModify the following fields to fix the error:\n")
                for error in e.errors():
                    field_name = error["loc"][0]

                    print(f"Field: {field_name}")
                    print(f"URL: {doc['_source']['url']}")
                    print(f"Previous value: {doc['_source'][field_name]}")
                    print(f"Error messages: {error['msg']}")
                    doc["_source"][field_name] = input(
                        f"Please enter a new value for {field_name}: "
                    )

                return modify_doc(doc)
            else:
                return None

    logger.info("Downloading all articles")
    search_q = ArticleSearchQuery(limit=0)
    articles, invalid_docs = config_options.es_article_client._query_large(
        search_q.generate_es_query(True), True
    )

    logger.info(
        f"Downloaded {len(articles)} articles and {len(invalid_docs)} invalid documents"
    )

    for doc in invalid_docs:
        print_json(data=doc["_source"])

        if get_binary_user_input("Delete the previous document?"):
            print("Removing document")
            config_options.es_article_client.delete_document(
                {
                    doc["_id"],
                }
            )
        else:
            modified_doc = modify_doc(doc)

            if modified_doc:
                print("Document now validates, saving it")
                config_options.es_article_client.save_document(modified_doc)
            else:
                print("Skipping to next document")


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
    profiles = list(config_options.es_article_client.get_unique_values("profile"))

    for profile in profiles:
        logger.info(f"Downloading list of articles for {profile}")

        articles = config_options.es_article_client.query_documents(
            ArticleSearchQuery(limit=0, sources=set(profile)), True
        )

        try:
            os.mkdir(os.path.join(folder_path, profile))
        except FileExistsError:
            pass

        logger.info(f"Converting {len(articles)} articles for {profile}")

        for article in articles:
            article_md = article_to_md(article)

            with open(
                os.path.join(folder_path, profile, f"{article.id}.md"), "w"
            ) as article_file:
                article_file.write(article_md)
