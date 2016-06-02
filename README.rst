Khan Academy Engineering Blog
===================

.. image:: https://travis-ci.org/Khan/engblog.svg?branch=master
	:target: https://travis-ci.org/Khan/engblog
	:alt: Travis build status

This repo houses the content and code used to build the `Khan Academy Engineering Blog <http://engineering.khanacademy.org>`_.

The instructions in this README are geared towards the general public. **If you're a KA employee** who wants to make a blog post, `this forge page <https://sites.google.com/a/khanacademy.org/forge/for-khan-employees/ka-engineering-blog>`_ is your best starting point.


Who can contribute?
-------------------

Anyone can contribute patches (`we're open source <https://github.com/Khan/engblog/blob/master/LICENSE.rst>`_) but posting to the blog is generally restricted to Khan Academy employees.


Building locally
----------------

The blog is a static website built using the code in this repo, from the content that is also in this repo.

In order to build and host the blog on your computer, first clone the repo, then run ``make deps``, and finally run ``make serve`` (if you just want to build the site into the ``output/`` directory without serving it, run ``make build`` instead of ``make serve``).

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

Create a new file in ``src/posts/`` with a ``.md`` extension if you want to write your post in `Markdown <https://help.github.com/articles/markdown-basics/>`_, or an ``.rst`` extension if you want to write your post in `reStructuredText <http://docutils.sourceforge.net/rst.html>`_. The file should contain some YAML frontmatter followed by your post's contents. For example:

.. code:: rst

	title: My great post file
	published_on: January 1, 2020
	author: Jane Doe
	team: Web Frontend
	async_scripts: ["javascript/some-javascript-i-want.js"]
	...

	Hello world! I'm some reStructuredText or Markdown!

The text above the three dots is parsed as YAML, the text below the three dots is parsed as `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ or `Markdown <https://help.github.com/articles/markdown-basics/>`_ depending on the file extension.

The available options of the frontmatter are:

``title``
  The title of your post (should be sentence case, ie: only the first word is capitalized). Regarding length, try not to make it so long that it exceeds two lines when rendered in the sidebar of the blog.

``published_on``
  The date your post was/will be/is published. Must be in the format ``Janurary 1, 2020`` (ie: ``[Full Month] [Day], [Full Year]``).

``author``
  The author's name. Must exactly match one of the keys of the ``authors`` dictionary in ``src/info.py``.

``team``
  The team at KA that the author belongs to (or feels like posting under). Must be one of ``Infrastructure``, ``Web Frontend``, ``Eng Leads``, or ``Team Design``. If your team is not listed, you can add another by adding a class to ``src/styles/post-template.less``. Search for ``team-infrastructure`` for the relevant code.
  
``async_scripts``
  A list of scripts to load. These will be loaded with the `async <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script#attr-async>`_ attribute.

If you'd like to add support for another markup language, see ``Post.get_html_content()`` in ``src/post.py``.


Publishing
----------

**If you're publishing a new blog post, make sure to update the upcoming post section first**, which you can do by editing the file ``src/info.py``.  You can find the information to update to in the `publish queue <https://app.asana.com/0/33397771830491/68184404290301>`_ -- or, at least, everything except the team, which you may need to figure out (from the list of categories above) yourself.  Or better yet, ask the author!  For team_class, just do ``team.lower().replace(' ', '-')``.

After this, just push your changes to master. `Travis <https://travis-ci.org/Khan/engblog>`_ will take care of everything else. 
You can ping `brownhead <https://github.com/brownhead>`_ (``@johnsullivan`` on HipChat) for help if anything explodes.

**If you're a KA employee**, make sure to follow `the remaining instructions on the forge page <https://sites.google.com/a/khanacademy.org/forge/for-khan-employees/ka-engineering-blog#TOC-Publishing->`_. This includes *at least* posting to the KA Engineering twitter account.
