from datetime import datetime, timedelta, timezone, tzinfo
from random import randrange
import os
import glob
from base64 import b64decode

from typing import Sequence, TypedDict, cast

from modules.objects import FullArticle
from modules.misc import create_folder
from scripts import config_options

from hashlib import md5
import logging
import typer
import frontmatter
from openai import OpenAI


app = typer.Typer(no_args_is_help=True)
logger = logging.getLogger("osinter")

openai_client = OpenAI(api_key=config_options.OPENAI_KEY)


class FakeContents(TypedDict):
    id: str
    title: str
    description: str
    source: str
    content: str
    image: str | None


class FakeFile(FakeContents):
    file_path: str


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


def gen_es_id(content: str) -> str:
    return md5(content.encode("utf-8")).hexdigest()


def gen_image(prompt: str, img_name: str) -> None:
    create_folder("fake-images", change_mode=False)

    logger.debug("Generating image")
    img_r = openai_client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="b64_json",
    )
    b64 = img_r.data[0].b64_json

    if not b64:
        raise Exception("Didn't recieve image contents from OpenAI")

    with open(os.path.join("fake-images", f"{img_name}.png"), "wb") as f:
        f.write(b64decode(b64))


def load_fakes(path: str) -> list[list[FakeFile]]:
    def load(file_path: str) -> FakeFile:
        f = frontmatter.load(file_path)
        meta = cast(dict[str, str], f.metadata)
        return {
            "id": meta["id"],
            "title": meta["title"],
            "description": meta["description"],
            "source": meta["source"],
            "image": meta["image"] if "image" in meta else None,
            "content": f.content,
            "file_path": file_path,
        }

    if path.endswith(".md"):
        return [[load(path)]]

    fakes: list[list[FakeFile]] = []
    for dir in glob.glob(os.path.join(path, "*")):
        fakes.append([])
        for file_path in glob.glob(os.path.join(dir, "*")):
            fakes[-1].append(load(file_path))

    return fakes


def create_fake_image(fake: FakeFile, root_url: str) -> None:
    es_id = gen_es_id(fake["id"])
    img_name = f"{es_id}-image"
    gen_image(
        f"I have the following title and description for a news article about a cyber security attack, please generate an image. Title: {fake['title']}. Description: {fake['description']}",
        img_name,
    )

    logger.debug("Loading article for writting img url")
    article = frontmatter.load(fake["file_path"])
    article.metadata["image"] = root_url + img_name + ".png"

    logger.debug("Saving article changes")
    with open(fake["file_path"], "wb") as f:
        frontmatter.dump(article, f)


def create_fake(
    id: str,
    publish_date: datetime,
    title: str,
    description: str,
    source: str,
    content: str,
    image: str | None,
) -> FullArticle:
    dt = publish_date.replace(tzinfo=timezone.utc)
    return FullArticle(
        id=gen_es_id(id),
        title=title,
        description=description,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        image_url=image if image else "",
        profile=source.lower().replace(" ", ""),
        source=source,
        author=source,
        publish_date=dt,
        inserted_at=dt,
        formatted_content=content,
        content=content,
    )


def create_fakes(
    articles: Sequence[FakeContents], start: datetime, end: datetime
) -> list[FullArticle]:
    fakes: list[FullArticle] = []

    for article in articles:
        publish_date = random_date(start, end)
        fakes.append(
            create_fake(
                id=article["id"],
                title=article["title"],
                description=article["description"],
                source=article["source"],
                content=article["content"],
                image=article["image"],
                publish_date=publish_date,
            )
        )

    return fakes


@app.command()
def upload_fakes(path: str, day_span: int = 60) -> None:
    start_date = datetime.now() - timedelta(days=day_span)
    stop_date = datetime.now() - timedelta(days=7)

    logger.info("Loading fakes")
    fakes = load_fakes(path)

    fake_articles: list[FullArticle] = []

    logger.info("Creating article objects")
    for fake_collection in fakes:
        collection_start = random_date(start_date, stop_date)
        collection_stop = collection_start + timedelta(days=7)

        fake_articles.extend(
            create_fakes(fake_collection, collection_start, collection_stop)
        )

    logger.info(f"Saving {len(fake_articles)} fake articles")
    config_options.es_article_client.save_documents(fake_articles)


@app.command()
def delete_fakes(path: str) -> None:
    logger.info("Loading fakes and generating ids")
    fakes = load_fakes(path)
    ids = {
        gen_es_id(fake["id"]) for fake_collection in fakes for fake in fake_collection
    }

    logger.info(f"Removing {len(ids)} fakes")
    config_options.es_article_client.delete_document(ids)


@app.command()
def generate_imgs(path: str, root_url: str) -> None:
    logger.info("Loading fakes")
    fakes = load_fakes(path)

    for i, fake_collection in enumerate(fakes):
        logger.info(f"Processing batch {i} out of {len(fakes)}")
        for fake in fake_collection:
            create_fake_image(fake, root_url)
