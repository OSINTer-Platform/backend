import logging
import os
from typing import Literal

import typer

from rich.markdown import Markdown as MD
from rich.console import Console
from rich.table import Table

from modules.files import article_to_md
from modules.profiles import get_profile, get_profiles, list_profiles
from scripts.scraping.articles import (
    gather_profile_urls,
    gather_profiles_urls,
    handle_single_article,
)

logger = logging.getLogger("osinter")

app = typer.Typer()
console = Console()


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


def profile_tester(profile_name: str, custom_url: str = "") -> None:
    current_profile = get_profile(profile_name)

    if custom_url:
        article_url_collection = [custom_url]
    else:
        article_url_collection = gather_profile_urls(current_profile, 10)

    articles = []
    for url in article_url_collection:
        logger.info(f"Scraping article with URL: {url}")

        try:
            articles.append(handle_single_article(url, current_profile))
        except Exception:
            logger.exception(
                f'Encountered problem with article with URL "{url}", skipping for now'
            )

    article_string = ""

    for article in articles:
        os.system(f"firefox {article.url}")
        article_string += article_to_md(article) + "\n\n"

    with open("./articles.md", "w") as f:
        f.write(article_string)


@app.command()
def verify_profiles() -> None:
    profiles = get_profiles()

    injection_lists = [profile.scraping.js_injections for profile in profiles]
    injections = [injection for sublist in injection_lists for injection in sublist]

    for injection_name in injections:
        path = os.path.normcase(f"./profiles/js_injections/{injection_name}.js")
        if not os.path.exists(path):
            raise Exception(f"JS Injection {injection_name} not found")

    print("All profiles and JS injections are present and correct")


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


@app.command()
def auto_test(
    size: str = typer.Option(
        "small",
        prompt="Would you like a small or large automated test?",
        help='Size of automated test, should be "small" or "large"',
    )
) -> None:
    while size != "small" and size != "large":
        size = input('Please enter a "small" or "large"')

    console.print(MD("# Auto test commencing"))
    console.print(MD("# *Collecting article URLs*"))

    article_url_collection = gather_profiles_urls(get_profiles())

    url_count_table = Table("Profile", "URL Count")
    for profile in sorted(article_url_collection):
        url_count_table.add_row(
            profile, f"{len(article_url_collection[profile])} articles"
        )

    console.print(MD("## URL count for profiles"))
    console.print(url_count_table)

    if size == "small":
        return

    console.print(MD("# *Scraping articles for large test*"))
    article_success: dict[str, dict[Literal["success", "failure"], int]] = {}

    for profile_name in article_url_collection.keys():
        console.print(MD(f"### Gathering articles for {profile_name}"))

        current_profile = get_profile(profile_name)
        article_success[profile_name] = {"success": 0, "failure": 0}

        for i, url in enumerate(article_url_collection[profile_name]):
            console.print(MD(f"*Article nr {i} on {url}*"))
            try:
                handle_single_article(url, current_profile)
                article_success[profile_name]["success"] += 1
            except:
                article_success[profile_name]["failure"] += 1

    success_table = Table("Profile", "Success", "Failure")
    for profile_name in sorted(article_url_collection):
        success_table.add_row(
            profile_name,
            str(article_success[profile_name]["success"]),
            str(article_success[profile_name]["failure"]),
        )

    console.print(MD("## Success count for profile"))
    console.print(success_table)
