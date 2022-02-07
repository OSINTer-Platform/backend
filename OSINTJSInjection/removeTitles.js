// This small JS script removes the title attribute from all elements before scraping. The reason for doing so, is that the titles, when converted to markdown will use quotation marks, which does not play well with the jinja autoescaping
document.osinterReady = false;

titleElements = document.querySelectorAll("[title]")
titleElements.forEach(titleElement => titleElement.removeAttribute("title"))

document.osinterReady = true;
