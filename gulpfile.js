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
    ("PYTHONPATH=./phial ./env/bin/python -m phial.__main__ --output " +
     "/tmp/engblog-phial -v ./app.py"),
]));

/**
 * Embeds some CSS directly into a page/pages.
 *
 * This will use gulp-inject to directly embed CSS into an HTML file. This is
 * done to improve load times for first-time users (the bulk of our users).
 *
 * html_glob: A glob (or an array of globs) of HTML files to process.
 * page_css_glob: A glob (or an array of globs) of CSS files to embed into each
 *     page.
 * output_dir: The directory to dump the results into.
 */
function embed_css(html_glob, page_css_glob, output_dir) {
    return gulp.src(html_glob)
        .pipe(foreach(function(stream, file){
            // Gather all of the CSS we want to inline in this post
            var css = (gulp
                .src([page_css_glob, "bower_components/normalize.css",
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
        .pipe(gulp.dest(output_dir));
}

/**
 * Embeds each post page's CSS.
 */
gulp.task("inline-posts-css", ["phial"], function() {
    return embed_css("/tmp/engblog-phial/posts/*", "styles/posts-template.less",
                      "output/posts/");
});

/**
 * Embeds the index's CSS.
 */
gulp.task("inline-index-css", ["phial"], function() {
    return embed_css("/tmp/engblog-phial/index.htm", "styles/main-page.css",
                      "output/");
});

/**
 * Move the RSS feed into the output directory.
 */
gulp.task("rss-feed", ["phial"], function() {
    // TODO(johnsullivan): Minify this. Stripping whitespace is probably the
    //     only safe thing we can do.
    return gulp.src("/tmp/engblog-phial/rss.xml").pipe(gulp.dest("output"));
});

/**
 * Shortcut task to create the site's content.
 */
gulp.task("content", ["inline-posts-css", "inline-index-css", "rss-feed"],
          function() {});

/**
 * Moves all of the images into the output directory (and optimizes them).
 */
gulp.task("images", function() {
    return gulp.src("images/*")
        .pipe(imagemin({optimizationLevel: 5, progressive: true}))
        .pipe(gulp.dest("output/images"));
});

gulp.task("default", ["content", "images"], function() {});

/**
 * Build and serve the site for testing.
 */
gulp.task("serve", ["default"], function() {
    gulp.watch(["app.py", "index.htm", "posts-template.htm", "rss.xml",
                "posts/*", "styles/*"],
               ["content"]);
    gulp.watch("images/*", ["images"]);

    return gulp.src("output")
        .pipe(webserver({
            livereload: true,
            port: 9103,
            fallback: "index.htm",
            open: "",
        }));
});
