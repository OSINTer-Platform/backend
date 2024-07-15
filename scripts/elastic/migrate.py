import logging
from datetime import datetime, timezone
from hashlib import md5
from typing import Any, cast
import multiprocessing
from tqdm import tqdm

from pydantic import Field, ValidationError

import typer
from rich import print_json

from modules.elastic import ArticleSearchQuery, ElasticDB, return_article_db_conn
from modules.objects import BaseArticle, FullArticle, PartialArticle

from .utils import get_user_yes_no
from .. import config_options
from ..scraping.articles.text import (
    generate_tags,
    locate_objects_of_interest,
    tokenize_text,
)

logger = logging.getLogger("osinter")


app = typer.Typer()


class FullArticleNoTimezone(FullArticle):
    publish_date: datetime
    inserted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


@app.command()
def add_timezone() -> None:
    customElasticDB = ElasticDB[
        BaseArticle, PartialArticle, FullArticleNoTimezone, ArticleSearchQuery
    ](
        es_conn=config_options.es_conn,
        index_name=config_options.ELASTICSEARCH_ARTICLE_INDEX,
        ingest_pipeline=config_options.ELASTICSEARCH_ELSER_PIPELINE,
        elser_model_id=config_options.ELASTICSEARCH_ELSER_ID,
        unique_field="url",
        document_object_classes={
            "base": BaseArticle,
            "partial": PartialArticle,
            "full": FullArticleNoTimezone,
            "search_query": ArticleSearchQuery,
        },
    )
    logger.debug("Downloading articles")
    articles = customElasticDB.query_all_documents()

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

    saved = config_options.es_article_client.update_documents(converted_articles)
    logger.debug(f"Saved {saved} articles")


def article_tag_regen(article: FullArticle) -> FullArticle:
    article.tags.automatic = generate_tags(tokenize_text(article.content))
    article.tags.interesting = locate_objects_of_interest(article.content)
    return article


@app.command()
def regenerate_tags() -> None:
    logger.debug("Downloading articles")
    articles = config_options.es_article_client.query_all_documents()

    logger.debug(f"Converting {len(articles)} articles")

    with multiprocessing.Pool(multiprocessing.cpu_count() - 2) as pool:
        new_articles = list(
            tqdm(pool.imap_unordered(article_tag_regen, articles), total=len(articles))
        )

    logger.debug("Saving articles")
    saved = config_options.es_article_client.update_documents(new_articles, ["tags"])
    logger.debug(f"Saved {saved} articles")


@app.command()
def clean_up() -> None:
    def modify_doc(doc: dict[str, Any]) -> None | FullArticle:
        try:
            validated_doc = FullArticle.model_validate(doc["_source"])
            validated_doc.id = doc["_id"]
            return validated_doc
        except ValidationError as e:
            if get_user_yes_no(
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
    articles, invalid_docs, _ = config_options.es_article_client.query_documents(
        search_q, True
    )

    logger.info(
        f"Downloaded {len(articles)} articles and {len(invalid_docs)} invalid documents"
    )

    for doc in invalid_docs:
        print_json(data=doc["_source"])

        if get_user_yes_no("Delete the previous document?"):
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
def update_ids() -> None:
    logger.debug("Downloading articles")
    articles = config_options.es_article_client.query_all_documents()

    logger.debug(f"Updating ids on {len(articles)} articles")

    articles_to_remove: set[str] = set()
    articles_to_save: list[FullArticle] = []

    for article in articles:
        hash = md5(str(article.url).encode("utf-8")).hexdigest()
        if hash != article.id:
            articles_to_remove.add(article.id)
            article.id = hash
            articles_to_save.append(article)

    logger.debug(f"Saving {len(articles_to_save)} new articles")
    saved = config_options.es_article_client.save_documents(articles_to_save)
    logger.debug(f"Saved {saved} articles")

    logger.debug(f"Removing {len(articles_to_remove)} old articles")
    removed = config_options.es_article_client.delete_document(articles_to_remove)
    logger.debug(f"Removed {removed} articles")


@app.command()
def update_temporary(from_index: str, to_index: str) -> None:
    TEMPORARY_FIELDS = ["ml", "tags", "summary", "read_times"]

    from_client = return_article_db_conn(config_options.es_conn, from_index, None, None)
    to_client = return_article_db_conn(config_options.es_conn, to_index, None, None)

    logger.debug(f'Downloading articles from "{from_index}"')
    from_articles = from_client.query_documents(
        ArticleSearchQuery(limit=0), TEMPORARY_FIELDS + ["url"]
    )[0]

    logger.debug(f"Found {len(from_articles)} articles")

    logger.debug(f'Removing articles which are not present in "{to_index}"')
    urls_not_present = to_client.filter_document_list(
        [cast(str, article.url) for article in from_articles]
    )

    if urls_not_present:
        logger.debug(f'{len(urls_not_present)} articles is not present in "{to_index}"')
        print("These were not present:\n", urls_not_present)
    else:
        logger.debug(f'All articles in "{from_index}" are present in "{to_index}"')

    to_articles: list[PartialArticle] = []

    for article in from_articles:
        if article.url not in urls_not_present:
            to_articles.append(
                PartialArticle.model_validate(
                    article, context={"fields_to_validate": TEMPORARY_FIELDS}
                )
            )

    logger.debug(f"Updating {len(to_articles)} articles")

    to_client.update_documents(to_articles, TEMPORARY_FIELDS)
