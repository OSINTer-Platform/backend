document.osinterReady = false;

var elementTypes = {"img": "src", "a": "href"}

for (const [elementType, urlAttribute] of Object.entries(elementTypes)) {
	currentElements = Array.from(document.getElementsByTagName(elementType));

	currentElements.forEach(currentElement => {
		currentElement.setAttribute(urlAttribute, currentElement[urlAttribute]);
	});
}

document.osinterReady = true;
