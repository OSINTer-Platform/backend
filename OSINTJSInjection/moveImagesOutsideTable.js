// This small JS script moves image outside of table, as the python library markdownify which is used for converting html to markdown has a problem with tables containing images for now https://github.com/matthewwithanm/python-markdownify/issues/61
document.osinterReady = false;

document.querySelectorAll("table").forEach(table => {
	images = Array.from(table.querySelectorAll("img"));
	if (images.length > 0){
		imageFrag = document.createDocumentFragment();
		images.forEach(image => imageFrag.appendChild(image))
		table.replaceWith(imageFrag)
	}
})

document.osinterReady = true;
