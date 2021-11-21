var elementTypes = {"img": "src", "a": "href"}

for (const [elementType, urlAttribute] of Object.entries(elementTypes)) {
	currentElements = Array.from(document.getElementsByTagName(elementType));

	currentElements.forEach(currentElement => {
		currentURL = currentElement[urlAttribute]
		fixedURL = currentURL.replace("www-therecord.recfut.com", "therecord.media")
		currentElement.setAttribute(urlAttribute, fixedURL)
	});
}
