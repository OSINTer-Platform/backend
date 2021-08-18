#!/usr/bin/python3

# The name of your obsidian vault
obsidianVault = ""
# The absolute path to your obsidian vault
vaultPath = ""

# For recognize the os
import sys

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

# Function checking whether the variables specifying which obsidian vault to use is set
def checkIfObsidianDetailsSet():
    if obsidianVault == "" or vaultPath == "":
        raise Exception("You need to specify which Obsidian vault to use, and the path to it. These details are defined in the very part of the script as variables.")

def openURILocally(URI):
    # And lastly open the file in obsidian by using an URI along with the open command for the currently used OS
    platform = sys.platform

    if platform.startswith('linux'):
        openCommand = "xdg-open '" + URI + "'"
    elif platform.startswith('win32'):
        openCommand = "start '" + URI + "'"
    elif platform.startswith('darwin'):
        openCommand = "open '" + URI + "'"
    elif platform.startswith('cygwin'):
        openCommand = "cygstart '" + URI + "'"
    else:
        raise Exception("Unfortunatly, your system isn't support. You should be running a new version of Windows, Mac or Linux.")

    os.system(openCommand)

def handleSingleArticle(vaultName, vaultPath, profileName, articleSource, articleURL):

    openURILocally(articleURL)

    # Load the profile for the article
    currentProfile = json.loads(getProfiles(profileName))

    # Gather the needed information from the article
    articleDetails, articleContent, articleClearText = OSINTextract.extractAllDetails(currentProfile, articleSource)

    # Generate the tags
    articleTags = OSINTtext.generateTags(OSINTtext.cleanText(articleClearText))

    # Create the markdown file
    MDFileName = OSINTfiles.createMDFile(currentProfile['source']['name'], articleURL, articleDetails, articleContent, articleTags)
    os.rename(str(Path(MDFileName).resolve()) + ".md", str(Path(vaultPath + MDFileName)) + ".md")


def main():
    checkIfObsidianDetailsSet()
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
