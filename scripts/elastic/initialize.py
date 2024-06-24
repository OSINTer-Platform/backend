from collections.abc import Mapping
import logging
from typing import Any
from dotenv import set_key

from elasticsearch import BadRequestError
from elasticsearch.client import (
    IndicesClient,
    IngestClient,
    MlClient,
    SearchApplicationClient,
)
import typer

from modules.elastic import ES_INDEX_CONFIGS, ES_SEARCH_APPLICATIONS

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
def init_elser(
    model_id: str = config_options.ELASTICSEARCH_ELSER_ID or ".elser_model_2",
    pipeline_name: str = "add-elser",
) -> None:
    es_ml_client = MlClient(config_options.es_conn)
    es_ingest_client = IngestClient(config_options.es_conn)

    logger.info("Verifying a running ELSER instance and setting up pipeline")
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
    processors: list[Mapping[str, Any]] = [
        {
            "foreach": {
                "field": "embeddings.content_chunks",
                "processor": {
                    "remove": {"field": "_ingest._value.elser", "ignore_missing": True}
                },
                "if": 'ctx?.embeddings?.containsKey("content_chunks")',
                "description": "Remove empty fields",
            }
        },
        {
            "foreach": {
                "field": "embeddings.content_chunks",
                "processor": {
                    "inference": {
                        "model_id": model_id,
                        "target_field": "_ingest._value.elser",
                        "field_map": {"_ingest._value.text": "text_field"},
                        "inference_config": {
                            "text_expansion": {"results_field": "tokens"}
                        },
                        "description": "Runs elser",
                    }
                },
                "if": 'ctx?.embeddings?.containsKey("content_chunks")',
            }
        },
    ]

    embedding_fields = ["title", "description"]

    processors.append(
        {
            "remove": {
                "field": [
                    f"embeddings.{field_name}.elser" for field_name in embedding_fields
                ],
                "ignore_missing": True,
            }
        }
    )

    for field_name in embedding_fields:
        processors.append(
            {
                "inference": {
                    "model_id": model_id,
                    "target_field": f"embeddings.{field_name}.elser",
                    "field_map": {field_name: "text_field"},
                    "inference_config": {"text_expansion": {"results_field": "tokens"}},
                }
            }
        )

    es_ingest_client.put_pipeline(
        id=pipeline_name,
        processors=processors,
    )

    logger.warning(
        "Writting details to env file, REMEMBER TO COPY NEW ENV DETAILS TO API DEPLOYMENT"
    )
    set_key(".env", "ELSER_PIPELINE", pipeline_name)
    set_key(".env", "ELSER_ID", model_id)


@app.command()
def init_search_apps(article_app_name: str = "osinter-articles") -> None:
    es_search_app_client = SearchApplicationClient(config_options.es_conn)

    es_search_app_client.put(
        name=article_app_name,
        search_application={
            "indices": [config_options.ELASTICSEARCH_ARTICLE_INDEX],
            "template": ES_SEARCH_APPLICATIONS["ARTICLES"]["template"],
        },
    )
