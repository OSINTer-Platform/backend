import logging
import os

from modules.files import convert_article_to_md
from modules.profiles import get_profile
from scripts.scraping.articles import gather_article_urls, handle_single_article

logger = logging.getLogger("osinter")


def main(profile_name, custom_url=""):
    current_profile = get_profile(profile_name)

    if custom_url:
        article_url_collection = [custom_url]
    else:
        article_url_collection = gather_article_urls([current_profile])[profile_name]

    articles = []
    for url in article_url_collection:
        logger.info(f"Scraping article with URL: {url}")
        articles.append(handle_single_article(url, current_profile))

    article_string = ""

    for article in articles:
        os.system(f"firefox {article.url}")
        article_string += convert_article_to_md(article).getvalue() + "\n\n"

    with open("./articles.md", "w") as f:
        f.write(article_string)
