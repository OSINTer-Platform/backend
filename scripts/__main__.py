from scripts.scrape_and_store import main as scrape
from scripts.profile_tester import main as profile_tester

from . import config_options
from .elastic import app as elastic_app

from modules.config import configure_elasticsearch
from modules.misc import download_driver, extract_driver_url, decode_keywords_file
from modules.profiles import get_profiles

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
    configure_elasticsearch(config_options)

@app.command()
def profile_tester():
    profile_list: list[str] = profiles.get_profiles(just_names=True)

    print("Available profiles:")

    for i, profile_name in enumerate(profile_list):
        print(f"{str(i)}: {profile_name}")

    profile: str = profile_list[int(typer.prompt("Which profile do you want to test? "))]

    url: str = typer.prompt("Enter specific URL or leave blank for scraping 10 urls by itself")

    profile_tester(profile, url)

@app.command()
def verify_keywords():
    if os.path.isdir(os.path.join("tools", "keywords")):
        for file in os.listdir(os.path.join("tools" "keywords")):
            current_keywords = decode_keywords_file(
                os.path.join("tools", "keywords", "{file}")
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
