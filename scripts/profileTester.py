#!/usr/bin/python3

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

from scripts.scrapeAndStore import scrapeUsingProfile

# Function checking whether the variables specifying which obsidian vault to use is set
def checkIfObsidianDetailsSet():
    if vaultPath == "":
        raise Exception("You need to specify the path to your obsidian vault. This is defined in the very start of the script as a variable.")


def main():
    checkIfObsidianDetailsSet()
    profile = input("Which profile do you want to test? ")
    articleURLLists = OSINTscraping.gatherArticleURLs([getProfiles(profile)])
    OGTagCollection = OSINTtags.collectAllOGTags(articleURLLists)[profile]
    for articleCollection in OGTagCollection:
        os.system(f"firefox {articleCollection['url']}")
    scrapeUsingProfile(OGTagCollection, profile, articlePath=vaultPath)

if __name__ == "__main__":
    main()
