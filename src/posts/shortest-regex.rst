title: "Minimizing the length of regular expressions, in practice"
published_on: May 23, 2016
author: Craig Silverstein
team: Infrastructure
...

The problem
-----------

Software engineering interviews tend to be full of "algorithms"
questions, because they're easy to explore in an hour, unlike the
messy problems that most programmers deal with day-to-day: moving data
from one place to another, error checking and recovery, etc.  Most times
when I do have to use a fancy algorithm, there's already a library to
do it for me.  But every so often I come across the need for a novel,
non-trivial algorithm.  This happened to me the other week, and the
process of getting it to work was, I think, really interesting.

Here is the problem: we wanted to improve the way we serve Khan
Academy urls by fetching our static urls (images, fonts, etc) from a
different place than our dynamic urls (homepage, /exercises, etc).
The way we would do this would be to give our CDN (the cache-friendly
frontend that actually gets our urls are forwards them on to us) a
regular expression that matches all our static urls.  The CDN would
know what to do based on whether the regexp matched the incoming url
or not.

Here's the trick: our CDN limits the size of this url to 512
characters.

It would be nice if we could just have a url like ``^/static/.*``, but
sadly our static urls are not organized in any way, and some of them
are in third-party code, so it's not practical to just reorganize
them.

It would also be nice if we could just have a regexp like
``.*\.(js|css|png|jpg|pdf)``, but sadly, we have some png files that are
dynamically generated, and we have other dynamic routes that would
match that regexp as well, such as
``/api/internal/ios/static_redirect/mobile-exercise-content-5.css``.

So I had to do something more clever.


My assets
---------

Google Appengine, which is the hosting platform we use, has you
specify which resources are static files for its own purposes.  You do
this via a configuration file that has entries like this:

.. code:: yaml

    - url: /images
      static_dir: images

    - url: /((fonts|khan-exercises|third_party)/.*\.eot)
      static_files: \1
      mime_type: application/vnd.ms-opentype
      upload: ((fonts|khan-exercises|third_party)/.*\.eot)

    - url: /((fonts|khan-exercises|third_party)/.*\.woff)
      static_files: \1
      mime_type: application/vnd.ms-opentype
      upload: ((fonts|khan-exercises|third_party)/.*\.woff)

The first kind just says that urls of the form ``/images/*`` should be
served by files on the local filesystem named ``images/*``.  The second
kind is more complicated: images matching that input regexp should be
served by files matching the ``static_files`` parameter.  (``\1`` means:
everything inside the outermost parenthesis of ``url``.)


First solution: 402,025 characters long
=======================================

The naive approach I tried first was to just use values of
``static_dir`` and ``static_files`` from the config file, match them
against every file in our repository, and join them all together into
a big regexp:

.. code::

    ^/downloads/KAOperationalPlan.xls$|
    ^/downloads/KhanAcademyAccounts.pdf$|
    ...|
    ^/videos/homepage-background.webm$

This regular expression was too big for our CDN.

It's also very fragile: we'd need to update the regexp in our CDN
every time we added a new static file to our filesystem.

Second solution: 2,400 characters long
======================================

Next, I realized that the config file already listed regular
expressions, so I could just concatenate those together instead:

.. code::

    ^/images|
    ^/((fonts|khan-exercises|third_party)/.*\.eot)|
    ^/((fonts|khan-exercises|third_party)/.*\.woff)|
    ...

This is a lot smaller than the above solution, and also more robust
since we'd only need to change the CDN regexp any time we changed
the config file, not every time we added a new file to our
filesystem.

But it was still well over the 512 character limit.

Third solution: 824 characters long
===================================

My next thought was to take the url from the second solution, and
"optimize" it.  The problem of how to minimize a regular expression is
actually well studied.  Unfortunately, the studying is to show how
hard it is.  (`PSPACE-complete <https://people.csail.mit.edu/meyer/rsq.pdf>`_,
which is -- probably -- even harder than NP-complete.)

(There's also several `well known results <https://en.wikipedia.org/wiki/DFA_minimization>`_
as to how to minimize the number of states in deterministic finite
automata.  But while DFAs are very closely related to regular
expressions, minimizing the number of states in a DFA is not very
related to minimizing the number of characters in a regular
expression.)

But there are things you can do in practice to get a smaller regexp,
even if not a minimal one, and it may be enough for your purposes.  In
this case, the biggest win seemed to be in combining shared prefixes,
to end up with a url like:

.. code::

    ^/images|
    ^/((fonts|khan-exercises|third_party)/.*\.(eot|woff))|
    ...

I could not find any resources for how to combine shared prefixes in
regular expressions, so I had to come up with an approach on my own.
This was surprisingly difficult.

My first approach was to just sort the regexp patterns and then go
through them one by one, keeping track of how
much of the prefix of this url matched the next one.  This worked in
simple cases, but I could not figure out how to get it to do the right
thing for nested parens like ``g(a(e_mini_profiler/|ndalf/)|enfiles/)``. 

I gave up on that approach and eventually came around to an approach
that just did one combine-step at a time.  Given my list of regexps
that I wanted to join together with ``|``, I'd find the two that shared
the longest prefix.  (If there were multiple such pairs, I picked one
arbitrarily.)  I'd then combine those two to be
``<prefix>(<suffix1>|<suffix2>)``.  I'd then repeat this algorithm
again, but with one fewer regexp in my list than before.  Eventually
my "list" would have only one regexp in it, and I'd be done.

There were two wrinkles to this approach.  Sometimes three or more
regexps would share a longest prefix:

.. code::

    ^/((fonts|khan-exercises|third_party)/.*\.eot
    ^/((fonts|khan-exercises|third_party)/.*\.woff
    ^/((fonts|khan-exercises|third_party)/.*\.otf

In that case, I'd combine all of them at once.

Second, I had to be careful of cases where the shared longest prefix
was inside parentheses:

.. code::

    ^/((fonts|khan-exercises|third_party)/.*\.woff
    ^/((fonts|khan-exercises)/.*\.svg

I didn't want to combine them to get
``^/((fonts|khan-exercises(|third_party)/.*\.woff|)/.*\.svg)``!  That
does not match what I want it to match.  So I had to tokenize the
regular expressions first, so that each parenthetical expression was
considered a single "charcter".

Afer all this work, my regular expression had lots of nice parentheses
in it, but was still 824 characters long.

Fourth solution: 208 characters long
====================================

This is where I had my big breakthrough.  I realized my goal wasn't to
find a regexp that matched all our static file urls, it was to find a
regexp that distinguished our static-file urls from our dynamic urls.

This difference is subtle but important.  For the second formulation
we don't care what our regexp does with invalid Khan Academy urls,
that is, urls that yield a 404.  (In the first case, we'd have to make
sure that all invalid KA urls were judged not-static.)  After all, we
don't care if our static-content provider or our dynamic-content
provider is the one who gives the 404!

After this realization, I changed the way I thought about the
static-file url regexps in our config file.  I took each such regexp
and shortened it to the shortest prefix that didn't match any of our
dynamic urls (such as ``/videos/*``).

This yielded a very minimal regexp: I could shorten, say,
``^/genfiles/javascript/.*|^/genfiles/stylesheets/.*`` to just ``^/ge``.
The result was well under 512 characters!

Fifth solution: 294 characters long
===================================

The fourth solution worked, but it was probably *too* minimal.  If
someone were to later add a dynamic route ``/get_id``, say, to our
website, the regexp-pattern ``^/ge`` would cause the CDN would think
that all ``/get_id`` urls were actually for a static file, and not
forward them to the right place.  This would cause confusion and
trouble.

We could go through efforts to make sure everyone updated the CDN
regular expression every time they added a dynamic route to our app,
but that seemed like a lot of work and also error-prone.

So instead I made the prefixes a bit less minimal, by forcing them to end
on a slash.  So instead of taking the unique prefix ``^/ge``, we'd take
the still-unique prefix ``^genfiles/``.

This increased the sizes of our regexp by almost 50%, but it's still
well under 512 characters, and the robustness improvement makes it
well worthwhile.

The big reveal
--------------

Are you curious what our final url was?  Here it is.  (I've broken it
into multiple lines to make it a bit easier to read.)

.. code::

   ^/(
   (fonts|khan-exercises|third_party)/.*\.(eot$|otf$|svg$|ttf$|woff($|2$))|
   .well-known/apple-app-site-association$|
   admin/extbackup/static/|
   ckeditor/|
   downloads/|
   g(a(e_mini_profiler/static/|ndalf/static/)|enfiles/)|
   images/|
   javascript/|
   khan-exercises/(css/|images/|third_party/|utils/)|
   s(ounds/|tylesheets/)|
   third_party/|
   videos/
   )

Not the shortest url in the world -- there are some mini-optimizations
that could make it even smaller, such as replacing ``($|2$)`` with
``2?$`` -- but well within the 512-character limit, and pretty
reasonable to read.

If you're interested in seeing how we got this, here is
the `source code </supporting-files/shortest_regex.py>`_.  The bits to
calculate the input routes are specific to Khan Academy, but the rest
should be more generally useful.
