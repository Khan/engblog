title: The Great Python Refactor of 2017 And Also 2018
published_on: March 19, 2018
author: Craig Silverstein
team: Infrastructure
...

Our codebase was a mess.  One day, we decided to do something about
it: namely, move a bunch of files around.  It took us two months.

This blog post is first in a series describing the Great Khan Academy
Python Refactor of 2017 And Also 2018.  In this post, I'll explain
where our codebase went wrong, what we wanted to do to fix it, and why
it was so difficult.  It will include tips and code that others can
use to avoid some of this difficulty themselves.  The second post will
describe Slicker, a tool we wrote which formed the backbone of our
refactoring effort.  The third post will describe how we used this
refactoring as an opportunity to reduce inter-file dependencies within
our codebase, and how that benefited us.

So what was wrong with our codebase?  Take your pick:

1) We had files named ``parent.py``, ``coaches/parent.py``,
   ``users/parent.py``, and ``api/internal/parent.py``, all holding
   different bits of logic pertaining to parents of students on Khan
   Academy.
2) We had a method named ``login.login.Login.login``.  (If you're
   wondering, this method was part of the login process.)
3) Our top-level directory had 234 python files in it.  More than 10%
   of our codebase was in our root directory.  Not surprisingly, those
   files were not very related to each other.  There were low level
   utility files like ``ip_util.py``.  There were weird specialized
   utilities like ``dismissed_items.py``.  There was application logic
   like ``activity_summary.py``, and dev-only tools like
   ``appengine_stats.py``.  Oh, there were also 93 Python
   subdirectories.  (Plus a few more for non-Python code.)  While the
   root directory was overstuffed, 30 of these subdirectories
   contained 5 files or less.

Now all our parent-related code is in two Python files.  (One for the
API and one for everything else.)  The login method is now called
``login.handlers.ka_login.login_and_set_current``.  And there are half
as many Python subdirectories as before, and 1/20th (!) as many Python
files in the root directory.


How did it all go wrong?
========================

The glib answer is: bit by bit.  People created new subdirectories
thinking they would turn into major projects, but they didn't.  Or
they would create a new file and put it in the root directory because
the closest analogue was at the root level.  Eventually the problems
fed on themselves.  When you can't find existing code relevant to what
you're doing, you write new code in a new file.  And when the
organization of the codebase makes no sense -- when it doesn't relate
to the company's current products or organizational structure -- you
have no good place to put your new file so you put it somewhere
arbitrary.  Without anyone "owning" the structure of the codebase, it
never got any pruning or reshaping.


What did we do about it?
========================

Khan Academy set aside 6 weeks at the end of 2017 for the entire
company to work on paying down technical debt, and three of us decided
to use that time to whip (the Python portion of) our codebase into
shape. [*]_

We started with the subdirectories.  One of our senior engineers,
familiar with most of the codebase, decided on a preliminary list of
directories we would have.  Some of these reflected our products, such
as ``test_prep`` or ``translation``.  Others reflected our major data
structures and workflows, such as ``coaches`` or ``login``.  Some
reflected lower-level infrastructure, such as ``email`` or ``pubsub``.
They then spent two days bucketing every file in our codebase into one
of these directories.  A few dozen files defied categorization and
were marked TODO.

After this rough cut the real work began.  Another group went through
every file in the codebase again, and recategorized as appropriate.
During this process, directories went away and were added, were split
and merged. Files would end up moved somewhere else after more careful
examination.  Often, files were slated to be broken up, since they
held unrelated pieces of functionality.  (Some particularly large
files were split up into 4 different directories!)  There were no
shortcuts here; in this step we scanned through almost every line of
code in the codebase.

The most interesting result of this step of the process is how we
rethought some parts of our codebase.  For instance, historically our
``emails`` directory knew about every type of email we could ever send
a user.  As part of this analysis, we realized the code would be
cleaner if only the email-sending framework lived in ``emails`` (now
renamed ``email``), and each specific email lived with the code most
appropriate to it (SAT-related emails in ``sat``, new-user emails in
``login``, etc.)  Similarly, we moved our API handlers out of a single
``api`` directory and into their relevant project directories.  Both
organizations have their merits, but we had fallen into one of them by
default.  This process made us think about these alternatives
explicitly.

Once we knew what files we wanted to go where, we used ``slicker`` to
do the actual moving.  It works as a smarter ``mv``, not only renaming
the file but also fixing all imports as well as references in comments
and strings (such as ``mock.patch('path.to.symbol')``.)  It can also
move individual functions and classes from one file to another, which
we used to split up files.


Why was this hard?
==================

1. **Code review**.  While slicker worked very well, there were enough
   ambiguous cases that every change had to be carefully reviewed.
   For instance, we renamed ``feeds.py`` to
   ``content_render/rss/feeds.py``.  Now consider code like this:

   .. code:: python

       _MODULE_WHITELIST = ['feeds', ...]
       user_data['feeds'] = _get_feeds_for_user()

   In the first case we want to rewrite ``feeds`` to
   ``content_render.rss.feeds``, but in the second case we don't.  There
   is no way an automated tool can know this, so we depended on code
   review (and, of course, tests).  I spent entire days doing nothing but
   code reviews.

2. **Merge conflicts**.  This was the most unexpected time-sink.  We
   expected merge conflicts with people who were actually working on
   our codebase while we did the moves, and coordinated carefully with
   our co-workers to minimize those.  But we did not expect all the
   merge conflicts we had with ourselves.  While we thought we would
   be able to do many renames in parallel, when we tried it we got
   tons of merge conflicts.  This is because whenever you move a file,
   you change import statements in other files.  If ``somefile.py``
   has both ``import foo`` and ``import bar``, and you rename
   ``foo.py`` while I rename ``bar.py``, then we're both editing
   ``somefile.py``. Whoever lands their changes second has to merge in
   the other change.  Unfortunately, import statements tend to be
   clumped together, and git treats these two changes as a conflict
   (even though they're really not).  Each such conflict has to be
   resolved by hand.  Resolving merge conflicts took longer --
   sometimes significantly longer -- than actually creating the commit
   in the first place.

3. **Implicit dependencies on directory structure**.  We had plenty of
   files that would do things like ``datafile = os.path.join(__file__,
   '..', 'testdata', 'whatever')``.  With the reorganization this code
   broke.  Fixing all of these was tedious.

4. **Pickling**.  When the pickle library pickles a class or a function,
   it does so by full name: ``path.to.module.myfunc``.  If the class
   or function moves, you can no longer unpickle the data.  While
   complaints about pickle are nothing new, there is no getting around
   this particular problem: if you want to store the name of a
   function in persistent storage so you can call it later, you need
   *some* way of saying what that function is.  And in fact, we need
   to do just that for AppEngine's useful deferred-execution library,
   which we use a lot.  And all those uses were slated to break when
   we moved files around.

Enter pickle_util.  This is a wrapper around pickle that we use in
Khan Academy code, that lets you register symbol renames.  When the
pickle_util unpickler finds a class, function, or other symbol that it
cannot import, it checks a look-up table for the symbol's new
location.  It then tries to import the symbol from there instead.
This lets you transparently unpickle symbols even after they have
moved.  The `source code </supporting-files/pickle_util.py>`_
is easy to adapt for your own use (works with both pickle and
cPickle, but it's only tested on python2).

But we had a problem: we didn't know what symbols we needed to
register with pickle_util, because we don't have any master list of
which functions and classes might be pickled somewhere.  We *could*
just register every single symbol in our codebase with pickle_util,
but that's unwieldy and slow.  So instead we used another solution:
pickle guards.

A pickle guard is a "forwarding file" we create whenever we move a
file to a new location.  The pickle guard file lives at the old
location and just imports files from the new location.  This
forwarding file should never be imported by our code (since all
references should go to the new location now), but it will still be
imported by pickle when unpickling symbols that reference that old
location.  So we have it log a message whenever it's imported saying
"pickle is using a symbol from this file!"  We can then examine our
logs to see places we need to register symbols with pickle_util.  Once
the logs are all clear, we can delete the pickle-guard files and have
a nice, clean codebase.

Here's an example pickle-guard file for when we renamed
``google_analytics.py`` to ``analytics/google_analytics.py``:

.. code:: python

    logging.error("Should not be importing %s, "
                  "update pickle_util.py", __file__)

    from analytics.google_analytics import _construct_event_payload  # NoQA: F401
    from analytics.google_analytics import _fix_payload_unicode  # NoQA: F401
    from analytics.google_analytics import _send_event_to_ga_sync  # NoQA: F401
    from analytics.google_analytics import google_analytics_user_id  # NoQA: F401
    from analytics.google_analytics import mark_ga_activation  # NoQA: F401
    from analytics.google_analytics import send_event_to_ga  # NoQA: F401

We created pickle-guard files whenever we moved a file.  The code to
automate that is `here </supporting-files/generate_pickle_guards.py>`_.


What did we get right?  What did we get wrong?
==============================================

We did a lot of things right, I think.  We were smart to figure out
exactly what we were going to do before we started doing it; the
mechanics of the moves were intricate enough without having to keep in
mind the semantics as well.

And we were smart not try to do all this in a single "flag day", where
nobody could work on the core product while we did the move, with the
goal of avoiding merge conflicts.  We considered it, but flag days,
however tempting, are never a good idea.  And they would not have been
here.  There were so many unexpected gotchas that it would have been
more like a flag month.  By planning from the beginning to work around
others' schedules, we were able to mostly avoid merge conflicts with
other developers while not blocking anyone's work.

However, in retrospect I wish we had invested more in a tool to
automatically resolve merge conflicts with each other, so we didn't
have to continually fix up import blocks.  It was time consuming and
error prone, and probably could have been automated.

I also wish we had generated pickle guards in a separate commit from
the one that moved the file around.  As it is, we did all of it
together, and now git does not recognize our file moves as moves.
Instead, it sees that we edited ``google_analytics.py`` a lot (getting
rid of the old content and replacing it with the pickle-guard content)
and created a new, seemingly unrelated, file called
``analytics/google_analytics.py``.  Now ``git blame`` and ``git log
<file>`` do not work very well.  (We can use ``git blame -C``, which
works ok but is slow.  There's no good solution for ``git log``.)  We
could have easily avoided this by putting the move in its own commit.


Two months later
================

There's always a risk that the minute you've finished a cleanup like
this, the weeds start growing again.  But we've not found that to be
the case.  The clearer organization makes it more obvious where new
code should go, and it's easier for teams to focus their code in just
one or two directories that match their project.  Of course, as the
company introduces new products and sunsets old ones, the code
structure will need to change to match, but now it's obvious how to do
that.  And it's easier for even the most long-tenured engineer to find
their way around the codebase.  As for our new employees, they don't
know how good they have it.

--------------

.. [*] We focused on Python because the Javascript code was already
       fairly well organized: the better organized JS code is, the
       more compact the bundles that users download, and the faster
       the user experience.  Thus, JS code gets cleaned up as part of
       performance projects, while Python code does not.
