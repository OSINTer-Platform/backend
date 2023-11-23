import typer

from .label import app as label_app

app = typer.Typer(no_args_is_help=True)
app.add_typer(label_app, name="label", no_args_is_help=True)
