#!/usr/bin/python3

import scripts
from scripts import *

scriptNames = [("initiateScrapingBackend", "Intiate the OSINTer backend"), ("profileTester", "Test a profile"), ("scrapeAndStore", "Scrape articles based on available profiles"), ("scrapePriorZdnetArticles", "Scrape old ZDNet articles"), ("verifyKeywordFiles", "Verify the available keyword files")]

print("Which script do want ro run?")

for i,script in enumerate(scriptNames):
    print(f"{str(i)}. {script[1]}")

try:
    scriptNumber = int(input("Write a number: "))
except:
    print("It doesn't look like you entered a number.")
    exit()

try:
    scriptName = scriptNames[scriptNumber][0]
except IndexError:
    print(f"The number you entered doesn't correspond to a script, it should be between 0 and {len(scriptNames) - 1}")
    exit()

if scriptName == "profileTester":
    from OSINTmodules import OSINTprofiles
    profileList = OSINTprofiles.getProfiles(justNames = True)

    print("Available profiles:")

    for i, profileName in enumerate(profileList):
        print(f"{str(i)}: {profileName}")

    profile = profileList[int(input("Which profile do you want to test? "))]

    url = input("Enter specific URL or leave blank for scraping 10 urls by itself: ")

    scripts.profileTester.main(profile, url)

eval(f"scripts.{scriptName}.main()")
