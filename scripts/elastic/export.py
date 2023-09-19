import json
import logging
import os
from typing import Any

import typer

from modules.elastic import (
    ArticleSearchQuery,
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
def json_to_articles(import_filename: str) -> None:
    logger.debug("Loading articles from file")

    with open(import_filename, "r") as import_file:
        local_articles: list[dict[str, Any]] = json.load(import_file)

    logger.debug(
        "Downloading list of articles from remote DB for removal of already stored articles"
    )
    remote_article_urls: list[str] = [
        article_url
        for article in config_options.es_article_client.query_documents(
            ArticleSearchQuery(limit=0), False
        )
        if (article_url := getattr(article, "url", None))
    ]

    logger.debug(f"Downloaded {len(remote_article_urls)} articles")

    logger.debug("Removing articles that's already stored in DB")

    new_articles: list[FullArticle] = []

    for article in local_articles:
        if article["url"] not in remote_article_urls:
            current_article_object = FullArticle(**article)
            new_articles.append(current_article_object)

    logger.debug(f"Saving {len(new_articles)} new articles")

    saved_count: int = 0
    for i, article_list in enumerate(
        [new_articles[i : i + 1000] for i in range(0, len(new_articles), 1000)]
    ):
        logger.debug(f"Saving batch nr {i}")
        saved_count += config_options.es_article_client.save_documents(article_list)

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

        articles = config_options.es_article_client.query_all_documents()

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
