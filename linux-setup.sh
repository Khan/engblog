# Linux seems to need sudo access to install global npm modules so
# this script will ask for sudo access.

echo "This setup script needs your password to install things as root."
sudo sh -c 'echo Thanks'

# Install our bower dependencies
sudo npm install -g bower
bower install normalize.css

# Install our own dependencies (gulp likes to be installed globally and
# locally).
sudo npm install -g gulp
npm install
