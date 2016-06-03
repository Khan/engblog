/**
 * Test that a page resizes to perfectly fit the width of the viewport.
 *
 * The script will return with an exit status of 0 on success, and 1 on
 * failure.
 */

var system = require("system");
var webpage = require("webpage");

if (system.args.length !== 3) {
    console.log("USAGE:", system.args[0], " [URL] [VIEWPORT_WIDTH]");
    phantom.exit(1);
}
var url = system.args[1];
var viewportWidth = parseInt(system.args[2]);

var page = webpage.create();
page.viewportSize = {width: viewportWidth, height: 320};
page.onLoadFinished = function(status) {
    if (status !== "success") {
        console.log("\tResponsiveness test failed. Failed to fetch", url);
        phantom.exit(1);
        return;
    }

    var width = page.evaluate(function() {
        // scrollWidth takes into account any oversized content, which is
        // exactly what we're looking for.
        return document.body.scrollWidth;
    });

    var testPassed = width === viewportWidth;
    if (!testPassed) {
        console.log("\tResponsiveness test failed. Expected width",
                    viewportWidth, "got", width);
    }

    phantom.exit(width === viewportWidth ? 0 : 1);
};
page.open(url);
