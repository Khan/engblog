KA Engineering Blog
===================

.. image:: https://travis-ci.org/Khan/engblog.svg?branch=master
	:target: https://travis-ci.org/Khan/engblog
	:alt: Travis build status

This repo houses the code used to build the `KA Engineering Blog <http://engineering.khanacademy.org>`_.

Usage
-----

In order to build and host the blog on your computer, first clone the repo, then run ``make deps``, and finally run ``make serve``.

.. code:: shell

	$ git clone https://github.com/Khan/engblog.git
	$ cd engblog
	$ make deps
	$ make serve

Linting
-------

Before committing any changes, make sure to run ``make lint``.


Publishing
----------

To publish your changes to the live site, follow these steps:

1. Discard any changes you've made to the ``output`` submodule/directory: ``bash -c 'cd output && git reset --hard && git clean -fd'``.
2. Commit the rest of your changes and push them to GitHub.
3. Run ``make ready-publish`` and follow the instructions it gives you.

After doing all that, your changes should be live! Yippee!
