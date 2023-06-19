import logging
import os

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
import typer

from modules.elastic import ES_INDEX_CONFIGS
from modules.misc import decode_keywords_file

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


@app.command()
def verify_keywords() -> None:
    if os.path.isdir(os.path.join("tools", "keywords")):
        for file in os.listdir(os.path.join("tools", "keywords")):
            current_keywords = decode_keywords_file(
                os.path.join("tools", "keywords", file)
            )

            for keyword_collection in current_keywords:
                try:
                    test = [
                        keyword_collection["keywords"],
                        keyword_collection["tag"],
                        keyword_collection["proximity"],
                    ]

                    if (
                        not isinstance(test[2], int)
                        or not isinstance(test[1], str)
                        or not isinstance(test[0], list)
                    ):
                        print(f"Error with {keyword_collection}")
                except:
                    print(f"Error with {keyword_collection}")
    else:
        print("No ḱeyword files were found")


app.command("scrape")(scrape)


if __name__ == "__main__":
    app()
