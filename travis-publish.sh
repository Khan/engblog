#!/usr/bin/env bash

# Expand variables and fail on first error
set -e
set -x

if [[ "$TRAVIS_PULL_REQUEST" != "false" ]]; then
	exit 0
fi

if [[ "$TRAVIS" != "true" ]]; then
	echo "Refusing to run outside of Travis"
	exit 1
fi

# Install the publish key so SSH will use it
cp ./travis-publish-key ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

# Clone the gh-pages branch into its own repo and update it with the new output
git clone --branch gh-pages git@github.com:Khan/engblog.git ~/engblog
rsync -rv --delete --exclude=.git ./output ~/engblog

# Actually push to GitHub
cd ~/engblog
git add -f .
git config --global user.email "travis@travis-ci.org"
git config --global user.name "Sir Travis"
git commit -m "Publish by Travis (#$TRAVIS_BUILD_NUMBER)"
git push -q origin gh-pages
echo "Publish completed"
