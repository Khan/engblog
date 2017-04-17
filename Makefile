.PHONY: serve server deps build build-prod ready-publish reset-output \
		push-to-live phantomjs-tests

build:
	-mkdir output
	cd src && gulp

build-prod:
	-mkdir output
	cd src && gulp --production

serve server:
	-mkdir output
	cd src && gulp serve

# Runs phantomjs tests on what's in the output directory
phantomjs-tests:
	./phantomjs-tests/run-tests.sh

lint linc:
	env/bin/python khan-linter/runlint.py src/*.py src/gulpfile.js \
				   phantomjs-tests/*.js

deps:
	./setup.sh

	if [ `uname -s` = Linux ]; then ./linux-setup.sh; fi
	if [ `uname -s` = Darwin ]; then ./mac-setup.sh; fi

