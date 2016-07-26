title: "Ensuring transaction-safety in Google App Engine"
published_on: June 27, 2016
author: Craig Silverstein
team: Infrastructure
...

In last week's exciting post, I described an `alternative to
transactions </posts/user-write-lock.htm>`_ that we use at Khan
Academy, to ensure atomic datastore operations.

When used correctly, both the user-write lock and transactions are
effective at avoiding a particular form of database corruption -- call
it "data stomping."  Data stomping happens when two requests try to
modify the same datastore entity at the same time.

.. image:: /images/txn-timeline.png
  :align: center

Request B does not see A's modifications, and its PUT overwrites A's
PUT.  A's modifications are entirely lost, even when they don't
conflict with B's.

Transactions solve this problem by noticing the contention at request
B's ``put()`` time, and forcing request B to retry from the beginning.
Locks solve the problem by not allowing the time-overlap at all.

Note that for both techniques, you need to follow the ``GET - MODIFY -
PUT`` idiom. It is an error -- a db stomping waiting to happen -- to
do the ``GET`` outside the transaction/lock!

In this blog post, I describe the infrastructure we put in place at
Khan Academy (which uses Google App Engine) to notice that error, and
to make it easy to modify the source code to prevent it.  We are
making the source code available in two files:

- `db_hooks.py </supporting-files/db_hooks.py>`_: a generic
  db/ndb hooking infrastructure
- `txn_safety.py </supporting-files/txn_safety.py>`_: the specific
  hooks we use to detect and alert for transaction-safety violations


How do people use transactions (and locks) wrong?
-------------------------------------------------

The mistake people make is simple: they do the ``GET`` outside the
transaction (or lock).  Then when the transaction retries, it doesn't
re-GET, so you end up with request B stomping out request A's
changes.

You may think it's easy to remember to always do your ``GET``'s inside
a transaction, but there are many ways to get this wrong:

- You do the ``PUT`` in a function that's far removed from the
  ``GET``.
- You are given an entity and forget to run ``entity =
  entity.key.get()`` to "re-GET" inside the transaction
- There are multiple codepaths used to ``GET`` an object, and only
  some of them -- maybe the ones used 99% of the time, so everything
  seems mostly-fine -- are done inside the transaction
- The ``get()`` call gives a cached result

This last cause was a big problem for us: we would cache the entity
corresponding to the current user, for efficiency.  Then, whenever we
wanted to update the current user, we'd do
``get_current_user().modify().put()`` inside a transaction, without
realizing that ``get_current_user()`` was returning some cached entity
that was fetched way before the transaction started.

The solution is pretty straightforward, once you realize there's a
problem.  The issue is finding out there's a problem in the first
place, and then tracing through the code to find the problematic
``GET``.

A Taxonomy of Data Stomping Errors
----------------------------------

While the GET-outside-transaction error is the most common, there are
many related types of data corruption.  The infrastructure we put in
place catches the following three types:

**Stomping**
    Doing the ``PUT`` inside a transaction or user-lock, but not the ``GET``.

    .. code:: python

        @ndb.transactional
        def seems_ok_but_is_not(uid):
             user_data = UserData.get_from_id(uid)   # cached!
             user_data.points += 5
             user_data.put()
        
    The problem here is that ``get_from_user_id()`` gets the user-data
    entity from a cache.  So even though it looks like you're doing the
    GET from within the transaction, you're actually (potentially) just
    seeing some object that was gotten much earlier in the request,
    outside this transaction.

**Totally unprotected stomping**
    Doing a ``GET - MODIFY - PUT`` entirely outside a transaction or user-lock.

    .. code:: python

        def badfunc(user_data):
             user_data_again = db.get(user_data.key())
             user_data_again.points += 5
             user_data_again.put()

**Internal stomping**
    Doing two nested (or interleaved) ``GET - MODIFY - PUT``'s inside a
    single transaction/lock.

    .. code:: python

        @ndb.transactional
        def _internal_fn(uid):
           user_data1 = get_user(uid)
           user_data1.points += 5
           user_data1.put()
        
        @ndb.transactional
        def public_fn(uid):
           user_data2 = get_user(uid)
           user_data2.points += 10
           _internal_fn(uid)
           user_data2.put()

    The problem here is that ``user_data1`` and ``user_data2`` are totally
    different python objects.  When we do the ``user_data2.put()``, it
    totally overwrites the change made in ``user_data1``.  This is the
    classical db-stomping problem, but within a single request!

How To Use It
-------------

To get the benefits of transaction-safety checking, you must annotate
a db/ndb model with a decorator saying what method you use to
guarantee safe ``put()``'s:

#. ``@never_written_model()`` -- super rare!
#. ``@abstract_model()`` -- commonly for polymodels and utility classes
#. ``@structured_property_model()`` -- for (Local)StructuredProperty models
#. ``@written_once_model()`` -- easiest to use correctly (no need for
   transactions)
#. ``@written_in_transaction_model()`` -- you put get-modify-put in a
   transaction
#. ``@written_with_user_lock_model(lockid_fn)`` -- you put
   get-modify-put in a `user write lock </posts/user-write-lock.html>`_
#. ``@written_via_cron_model()`` -- appengine lets you schedule
   cron jobs; if an entity is only accessed via a cron job, we know
   two requests will never access that entity at the same time
#. ``@dangerously_written_outside_transaction_model()`` -- for legacy code
#. ``@dangerously_written_outside_transaction_model_or_user_lock()`` -- ditto

These instruct the transaction-safety system what kinds of violations
to look for.  There is much more documentation of each choice at the
bottom of `txn_safety.py </supporting-files/txn_safety.py>`_.  Note that
``@written_with_user_lock_model`` takes an argument: that should a be
a function that takes an entity and returns the ``lock_id`` for that
entity.  For instance, if the lock is protecting a single user, the
``lock_id`` might be the user-id.  This is necessary because a single
lock can protect many different entities.  Example:

.. code:: python

    @db_decorators.written_with_user_lock_model(lambda e: e.kaid)
    class UserVideo(db.Model):
        """A single user's interaction with a single video."""
        user = db.UserProperty(indexed=True)
        kaid = db.StringProperty(indexed=True)   # user's user-id
        video_key = object_property.KeyProperty(indexed=True)
        ...

Second, you have to wrap your WSGI application in the
transaction-safety middleware:

.. code:: python

    app = webapp2.WSGIApplication([...routes...])
    app = txn_safety.TransactionSafetyMiddleware(app)

Then you just run your application.  If there is a transaction-safety
violation, the system will log it:

.. code::

    Did a put() of the same entity from two different python objects: <class 'user_models.UserData'>.
    Other put:
    --- 
    File "/api/internal/scratchpads.py", line 408, in update_user_scratchpad old_points, old_challenge_status, client_dt, time_taken) 
    File "/api/internal/scratchpads.py", line 436, in add_actions_for_user_scratchpad finished=(progress == "complete")) 
    File "/scratchpads/models.py", line 2775, in record_for_user_and_scratchpad scratchpad=scratchpad) 
    File "/rewards/triggers.py", line 119, in update_with_triggers_no_put user_data, possible_badges, dry_run=dry_run, **kwargs) 
    File "/rewards/util_rewards.py", line 158, in maybe_award_badges_no_put badge.award_to(user_data=user_data, **kwargs) 
    File "/badges/cs_badges.py", line 450, in award_to user_data, self.name, self.description) 
    File "/notifications/cs_notifications.py", line 201, in send_certificate_notifications coach.put() 
    File "/user_models.py", line 4173, in put result = super(UserData, self).put(*args, **kwargs)
    ---
    Traceback (most recent call last): 
    File "/api/internal/scratchpads.py", line 408, in update_user_scratchpad old_points, old_challenge_status, client_dt, time_taken) 
    File "/api/internal/scratchpads.py", line 436, in add_actions_for_user_scratchpad finished=(progress == "complete")) 
    File "/scratchpads/models.py", line 2777, in record_for_user_and_scratchpad user_data.put() 
    File "/user_models.py", line 4173, in put result = super(UserData, self).put(*args, **kwargs) 
    File "/db_hooks.py", line 55, in wrapper hook(model_or_models) 
    File "/db_patching.py", line 613, in _examine_put_state _examine_tainted_put(entity) 
    File "/db_patching.py", line 605, in _examine_tainted_put % (type(entity), tb)) 

This is an example of "internal stomping."  If you had access to the
source code, these tracebacks would be enough to tell you that
``record_for_user_and_scratchpad`` does a ``get()`` + ``put()`` of
some user-data, and ``send_certificate_notifications`` does a nested
``get()`` + ``put()`` of the same user-data.

For power users, the source code documents functions like
``disable_user_write_lock_checking_in_test()``.

In the `last blog post </posts/user-write-lock.html>`_ I mentioned
that ``lock_util.py``'s ``fetch_under_user_write_lock`` could not be
used at that time.  Well, with the functionality in this blog post, it
can be!, making it really easy to re-fetch an entity -- or not, as
needed -- under the user write lock.

.. code:: python

   def update_points(user_data):
       with fetch_under_user_write_lock(user_data) as ud_again:
           ud_again.points += 5

If we are already under the write lock, this is a noop, otherwise it
will re-fetch the entity under the lock.  It works for both db and ndb
entities.


How It Works
------------

The basic approach of the transaction-safety infrastructure is to
annotate every datastore entity with a history of when it was
retrieved from the datastore and what the state of the world was at
the time: in transaction X, or under user lock Y.  At ``put()`` time,
it examines that history to make sure it's in the same transaction or
user lock -- or indeed in any transaction at all -- and complains if
so, giving a traceback of the ``put()`` call to help with debugging.
It also keeps track of whether the same entity was ``get()``-ed
multiple times, which is needed to detect internal stomping.

Here is a snippet from `txn_safety.py
</supporting-files/txn_safety.py>`_ to demonstrate how it works:

.. code:: python

        # For a newly created entity, we don't need a transaction.
        if not hasattr(entity, '_ts_get_nonce'):
            return     # not created via a get()
        get_transaction = getattr(
            entity, '_transaction_at_request_time', None)
        put_transaction = _transaction_object()
        if not get_transaction and not put_transaction:
            _ts_violation('Did not use a transaction')
        elif not get_transaction:
            _ts_violation('Did the get() outside a transaction')
        elif not put_transaction:
            _ts_violation('Did the put() outside a transaction')
        elif get_transaction != put_transaction:
            _ts_violation('Did the get() and put() in different txns')

The bulk of the complexity is actually in `db_hooks.py
</supporting-files/db_hooks.py>`_: the code for adding get-hooks and
put-hooks in App Engine db and ndb models.  While there is a `built-in
hook system for ndb
<https://cloud.google.com/appengine/docs/python/ndb/modelclass#hooks>`_,
it is not adequate for our purposes because it only hooks `get()`
calls, not queries.  And the older db library has no hooks at all.
``db_hooks.py`` provides a uniform interface for hooking all functions
that get or return entities in both db libraries.


Appendix: Non-Data Stomping Errors
----------------------------------

Data stomping is not the only problems you can run into with db data.
Here are 4 cases our infrastructure does not detect.

**Stale reads**
    ``GET`` + ``GET - MODIFY - PUT`` + ``<use first GET>``

    .. code:: python

        @ndb.transactional
        def goodfunc(user_data):
           user_data_again = user_data.key.get()
           user_data_again.points += 5
           user_data_again.put()
        
        def oopsfunc(user_data):
           if should_assign_points:
               goodfunc(user_data)
           if user_data.points > 100:   # stale read!
               ...

    The problem here is that ``goodfunc()`` updates ``user_data_again``,
    but leaves ``user_data`` untouched.  So the ``user_data.points`` read
    will never see the 5 points you just awarded!

**Consistency**
    Two ``PUT``'s that should be in a transaction together.

    This (not db data stomping) is the traditional motivation for using
    transactions.  If you are modifying both a coach and student to teach
    each about the other, that should happen inside a transaction.  We do
    nothing to check that you do.

**Overwrites**
    Two new-entity ``PUT``'s with the same key at the same time.

    If request A does ``MyModel(key='foo', value=1).put()`` and request B
    does ``MyModel(key='foo', value=2).put()``, only one will win and the
    other will be thrown away.

    App Engine provides ``get_or_insert()``, which you can use in lieu of
    ``put()`` in situations where that is a concern.  Note that this is
    only an issue if you explicitly specify a ``key`` param.
    Otherwise, unique keys are assigned automatically, and it's
    impossible for two new-entity ``put()``'s to conflict.

**Races**
    You want A's ``GET - MODIFY - PUT`` to happen before B's, but B goes
    before A.

    API X is a call that gives a user some points.  API Y is a call that
    sees if a user has enough points for a particular badge, and awards it
    if so.  You want to make sure, in your request, that API X is called
    before API Y.  But while our code guarantees those two API's won't
    update the user-data at the same time, nothing guarantees one request
    will run first.  You have to do that ordering constraint in your own
    code.
