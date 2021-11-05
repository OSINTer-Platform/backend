# OSINTbackend

![OSINTer](https://github.com/bertmad3400/OSINTer/blob/master/logo.png)

## What is the purpose of OSINTbackend?
The OSINTbackend repo is a part of the whole OSINT'er project which is aiming
at providing the tools for scraping large information from news sites and in
combination with the
[OSINTmodules](https://github.com/bertmad3400/OSINTmodules) and the
[OSINTprofiles](https://github.com/bertmad3400/OSINTprofiles), the scripts in
OSINTbackend offers a way of collecting and organizing the relevant information
from news articles in a simple, futureproof and scalable fashion.

Whereas the [OSINTprofiles](https://github.com/bertmad3400/OSINTprofiles) are
used for locating the relevant information on the newssites, and the
[OSINTmodules](https://github.com/bertmad3400/OSINTmodules) are the code that
runs behind the scenes organized in a simple and manageable way, the
OSINTbackend is a collection of simple scripts bringing those to together into a
single project that allows you to easily scrape large amounts of data from news
sites and organize an overview into a postgresql database, along with the whole
article into folders of markdown files, parsed from the HTML code from the
websites. For more information, check out the README at the
[OSINT'er](https://github.com/bertmad3400/OSINTer) project and for setup
have a look at [OSINTansible](https://github.com/bertmad3400/OSINTansible)

### Specific keywords
OSINTbackend already automatically generate a lot of keywords, called tags for
the different articles (something that is especially relevant if you're using
Obsidian for handling the markdown files). These can contain technical terms
thats used a lot in the articles or possibly objects of interrest like email or
ip adresses found in the article, but you also have the option to define some
patterns that OSINTer should look for in the article, and tag the article with
it if found.

This works by OSINTer having a list of lists of words to look for. One of these
lists inside the main list could look something like this:

[ cobalt, strike ]

OSINTer then first looks for the word cobalt in the article, and if found, it
then looks for the word strike withing a certain proximity of the location of
where it found cobalt. This means that it will tag the article with
Cobalt-Strike no matter whether its spelt like "Cobalt-Strike", "Cobalt Strike",
"CobaltStrike" or "cobalt_strike" in the article, but at the same time also not
tagging it with Cobalt-Strike if theres one section describing Cobalt, and then
another section having the word strike in it.

To define these custom tags for OSINTer to look for and tag the articles with,
you will first have to create a file inside OSINTbackend/tools called
"keywords.txt" (so the full path is ./OSINTbackend/tools/keywords.txt). In here
you can then specify the custom tags in this format:

(keyword),(keyword),(keyword);(tag);[proximity]

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

cobalt,strike;Cobalt-Strike

Alternativly you could also specify a smaller proximity, as Cobalt-Strike is a
name, that isn't written with words or many spaces in between, which would look
like this:

cobalt,strike;Cobalt-Strike;10

Now, if you wanted to add more tags, you would simply do that on a new line, so
it would look like this:

cobalt,strike;Cobalt-Strike;10
windows,may,2021;21H1;60
revil;ransomware
