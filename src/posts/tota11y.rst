title: tota11y - an accessibility visualization toolkit
published_on: June 8, 2015
author: Jordan Scales
team: Web Frontend
...

Today we're releasing `tota11y <http://khan.github.io/tota11y>`_ (`on GitHub <http://github.com/Khan/tota11y>`_), an accessibility visualization
toolkit that aims to reduce the friction of a11y testing.

.. image:: /images/tota11y-logo.png
   :alt: tota11y logo

Inspiration
===========

Accessibility is hard for many reasons. While current tooling provides
mechanisms for detecting most accessibility violations, there remains a
certain amount of disconnect between the developer and the problems they are
causing. Most of these errors are things we can't see, things that won't
affect us, and things without a perfect, exact *fix*.

tota11y aims to solve these problems by providing a fun, interactive way to
**see** accessibility issues. Not only should the web be fully accessible to
all, but developers should feel **empowered** to fix and prevent accessibility
violations from happening in the first place.

A bit of history
================

We've been explicitly working to improve the accessibility of `Khan Academy
<http://khanacademy.org>`_ since early January. In that time we've seen first
hand what it takes to go through each and every page on our website and fix
things that may prove to be troublesome to assistive technologies.

`John <http://ejohn.org>`_ and I were both very new to this, so we set out and
did our research, wrote some tests to detect violations using `Chrome's
Accessibility Developer Tools <https://github.com/GoogleChrome/accessibility-developer-tools>`_,
and got to work.

A few weeks later we had fixed a significant chunk of accessibility errors on
our site, and learned an immense amount about assistive technologies.

.. image:: /images/a11y-devtools.png
   :alt: Chrome's Accessibility Developer Tools reporting some errors on our homepage
   :width: 100%

Then the hard part came.

*We* felt capable of fixing most accessibility violations on our site, but
how could we spread that knowledge to *the team* efficiently? How could we make
every `Khan Academy employee <http://khanacademy.org/about/the-team>`_ feel
empowered to report and fix accessibility violations?

We gave talks, wrote docs, sent out emails, but regressions still popped up.
Our tests ran, but were flaky, and didn't gain the same level of respect as our
unit tests or linter.

Simply put, our dev team still didn't fully understand the problems they were
causing, and how to fix them.

Meet tota11y
============

About a month ago we set out to build `tota11y <http://khan.github.io/tota11y>`_
as an internal project for Khan Academy's "Web Frontend" team.

The aim was to make it as simple as possible for developers to do manual
accessibility testing as part of their normal work. Rather than requiring
our dev team to dig through long-winded audit reports for violations they
didn't understand, we wanted provide simple visualizations where they already
were - the browser, right in front of them.

So we started off with the idea of "annotations." We highlight parts of the
current document, either to point out errors, successes, or just to label
important tags like headings or `ARIA landmarks <http://www.w3.org/WAI/GL/wiki/Using_ARIA_landmarks_to_identify_regions_of_a_page>`_.

.. image:: /images/early-tota11y.png
   :alt: An early tota11y demo showing heading annotations
   :width: 100%

*A (very) early proof-of-concept for tota11y.*

We ran with this core idea of "annotations" and expanded it, as you'll see,
to include detailed error messages, suggestions for fixes, and more.

What can tota11y do
===================

tota11y is a `single JavaScript file <https://github.com/Khan/tota11y/releases/latest>`_ that you can include in your document like so:

``<script src="tota11y.min.js"></script>``

Once you see the glasses in the bottom left corner of your window, you're good
to go.

.. image:: /images/tota11y-button.png
   :alt: The collapsed tota11y toolbar, a small button with a glasses icon
   :width: 100%

tota11y currently includes `plugins <https://github.com/Khan/tota11y/tree/master/plugins>`_ for
the following:

* detecting images with/without alt text (and presentation images)
* labeling text with contrast violations (and suggesting appropriate color combinations)
* outlining a document's heading structure and pointing out any errors with it
* highlighting input fields without appropriate labels (and suggesting fixes based on context)
* labeling all ARIA landmarks on the page
* detecting unclear link text such as "Click here" and "More"

Many of these come directly from `Google Chrome's Accessibility Developer Tools <https://github.com/GoogleChrome/accessibility-developer-tools>`_.

.. image:: /images/tota11y-expanded.png
   :alt: The expanded tota11y toolbar displaying a list of plugins
   :width: 100%

Some plugins (like the landmarks plugin) are as simple as labeling parts of the
page.

.. image:: /images/tota11y-wikipedia.png
   :alt: tota11y highlighting aria landmarks on wikipedia.org
   :width: 100%

Others provide an extended summary of the page, like the headings plugin, using
what's known as the "info panel."

.. image:: /images/tota11y-wikipedia-headings.png
   :alt: tota11y highlighting heading tags and structure on wikipedia.org
   :width: 100%

Also using this info panel, we can report errors in more detail and offer
suggestions.

.. image:: /images/tota11y-github-contrast.png
   :alt: tota11y explaining contrast violations and offering suggestions on github.com
   :width: 100%

While we can't guarantee to solve all of your accessibility troubles, we think
this approach makes violations easier to digest and will inspire developers to
think differently about accessibility.

What's in store?
================

We want to see how others use tota11y, and figure out what other sorts of
accessibility violations we can help fix. Some ideas include:

* proper/improper usage of the "tabindex" attribute
* improper disabling of focus styling
* buttons that are not keyboard-accessible

We also want to continue building a solid API for tota11y, enabling developers
to write their own tota11y plugins which may not be included in the original
source.

And we're planning on bundling tota11y as a series of browser extensions to
make it easier to test websites without the need to include a script in your
application.

We hope using tota11y makes you feel empowered to spot, diagnose, and fix
accessibility issues on your webpages. Be sure to `check us out on GitHub <http://github.com/Khan/tota11y>`_ and let us know how we can help.
