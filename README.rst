Khan Academy Engineering Blog
===================

.. image:: https://travis-ci.org/Khan/engblog.svg?branch=master
	:target: https://travis-ci.org/Khan/engblog
	:alt: Travis build status

This repo houses the code used to build the `Khan Academy Engineering Blog <http://engineering.khanacademy.org>`_.

The instructions in this README are geared towards the general public. If you're a KA employee who wants to make a blog post, `this forge page <https://sites.google.com/a/khanacademy.org/forge/for-khan-employees/ka-engineering-blog>`_ should be your best starting point.


Who can contribute?
-------------------

Anyone can contribute patches (`we're open source <https://github.com/Khan/engblog/blob/master/LICENSE.rst>`_) but posting to the blog is generally restricted to Khan Academy employees.


Building locally
----------------

In order to build and host the blog on your computer, first clone the repo, then run ``make deps``, and finally run ``make serve`` (if you just want to build the site into the ``output/`` directory without serving it locally, run ``make build`` instead).

.. code:: shell

	$ git clone https://github.com/Khan/engblog.git
	$ cd engblog
	$ make deps
	$ make serve


Linting
-------

Before committing any changes, make sure to run ``make lint``.


Making a new post
-----------------

Create a new file in ``src/posts/`` with a ``.rst`` extension. It should follow the format:

.. code:: rst

	title: My great post file
	published_on: January 1, 2020
	author: Jane Doe
	team: Web Frontend
	...

	Hello ``world``!

The text above the three dots is parsed as YAML, the text below the three dots is parsed as `reStructuredText <http://docutils.sourceforge.net/rst.html>`_.

If you haven't posted before, you'll need to add yourself as an author to the ``src/info.py`` file. **You also need to update the upcoming post section**, which you can do from that same file.

Note that supporting other markup languages is trivial, including HTML and custom CSS and all kinds of crazy JS (including Perseus), just `open up an issue <https://github.com/Khan/engblog/issues>`_, ping ``@johnsullivan`` on HipChat (KAers only), or dive into the code yourself!


Publishing
----------

To publish your changes to the live site, just push your changes to master. `Travis <https://travis-ci.org/Khan/engblog>`_ will take care of everything else.

You can ping `brownhead <https://github.com/brownhead>`_ (``@johnsullivan`` on HipChat) for help if anything explodes.

**If you're a KA employee**, and you just finished publishing to the live site, make sure to follow `the remaining instructions on the forge page <https://sites.google.com/a/khanacademy.org/forge/for-khan-employees/ka-engineering-blog#TOC-Publishing->`_. This includes *at least* posting to the KA Engineering twitter account.
