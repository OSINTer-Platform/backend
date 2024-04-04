from collections import Counter
import re
from typing import Callable, Iterator
import unicodedata
import iocextract

from modules.objects import TagsOfInterest

dashes = re.compile(
    "[\u002D\u058A\u05BE\u2010\u2011\u2012\u2013\u2014\u2015\u2E3A\u2E3B\uFE58\uFE63\uFF0D]"
)


# Function for taking in text from article (or basically any source) and outputting a list of words cleaned for punctuation, sole numbers, double spaces and other things so that it can be used for text analyssis
def clean_text(clear_text: str) -> str:
    # Normalizing the text, to remove weird characthers that sometimes pop up in webarticles
    clean_clear_text = unicodedata.normalize("NFKD", clear_text)
    # Remove line endings
    clean_clear_text = re.sub(r"\n", " ", clean_clear_text)

    clean_clear_text = dashes.sub("-", clean_clear_text)

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


external_identifiers: dict[str, Callable[[str], Iterator[str]]] = {
    "ipv4-adresses": lambda text: iocextract.extract_ipv4s(text, refang=True),
    "ipv6-adresses": lambda text: iocextract.extract_ipv6s(text),
    "email-adresses": lambda text: iocextract.extract_emails(text, refang=True),
    "urls": lambda text: iocextract.extract_urls(text, refang=True),
    "MD5-hash": lambda text: iocextract.extract_md5_hashes(text),
    "SHA1-hash": lambda text: iocextract.extract_sha1_hashes(text),
    "SHA256-hash": lambda text: iocextract.extract_sha256_hashes(text),
    "SHA512-hash": lambda text: iocextract.extract_sha512_hashes(text),
}

internal_identifiers: dict[str, re.Pattern[str]] = {
    "CVE's": re.compile(r"[Cc][Vv][Ee]-\d{4}-\d{4,7}"),
    "MITRE IDs": re.compile(r"(?:[TMSGO]|TA)\d{4}\.\d{3}"),
}


# Function for locating interesting bits and pieces in an article like ip adresses and emails
def locate_objects_of_interest(clear_text: str) -> list[TagsOfInterest]:
    results: list[TagsOfInterest] = []

    for object_name in internal_identifiers:
        # Sometimes the regex's will return a tuple of the result split up based on the groups in the regex. This will combine each of the, before reuniting them as a list
        result = [
            result if not isinstance(result, tuple) else "".join(result)
            for result in internal_identifiers[object_name].findall(clear_text)
        ]

        result = [r.upper() for r in result]

        if result:
            # Use list->set->list for duplicate removal
            results.append(TagsOfInterest(name=object_name, values=list(set(result))))

    for object_name, identifier in external_identifiers.items():
        # print(list(identifier(clear_text)), object_name, len(clear_text))
        result = list(set(identifier(clear_text)))

        if result:
            results.append(TagsOfInterest(name=object_name, values=result))

    return results
