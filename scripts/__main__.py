import logging

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
import typer

from modules.elastic import ES_INDEX_CONFIGS

from scripts.scraping import main as scrape

from . import config_options
from .elastic import app as elastic_app
from .profile_tester import app as profile_app

logger = logging.getLogger("osinter")


app = typer.Typer(no_args_is_help=True)
app.add_typer(elastic_app, name="elastic", no_args_is_help=True)
app.add_typer(profile_app, name="profile", no_args_is_help=True)


@app.command()
def initiate_db() -> None:
    logger.info("Configuring elasticsearch")
    es_index_client = IndicesClient(config_options.es_conn)

    for index_name in ES_INDEX_CONFIGS:
        try:
            es_index_client.create(
                index=config_options[index_name],
                mappings=ES_INDEX_CONFIGS[index_name],
            )
        except BadRequestError as e:
            if e.status_code != 400 or e.error != "resource_already_exists_exception":
                raise e
            else:
                logger.info(f"The {index_name} already exists, skipping.")

app.command("scrape")(scrape)


if __name__ == "__main__":
    app()
