import json
import logging
import os
import tarfile

from elasticsearch import BadRequestError
from elasticsearch.client import IndicesClient
import requests
import typer

from modules.elastic import ES_INDEX_CONFIGS
from modules.misc import create_folder, decode_keywords_file
from modules.profiles import list_profiles
from scripts.profile_tester import main as profile_tester
from scripts.scraping import main as scrape

from . import config_options
from .elastic import app as elastic_app

logger = logging.getLogger("osinter")


app = typer.Typer(no_args_is_help=True)
app.add_typer(elastic_app, name="elastic", no_args_is_help=True)


@app.command()
def initiate_db() -> None:

    # Mozilla will have an api endpoint giving a lot of information about the latest releases for the geckodriver, from which the url for the linux 64 bit has to be extracted
    def extract_driver_url():
        driver_details = json.loads(
            requests.get(
                "https://api.github.com/repos/mozilla/geckodriver/releases/latest"
            ).text
        )

        for platform_release in driver_details["assets"]:
            if platform_release["name"].endswith("linux64.tar.gz"):
                return platform_release["browser_download_url"]

    # Downloading and extracting the .tar.gz file the geckodriver is stored in into the tools directory
    def download_driver(driver_url):
        driver_contents = requests.get(driver_url, stream=True)
        with tarfile.open(fileobj=driver_contents.raw, mode="r|gz") as driver_file:
            driver_file.extractall(path=os.path.normcase("./tools/"))
        logger.info("Downloading and extracting the geckodriver...")

    create_folder("tools")

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
                logger.info(f"The {index_name} already exists, skipping.")


def get_profile_list() -> list[str]:
    profile_list: list[str] = list_profiles()
    profile_list.sort()

    return profile_list


def get_profile_prompt() -> str:
    profile_list: list[str] = get_profile_list()

    ret_val: str = ""

    for i, profile_name in enumerate(profile_list):
        ret_val += f"{str(i)}: {profile_name}\n"

    ret_val += "Available profiles"

    return ret_val


def calculate_profile(value: str) -> str:
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
) -> None:

    profile_tester(profile, url)


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
