#!/usr/bin/python3

import os
from time import sleep

from OSINTmodules import *
from scripts.scrapeAndStore import scrapeUsingProfile

import elasticsearch

configOptions = OSINTconfig.backendConfig()

esClient = OSINTelastic.elasticDB(configOptions.ELASTICSEARCH_URL, configOptions.ELASTICSEARCH_ARTICLE_INDEX)


def main():
    profileList = OSINTprofiles.getProfiles(justNames = True)

    print("Available profiles:")

    for i, profileName in enumerate(profileList):
        print(f"{str(i)}: {profileName}")

    profile = profileList[int(input("Which profile do you want to test? "))]

    url = input("Enter specific URL or leave blank for scraping 10 urls by itself: ")

    if url:
        articleURLCollection = {profile : [url]}
    else:
        articleURLCollection = OSINTscraping.gatherArticleURLs([OSINTprofiles.getProfiles(profile)])

    articleIDs = scrapeUsingProfile(articleURLCollection[profile], profile)

    sleep(1)

    currentArticles = esClient.searchArticles({"IDs" : articleIDs})

    for ID in articleIDs:
        os.system(f"firefox http://localhost:5000/renderMarkdownById/{ID}")

    for article in currentArticles["articles"]:
        os.system(f"firefox {article.url}")




if __name__ == "__main__":
    main()
