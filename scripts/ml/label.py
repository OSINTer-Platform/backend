import logging
import typer
from rich.console import Console
from modules.objects import FullArticle


from scripts import config_options
from modules.elastic import ArticleSearchQuery

app = typer.Typer()
console = Console()

logger = logging.getLogger("osinter")

labels = [
    "trends",
    "vulnerability",
    "incident",
    "research",
    "apt",
    "ransomware group",
    "malware",
]


@app.command()
def manual() -> None:
    def print_details(article: FullArticle) -> None:
        print(article.title)
        print(article.description)
        print("\n\n", article.summary, "\n\n")
        print(f"Tags: {' | '.join(article.tags.automatic)}\n\n")
        print("The following labels are available:")
        for i, label in enumerate(labels):
            print(f"{i}: {label}")

    def get_labels(prompt: str | None = None) -> list[str]:
        prompt = (
            prompt
            if prompt
            else f"Enter comma-seperated list corrensponding to the applicable labels: [0 - {len(labels) - 1}] "
        )

        inputs = input(prompt).split(",")

        if len(inputs) == 1 and inputs[0] == "":
            return []

        choices: list[str] = []

        for user_input in inputs:
            try:
                choices.append(labels[int(user_input)])
            except ValueError:
                return get_labels(f'"{user_input}" isn\'t a number. Try again: ')
            except IndexError:
                return get_labels(
                    f"The length max index value is {len(labels) - 1}, {user_input} is too big. Try again: "
                )

        return choices

    logger.info("Downloading articles")
    articles = config_options.es_article_client.query_documents(
        ArticleSearchQuery(limit=1000, sort_by="publish_date", sort_order="desc"), True
    )[0]

    logger.info("Filtering articles")
    articles_without_label = [article for article in articles if not article.ml.labels]

    logger.info(f"Found {len(articles_without_label)} articles to label")

    for article in articles_without_label:
        console.clear()
        print_details(article)
        article.ml.labels = get_labels()

        if not article.ml.labels:
            article.ml.labels = ["none"]

        logger.info(f'Updating article with id "{article.id}"')
        print(f'Updating article with id "{article.id}"\n\n')

        config_options.es_article_client.update_documents([article], ["ml"])
