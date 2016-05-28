#!/usr/bin/env bash

# Note that $(cd x; pwd) is simlar to $(realpath x)
TEST_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(cd "$TEST_DIR/.."; pwd)"
OUTPUT_DIR="$(cd "$ROOT_DIR/output"; pwd)"

"$ROOT_DIR/node_modules/http-server/bin/http-server" "$OUTPUT_DIR" -p 9104 -a 127.0.0.1 -d false -e htm &
SERVER_PID=$!

# Wait until the server starts up
until $(curl --head --fail http://127.0.0.1:9104 > /dev/null 2>&1); do
    sleep 1
done

# Grab a list of all the URLs (we do this by mining the RSS feed)
# TODO(johnsullivan): make a sitemap and then mine that
LINK_RE='<link>http://engineering.khanacademy.org\(.*\)</link>'
REPLACEMENT='http://127.0.0.1:9104\1'
URLS=$(
    curl http://127.0.0.1:9104/rss.xml 2> /dev/null |
    sed -n "s#$LINK_RE#$REPLACEMENT#p" |
    xargs echo
)

# By default, return a successful exit code
EXIT_CODE=0

for script in $TEST_DIR/*.js; do
    echo "Running $script"

    # Start the test
    PHANTOM_OUTPUT_FILE="$(mktemp /tmp/phantom-output.XXXXXXX)"
    phantomjs "$script" $URLS 2>&1 | tee "$PHANTOM_OUTPUT_FILE" &
    PHANTOM_PID="$!"

    # Wait until the test is finished
    until $(grep "TEST FINISHED" "$PHANTOM_OUTPUT_FILE" > /dev/null 2>&1); do
        sleep 1
    done

    # Kill phantomjs (it doesn't cleanly exit, so kill it for it)
    kill "$PHANTOM_PID"

    # Note whether there was a failure
    if $(grep "TEST FAILURE" "$PHANTOM_OUTPUT_FILE" > /dev/null 2>&1); then
        EXIT_CODE=1
    fi

    # Print the output of the test
    echo "Finished running $script. Output:"
    cat "$PHANTOM_OUTPUT_FILE"
    rm "$PHANTOM_OUTPUT_FILE"
done

# Make sure the HTTP server dies
kill "$SERVER_PID"

exit "$EXIT_CODE"
