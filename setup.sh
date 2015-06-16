# This setup must take place whether you are using MacOS or Linux

# Make sure we have a gh-pages branch so our output submodule has a proper
# target.
git fetch origin
git branch gh-pages origin/gh-pages || true

# We have a few submodules, make sure they're all set
git submodule update --recursive --init

# Create a virtual environment with all of our Python dependencies
virtualenv --prompt '(engblog)' env
env/bin/pip install -r ./khan-linter/requirements.txt -r ./requirements.txt

# Install khan-linter's dependencies
cd ./khan-linter; npm install

