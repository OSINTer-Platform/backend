import typer

from .export import app as export_app
from .migrate import app as migrate_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(export_app, name="export", no_args_is_help=True)
app.add_typer(migrate_app, name="migrate", no_args_is_help=True)
