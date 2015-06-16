.PHONY: serve server deps build ready-publish reset-output push-to-live

build:
	cd src && gulp

reset-output:
	cd output && git checkout . && git clean -fd

ready-publish:
	# Build the site
	cd src && gulp

	# Commit the changes (if there are any changes to commit)
	cd output && git add -A
	cd output && if ! git diff-index --quiet --cached HEAD; then git commit -nm "publish"; else echo "No changes in output directory. Maybe you meant to run make push-to-live?" && exit 1; fi

	@echo
	@echo The blog has been built. Double check that all is well by running:
	@echo "    bash -c 'cd output; python -m SimpleHTTPServer 9029 2> /dev/null'"
	@echo And then going to http://localhost:9029 in your browser.
	@echo
	@echo When "you're" sure everything is OK, run
	@echo "    make push-to-live"

push-to-live:
	cd output && if ! git diff-index --quiet --cached HEAD || ! git diff-files --quiet || ! git ls-files --others; then echo "Output directory is dirty. Refusing to push to live." && exit 1; fi
	if ! git diff-index --quiet --cached HEAD; then echo "There are staged changes. Refusing to push to live." && exit 1; fi

	git add output && git commit -nm 'output substate'
	cd output && git push origin HEAD:gh-pages
	git push origin master

serve server:
	cd src && gulp serve

lint linc:
	env/bin/python khan-linter/runlint.py src/app.py src/gulpfile.js

deps:
	./setup.sh

	if [ `uname -s` = Linux ]; then ./linux-setup.sh; fi
	if [ `uname -s` = Darwin ]; then ./mac-setup.sh; fi

