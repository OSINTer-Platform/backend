document.osinterReady = false;

function scroll(lastOffset, i) {
	window.scrollTo(lastOffset, lastOffset + document.documentElement.clientHeight);
	var newOffset = window.pageYOffset;

	i = i + 1;

	if (i <= 10 && newOffset != lastOffset) {
		setTimeout(scroll, 1000, newOffset, i);
	} else {
		document.osinterReady = true;
		console.log(newOffset, lastOffset)
	}
}

scroll(0, 0);
