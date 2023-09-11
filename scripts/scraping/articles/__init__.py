import logging
from typing import Any, cast

from bs4 import BeautifulSoup as bs
from markdownify import MarkdownConverter  # type: ignore
from pydantic import HttpUrl, ValidationError

from modules.objects import FullArticle
from modules.profiles import get_profile, get_profiles

from .text import clean_text, generate_tags, locate_objects_of_interrest, tokenize_text
from .extract import extract_article_content, extract_meta_information
from .scraping import (
    get_article_urls_from_rss,
    scrape_article_urls,
    scrape_page_dynamic,
)

from scripts import config_options

logger = logging.getLogger("osinter")


class custom_md_converter(MarkdownConverter):  # type: ignore
    def convert_figure(self, el: Any, text: str, _: bool) -> str:
        self.process_tag(el, False, children_only=True)
        return text + "\n\n"

    def convert_a(self, el: Any, text: str, convert_as_inline: bool) -> str:
        try:
            del el["title"]
        except KeyError:
            pass

        return cast(str, super().convert_a(el, text, convert_as_inline))


# Function for gathering list of URLs for articles from newssite
def gather_article_urls(profiles: list[dict[str, Any]]) -> dict[str, list[str]]:
    article_urls: dict[str, list[str]] = {}

    for profile in profiles:
        profile_name = profile["source"]["profile_name"]

        logger.debug(f'Gathering URLs for the "{profile_name}" profile.')

        try:
            # For those were the RSS feed is useful, that will be used
            if profile["source"]["retrival_method"] == "rss":
                logger.debug("Using RSS for gathering links.\n")
                article_urls[profile_name] = get_article_urls_from_rss(
                    profile["source"]["news_path"]
                )

            # For basically everything else scraping will be used
            elif profile["source"]["retrival_method"] == "scraping":
                logger.debug("Using scraping for gathering links.\n")
                article_urls[profile_name] = scrape_article_urls(
                    profile["source"]["address"],
                    profile["source"]["news_path"],
                    profile["source"]["scraping_targets"],
                    profile_name,
                )
            elif profile["source"]["retrival_method"] == "dynamic":
                logger.debug("Using dynamic scraping for gathering links.\n")

                articles_source = scrape_page_dynamic(
                    profile["source"]["news_path"], []
                )
                frontpage_soup = bs(articles_source, "html.parser")

                article_urls[profile_name] = scrape_article_urls(
                    profile["source"]["address"],
                    profile["source"]["news_path"],
                    profile["source"]["scraping_targets"],
                    profile_name,
                    web_soup=frontpage_soup,
                )
            else:
                raise NotImplementedError

        except Exception as e:
            article_urls[profile_name] = []
            logger.exception(
                f'Problem with gathering URLs for the "{profile_name}" profile. Skipping for now. Error {e}'
            )

    return article_urls


def handle_single_article(url: str, current_profile: dict[str, Any]) -> FullArticle:
    # Scrape the whole article source based on how the profile says
    scraping_types: list[str] = current_profile["scraping"]["type"].split(";")
    articles_source = scrape_page_dynamic(url, scraping_types)
    article_soup = bs(articles_source, "html.parser")

    article_meta = extract_meta_information(
        article_soup,
        current_profile["scraping"]["meta"],
        current_profile["source"]["address"],
    )

    article_text, article_clear_text = extract_article_content(
        current_profile["scraping"]["content"], article_soup
    )

    article_clear_text = clean_text(article_clear_text)

    current_article = FullArticle(
        title=article_meta.title,
        description=article_meta.description,
        image_url=HttpUrl(article_meta.image_url),
        publish_date=article_meta.publish_date,
        author=article_meta.author,
        url=HttpUrl(url),
        profile=current_profile["source"]["profile_name"],
        source=current_profile["source"]["name"],
        content=article_clear_text,
        formatted_content=custom_md_converter(heading_close="closed_atx").convert(
            article_text
        ),
        tags={
            "automatic": generate_tags(tokenize_text(article_clear_text)),
            "interresting": locate_objects_of_interrest(article_clear_text),
        },
    )

    return current_article


def scrape_using_profile(article_url_list: list[str], profile_name: str) -> None:
    logger.info(
        f'Scraping {len(article_url_list)} articles using the "{profile_name}" profile.'
    )

    # Loading the profile for the current website
    current_profile = get_profile(profile_name)

    for i, url in enumerate(article_url_list):
        logger.debug(
            f'Scraping article number {i + 1} with the types "{current_profile["scraping"]["type"]}" and following URL: {url}.'
        )
        try:
            current_article = handle_single_article(url, current_profile)
            config_options.es_article_client.save_document(current_article)
        except ValidationError as e:
            logger.error(
                f'Encountered problem with article with URL "{url}", skipping for now. Error: {e}'
            )


def scrape_articles() -> None:
    logger.debug("Scraping articles from frontpages and RSS feeds")
    article_url_collection = gather_article_urls(get_profiles())

    logger.debug(
        "Removing those articles that have already been stored in the database"
    )

    filtered_article_url_collection: dict[str, list[str]] = {}

    for articles_source in article_url_collection:
        filtered_article_url_collection[
            articles_source
        ] = config_options.es_article_client.filter_document_list(
            article_url_collection[articles_source]
        )

    article_number_after_filter = sum(
        [
            len(filtered_article_url_collection[profile_name])
            for profile_name in filtered_article_url_collection
        ]
    )

    if article_number_after_filter == 0:
        logger.info("All articles seems to have already been stored, exiting.")
        return
    else:
        logger.info(
            f"Found {article_number_after_filter} articles left to scrape, will begin that process now"
        )

    # Looping through the list of articles from specific news site in the list of all articles from all sites
    for profile_name in filtered_article_url_collection:
        scrape_using_profile(
            filtered_article_url_collection[profile_name], profile_name
        )