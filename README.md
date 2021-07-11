# OSINTbackend

![OSINTer](https://github.com/Combitech-DK/OSINTer/blob/master/logo.png)

## What is the purpose of OSINTbackend?
The OSINTbackend repo is a part of the whole OSINT'er project which is aiming
at providing the tools for scraping large information from news sites and in
combination with the
[OSINTmodules](https://github.com/Combitech-DK/OSINTmodules) and the
[OSINTprofiles](https://github.com/Combitech-DK/OSINTprofiles), the scripts in
OSINTbackend offers a way of collecting and organizing the relevant information
from news articles in a simple, futureproof and scalable fashion.

Whereas the [OSINTprofiles](https://github.com/Combitech-DK/OSINTprofiles) are
used for locating the relevant information on the newssites, and the
[OSINTmodules](https://github.com/Combitech-DK/OSINTmodules) are the code that
runs behind the scenes organized in a simple and manageable way, the
OSINTbackend is a collection of simple scripts bringing those to together into a
single project that allows you to easily scrape large amounts of data from news
sites and organize an overview into a postgresql database, along with the whole
article into folders of markdown files, parsed from the HTML code from the
websites. For more information, check out the README at the
[OSINT'er](https://github.com/Combitech-DK/OSINTer) project and for setup
instructions have a look in the next section.

## Setup
1. Firstly, make sure you are running Linux along with the newest version of
   Python 3. The newest version of Firefox will also be needed installed for the
   webscraping.
2. Clone this repo to a local directory.
3. Enter the newly cloned "OSINTbackend" directory and clone both the 
   [OSINTmodules](https://github.com/Combitech-DK/OSINTmodules) and the
   [OSINTprofiles](https://github.com/Combitech-DK/OSINTprofiles) repo, so that
   you get a folder structure with "OSINTbackend" as the root with the two
   directories "OSINTmodules" and "OSINTprofiles" inside.
4. Download the [latest
   geckodriver](https://github.com/mozilla/geckodriver/releases), extract it and
   put it in the "OSINTbackend" directory.
5. Install the depencies specified [here, in the the OSINT'er
   repo](https://github.com/Combitech-DK/OSINTer/blob/master/requirements.txt).
   Most of them can be installed using pip, but others (especially psycopg2) may
   give of an error during an attempt at installing it. If that's the case, you
   will have to install the failed packages from your distrobutions own
   repositories. On both Arch most of the packages can be found under
   "python-[packageName]" and on Debian under "python3-[packageName]"
6. Setup a postgresql database, change the authentication of the default
   postgres user in the postgresql database to password based authentication and
   change to password to something you can remember (or simply write it down).
   Information on how to do this can be found in the [Arch
   wiki](https://wiki.archlinux.org/title/PostgreSQL)
7. Modify the variable "postgresqlPassword" in both the
   "initiateScrapingBackend.py" and "scrapeAndStore.py" script to the password
   you set for the postgres user in the last point.
8. Now simply run the "initiateScrapingBackend.py" (only needed the first time)
   and then the "scrapeAndStore.py" script to start the scraping.
