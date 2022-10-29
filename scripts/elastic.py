import os
import json
from datetime import datetime

from . import config_options
from modules.elastic import SearchQuery
from modules.objects import FullArticle
from modules.files import convert_article_to_md

import typer

app = typer.Typer()

@app.command()
def articles_to_json(export_filename: str):
    articles = config_options.es_article_client.query_documents(
        SearchQuery(limit = 0, complete=True)
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

