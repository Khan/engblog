KA Engineering Blog
===================

.. image:: https://travis-ci.org/Khan/engblog.svg?branch=master

This repo houses the code used to build the KA Engineering Blog, which is not yet live.

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
