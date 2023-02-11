import logging
import os

from searchtweets import load_credentials

from modules.objects import FullTweet
from modules.twitter import gather_tweet_data, process_tweet_data
from scripts import config_options

logger = logging.getLogger("osinter")


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
            tweet_data = gather_tweet_data(credentials, author_list, last_id)
        except AttributeError:
            logger.debug("These are the first tweets by these authors.")
            tweet_data = gather_tweet_data(credentials, author_list)

        if tweet_data:
            logger.debug("Converting twitter data to python objects.")
            for tweet in process_tweet_data(tweet_data):
                tweets.append(FullTweet(**tweet))
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
