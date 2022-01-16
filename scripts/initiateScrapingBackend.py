#!/usr/bin/python3

try:
    # For if the user wants verbose output
    from __main__ import debugMessages
except:
    debugMessages = True

import os
from pathlib import Path
import requests
import json
# For decompressing the geckodriver that comes compressed in the .tar.gz format when downloading it
import tarfile

import sqlite3

from OSINTmodules import OSINTelastic
from OSINTmodules.OSINTmisc import printDebug

def createFolder(folderName):
    if not os.path.isdir(Path("./" + folderName)):
        try:
            os.mkdir(Path("./" + folderName), mode=0o750)
        except:
            # This shoudln't ever be reached, as it would imply that the folder doesn't exist, but the script also is unable to create it. Could possibly be missing read permissions if the scripts catches this exception
            raise Exception("The folder {} couldn't be created, exiting".format(folderName))
    else:
        try:
            os.chmod(Path("./" + folderName), 0o750)
        except:
            raise Exception("Failed to set the 750 permissions on {}, either remove the folder or set the right perms yourself and try again.".format(folderName))

# Mozilla will have an api endpoint giving a lot of information about the latest releases for the geckodriver, from which the url for the linux 64 bit has to be extracted
def extractDriverURL():
    driverDetails = json.loads(requests.get("https://api.github.com/repos/mozilla/geckodriver/releases/latest").text)

    for platformRelease in driverDetails['assets']:
        if platformRelease['name'].endswith("linux64.tar.gz"):
            return platformRelease['browser_download_url']

# Downloading and extracting the .tar.gz file the geckodriver is stored in into the tools directory
def downloadDriver(driverURL):
    driverContents = requests.get(driverURL, stream=True)
    with tarfile.open(fileobj=driverContents.raw, mode='r|gz') as driverFile:
        driverFile.extractall(path=Path("./tools/"))

def main():

    printDebug("Downloading and extracting the geckodriver...")

    downloadDriver(extractDriverURL())

    printDebug("Create folder for logs")

    createFolder("logs")

    printDebug("Configuring elasticsearch")
    esAddress = os.environ.get('ELASTICSEARCH_URL') or "http://localhost:9200"
    OSINTelastic.configureElasticsearch(esAddress, "osinter_articles")

if __name__ == "__main__":
    main()
