#!/usr/bin/python3

import os

from pathlib import Path

from modules import misc


def main():
    if os.path.isdir(Path("./tools/keywords/")):
        for file in os.listdir(Path("./tools/keywords/")):
            current_keywords = misc.decode_keywords_file(
                Path(f"./tools/keywords/{file}")
            )

            for keyword_collection in current_keywords:
                try:
                    test = [
                        keyword_collection["keywords"],
                        keyword_collection["tag"],
                        keyword_collection["proximity"],
                    ]

                    if (
                        not isinstance(test[2], int)
                        or not isinstance(test[1], str)
                        or not isinstance(test[0], list)
                    ):
                        print(f"Error with {keyword_collection}")
                except:
                    print(f"Error with {keyword_collection}")
    else:
        print("No ḱeyword files were found")
        exit()


if __name__ == "__main__":
    main()
