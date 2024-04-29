from typing import Annotated, Pattern
from dateparser import parse as date_parse
from datetime import datetime, timezone
import json
import re

from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet
from pydantic import AwareDatetime, BaseModel

from modules.profiles import ArticleContent, ArticleMeta, ElementSelector

# Used for matching the relevant information from LD+JSON
json_patterns = {
    "publish_date": re.compile(r'("datePublished": ")(.*?)(?=")'),
    "author": re.compile(r'("@type": "Person",.*?"name": ")(.*?)(?=")'),
}


class OGTags(BaseModel):
    author: str | None
    title: str
    description: str
    image_url: str
    publish_date: Annotated[datetime, AwareDatetime]


def extract_article_content(
    selectors: ArticleContent, soup: BeautifulSoup, delimiter: str = "\n"
) -> tuple[str, str]:
    def locate_content(css_selector: str, soup: BeautifulSoup) -> ResultSet[Tag] | None:
        try:
            return soup.select(css_selector)
        except:
            return None

    def clean_soup(
        soup: BeautifulSoup, profile_remove_selectors: list[str]
    ) -> BeautifulSoup:
        remove_selectors = ["style", "script"]
        remove_selectors.extend(profile_remove_selectors)

        for css_selector in remove_selectors:
            for tag in soup.select(css_selector):
                tag.decompose()

        return soup

    # Clean the textlist for unwanted html elements
    soup = clean_soup(soup, selectors.remove)

    text_list = locate_content(selectors.container, soup)

    if text_list is None:
        raise Exception(
            "Wasn't able to fetch the text for the following soup:" + str(soup)
        )

    assembled_text = ""
    assembled_clear_text = ""
    text_tag_types = ["p", "span"] + [f"h{i}" for i in range(1, 7)]

    for text_soup in text_list:
        for text_tag in text_soup.find_all(text_tag_types):
            if text_tag.string:
                text_tag.string.replace_with(text_tag.string.strip())

        assembled_clear_text = assembled_clear_text + text_soup.get_text() + delimiter
        assembled_text = assembled_text + str(text_soup) + delimiter

    return assembled_text, assembled_clear_text


# Function for scraping meta information (like title, author and publish date) from articles. This both utilizes the OG tags and LD+JSON data, and while the proccess for extracting the OG tags is fairly simply as those is (nearly) always following the same standard, the LD+JSON data is a little more complicated. Here the data isn't parsed as JSON, but rather as a string where the relevant pieces of information is extracted using regex. It's probably ugly and definitly not the officially "right" way of doing this, but different placement of the information in the JSON object on different websites using different attributes made parsing the information from a python JSON object near impossible. As such, be warned that this function is not for the faint of heart
def extract_meta_information(
    page_soup: BeautifulSoup, scraping_targets: ArticleMeta, site_url: str
) -> OGTags:
    def extract_with_selector(selector: str | ElementSelector) -> None | str:
        # Skip empty selectors, as some profiles rely on LD+JSON for some fields and therefore doesn't have CSS selectors for author and date
        if not selector:
            return None

        try:
            if isinstance(selector, str):
                tag = page_soup.select(selector)[0]
                return tag.text
            elif isinstance(selector, ElementSelector):
                tag = page_soup.select(selector.element)[0]
                contents = tag.get(selector.content_field)

                if isinstance(contents, str):
                    return contents
                else:
                    return None
        except IndexError:
            return None

    # Use ld+json to extract extra information not found in the meta OG tags like author and publish date
    def extract_json(pattern: Pattern[str]) -> str | None:
        json_script_tags = page_soup.find_all("script", {"type": "application/ld+json"})

        for script_tag in json_script_tags:
            # Converting to and from JSON to standardize the format to avoid things like line breaks and excesive spaces at the end and start of line. Will also make sure there spaces in the right places between the keys and values so it isn't like "key" :"value" and "key  : "value" but rather "key": "value" and "key": "value".
            try:
                script_tag_string = json.dumps(json.loads("".join(script_tag.contents)))
            except json.decoder.JSONDecodeError:
                continue

            detail_match = pattern.search(script_tag_string)

            if detail_match:
                return detail_match.group(2)

        return None

    def extract_datetime() -> datetime | None:
        meta = extract_with_selector(scraping_targets.publish_date)
        if meta:
            return date_parse(meta)

        json = extract_json(json_patterns["publish_date"])
        if json:
            return date_parse(json)

        return None

    publish_date = extract_datetime() or datetime.now(timezone.utc)

    if publish_date.tzinfo is None:
        publish_date = publish_date.replace(tzinfo=timezone.utc)

    title = extract_with_selector(scraping_targets.title)
    description = extract_with_selector(scraping_targets.description)
    author = extract_with_selector(scraping_targets.author) or extract_json(json_patterns["author"])
    author = author.strip() if author else author

    if not title or not description:
        raise Exception("Either title or description wasn't available")

    return OGTags(
        title=title,
        description=description,
        image_url=extract_with_selector(scraping_targets.image_url)
        or f"{site_url}/favicon.ico",
        author=author,
        publish_date=publish_date,
    )
