import gzip
import itertools
import json
import logging
import os
from typing import Any
from datetime import datetime

import typer

from modules.elastic import (
    ArticleSearchQuery,
    return_article_db_conn,
)
from modules.files import article_to_md
from modules.objects import FullArticle

from .. import config_options

logger = logging.getLogger("osinter")


app = typer.Typer()


@app.command()
def articles_to_json(export_filename: str) -> None:
    logger.debug("Downloading articles")
    articles = config_options.es_article_client.query_all_documents()

    logger.debug(
        f"Downloaded {len(articles)} articles. Converting them to json objects"
    )

    article_dicts = []

    for article in articles:
        article_dicts.append(article.model_dump(mode="json"))

    logger.debug(f"Converted {len(article_dicts)} articles. Writing them to json file")

    with open(export_filename, "w") as export_file:
        json.dump(article_dicts, export_file, default=str)


@app.command()
def json_to_articles(
    import_filename: str, bypass_ingest_pipeline: bool = False, use_bulk: bool = True
) -> None:
    logger.debug("Loading articles from file")

    with open(import_filename, "r") as import_file:
        local_articles: list[dict[str, Any]] = json.load(import_file)

    logger.debug("Removing already present articles")

    local_article_urls = [
        article["url"] for article in local_articles if "url" in article
    ]
    remote_article_urls = config_options.es_article_client.exists_in_db(
        local_article_urls
    )

    new_articles: list[FullArticle] = []

    for article in local_articles:
        if article["url"] not in remote_article_urls:
            current_article_object = FullArticle(**article)
            new_articles.append(current_article_object)

    logger.debug(f"Saving {len(new_articles)} new articles")

    saved_count = 0
    if use_bulk:
        saved_count = config_options.es_article_client.save_documents(
            new_articles, not bypass_ingest_pipeline
        )
    else:
        for new_article in new_articles:
            config_options.es_article_client.save_document(new_article)
            saved_count += 1

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
        )[0]

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


current_day = datetime.today().strftime("%Y-%m-%d-%H:%M:%S")


@app.command()
def backup(
    indicies: list[str] = [config_options.ELASTICSEARCH_ARTICLE_INDEX],
    backup_path: str = "./",
    backup_file_name: str = f"elastic-backup-{current_day}.gz",
) -> None:
    backup_full_path = backup_path + backup_file_name
    indicies_content: dict[str, list[dict[str, Any]]] = {}

    for index_name in indicies:
        logger.debug(f'Downloading articles for "{index_name}"')
        article_client = return_article_db_conn(
            config_options.es_conn,
            index_name,
            config_options.ELASTICSEARCH_ELSER_PIPELINE,
            config_options.ELASTICSEARCH_ELSER_ID,
        )

        articles = article_client.query_all_documents()

        logger.debug(
            f'Downloaded {len(articles)} articles for "{index_name}". Converting'
        )

        article_dicts = [
            article.model_dump(exclude={"highlights"}, mode="json")
            for article in articles
        ]
        indicies_content[index_name] = article_dicts

    logger.debug(f'Writing backup to disk at "{backup_full_path}"')
    with gzip.open(backup_full_path, "wt", encoding="utf-8") as f:
        json.dump(indicies_content, f)
