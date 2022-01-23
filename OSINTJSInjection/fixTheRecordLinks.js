document.osinterReady = false;

// For fixing general links and source links for images
var elementTypes = {"img": "src", "a": "href"}

for (const [elementType, urlAttribute] of Object.entries(elementTypes)) {
	currentElements = Array.from(document.getElementsByTagName(elementType));

	currentElements.forEach(currentElement => {
		currentURL = currentElement[urlAttribute]
		fixedURL = currentURL.replace("www-therecord.recfut.com", "therecord.media")
		currentElement.setAttribute(urlAttribute, fixedURL)
	});
}

// For fixing the og tag containing the source for the og:image
ogElement = document.querySelector("meta[property='og:image']")
ogURL = ogElement["content"]
ogFixedURL = ogURL.replace("www-therecord.recfut.com", "therecord.media")
ogElement.setAttribute("content", ogFixedURL)

document.osinterReady = true;
