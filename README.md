# OSINTbackend

[![OSINTer](https://raw.githubusercontent.com/bertmad3400/OSINTer/master/logo.png)](https://osinter.dk)

## Welcome to OSINTer
This repo is a part of a larger project called
![OSINTer](https://github.com/bertmad3400/OSINTer). For more information on the
project as a whole, you can find OSINTer at
![https://github.com/bertmad3400/OSINTer](https://github.com/bertmad3400/OSINTer).

## What is OSINTbackend?
OSINTbackend is responsible for acting as a collection of scripts, written to
utilize [OSINTmodules](https://github.com/bertmad3400/OSINTmodules) to scrape
modern news sites, and store the information in a standardized and managable
form. It allows for collecting large amounts of information, while still being
secure and scalable and not containing much boiler-plate code.

### Specific keywords
OSINTbackend already automatically generate a lot of keywords, called tags for
the different articles (something that is especially relevant if you're using
Obsidian for handling the markdown files), which is used to group articles by
field or subjects. These can contain technical terms thats used a lot in the
articles or possibly objects of interrest like email or ip adresses found in
the article, but you also have the option to define some patterns that OSINTer
should look for in the article, and tag the article with it if found.

This works by OSINTer having a list of lists of words to look for. One of these
lists inside the main list could look something like this:

```[ cobalt, strike ]```

OSINTer then first looks for the word cobalt in the article, and if found, it
then looks for the word strike withing a certain proximity of the location of
where it found cobalt. This means that it will tag the article with
Cobalt-Strike no matter whether its spelt like "Cobalt-Strike", "Cobalt Strike",
"CobaltStrike" or "cobalt_strike" in the article, but at the same time also not
tagging it with Cobalt-Strike if theres one section describing Cobalt, and then
another section having the word strike in it.

To define these custom tags for OSINTer to look for and tag the articles with,
you will first have to create a file inside OSINTbackend/tools/keywords/ called
a name that describes that type of keywords (so the full path is
./OSINTbackend/tools/keywords/[fileName]). The reason for the file name needing
to have something to do with that category of keywords, is becaused the
filename will be used as the title for the keywords in the article MD File.
Once this is done, you can then specify the custom tags in this format in the
file:

```(keyword),(keyword),(keyword);(tag);[proximity]```

The keywords here are the words to look for in the article in a comma-seperated
(so in the previous example that was cobalt and strike). The "tag" is then what
the articles should be tagged with if these keywords are found, and the
proximity is an optional paramater, that (in number of characthers from each
side of the first keyword) describes how far away from the first keyword OSINTer
should look for the other keywords. If not specified this will default to 30 (so
OSINTer will look 30 characthers to the right of the word cobalt, and 30
characthers to the left of it for the word strike).

This means that if you wanted to follow through with the previous example you
would specify it like this:

```cobalt,strike;Cobalt-Strike```

Alternativly you could also specify a smaller proximity, as Cobalt-Strike is a
name, that isn't written with words or many spaces in between, which would look
like this:

```cobalt,strike;Cobalt-Strike;10```

Now, if you wanted to add more tags, you would simply do that on a new line, so
it would look like this:

```
cobalt,strike;Cobalt-Strike;10
windows,may,2021;21H1;60
revil;ransomware
```
