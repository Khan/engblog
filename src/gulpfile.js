/* eslint-disable no-var */      // TODO(csilvers): does gulp support const?

var fs = require("fs");

var concat = require("gulp-concat");
var foreach = require("gulp-foreach");
var gulp = require("gulp");
var imagemin = require("gulp-imagemin");
var inject = require("gulp-inject");
var less = require("gulp-less");
var minifyCss = require("gulp-minify-css");
var minifyHTML = require("gulp-minify-html");
var minifyInline = require("gulp-minify-inline");
var shell = require("gulp-shell");
var webserver = require("gulp-webserver");
var argv = require("yargs").argv;

// Prefer PYTHON from the virtualenv, but if it doesn't exist, just
// use the system python.
var PYTHON = "../env/bin/python";
try {
    fs.statSync(PYTHON);
} catch (e) {
    PYTHON = "python";
}

/**
 * Runs the Phial app to generate the site.
 *
 * TODO(johnsullivan): Don't use a hardcoded directory.
 */
gulp.task("phial", shell.task([
    "rm -rf /tmp/engblog-phial",
    "mkdir /tmp/engblog-phial",
    PYTHON + " ./app.py /tmp/engblog-phial",
]));

function inlinePostCss(inputGlob, outputDir) {
    return gulp.src(inputGlob)
        .pipe(foreach(function(stream, file) {
            // Gather all of the CSS we want to inline in this post
            var css = (gulp
                .src(["styles/post-template.less",
                      "../bower_components/normalize.css",
                      "styles/pygments.css"])
                .pipe(less())
                .pipe(concat("all.css")))
                .pipe(minifyCss());

            return stream
                .pipe(inject(css, {
                    starttag: "<!-- inject:head:css -->",
                    transform: function(filePath, file) {
                        // return file contents as string
                        return (
                            "<style>" + file.contents.toString("utf8") +
                            "</style>");
                    },
                }));
        }))
        .pipe(minifyHTML({loose: true}))
        .pipe(minifyInline({css: false}))
        .pipe(gulp.dest(outputDir));
}

/**
 * Embeds each post page's CSS.
 */
gulp.task("inline-css", ["phial"], function() {
    return inlinePostCss("/tmp/engblog-phial/posts/*", "../output/posts/");
});

/**
 * The index page (which is just one of the posts) needs the same treatment
 */
gulp.task("inline-index-css", ["phial"], function() {
    return inlinePostCss("/tmp/engblog-phial/index.htm", "../output/");
});

/**
 * Move the RSS feed into the output directory.
 */
gulp.task("rss-feed", ["phial"], function() {
    // TODO(johnsullivan): Minify this. Stripping whitespace is probably the
    //     only safe thing we can do.
    return gulp.src("/tmp/engblog-phial/rss.xml").pipe(gulp.dest("../output"));
});

/**
 * Shortcut task to create the site's content.
 */
gulp.task("content", ["inline-css", "inline-index-css", "rss-feed"],
          function() {});

/**
 * Moves all of the images into the output directory (and optimizes them).
 */
gulp.task("images", function() {
    var source = gulp.src("images/**");

    if (argv.production) {
        source = source.pipe(
            imagemin({optimizationLevel: 5, progressive: true}));
    }

    return source.pipe(gulp.dest("../output/images"));
});

/**
 * Moves all of the videos into the output directory.
 */
gulp.task("videos", function() {
    var source = gulp.src("videos/**");

    return source.pipe(gulp.dest("../output/videos"));
});

gulp.task("supporting-files", function() {
    return gulp.src("supporting-files/**")
        .pipe(gulp.dest("../output/supporting-files"));
});

gulp.task("javascript", function() {
    return gulp.src("javascript/**")
        .pipe(gulp.dest("../output/javascript"));
});

gulp.task("default",
    ["content", "images", "videos", "supporting-files", "javascript"],
    function() {}
);

/**
 * Build and serve the site for testing.
 */
gulp.task("serve", ["default"], function() {
    gulp.watch(["**"], ["content", "images", "videos", "supporting-files"]);

    return gulp.src("../output")
        .pipe(webserver({
            // Uncomment this line to expose the webserver to your private
            // network (you would never do this on an unsafe public network
            // would you?).
            // host: "0.0.0.0",
            livereload: true,
            port: 9103,
            fallback: "index.htm",
            open: "",
        }));
});
