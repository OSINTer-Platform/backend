#!/usr/bin/python3

# The name of your obsidian vault
obsidianVault = "Testing"
# The absolute path to your obsidian vault
vaultPath = "/home/bertmad/Obsidian/Testing/"


import os

# Mainly used for sleeping
import time

# The profiles mapping the different websites are in json format
import json

# Used for detecting when the user closes the web driver
import selenium

from pathlib import Path

debugMessages = True

from OSINTmodules.OSINTprofiles import getProfiles
from OSINTmodules import *

def handleSingleArticle(vaultName, vaultPath, profileName, articleSource, articleURL):

    OSINTlocal.openURILocally(articleURL)

    # Load the profile for the article
    currentProfile = json.loads(getProfiles(profileName))

    # Gather the needed information from the article
    articleDetails, articleContent, articleClearText = OSINTextract.extractAllDetails(currentProfile, articleSource)

    # Generate the tags
    articleTags = OSINTtext.generateTags(OSINTtext.cleanText(articleClearText))

    # Create the markdown file
    MDFileName = OSINTfiles.createMDFile(currentProfile['source']['name'], articleURL, articleDetails, articleContent, articleTags)
    os.rename(Path(MDFileName).resolve(), Path(vaultPath + MDFileName))


def main():
    profile = input("Which profile do you want to test? ")
    articleURLLists = OSINTscraping.gatherArticleURLs([getProfiles(profile)])

    for URLlist in articleURLLists:
        currentProfile = URLlist.pop(0)
        for url in URLlist:
            OSINTmisc.printDebug("Scraping: " + url)
            articleSource = OSINTscraping.scrapePageDynamic(url)
            handleSingleArticle(obsidianVault, vaultPath, currentProfile, articleSource, url)

if __name__ == "__main__":
    main()
