import logging
from modules.profiles import get_profile

from scripts.profile_tester import calculate_profile, get_profile_prompt
from scripts.scraping.articles import (
    gather_profile_urls,
    scrape_articles,
    scrape_using_profile,
)
from scripts import config_options

import typer


app = typer.Typer()
logger = logging.getLogger("osinter")


@app.command()
def main() -> None:
    for scraping_function in [scrape_articles]:
        try:
            logger.info(f'Running the "{scraping_function.__name__}" function.')
            scraping_function()

        except Exception as e:
            logger.critical(
                f'Critical error prevented running the "{scraping_function.__name__}". Error: {e}',
                exc_info=True,
            )


@app.command()
def timetravel(
    profile: str = typer.Option(
        ..., prompt=get_profile_prompt(), callback=calculate_profile
    ),
    url: str = typer.Option(prompt="Enter URL with % for substitution of page number"),
    start_page: int = 2,
    batch_size: int = 5,
) -> None:
    if not "%" in url:
        raise Exception("Need a % for substituting the page number")

    current_profile = get_profile(profile)

    while True:
        logger.info(f"Scraping page {start_page} to {start_page + batch_size}")

        frontpage_urls = [
            url.replace("%", str(i)) for i in range(start_page, start_page + batch_size)
        ]

        urls = gather_profile_urls(current_profile, 1000, frontpage_urls)

        logger.debug(
            "Removing those articles that have already been stored in the database"
        )

        filtered_urls = config_options.es_article_client.filter_document_list(urls)
        scrape_using_profile(filtered_urls, profile)

        start_page += batch_size
