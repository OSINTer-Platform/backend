import logging
import os

import typer

from modules.files import convert_article_to_md
from modules.profiles import get_profile, list_profiles
from scripts.scraping.articles import gather_article_urls, handle_single_article

logger = logging.getLogger("osinter")

app = typer.Typer()


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

def profile_tester(profile_name, custom_url=""):
    current_profile = get_profile(profile_name)

    if custom_url:
        article_url_collection = [custom_url]
    else:
        article_url_collection = gather_article_urls([current_profile])[profile_name]

    articles = []
    for url in article_url_collection:
        logger.info(f"Scraping article with URL: {url}")
        articles.append(handle_single_article(url, current_profile))

    article_string = ""

    for article in articles:
        os.system(f"firefox {article.url}")
        article_string += convert_article_to_md(article).getvalue() + "\n\n"

    with open("./articles.md", "w") as f:
        f.write(article_string)

@app.command()
def manual_test(
    profile: str = typer.Option(
        ..., prompt=get_profile_prompt(), callback=calculate_profile
    ),
    url: str = typer.Option(
        "", prompt="Enter specific URL or leave blank for scraping 10 urls by itself"
    ),
) -> None:

    profile_tester(profile, url)
