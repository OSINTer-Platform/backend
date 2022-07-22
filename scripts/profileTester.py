#!/usr/bin/python3

import os

from modules import *
from scripts.scrapeAndStore import handleSingleArticle, gatherArticleURLs
from scripts import configOptions


def main(profileName, customURL=""):
    currentProfile = profiles.getProfiles(profileName)

    if customURL:
        articleURLCollection = [customURL]
    else:
        articleURLCollection = gatherArticleURLs([currentProfile])[profileName]

    articles = []
    for URL in articleURLCollection:
        configOptions.logger.info(f"Scraping article with URL: {URL}")
        articles.append(handleSingleArticle(URL, currentProfile))

    articleString = ""

    for article in articles:
        os.system(f"firefox {article.url}")
        articleString += files.convertArticleToMD(article).getvalue() + "\n\n"

    with open("./articles.md", "w") as f:
        f.write(articleString)


if __name__ == "__main__":
    main()
