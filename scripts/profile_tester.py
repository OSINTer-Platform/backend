#!/usr/bin/python3

import os

from modules import *
from scripts.scrape_and_store import handle_single_article, gather_article_urls
from scripts import config_options


def main(profile_name, custom_url=""):
    current_profile = profiles.get_profiles(profile_name)

    if custom_url:
        article_url_collection = [custom_url]
    else:
        article_url_collection = gather_article_urls([current_profile])[profile_name]

    articles = []
    for url in article_url_collection:
        config_options.logger.info(f"Scraping article with URL: {url}")
        articles.append(handle_single_article(url, current_profile))

    article_string = ""

    for article in articles:
        os.system(f"firefox {article.url}")
        article_string += files.convert_article_to_md(article).getvalue() + "\n\n"

    with open("./articles.md", "w") as f:
        f.write(article_string)


if __name__ == "__main__":
    main()
