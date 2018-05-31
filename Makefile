.PHONY: serve server deps build build-prod ready-publish reset-output
.PHONY: push-to-live phantomjs-tests deps

build: node_modules/.bin/gulp
	mkdir -p output
	cd src && ../node_modules/.bin/gulp

build-prod: node_modules/.bin/gulp
	mkdir -p output
	cd src && ../node_modules/.bin/gulp --production

serve server: node_modules/.bin/gulp
	mkdir -p output
	cd src && ../node_modules/.bin/gulp serve

# Runs phantomjs tests on what's in the output directory
phantomjs-tests:
	# TODO (INFRA-1347): tests are disabled because of unreliability
	#./phantomjs-tests/run-tests.sh

lint linc: khan-linter/runlint.py
	env/bin/python khan-linter/runlint.py src/*.py src/gulpfile.js \
				   phantomjs-tests/*.js

node_modules/.bin/gulp khan-linter/runlint.py:
	$(MAKE) deps

deps:
	# Make sure we have a gh-pages branch so our output submodule has a proper
	# target.
	git fetch origin
	git branch gh-pages origin/gh-pages || true

	# We have a few submodules, make sure they're all set
	git submodule update --recursive --init

	# Create a virtual environment with all of our Python dependencies
	virtualenv --prompt '(engblog)' env
	# These next two are separate so if they have conflicting/duplicate
	# requirements, ours win.
	env/bin/pip install -r ./khan-linter/requirements.txt
	env/bin/pip install -r ./requirements.txt

	# Install khan-linter's dependencies
	cd ./khan-linter; npm install

	# Install our own dependencies
	npm install
