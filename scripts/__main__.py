from scripts.scrape_and_store import main as scrape
from scripts.profile_tester import main as profile_tester

from . import config_options
from .elastic import app as elastic_app

from modules.misc import download_driver, extract_driver_url, decode_keywords_file
from modules.profiles import get_profiles
from modules.elastic import ES_INDEX_CONFIGS

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient

import os

import logging

logger = logging.getLogger("osinter")

import typer

app = typer.Typer(no_args_is_help=True)
app.add_typer(elastic_app, name="elastic", no_args_is_help=True)


@app.command()
def initiate_db():
    logger.info("Downloading and extracting the geckodriver...")

    download_driver(extract_driver_url())

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
                logger.info(f'The {index_name} already exists, skipping.')


def get_profile_list() -> list[str]:
    profile_list: list[str] = get_profiles(just_names=True)
    profile_list.sort()

    return profile_list


def get_profile_prompt() -> str:
    profile_list: list[str] = get_profile_list()

    ret_val: str = ""

    for i, profile_name in enumerate(profile_list):
        ret_val += f"{str(i)}: {profile_name}\n"

    ret_val += "Available profiles"

    return ret_val


def calculate_profile(value: str):
    profile_list: list[str] = get_profile_list()

    try:
        return get_profile_list()[int(value)]
    except ValueError:
        if value in profile_list:
            return value
        else:
            raise typer.BadParameter(
                f'"{value}" was not recognized amongst the available profiles'
            )


@app.command()
def test_profile(
    profile: str = typer.Option(
        ..., prompt=get_profile_prompt(), callback=calculate_profile
    ),
    url: str = typer.Option(
        "", prompt="Enter specific URL or leave blank for scraping 10 urls by itself"
    ),
):

    profile_tester(profile, url)


@app.command()
def verify_keywords():
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
