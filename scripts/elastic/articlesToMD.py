import os

from OSINTmodules import *

from scripts import configOptions


def main(folderPath):
    try:
        os.mkdir(os.path.join(folderPath, "MDArticles"))
    except FileExistsError:
        pass

    folderPath = os.path.join(folderPath, "MDArticles")
    configOptions.logger.info("Downloading list of profiles...")
    profiles = configOptions.esArticleClient.requestSourceCategoryListFromDB()

    for profile in profiles:

        configOptions.logger.info(f"Downloading list of articles for {profile}")
        articles = configOptions.esArticleClient.queryDocuments(
            OSINTelastic.searchQuery(
                complete=True, limit=10_000, sourceCategory=[profile]
            )
        )["documents"]

        try:
            os.mkdir(os.path.join(folderPath, profile))
        except FileExistsError:
            pass

        configOptions.logger.info(f"Converting {len(articles)} articles for {profile}")
        for article in articles:
            articleMD = OSINTfiles.convertArticleToMD(article)

            with open(
                os.path.join(folderPath, profile, f"{article.id}.md"), "w"
            ) as articleFile:
                articleFile.write(articleMD.getvalue())
