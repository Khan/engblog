/**
 * Test that all pages resize to fit the width of the viewport.
 *
 * This script will render all the URLs that are passed into it at a specific
 * viewport width, and then ensure that the width of the body element is
 * exactly that width.
 *
 * The script will return with an exit status of 0 on success, and 1 on
 * failure.
 *
 * Usage:
 *
 *     phantomjs phantomjs-tests/pages-are-responsive.js [URL [URL] ...]
 */

var system = require("system");
var webpage = require("webpage");

// The width we'll set the viewport to (we expect the content to resize to
// match this number).
VIEWPORT_WIDTH = 568;

// The results of the testing (each item will be a 2-list with [url, width])
results = [];

// Bind polyfill from
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/bind
if (!Function.prototype.bind) {
  Function.prototype.bind = function(oThis) {
    if (typeof this !== 'function') {
      // closest thing possible to the ECMAScript 5
      // internal IsCallable function
      throw new TypeError('Function.prototype.bind - what is trying to be bound is not callable');
    }

    var aArgs   = Array.prototype.slice.call(arguments, 1),
        fToBind = this,
        fNOP    = function() {},
        fBound  = function() {
          return fToBind.apply(
                this instanceof fNOP ? this : oThis,
                aArgs.concat(Array.prototype.slice.call(arguments)));
        };

    if (this.prototype) {
      // Function.prototype doesn't have a prototype property
      fNOP.prototype = this.prototype;
    }
    fBound.prototype = new fNOP();

    return fBound;
  };
}

// Exit if all the tests have finished
var maybeExit = function() {
    if (results.length !== system.args.length - 1) {
        return;
    }

    var success = true;
    for (var i = 0; i < results.length; ++i) {
        if (results[i][1] !== VIEWPORT_WIDTH) {
            console.log("TEST FAILURE: " + results[i][0] +
                        " failed with width " + results[i][1]);
            success = false;
        }
    }

    console.log("TEST FINISHED");
};

var args = system.args;
for (var i = 1; i < args.length; ++i) {
    var page = webpage.create();
    page.viewportSize = {width: VIEWPORT_WIDTH, height: 320};

    page.onLoadFinished = function(url) {
        setTimeout(function() {
            var width = this.evaluate(function() {
                return document.body.scrollWidth;
            });
            results.push([url, width]);
            maybeExit();
        }.bind(this), 1000);
    }.bind(page, args[i]);

    page.onError = function() {};

    page.open(args[i]);
}
