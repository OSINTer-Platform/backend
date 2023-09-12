import logging

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
import typer

from modules.elastic import ES_INDEX_CONFIGS

from .. import config_options

import typer

logger = logging.getLogger("osinter")


app = typer.Typer()


@app.command()
def init_db() -> None:
    logger.info("Configuring elasticsearch")
    es_index_client = IndicesClient(config_options.es_conn)

    for index_name in ES_INDEX_CONFIGS:
        logger.info(f'Creating "{index_name}" index')
        try:
            es_index_client.create(
                index=config_options[index_name],
                mappings=ES_INDEX_CONFIGS[index_name],
            )
        except BadRequestError as e:
            if e.status_code != 400 or e.error != "resource_already_exists_exception":
                raise e
            else:
                logger.info(f'The index "{index_name}" already exists, skipping.')
