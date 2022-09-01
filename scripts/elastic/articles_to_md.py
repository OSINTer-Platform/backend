import os

from modules import *

from scripts import config_options


def main(folder_path):
    try:
        os.mkdir(os.path.join(folder_path, "MDArticles"))
    except FileExistsError:
        pass

    folder_path = os.path.join(folder_path, "MDArticles")
    config_options.logger.info("Downloading list of profiles...")
    profiles = list(config_options.es_article_client.get_unique_values())

    for profile in profiles:

        config_options.logger.info(f"Downloading list of articles for {profile}")
        articles = config_options.es_article_client.query_documents(
            elastic.SearchQuery(complete=True, limit=10_000, source_category=[profile])
        )["documents"]

        try:
            os.mkdir(os.path.join(folder_path, profile))
        except FileExistsError:
            pass

        config_options.logger.info(f"Converting {len(articles)} articles for {profile}")
        for article in articles:
            article_md = files.convert_article_to_md(article)

            with open(
                os.path.join(folder_path, profile, f"{article.id}.md"), "w"
            ) as article_file:
                article_file.write(article_md.getvalue())
