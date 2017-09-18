#!/usr/bin/env bash

# This file (when run by Travis) will publish the site by pushing to the
# gh-pages branch of this repo.

# Expand variables and fail on first error
set -e
set -x

if [[ "$TRAVIS_PULL_REQUEST" != "false" ]]; then
	echo "Refusing to publish pull request"
	exit 0
fi

if [[ "$TRAVIS_BRANCH" != "master" ]]; then
	echo "Refusing to publish from non-master branch $TRAVIS_BRANCH"
	exit 0
fi

if [[ "$TRAVIS" != "true" ]]; then
	echo "Refusing to run outside of Travis"
	exit 0
fi

if [[ $(find ./output -type f | wc -l) < 100 ]]; then
	echo "Failed to generate output correctly."
	echo "Current Directory is $PWD"
	tree .
	exit 1
fi

# Install the publish key so SSH will use it. The publish key is encrypted in
# the git repo using Travis's public key, and is decrypted in the
# before_install step (see the .travis.yml file).
cp ./travis-publish-key ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

# Clone the gh-pages branch into its own repo and update it with the new output
git clone --branch gh-pages git@github.com:Khan/engblog.git ~/engblog
rsync -rv --delete --exclude=.git ./output/ ~/engblog/

# Actually push to GitHub
cd ~/engblog
git add -f .
git config --global user.email "travis@travis-ci.org"
git config --global user.name "Sir Travis"
git commit --allow-empty -m "Publish by Travis (#$TRAVIS_BUILD_NUMBER)" \
                         -m "Built from commit $TRAVIS_COMMIT"
git push origin gh-pages
echo "Publish completed"
