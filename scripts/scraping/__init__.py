import logging

from .articles import scrape_articles
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
