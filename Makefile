.PHONY: serve server deps build

build:
	gulp

serve server:
	gulp serve

lint linc:
	env/bin/python khan-linter/runlint.py app.py gulpfile.js

deps:
	# We have a few submodules, make sure they're all set
	git submodule update --recursive --init

	# Create a virtual environment with all of our Python dependencies
	virtualenv --prompt '(engblog)' env
	env/bin/pip install -r ./khan-linter/requirements.txt -r ./requirements.txt

	# Install our bower dependencies
	npm install -g bower
	bower install normalize.css

	# Install our node dependencies (note that ./npm-shrinkwrap.json will be
	# used to get very particular versions of everything).
	cd ./khan-linter; npm install
	npm install
