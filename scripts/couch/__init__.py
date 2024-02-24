import json
import gzip
from datetime import datetime
import logging
from typing import Any
from scripts import config_options
import typer
from couchdb import Database, Server

app = typer.Typer(no_args_is_help=True)
logger = logging.getLogger("osinter")

current_day = datetime.today().strftime("%Y-%m-%d")


def getDB() -> Database:
    return Server(config_options.COUCHDB_URL)[config_options.COUCHDB_NAME]


@app.command()
def backup(backup_file_name: str = f"./couch-backup-{current_day}.gz") -> None:
    db = getDB()
    docs: list[dict[str, Any]] = []

    logger.debug("Downloading documents")
    for id in db:
        docs.append(dict(db[id]))

    logger.debug(f'Downloaded {len(docs)}, writing to disk at "{backup_file_name}"')
    with gzip.open(backup_file_name, "wt", encoding="utf-8") as f:
        json.dump(docs, f)
