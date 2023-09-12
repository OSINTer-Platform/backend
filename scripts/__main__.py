import logging

import typer

from scripts.scraping import main as scrape

from .elastic import app as elastic_app
from .profile_tester import app as profile_app

logger = logging.getLogger("osinter")


app = typer.Typer(no_args_is_help=True)
app.add_typer(elastic_app, name="elastic", no_args_is_help=True)
app.add_typer(profile_app, name="profile", no_args_is_help=True)


app.command("scrape")(scrape)


if __name__ == "__main__":
    app()
