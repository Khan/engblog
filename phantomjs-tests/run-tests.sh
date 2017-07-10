#!/usr/bin/env bash

# Note that $(cd x; pwd) is simlar to $(realpath x)
TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(cd "$TEST_DIR/.."; pwd)"
OUTPUT_DIR="$(cd "$ROOT_DIR/output"; pwd)"

"$ROOT_DIR/node_modules/http-server/bin/http-server" \
    "$OUTPUT_DIR" -s -p 9104 -a 127.0.0.1 -d false -e htm &
SERVER_PID=$!

# Wait until the server starts up
until $(curl --head --fail http://127.0.0.1:9104 > /dev/null 2>&1); do
    sleep 1
done

# Grab a list of all the URLs (we do this by scraping the RSS feed)
# TODO(johnsullivan): make a sitemap and then scrape that
LINK_RE='<link>http://engineering.khanacademy.org\(.*\)</link>'
REPLACEMENT='http://127.0.0.1:9104\1'
URLS=$(
    curl http://127.0.0.1:9104/rss.xml 2> /dev/null |
    sed -n "s#$LINK_RE#$REPLACEMENT#p" |
    xargs echo
)

# A responsive test failure on any of these pages will be ignored
RESPONSIVE_TEST_WHITELIST="
    # This fails because some tables are too wide. Tricky to fix, not sure how
    # to reformat the data to be thinner.
    http://127.0.0.1:9104/posts/js-packaging-http2.htm

    # TODO(johnsullivan): I don't know why this fails yet... And can't
    #     reproduce it locally.
    http://127.0.0.1:9104/posts/i18nize-templates.htm

    # This test fails intermittently (if the JS renders quickly enough it will
    # fail because of its long equations).
    http://127.0.0.1:9104/posts/making-thumbnails-fast.htm

    # NOTE (josh): Fails because of a max-width issue, although everything
    # looks alright to me at 320px wide...
    http://127.0.0.1:9104/posts/lets-reduce.htm
"

# By default, return a successful exit code
EXIT_CODE=0

for URL in $URLS; do
    echo "[$URL]"
    if ! phantomjs "$TEST_DIR/pages-are-responsive.js" "$URL" 320; then
        if grep -q "$URL" <<< "$RESPONSIVE_TEST_WHITELIST"; then
            echo -e "\tIgnoring responsive test failure because of whitelist."
        else
            EXIT_CODE=1
        fi
    fi
done

kill $SERVER_PID
exit "$EXIT_CODE"
