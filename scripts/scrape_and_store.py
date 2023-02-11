from datetime import datetime, timezone
import logging
import os
from typing import Any, cast

from bs4 import BeautifulSoup as bs
from markdownify import MarkdownConverter
from pydantic import HttpUrl, ValidationError
from searchtweets import load_credentials

from modules import text
from modules.extract import extract_article_content, extract_meta_information
from modules.misc import decode_keywords_file
from modules.objects import FullArticle
from modules.profiles import get_profile, get_profiles
from modules.scraping import (
    get_article_urls_from_rss,
    scrape_article_urls,
    scrape_page_dynamic,
)
from scripts import config_options

logger = logging.getLogger("osinter")


class custom_md_converter(MarkdownConverter):
    def convert_figure(self, el, text, convert_as_inline): # pyright: ignore
        self.process_tag(el, False, children_only=True)
        return text + "\n\n"

    def convert_a(self, el, text, convert_as_inline):
        try:
            del el["title"]
        except KeyError:
            pass

        return super().convert_a(el, text, convert_as_inline)


# Function for gathering list of URLs for articles from newssite
def gather_article_urls(profiles) -> dict[str, list[str]]:

    article_urls = {}

    for profile in profiles:

        logger.debug(
            f'Gathering URLs for the "{(profile_name := profile["source"]["profile_name"])}" profile.'
        )

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
            else:
                raise NotImplementedError

        except Exception as e:
            logger.exception(
                f'Problem with gathering URLs for the "{profile_name}" profile. Skipping for now. Error {e}'
            )

    return article_urls


def handle_single_article(url: str, current_profile: dict[str, Any]) -> FullArticle:

    # Scrape the whole article source based on how the profile says
    scraping_types: list[str] = current_profile["scraping"]["type"].split(";")
    articles_source = scrape_page_dynamic(url, scraping_types)
    article_soup = bs(articles_source, "html.parser")

    article_meta_information = extract_meta_information(
        article_soup,
        current_profile["scraping"]["meta"],
        current_profile["source"]["address"],
    )

    current_article = FullArticle(
        url=cast(HttpUrl, url),
        profile=current_profile["source"]["profile_name"],
        source=current_profile["source"]["name"],
        **article_meta_information.dict(),
    )

    article_text, article_clear_text = extract_article_content(
        current_profile["scraping"]["content"], article_soup
    )

    article_clear_text = text.clean_text(article_clear_text)

    current_article.content = article_clear_text
    current_article.formatted_content = custom_md_converter(
        heading_style="closed_atx"
    ).convert(article_text)

    # Generate the tags
    current_article.tags["automatic"] = text.generate_tags(
        text.tokenize_text(article_clear_text)
    )
    current_article.tags["interresting"] = text.locate_objects_of_interrest(
        article_clear_text
    )
    current_article.tags["manual"] = {}

    if os.path.isdir(os.path.normcase("./tools/keywords/")):
        for filename in os.listdir(os.path.normcase("./tools/keywords/")):
            current_tags = text.locate_keywords(
                decode_keywords_file(os.path.normcase(f"./tools/keywords/{filename}")),
                article_clear_text,
            )
            if current_tags != []:
                current_article.tags["manual"][filename] = current_tags

    current_article.inserted_at = datetime.now(timezone.utc)

    return current_article


def scrape_using_profile(article_url_list: list[str], profile_name: str) -> None:
    logger.info(
        f'Scraping {len(article_url_list)} articles using the "{profile_name}" profile.'
    )

    # Loading the profile for the current website
    current_profile = get_profile(profile_name)

    for i, url in enumerate(article_url_list):
        logger.debug(
            f'Scraped article number {i + 1} with the types "{current_profile["scraping"]["type"]}" and following URL: {url}.'
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


def gather_tweets(major_author_list, credentials, chunck_size=10):
    chuncked_author_list = [
        major_author_list[i : i + chunck_size]
        for i in range(0, len(major_author_list), chunck_size)
    ]

    tweets = []

    for author_list in chuncked_author_list:
        logger.debug(f"Scraping tweets for these authors: {' '.join(author_list)}")
        try:
            last_id = config_options.es_tweet_client.get_last_document(
                author_list
            ).twitter_id
            tweet_data = twitter.gather_tweet_data(credentials, author_list, last_id)
        except AttributeError:
            logger.debug("These are the first tweets by these authors.")
            tweet_data = twitter.gather_tweet_data(credentials, author_list)

        if tweet_data:
            logger.debug("Converting twitter data to python objects.")
            for tweet in twitter.process_tweet_data(tweet_data):
                tweets.append(objects.FullTweet(**tweet))
        else:
            logger.debug("No tweets was found.")
            return []

    return tweets


def scrape_tweets(author_list_path=os.path.normcase("./tools/twitter_authors")):
    logger.debug("Trying to load twitter credentials and authorlist.")
    if os.path.isfile(author_list_path) and os.path.isfile(
        config_options.TWITTER_CREDENTIAL_PATH
    ):
        credentials = load_credentials(
            config_options.TWITTER_CREDENTIAL_PATH,
            yaml_key="search_tweets_v2",
            env_overwrite=False,
        )

        author_list = []

        with open(author_list_path, "r") as f:
            for line in f.readlines():
                # Splitting by # to allow for comments
                author_list.append(line.split("#")[0].strip())

        logger.debug("Succesfully loaded twitter credentials and authorlist.")

        tweet_list = gather_tweets(author_list, credentials)

        logger.debug("Saving the tweets.\n")
        for tweet in tweet_list:
            config_options.es_tweet_client.save_document(tweet)

    else:
        logger.debug("Couldn't load twitter credentials and authorlist.\n")


def main():

    for scraping_function in [scrape_tweets, scrape_articles]:
        try:
            logger.info(f'Running the "{scraping_function.__name__}" function.')
            scraping_function()

        except Exception as e:
            logger.critical(
                f'Critical error prevented running the "{scraping_function.__name__}". Error: {e}',
                exc_info=True,
            )


if __name__ == "__main__":
    main()
