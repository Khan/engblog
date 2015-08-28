/*
 * Entry point to auto-render KaTeX in the article once loaded.
 */
var id = setInterval(function() {
    if (!(window.katex && window.renderMathInElement)) {
        return;
    }
    window.clearInterval(id);
    var article = document.getElementsByTagName('article')[0];

    // We add single-dollar delimiters because escaping Markdown is annoying.
    // Note that $$ must come before $ for the former to ever be parsed.
    var delimiters = [
        {left: "$$", right: "$$", display: true},
        {left: "$", right: "$", display: false},  // must come after $$
        {left: "\\[", right: "\\]", display: true},
        {left: "\\(", right: "\\)", display: false}
    ];
    renderMathInElement(article, { delimiters: delimiters });
}, 100);
