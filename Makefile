.PHONY: serve server deps build build-prod ready-publish reset-output push-to-live

build:
	-mkdir output
	cd src && gulp

build-prod:
	-mkdir output
	cd src && gulp --production

serve server:
	-mkdir output
	cd src && gulp serve

lint linc:
	env/bin/python khan-linter/runlint.py src/*.py src/gulpfile.js

deps:
	# Make sure we have a gh-pages branch so our output submodule has a proper
	# target.
	git fetch origin
	git branch gh-pages origin/gh-pages || true

	# We have a few submodules, make sure they're all set
	git submodule update --recursive --init

	# Create a virtual environment with all of our Python dependencies
	virtualenv --prompt '(engblog)' env
	env/bin/pip install -r ./khan-linter/requirements.txt -r ./requirements.txt

	# Install our bower dependencies
	npm install -g bower
	bower install normalize.css

	# Install khan-linter's dependencies
	cd ./khan-linter; npm install

	# Install our own dependencies (gulp likes to be installed globally and
	# locally).
	npm install -g gulp
	npm install
