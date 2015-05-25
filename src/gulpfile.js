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

/**
 * Runs the Phial app to generate the site.
 *
 * TODO(johnsullivan): Don't use a hardcoded directory.
 */
gulp.task("phial", shell.task([
    "rm -rf /tmp/engblog-phial",
    ("PYTHONPATH=../phial ../env/bin/python -m phial.__main__ --output " +
     "/tmp/engblog-phial -v ./app.py"),
]));

/**
 * Embeds each post page's CSS.
 */
gulp.task("inline-css", ["phial"], function() {
    return gulp.src("/tmp/engblog-phial/posts/*")
        .pipe(foreach(function(stream, file){
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
                    transform: function (filePath, file) {
                        // return file contents as string 
                        return (
                            "<style>" + file.contents.toString("utf8") +
                            "</style>");
                    }
                }));
        }))
        .pipe(minifyHTML({comments: true, loose: true}))
        .pipe(minifyInline({css: false}))
        .pipe(gulp.dest("../output/posts/"));
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
gulp.task("content", ["inline-css", "rss-feed"], function() {});

/**
 * Moves all of the images into the output directory (and optimizes them).
 */
gulp.task("images", function() {
    return gulp.src("images/*")
        .pipe(imagemin({optimizationLevel: 5, progressive: true}))
        .pipe(gulp.dest("../output/images"));
});

gulp.task("default", ["content", "images"], function() {});

/**
 * Build and serve the site for testing.
 */
gulp.task("serve", ["default"], function() {
    gulp.watch(["app.py", "index.htm", "post-template.htm", "rss.xml",
                "posts/*", "styles/*"],
               ["content"]);
    gulp.watch("images/*", ["images"]);

    return gulp.src("../output")
        .pipe(webserver({
            host: "0.0.0.0",
            livereload: true,
            port: 9103,
            fallback: "index.htm",
            open: "",
        }));
});
