#!/usr/bin/python3

try:
    # For if the user wants verbose output
    from __main__ import debugMessages
except:
    debugMessages = True

# Used for creating a connection to the database
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

import os
from pathlib import Path
import requests
import json
# For decompressing the geckodriver that comes compressed in the .tar.gz format when downloading it
import tarfile

from OSINTmodules import OSINTdatabase
from OSINTmodules.OSINTmisc import printDebug

postgresqlPassword = ""

def createFolder(folderName):
    if not os.path.isdir(Path("./" + folderName)):
        try:
            os.mkdir(Path("./" + folderName))
        except:
            # This shoudln't ever be reached, as it would imply that the folder doesn't exist, but the script also is unable to create it. Could possibly be missing read permissions if the scripts catches this exception
            raise Exception("The folder {} couldn't be created, exiting".format(folderName))

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

def saveCredential(fileName, filePerms, password):
    with os.fdopen(os.open(Path("./credentials/{}.password".format(fileName)), os.O_WRONLY | os.O_CREAT, int(filePerms)), 'w') as file:
        file.write(password)

def main():

    printDebug("Downloading and extracting the geckodriver...")

    downloadDriver(extractDriverURL())

    printDebug("Creating the folders for storing the scraped articles and logs...")

    for folder in ['articles', 'logs', 'credentials']:
        createFolder(folder)

    printDebug("Creating the \"osinter\" postgresql database...")

    # Connecting to the database
    conn = psycopg2.connect("user=postgres")

    # Needed ass create database cannot be run within transaction
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

    # Creating a new database
    with conn.cursor() as cur:
        try:
            cur.execute("CREATE DATABASE osinter;")
            printDebug("Database created.")
        except psycopg2.errors.DuplicateDatabase:
            printDebug("Database already exists, skipping.")

    conn.close()

    printDebug("Creating a new superuser in the new database.")

    # Connecting to the newly created database
    conn = psycopg2.connect("dbname=osinter user=postgres")

    # Create the new users, and switch the connection to the new super user in the process
    adminPassword, conn = OSINTdatabase.initiateAdmin(conn)

    printDebug("Writing the superuser credential to disk")

    saveCredential("admin", 0o000, adminPassword)

    printDebug("Creating the needed \"article\" table...")
    # Making sure the database has gotten the needed table(s)
    if OSINTdatabase.initiateArticleTable(conn):
        printDebug("The \"article\" table has been created.")
    else:
        printDebug("The \"article\" table already exists, skipping.")

    printDebug("Creating the other needed users")

    writerPassword = OSINTdatabase.initiateUsers(conn)

    printDebug("Writing the password for the writer user to disk")

    saveCredential("writer", 0o400, writerPassword)

if __name__ == "__main__":
    main()
