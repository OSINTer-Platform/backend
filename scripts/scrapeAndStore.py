#!/usr/bin/python3

# Used for creating a connection to the database
import psycopg2

# Used for loading the profile
import json

# Used for reading from file
from pathlib import Path

debugMessages = True

from OSINTmodules.OSINTprofiles import getProfiles
from OSINTmodules.OSINTmisc import printDebug
from OSINTmodules import *

def fromURLToMarkdown(URL, currentProfile, MDFilePath="./"):

    printDebug("\n", False)
    # Scrape the whole article source based on how the profile says
    if currentProfile['scraping']['type'] == "no-action":
        printDebug("No-action scraping: " + URL)
        articleSource = OSINTscraping.scrapePageDynamic(URL)
    else:
        raise Exception(profile['source']['name'] + " apparently didn't have a specified way of scraping the articles autonomously, exiting.")

    printDebug("Extracting the details")
    # Gather the needed information from the article
    articleDetails, articleContent, articleClearText = OSINTextract.extractAllDetails(currentProfile, articleSource)

    printDebug("Generating tags")
    # Generate the tags
    articleTags = OSINTtext.generateTags(OSINTtext.cleanText(articleClearText))

    printDebug("Creating the markdown file")
    # Create the markdown file
    MDFileName = OSINTfiles.createMDFile(currentProfile['source']['name'], URL, articleDetails, articleContent, articleTags, MDFilePath)

    return MDFileName

def scrapeUsingProfile(connection, articleList):
    currentProfileName = articleList.pop(0)
    printDebug("\n", False)
    printDebug("Scraping using this profile: " + currentProfileName)

    # Making sure the folder for storing the markdown files for the articles in exists, will throw exception if not
    OSINTmisc.createNewsSiteFolder(currentProfileName)

    # Loading the profile for the current website
    currentProfile = json.loads(getProfiles(currentProfileName))

    # Creating the path to the article for the news site
    articlePath = "./articles/{}/".format(currentProfileName)

    for articleURL in articleList:
        fromURLToMarkdown(articleURL, currentProfile, articlePath)
        OSINTdatabase.markAsScraped(connection, articleURL, 'articles')


def main():
    # Get the password for the writer account
    postgresqlPassword = Path("./credentials/writer.password").read_text()

    # Connecting to the database
    conn = psycopg2.connect("dbname=osinter user=writer password=" + postgresqlPassword)

    printDebug("Looking for articles that has been written to the database but not scraped...")
    articleCollection = OSINTdatabase.findUnscrapedArticles(conn, 'articles', OSINTdatabase.requestProfileListFromDB(conn, 'articles'))
    # Finding the number of articles found in need of being scraped, subtracting one for each list to compensate for each list being one to big as a result of also containing the profile name
    numberOfArticles = sum ([ len(articleList) for articleList in articleCollection ]) - len(articleCollection)

    if numberOfArticles > 0:
        printDebug("Found {} articles that has yet to be scraped, scraping them now. Given no interruptions it should take around {} seconds.".format(str(numberOfArticles), str(numberOfArticles * 6)))
        for articleList in articleCollection:
            scrapeUsingProfile(conn, articleList)
        printDebug("Finished scraping articles from database, looking for new articles online")
    else:
        printDebug("Found no articles in database left to scrape, looking for new articles online")

    printDebug("Scraping articles from frontpages and RSS feeds")
    articleURLCollection = OSINTscraping.gatherArticleURLs(getProfiles())

    printDebug("Removing those articles that have already been stored in the database")
    filteredArticleURLCollection = OSINTdatabase.filterArticleURLList(conn, 'articles', articleURLCollection)

    numberOfArticleAfterFilter = sum ([ len(filteredArticleURLList) for filteredArticleURLList in filteredArticleURLCollection ]) - len(filteredArticleURLCollection)

    if numberOfArticleAfterFilter == 0:
        printDebug("All articles seems to have already been stored, exiting.")
        return
    else:
        printDebug("Found {} articles left to scrape, will begin that process now".format(str(numberOfArticleAfterFilter)))

    printDebug("Collecting the OG tags")
    OGTagCollection = OSINTtags.collectAllOGTags(filteredArticleURLCollection)

    printDebug("Writting the OG tags to the DB")
    # Writting the OG tags to the database and finding those that haven't already been scraped
    articleCollection = OSINTdatabase.writeOGTagsToDB(conn, OGTagCollection, "articles")

    # Looping through the list of articles from specific news site in the list of all articles from all sites
    for articleList in articleCollection:
        scrapeUsingProfile(conn, articleList)

    printDebug("\n---\n", False)

if __name__ == "__main__":
    main()
