from dateparser import parse as date_parse
from datetime import datetime, timezone
import json
import re

from bs4 import BeautifulSoup, Tag
from bs4.element import ResultSet
from pydantic import BaseModel

# Used for matching the relevant information from LD+JSON
json_patterns = {
    "publish_date": re.compile(r'("datePublished": ")(.*?)(?=")'),
    "author": re.compile(r'("@type": "Person",.*?"name": ")(.*?)(?=")'),
}


class OGTags(BaseModel):
    author: str | None = None
    title: str | None = None
    description: str | None = None
    image_url: str | None = None
    publish_date: datetime | str | None = None


def extract_article_content(
    selectors: dict[str, str], soup: BeautifulSoup, delimiter: str = "\n"
) -> tuple[str, str]:
    def locate_content(css_selector: str, soup: BeautifulSoup) -> ResultSet[Tag] | None:
        try:
            return soup.select(css_selector)
        except:
            return None

    def clean_soup(soup: BeautifulSoup, remove_selectors: str) -> BeautifulSoup:
        for css_selector in remove_selectors.split(";"):
            for tag in soup.select(css_selector):
                tag.decompose()

        return soup

    # Clean the textlist for unwanted html elements
    if selectors["remove"] != "":
        soup = clean_soup(soup, selectors["remove"])

    text_list = locate_content(selectors["container"], soup)

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
    page_soup: BeautifulSoup, scraping_targets: dict[str, str], site_url: str
) -> OGTags:
    OG_tags = OGTags()

    for meta_type in scraping_targets:
        try:
            tag_selector, tag_field = scraping_targets[meta_type].split(";")
        except ValueError:
            tag_selector = scraping_targets[meta_type]

            if "meta" in tag_selector:
                tag_field = "content"
            elif "time" in tag_selector:
                tag_field = "datetime"
            else:
                tag_field = None

        # Skip empty selectors, as some profiles rely on LD+JSON for some fields and therefore doesn't have CSS selectors for author and date
        if not tag_selector:
            continue

        try:
            tag = page_soup.select(tag_selector)[0]
        except IndexError:
            continue

        if tag_field:
            tag_contents = tag.get(tag_field)
        else:
            tag_contents = tag.text

        if isinstance(tag_contents, str):
            setattr(OG_tags, meta_type, tag_contents)

    if not OG_tags.author or not OG_tags.publish_date:
        # Use ld+json to extract extra information not found in the meta OG tags like author and publish date
        json_script_tags = page_soup.find_all("script", {"type": "application/ld+json"})

        for script_tag in json_script_tags:
            # Converting to and from JSON to standardize the format to avoid things like line breaks and excesive spaces at the end and start of line. Will also make sure there spaces in the right places between the keys and values so it isn't like "key" :"value" and "key  : "value" but rather "key": "value" and "key": "value".
            try:
                script_tag_string = json.dumps(json.loads("".join(script_tag.contents)))
            except json.decoder.JSONDecodeError:
                continue

            for pattern in json_patterns:
                if getattr(OG_tags, pattern, None) is None:
                    detail_match = json_patterns[pattern].search(script_tag_string)

                    if detail_match:
                        # Selecting the second group, since the first one is used to located the relevant information. The reason for not using lookaheads is because python doesn't allow non-fixed lengths of those, which is needed when trying to select pieces of text that doesn't always conform to a standard.
                        setattr(OG_tags, pattern, detail_match.group(2))

    if not OG_tags.image_url:
        OG_tags.image_url = f"{site_url}/favicon.ico"

    if not OG_tags.publish_date:
        OG_tags.publish_date = datetime.now(timezone.utc)
    elif isinstance(OG_tags.publish_date, str):
        OG_tags.publish_date = date_parse(OG_tags.publish_date, languages=["en"])

    return OG_tags
