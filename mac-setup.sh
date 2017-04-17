# Macs don't seem to need sudo access to install global npm modules
# so this can be run without sudo access

# Install our bower dependencies
npm install -g bower
bower install normalize.css

# Install our own dependencies (gulp likes to be installed globally and
# locally).
npm install -g gulp
npm install
