import logging

from .articles import scrape_articles


logger = logging.getLogger("osinter")


def main():
    for scraping_function in [scrape_articles]:
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
