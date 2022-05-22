#!/usr/bin/python3

import os

from pathlib import Path

from OSINTmodules import OSINTmisc


def main():
    if os.path.isdir(Path("./tools/keywords/")):
        for file in os.listdir(Path("./tools/keywords/")):
            currentKeywords = OSINTmisc.decodeKeywordsFile(
                Path(f"./tools/keywords/{file}")
            )

            for keywordCollection in currentKeywords:
                try:
                    test = [
                        keywordCollection["keywords"],
                        keywordCollection["tag"],
                        keywordCollection["proximity"],
                    ]

                    if (
                        not isinstance(test[2], int)
                        or not isinstance(test[1], str)
                        or not isinstance(test[0], list)
                    ):
                        print(f"Error with {keywordCollection}")
                except:
                    print(f"Error with {keywordCollection}")
    else:
        print("No ḱeyword files were found")
        exit()


if __name__ == "__main__":
    main()
