#!/usr/bin/python3

from pathlib import Path

import scripts
from scripts import *
from scripts.elastic import *


def select_script(script_names):
    print("Which script do you want ro run?")

    for i, script in enumerate(script_names):
        print(f"{str(i)}. {script[1]}")

    try:
        script_number = int(input("Write a number: "))
    except:
        print("It doesn't look like you entered a number.")
        exit()

    try:
        return script_names[script_number][0]
    except IndexError:
        print(
            f"The number you entered doesn't correspond to a script, it should be between 0 and {len(script_names) - 1}"
        )
        exit()


def main():
    script_names = [
        ("initiate_scraping_backend", "Intiate the OSINTer backend"),
        ("profile_tester", "Test a profile"),
        ("scrape_and_store", "Scrape articles based on available profiles"),
        ("verify_keyword_files", "Verify the available keyword files"),
        ("elastic", "Run a series of elasticsearch-based scripts"),
    ]

    script_name = select_script(script_names)

    if script_name == "profile_tester":
        from modules import profiles

        profile_list = profiles.get_profiles(just_names=True)

        print("Available profiles:")

        for i, profile_name in enumerate(profile_list):
            print(f"{str(i)}: {profile_name}")

        profile = profile_list[int(input("Which profile do you want to test? "))]

        url = input(
            "Enter specific URL or leave blank for scraping 10 urls by itself: "
        )

        scripts.profile_tester.main(profile, url)
        exit()

    elif script_name == "elastic":
        elastic_script_names = [
            ("download", "Download articles from remote cluster"),
            (
                "articles_to_json",
                "Export the OSINTer article index as json object to file",
            ),
            (
                "json_to_articles",
                "Import OSINTer article index as json object from file",
            ),
            ("articles_to_md", "Export all articles as markdown files"),
        ]
        elastic_script_name = select_script(elastic_script_names)

        if elastic_script_name == "download":
            remote_es_address = input(
                "Please enter the full URL (with read access) of the remote Elasticsearch cluster: "
            )
            scripts.elastic.download.main(remote_es_address)
            exit()
        elif elastic_script_name in [
            "json_to_articles",
            "articles_to_json",
            "articles_to_md",
        ]:
            file_path = Path(
                input(
                    "Please enter the absolute or relative path to the export file/dir: "
                )
            ).resolve()
            eval(f"scripts.{script_name}.{elastic_script_name}.main(file_path)")
            exit()

        eval(f"scripts.{script_name}.{elastic_script_name}.main()")
        exit()

    eval(f"scripts.{script_name}.main()")


if __name__ == "__main__":
    main()
