#!/usr/bin/python3

from pathlib import Path

import scripts
from scripts import *
from scripts.elastic import *


def selectScript(scriptNames):
    print("Which script do you want ro run?")

    for i, script in enumerate(scriptNames):
        print(f"{str(i)}. {script[1]}")

    try:
        scriptNumber = int(input("Write a number: "))
    except:
        print("It doesn't look like you entered a number.")
        exit()

    try:
        return scriptNames[scriptNumber][0]
    except IndexError:
        print(
            f"The number you entered doesn't correspond to a script, it should be between 0 and {len(scriptNames) - 1}"
        )
        exit()


def main():
    scriptNames = [
        ("initiateScrapingBackend", "Intiate the OSINTer backend"),
        ("profileTester", "Test a profile"),
        ("scrapeAndStore", "Scrape articles based on available profiles"),
        ("scrapePriorZdnetArticles", "Scrape old ZDNet articles"),
        ("verifyKeywordFiles", "Verify the available keyword files"),
        ("elastic", "Run a series of elasticsearch-based scripts"),
    ]

    scriptName = selectScript(scriptNames)

    if scriptName == "profileTester":
        from OSINTmodules import OSINTprofiles

        profileList = OSINTprofiles.getProfiles(justNames=True)

        print("Available profiles:")

        for i, profileName in enumerate(profileList):
            print(f"{str(i)}: {profileName}")

        profile = profileList[int(input("Which profile do you want to test? "))]

        url = input(
            "Enter specific URL or leave blank for scraping 10 urls by itself: "
        )

        scripts.profileTester.main(profile, url)
        exit()

    elif scriptName == "elastic":
        elasticScriptNames = [
            ("download", "Download articles from remote cluster"),
            (
                "articlesToJSON",
                "Export the OSINTer article index as json object to file",
            ),
            ("JSONToArticles", "Import OSINTer article index as json object from file"),
            ("articlesToMD", "Export all articles as markdown files"),
        ]
        elasticScriptName = selectScript(elasticScriptNames)

        if elasticScriptName == "download":
            remoteEsAddress = input(
                "Please enter the full URL (with read access) of the remote Elasticsearch cluster: "
            )
            scripts.elastic.download.main(remoteEsAddress)
            exit()
        elif elasticScriptName in ["JSONToArticles", "articlesToJSON", "articlesToMD"]:
            filePath = Path(
                input(
                    "Please enter the absolute or relative path to the export file/dir: "
                )
            ).resolve()
            eval(f"scripts.{scriptName}.{elasticScriptName}.main(filePath)")
            exit()

        eval(f"scripts.{scriptName}.{elasticScriptName}.main()")
        exit()

    eval(f"scripts.{scriptName}.main()")


if __name__ == "__main__":
    main()
