from collections.abc import Mapping
import logging
from typing import Any
from dotenv import set_key

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient, IngestClient, MlClient
import typer

from modules.elastic import ES_INDEX_CONFIGS

from .utils import get_user_yes_no
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
                logger.info(f'The index "{index_name}" already exists.')

                update_mapping = get_user_yes_no(
                    "Index already exists. Do you want to attempt to update the mapping?"
                )
                if not update_mapping:
                    continue

                try:
                    es_index_client.put_mapping(
                        index=config_options[index_name],
                        properties=ES_INDEX_CONFIGS[index_name]["properties"],
                    )
                    logger.debug(f'Succesfully updated mappings for "{index_name}".')
                except BadRequestError:
                    logger.exception("Updating mapping failed")


@app.command()
def init_elser(model_id: str = ".elser_model_2", current: bool = True) -> None:
    FIELDS_TO_TOKENIZE = ["title", "description", "content"]
    ELSER_INDEX_NAME = config_options.ELASTICSEARCH_ARTICLE_INDEX + (
        "" if current else "_elser"
    )
    ELSER_PIPELINE_NAME = "add-elser"

    es_ml_client = MlClient(config_options.es_conn)
    es_ingest_client = IngestClient(config_options.es_conn)
    es_index_client = IndicesClient(config_options.es_conn)

    logger.info("Setting up pipeline and new index for use with ELSER")
    logger.debug(f'Checking for running model by id "{model_id}"')

    for trained_model in es_ml_client.get_trained_models_stats()["trained_model_stats"]:
        if trained_model["model_id"] == model_id:
            if "deployment_stats" not in trained_model:
                raise Exception(
                    f'Model with id "{model_id}" found, but it isn\'t running'
                )
            break
    else:
        raise Exception(f'No running model with id "{model_id}" found')

    logger.debug("Model found")

    logger.debug("Creating ingest pipeline for adding elser")
    processors: list[Mapping[str, Any]] = []

    for field_name in FIELDS_TO_TOKENIZE:
        processors.append(
            {
                "remove": {
                    "field": f"elastic_ml.{field_name}_tokens",
                    "ignore_missing": True,
                }
            }
        )

        processors.append(
            {
                "inference": {
                    "model_id": model_id,
                    "target_field": "elastic_ml",
                    "field_map": {field_name: "text_field"},
                    "inference_config": {
                        "text_expansion": {"results_field": f"{field_name}_tokens"}
                    },
                }
            }
        )

    es_ingest_client.put_pipeline(
        id=ELSER_PIPELINE_NAME,
        processors=processors,
    )

    logger.debug("Creating new index to fit tokens")

    ARTICLE_INDEX = ES_INDEX_CONFIGS["ELASTICSEARCH_ARTICLE_INDEX"]

    ARTICLE_INDEX["properties"]["elastic_ml"] = {
        "type": "object",
        "properties": {
            f"{field_name}_tokens": {"type": "rank_features"}
            for field_name in FIELDS_TO_TOKENIZE
        },
    }

    try:
        es_index_client.create(
            index=ELSER_INDEX_NAME,
            mappings=ARTICLE_INDEX,
        )
    except BadRequestError as e:
        if e.status_code != 400 or e.error != "resource_already_exists_exception":
            raise e
        else:
            es_index_client.put_mapping(
                index=ELSER_INDEX_NAME, properties=ARTICLE_INDEX["properties"]
            )

    logger.warning(
        "Writting details to env file, REMEMBER TO COPY NEW ENV DETAILS TO API DEPLOYMENT"
    )
    set_key(".env", "ARTICLE_INDEX", ELSER_INDEX_NAME)
    set_key(".env", "ELSER_PIPELINE", ELSER_PIPELINE_NAME)
    set_key(".env", "ELSER_ID", model_id)

    logger.info("Starting to reindinx old articles into new index using ELSER")

    task_id = config_options.es_conn.reindex(
        source={
            "index": config_options.ELASTICSEARCH_ARTICLE_INDEX,
            "size": 50,
        },
        dest={"index": ELSER_INDEX_NAME, "pipeline": ELSER_PIPELINE_NAME},
        wait_for_completion=False,
    )["task"]

    config_options.es_article_client.await_task(
        task_id,
        "batches",
        lambda status: f"Creating batch nr {status['batches']} totalling {status['updated']} updated articles and {status['created']} created articles out of {status['total']} total articles",
    )
