title: "The User Write Lock: an Alternative to Transactions for Google App Engine"
published_on: June 20, 2016
author: Craig Silverstein
team: Infrastructure
...


Transactions are the standard method in Google App Engine's datastore
-- as in many databases -- to ensure atomicity.  This is true for both
atomic writes of multiple entities, and atomic writes of a single
entity:

.. code:: python

       @ndb.transactional
       def safe_watched_video(user_id, video):
            user = GetUser(user_id)
            user.num_videos_watched += 1
            user.put()
            video_log = GetUserVideoLog(user)
            video_log.add_watched_video(video)
            video_log.put()

       @ndb.transactional
       def safe_login_counter(user_id):
            user = GetUser(user_id)
            user.num_logins += 1
            user.put()

Transactions work by checking all the entities that you plan on
``put()``-ing at both the beginning and end of the function.  If
someone else had changed an entity in the datastore while the function
was running, the transaction rolls back the function and retries.

When people think of transactions, they often think of atomically
updating multiple entities; a transaction ensures that either both the
video-log and the user are updated, or neither is.  But the "someone
else can modify" problem exists just as much for a single entity,
which is why a transaction is needed even for ``safe_login_counter``.
Without it, if two processes called ``safe_login_counter()`` at the
same time with the same user_id, the db operations might end up
interleaved in such a way that causes ``num_logins`` to end up
incremented by 1, not by 2.


The trouble with transactions
-----------------------------

While transactions are effective, they can be hard to use,
particularly within Google App Engine.  One problem is that
transactions "freeze" the state of the datastore at the time the
transaction starts, yielding surprising results.  Suppose you have a
function like this:

.. code:: python

       @ndb.transactional
       def login_twice(user_id):
           login_info = GetLoginInfo(user_id)
           login_info.last_login = datetime.datetime.now()
           login_info.put()
           # Don't ask why, but we need to call this twice
           safe_login_counter(user_id)
           safe_login_counter(user_id)

You might expect this to update num_logins by 2, but in fact it only
updates it by 1, because when ``safe_login_counter`` calls ``get()``,
those call see the "frozen" datastore as it existed at the beginning
of ``login_twice``, ignoring the ``put()``'s that we did.

While this example is somewhat contrived, such a scenario does come up
(typically, as here, with nested transactions), and can be hard to
debug.  It comes up particularly with the older db interface, since
ndb does some caching to try to ameliorate the problem.

A second problem is that code inside transactions must be idempotent,
since it is can be called more than once if the transaction needs to
retry.  This is particularly difficult to ensure when using
transaction in relatively high-level code, which calls other functions
that may not be aware they're being called inside a transaction.

.. code:: python

       def update_points_after_watching_video(self, video):
            # protect against this being called twice.
            key = 'points_updated.%s.%s' % (user.id, video.id)
            if not memcache.get(key):
                self.points += video.points_value
                memcache.set(key, True)   # UNSAFE
   
       @ndb.transactional
       def update_after_watching_video(user_id, video):
           user = GetUser(user_id)
           user.update_points_after_watching_video(video)
           video_log = GetUserVideoLog(user)
           video_log.add_watched_video(video)
           video_log.put()

An equally serious problem is that you cannot do a datastore query
inside a transaction:

.. code:: python

       @ndb.transactional
       def update_videos_seen(user_id):
           user = GetUser(user_id)
           video_query = UserVideoLog.query().filter(
               UserVideoLog.user == user,
               UserVideoLog.finished_watching=True)
           user.video_count += video_query.count()  # ILLEGAL
           user.put()

This restriction has hit Khan Academy hard.  As with the idempotence
requirement, it's particularly onerous when using transactions in
higher-level code, which calls helper functions that do queries.  We
have one API endpoint that we call when a user successfully completes
an exercise, which updates a lot of state: the list of exercises a
user has done, of course, but also their proficiency model, list of
future recommended exercises, user notifications, etc.  Many of these
updates require datastore queries, often in helper functions buried
deep in the call-stack.  As a result, we cannot use transactions to
atomically update the user-state upon exercise completion.


Locking: a transaction alternative
----------------------------------

At Khan Academy, we have developed an alternative to transactions,
which we are introducing today, complete with `source code
</supporting-files/lock_util.py>`_.  This alternative uses a simple
locking scheme in lieu of transactions.  It works with transactions:
for a given datastore model, you can decide if you want to use
transactions or locking to protect its atomicity.  If you have a
function that updates two entities, one of which requires a
transaction and the other of which requires a lock, you can make your
function both transactional and lock-acquiring; the two can co-exist.

Locks are a simple way to ensure atomicity for a single entity: while
you hold the lock for an entity, nobody else can read or write the
entity.  It is easy to see how this ensures atomic operation.  (This
is a simplification; I discuss below how we allow concurrent read-only
operations while a lock is being held.)

As this simple description makes clear, locks have several
disadvantages:

* Unless your locks are very fine-grained, forcing other applications
  to wait while you hold a lock is less efficient than transactions
* When acquiring multiple locks, you have to worry about deadlock
* Locks do not use rollbacks, meaning they cannot guarantee "both or
  neither" update semantics
* Writing a global lockservice is actually quite hard

These problems are all solvable, as described below.  And the
advantages locks have -- intuitive data-access, no restrictions on
datastore queries -- make them very appealing in the right situations.

How our locks work
------------------

The pubic API is very simple:

.. code:: python

    class FinishedExercise(RequestHandler):
        def get(self, user_id):
            with lock_util.global_lock(key=user_id,
                                       wait_timeout=5):
                user = GetUser(user_id)
                update_exercise_stats(user)
                ...

Now the finished-exercise API call will only run once it has acquired
the lock for ``user_id`` from the lockservice.  In the meantime, no
other code that acquires the lock for ``user_id`` can run until this
routine has finished.  If we are unable to acquire the lock within 5
seconds, ``global_lock`` raises an exception.

While I describe this mechanism as a "lock" mechanism, it would be
more accurately described as a lease: when you acquire the lock, the
lockservice only promises it to you for a certain amount of time.
This works well in the context of App Engine because App Engine will
abort a request that takes too long (a minute for "frontend" requests,
10 minutes for "backend" requests).  We hard-code that knowledge into
``lock_util``, though you can override it using the ``lock_timeout``
parameter.  By using a leasing model, we ensure that a bug or
networking error can't cause a lock to be held forever.

The locking code logs when a lock was acquired and released, and if
there was contention when acquiring it.  This has had a surprising
benefit to us: it's made it significantly easier to diagnose the
sources of contention than it was with transactions.


When do locks make sense?
-------------------------

Transactions are more efficient than locks because typically locks are
too coarse.  At Khan Academy, we use a single lock for a user, which
protects all datastore entities associated with that user.  So if one
function wants to update a UserData entity, while the other wants to
update a UserVideoLog entity, they could both run in parallel in a
transaction world but would block each other in a locking world.

A per-user lock works well for us because typically a Khan Academy
user is only doing one thing at a time.  So it's unlikely that two
processes would want to update two different user-specific entities in
parallel.  (But see "batch processing," below.)  

In general we consider transactions to be superior to locks when they
work: when a model only needs protection in idempotent, low-level,
query-free code.  When possible, we'll use transacations even for
per-user models.  Likewise, we've never replaced existing uses of
transactions with locks.  Instead, we use locks to protect code that
previously ran entirely unprotected.

In our experience, a user lock is the most useful kind of lock to
have: it's unusual for two parallel requests to both be modifying
information about a single user, and there are typically many
datastore entities associated with a single user.  Acquiring a single
lock for the user at the beginning of the request can yield a lot of
datastore safety with very little cognitive cost.

Avoiding deadlock
-----------------

Whenever you acquire multiple locks at once, you have the potential
for deadlock.  At Khan Academy we attempt to avoid deadlock by having
a canonical order in which we acquire locks: first we acquire the lock
for the "current" user, then any children they have, then their coach,
etc.  If that doesn't work, the deadlock will be broken when a lease
expires.

That said, only rarely do we need to acquire multiple locks in a
single request.  If we used more kinds of locks than just a user lock,
this might become more of an issue.

Using locks with transactions
-----------------------------

Locks do not guarantee "both or neither" semantics.  Consider this
code:

.. code:: python

       def watched_video_locked(user_id, video):
            with lock_util.acquire_lock(user_id):
                user = GetUser(user_id)
                user.num_videos_watched += 1
                user.put()
                video_log = GetUserVideoLog(user)
                video_log.add_watched_video(video)
                video_log.put()


If ``add_watched_video`` throws an exception, we'll end up with
``num_videos_watched`` being updated but the video_log *not* being
updated.

The solution is simple: use a transaction as well.

.. code:: python

       @ndb.transactional
       def watched_video_locked(user_id, video):
            with lock_util.acquire_lock(user_id):
                ...

If we still have to use a transaction, what benefit is the lock?  The
answer is: we can use transactions more sparingly, in places where
their restrictions are less onerous.  In particular, at Khan Academy
we now use transactions only in low-level code, after we've done the
datastore queries we need to do, and in addition we do not have to
worry about all the problems (described above) that arise with
"nested" transactions.

Our global lockservice: memcache
--------------------------------

Implementing a reliable, global lockservice is not a trivial task.
Google has one it uses internally, called Chubby, but it is not made
available to App Engine users.  So we had to develop our own,
application-layer lockservice.  We did it using memcache.

On the face of it, memcache is a terrible choice for a lockservice,
because by design it does not guarantee that inserted items remain in
the cache.  It's not very useful to have a lockservice that's always
forgetting about your locks!

But in practice, this has not been a problem.  Locks are very small, so
are unlikely to fill a memcache by themselves.  And any reasonable
memcache implementation is going to evict old entries before new
ones.  Locks, by our design, are short-lived -- 10 minutes at most --
so are unlikely to be evicted.  (To be sure, I would feel less
confident were Khan Academy using a shared memcache instead of a
dedicated instance.)

The bigger problem with memcache is that you communicate with it over
the network, and the network can be flaky.  While memcache evictions
have not been a problem, failed memcache writes are a fact of
life for us.  We have to be careful handling them, since we do not
want our entire site to go down if memcache is unreachable.  We've
chosen to continue optimistically -- assume we have the lock even
though memcache has not confirmed it -- risking the potential for
non-atomic writes in order to gain site reliability.

On the plus side, memcache supports the operations a locking service
needs: atomic reads and writes, shared state across processes, and
fast access.

We implement the locking via busy-waiting: we do an atomic
memcache-create of the lock-key, and if it fails (meaning someone else
is holding the lock), we wait a second and then try again.  Once it
succeeds, we hold the lock.  At the end of the request, we do an
atomic memcache-delete to release the lock.  The "lease" functionality
comes automatically with memcache: when we create the memcache entry,
we do so with a timeout, causing memcache to automatically flush the
entry if we do not manually delete it first.


Batch processing
----------------

I mentioned above that the user-lock works well for us because
typically only one process is trying to access a single user at a
time.  There's one big exception to this rule though: batch processes
that run over all our users.  For instance, we have a nightly cronjob
that can award users time-based badges ("You've used Khan Academy
every day this month!").  It's very possible for a user's interactive
requests to run at the same time as the batch request hits that user.

To maintain interactive behavior in that situation, we have a simple
form of lock priority: locks can either say they are for interactive
tasks, or batch tasks.  (In practice, we determine this automatically
based on the url of the current request, but it could easily be an
input parameter.)  

We implement the priority scheme by having batch processes wait 1.1
seconds before first trying to acquire the lock.  Since any concurrent
client for the lock is retrying the memcache-create once a second,
this guarantees anyone else waiting will have a chance to acquire the
lock before the batch process does.  While interactive processes can
still starve each other, batch processes cannot starve interactive
ones.

Allowing read-only datastore access
-----------------------------------

There remains one final situation I promised to address: what to do
with read-only access.  You don't *need* to acquire a lock for
read-only access, and in general you don't want to, so that two
processes can read the same data the same time.  The trouble is the
code can't tell *a priori* that an access is going to be read-only
(and indeed, a data access in a low-level function might be read-only
in some cases but part of a read-write pattern in others).  We could
require applications to tell the locking system if an access was
read-only or not, but that's onerous and brittle.  We'd like to do
what transactions do, and automatically figure out if a read was
read-only or not at write-time, and to handle things appropriately in
either case.

We can't do that, but we can get close, by using runtime assertions.

Our basic scheme is to allow a process to read an entity without
holding the lock.  That is, we assume *all* reads are made by
read-only processes.  But we also keep track of the fact that that
process has read that entity without holding a lock.  If the process
then ever tries to ``put()`` the entity, we notice it had done a prior
read without a lock, and complain loudly at that time.

The fundamental idea here is that a process has to know if an
entity-read might lead to a subsequent write.  If so, it is the
application's responsibility to acquire the lock before the read.  We
have some runtime checks to make sure that happens.

But wait, there's more...
-------------------------

How these runtime checks are implemented in App Engine is a fascinating
story in its own right.  Stay tuned for our next blog post, where I
talk about that in a lot more detail.

In the meantime, if you're interested in the source code for our
locking scheme, `have at it </supporting-files/lock_util.py>`_!  The
uber-high-level `fetch_under_user_write_lock()` function requires some
code from the next blog post, but the rest of it is usable today.
