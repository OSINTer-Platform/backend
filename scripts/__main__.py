import logging

import typer

from .elastic import app as elastic_app
from .profile_tester import app as profile_app
from .ml import app as ml_app
from .scraping import app as scrape_app

logger = logging.getLogger("osinter")


app = typer.Typer(no_args_is_help=True)
app.add_typer(elastic_app, name="elastic", no_args_is_help=True)
app.add_typer(profile_app, name="profile", no_args_is_help=True)
app.add_typer(ml_app, name="ml", no_args_is_help=True)
app.add_typer(scrape_app, name="scrape", no_args_is_help=True)


if __name__ == "__main__":
    app()
