from collections import Counter
import re
from typing import TypedDict
import unicodedata

from modules.objects import TagsOfInterest


# Function for taking in text from article (or basically any source) and outputting a list of words cleaned for punctuation, sole numbers, double spaces and other things so that it can be used for text analyssis
def clean_text(clear_text: str) -> str:
    # Normalizing the text, to remove weird characthers that sometimes pop up in webarticles
    clean_clear_text = unicodedata.normalize("NFKD", clear_text)
    # Remove line endings
    clean_clear_text = re.sub(r"\n", " ", clean_clear_text)

    return clean_clear_text


def tokenize_text(clean_clear_text: str) -> list[str]:
    # Removing all contractions and "'s" created in english by descriping possession
    clean_clear_text = re.sub(r"(?:\'|’)\S*", "", clean_clear_text)
    # Remove punctuation
    clean_clear_text = re.sub(
        r'\s(?:,|\.|"|\'|\/|\\|:|-)+|(?:,|\.|"|\'|\/|\\|:|-)+\s', " ", clean_clear_text
    )
    clean_clear_text = re.sub(r"(?:\{.*\})", "", clean_clear_text)
    clean_clear_text = re.sub(r"“|\"|\(|\)", " ", clean_clear_text)
    # Remove all "words" where the word doesn't have any letters in it. This will remove "-", "3432" (words consisting purely of letters) and double spaces.
    clean_clear_text = re.sub(r"\s[^a-zA-Z]*\s", " ", clean_clear_text)

    # Converting the cleaned cleartext to a list
    clear_text_list = clean_clear_text.lower().split(" ")

    return clear_text_list


def generate_tags(clear_text_list: list[str]) -> list[str]:
    """clear_text_list needs to be lowercase"""
    common_words = set(line.strip() for line in open("./tools/wordlist.txt", "r"))

    word_counts = Counter(clear_text_list)

    tags: list[str] = []
    for word, count in word_counts.most_common():
        if count < 3:
            break
        if word and word not in common_words:
            tags.append(word)
        if len(tags) > 9:
            break

    return tags


class ObjectsOfInterest(TypedDict):
    pattern: re.Pattern[str]
    tag: bool


# Function for locating interesting bits and pieces in an article like ip adresses and emails
def locate_objects_of_interest(clear_text: str) -> list[TagsOfInterest]:
    objects: dict[str, ObjectsOfInterest] = {
        "ipv4-adresses": {
            "pattern": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
            "tag": False,
        },
        "ipv6-adresses": {
            "pattern": re.compile(
                r"\b(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))\b"
            ),
            "tag": False,
        },
        "email-adresses": {
            "pattern": re.compile(
                r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b"
            ),
            "tag": False,
        },
        "urls": {
            "pattern": re.compile(r'\b(?:[a-zA-Z]+:\/{1,3}|www\.)[^"\s]+'),
            "tag": False,
        },
        "CVE's": {"pattern": re.compile(r"CVE-\d{4}-\d{4,7}"), "tag": True},
        "MITRE IDs": {
            "pattern": re.compile(r"(?:[TMSGO]|TA)\d{4}\.\d{3}"),
            "tag": True,
        },
        "MD5-hash": {
            "pattern": re.compile(r"\b(?:[a-f0-9]{32}|[A-F0-9]{32})\b"),
            "tag": False,
        },
        "SHA1-hash": {
            "pattern": re.compile(r"\b(?:[a-f0-9]{40}|[A-F0-9]{40})\b"),
            "tag": False,
        },
        "SHA256-hash": {
            "pattern": re.compile(r"\b(?:[a-f0-9]{64}|[A-F0-9]{64})\b"),
            "tag": False,
        },
        "SHA512-hash": {
            "pattern": re.compile(r"\b(?:[a-f0-9]{128}|[A-F0-9]{128})\b"),
            "tag": False,
        },
    }
    results: list[TagsOfInterest] = []

    for object_name in objects:
        # Sometimes the regex's will return a tuple of the result split up based on the groups in the regex. This will combine each of the, before reuniting them as a list
        result = [
            result if not isinstance(result, tuple) else "".join(result)
            for result in objects[object_name]["pattern"].findall(clear_text)
        ]

        if result != []:
            # Use list->set->list for duplicate removal
            results.append(TagsOfInterest(name=object_name, values=list(set(result))))

    return results
