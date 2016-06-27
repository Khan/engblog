"""Code that monkey-patches GAE's db and ndb classes to ensure txn safety.

"Transaction safety" means detecting and logging instances of possible
corruption of datastore contents.  For more information, see
    http://engineering.khanacademy.org/posts/transaction-safety.htm

This system works to detect safety violations for both db/ndb
transactions, and for Khan Academy-style user locks as described in
    http://engineering.khanacademy.org/posts/user-write-lock.htm

USAGE
-----

1) You need to wrap your WSGI app in TransactionSafetyMiddleware:
     app = webapp2.WSGIApplication([...routes...])
     app = txn_safety.TransactionSafetyMiddleware(app)

2) You will need to decorate all your db and ndb Models with one of the
   decorators at the bottom of this file: @written_in_transaction_model(),
   etc.

Then, just run your app normally.  If there are any unsafe operations
in your code, they will be logged, including a stacktrace to help with
debugging.  You can also change the code to raise on unsafe
operations, which may help when developing (using dev_appserver.py on
your local machine, say).
"""

import contextlib
import os
import logging
import random
import threading
import traceback

from google.appengine.api import datastore

import db_hooks
# lock_util defines KA-style write locks, and is needed to guarantee
# txn-safety for them.  If you don't use write locks, then you don't
# need this file.  (We'll die with an attribute-error if you use
# @written_with_user_lock_model anywhere in your code.)
# See http://engineering.khanacademy.org/posts/user-write-lock.htm
try:
    import lock_util
except ImportError:
    lock_util = None


# If this is true, we will raise an exception when we notice a
# transaction-safety violation.  If it's false, we will just log an
# error and continue.  Regardless of this value, we will raise an
# error if we detect we are running in a test (because *_test.py is in
# the stacktrace).
_RAISE_ON_TS_VIOLATION = False


def _user_lock_nonce_for(entity):
    """Return lock-id of the user lock for this entity, or None if not held."""
    lockid_fn = entity._transaction_safety_kaid_fn
    if callable(lockid_fn):
        lock_id = lockid_fn()  # might also be None; see below.
    else:
        lock_id = None
    if lock_id is not None:
        return lock_util.nonce_of_user_write_lock_held_by_request(lock_id)
    else:
        # This can happen when we haven't written the lockid-fn for this
        # entity yet (it's a TODO).  We just log it and just store
        # whether we have *any* user lock or not.  This isn't perfect:
        # we could still see a transaction-safety error if hold
        # multiple user-locks, guess the wrong one here, and later add
        # a lock_id to the entity.  But that should be pretty rare.
        logging.info("Entity has no lock_id (or no lockid_fn): %s"
                     % type(entity))
        return lock_util.nonce_of_any_user_write_lock_held_by_request()


def _transaction_object():
    """Return the transaction this entity is currently under, or None."""
    try:
        return getattr(datastore._GetConnection(), 'transaction', None)
    except Exception as e:
        # Probably means the internal _GetConnection() function went away.
        logging.error("datastore._GetConnection() isn't working!: %s" % e)
        return None


_REQUEST_STATE = threading.local()


def _is_running_tests():
    """An imperfect check for whether we're in a test: we see *_test.py."""
    for (fname, _, __, ___) in traceback.extract_stack():
        if '_test.py' in fname:
            return True
    return False


def _set_transaction_safety_enforcement_policy(policy):
    """Specify the policy for enforcing the transaction safety via db hooks.

    This controls whether we raise/log errors or not (whether a
    given error is logged or raised is determined by whether we're in
    test, dev, or prod). The policy can be one of the following:

    ts-enforce-all: All transaction enforcement policies are enabled, causing
        any violation to be logged or raised. This is the default in dev/prod.
    ts-enforce-none: All transaction enforcement policies are ignored, and
        nothing is logged or raised when the policy is violated. This policy
        can be temporarily set via suppress_transaction_safety_checks_in_test
        or dangerously_suppress_transaction_safety_checks.
    ts-enforce-all-except-user-lock: All transaction enforcement policies are
        enabled, except enforcement of the user write lock. This is available
        for historical reasons but is not recommended.
    """
    assert policy in ('ts-enforce-none', 'ts-enforce-all',
                      'ts-enforce-all-except-user-lock'), policy
    _REQUEST_STATE.ts_enforcement_policy = policy


def _get_transaction_safety_enforcement_policy():
    if not hasattr(_REQUEST_STATE, 'ts_enforcement_policy'):
        if _is_running_tests():
            _REQUEST_STATE.ts_enforcement_policy = 'ts-enforce-all'

    return _REQUEST_STATE.ts_enforcement_policy


def _truncated_backtrace():
    """Return a stacktrace without useless middleware and db-hook calls.

    A 'full' appengine traceback is full of a bunch of useless frames:
    GAE framework code, third-party wrapper code, decorator code
    (including flask decorator 'middleware').  Wading through these is
    annoying, and they can cause problems with GAE's max-log-line
    limits.  This function just gets rid of them, and returns a list of
    stack objects with them removed.
    """
    # We get rid of these frames, which are part of our reporting
    # system, and appear at the end of all stack traces.
    files_holding_wrapper_code = ['db_hooks.py', 'txn_safety.py']
    # TODO(csilvers): support other frameworks as well.
    _MIDDLEWARE_FILES = ['webapp2.py']

    stack = traceback.extract_stack()
    last_middleware_call = max(i for i in xrange(-1, len(stack))
                               if (i == -1 or
                                   any(f in stack[i][0]
                                       for f in _MIDDLEWARE_FILES)))
    last_wrapper_call = max(i for i in xrange(-1, len(stack))
                            if (i == -1 or
                                any(f in stack[i][0]
                                    for f in files_holding_wrapper_code)))
    if last_wrapper_call == -1:
        last_wrapper_call = len(stack) - 1

    # The wrapper-file can call other internal functions inside it, so
    # we actually want "the first wrapper-file call in the last
    # run-of-wrapper-file calls."
    while (last_wrapper_call > 0 and
           any(f in stack[last_wrapper_call - 1][0]
               for f in files_holding_wrapper_code)):
        last_wrapper_call -= 1

    stack = stack[last_middleware_call + 1:last_wrapper_call]
    return traceback.format_list(stack)


def _add_to_get_put_list(entity, get_or_put):
    """Add this entity to the per-request get-and-put list if it has a key.

    get_or_put is either the string 'get' or the string 'put'.  Returns
    the newly updated get-put-list, or None if we couldn't add this entity
    to the list (because it's a put without a corresponding get).
    """
    get_nonce = getattr(entity, '_ts_get_nonce', None)
    if get_nonce is None:
        return None

    # The entity should definitely have a key if _ts_get_nonce is set,
    # since that means this entity was retrieved via a get().
    entity_key = entity.key() if callable(entity.key) else entity.key

    # Each entry is ('get' or 'put', python_id, backtrace).  For efficiency,
    # I only store the backtrace for put's.
    backtrace = (''.join(_truncated_backtrace()) if get_or_put is 'put'
                 else None)

    if not hasattr(_REQUEST_STATE, 'ts_get_put_list'):
        _REQUEST_STATE.ts_get_put_list = {}
    get_put_list = _REQUEST_STATE.ts_get_put_list.setdefault(entity_key, [])
    get_put_list.append((get_or_put, get_nonce, backtrace))
    return get_put_list


def _store_get_state(entity):
    """After a get, store data on the entity that we will use to sanity-check.

    In general, this is data that we will look at again at put time,
    to make sure that the get and put were in the same transaction,
    say.

    We store the data on the entity itself, in a protected field named
    '_ts_<whatever>'.  ('ts' == 'transaction safety')
    """
    entity._ts_get_nonce = random.random()

    # If this entity is for a user-specific db model, store whether
    # the user lock for this user is currently set.
    # NOTE: for historical reasons, the thing holding the lock-nonce
    # is (very confusingly) called _ts_user_lock_id.
    if getattr(entity, '_transaction_safety_policy', None) == 'user-specific':
        entity._ts_user_lock_id = _user_lock_nonce_for(entity)
    elif hasattr(entity, '_ts_user_lock_id'):
        del entity._ts_user_lock_id

    # Add this get to our list of get's and put's for this entity, so
    # we can detect bad interleaving of get's and puts.
    _add_to_get_put_list(entity, 'get')


class TransactionSafetyViolation(Exception):
    """Raised when code violates a model's transaction safety policy."""
    pass


def _ts_violation(msg):
    """Log or raise a transaction safety violation."""
    if _RAISE_ON_TS_VIOLATION or _is_running_tests():
        raise TransactionSafetyViolation(msg)
    else:
        logging.error(msg)


def _examine_ts_policy(entity):
    """What invariant we check for depends on the ts-policy."""
    if _get_transaction_safety_enforcement_policy() == 'ts-enforce-none':
        return

    # We allow the put if it's done directly by a test file.  We don't
    # need test code to be transaction-safe!  (Though the code it is
    # testing *does* need to be transaction-safe, of course.)
    # txn_safety_test.py is excepted; there we want to test the
    # 'normal' behavior.
    if _is_running_tests():     # speed optimization
        backtrace = _truncated_backtrace()
        # UserData, and maybe some other models, overrides put(), so a
        # user_data.put() from a test has user_models.py:put() as the
        # last frame in the backtrace.  Read past that.
        while backtrace and ', in put' in backtrace[-1]:
            backtrace = backtrace[:-1]
        if (backtrace and '_test.py", line' in backtrace[-1]
                and 'txn_safety_test.py' not in backtrace[-1]):
            return

    policy = getattr(entity, '_transaction_safety_policy', None)
    if not policy:        # true for models in third-party libraries
        return

    elif policy == 'never-written':
        _ts_violation('Seeing a put() on a never-written model: '
                      '%s' % type(entity))

    elif policy == 'abstract-model':
        _ts_violation('Seeing a direct put() on an abstract model: '
                      '%s' % type(entity))

    elif policy == 'structured-property':
        _ts_violation('Seeing a direct put() on a structured-property model: '
                      '%s' % type(entity))

    elif policy == 'written-once':
        if hasattr(entity, '_ts_get_nonce'):   # we did a get() on it first
            _ts_violation('Seeing a get() before put() for a written-once '
                          'model: %s' % type(entity))

    elif policy == 'user-specific':
        # NOTE: for historical reasons, the thing holding the
        # lock-nonce is (very confusingly) called _ts_user_lock_id.
        newly_created = not hasattr(entity, '_ts_user_lock_id')
        if not newly_created:
            get_lock_nonce = getattr(entity, '_ts_user_lock_id')
        put_lock_nonce = _user_lock_nonce_for(entity)
        if newly_created and put_lock_nonce:
            # If it's newly created, we didn't set the _ts_user_lock_id
            # when creating it, which was unfortunate (but hard to avoid).
            # Let's put it now, so at least we know for the future.
            entity._ts_user_lock_id = put_lock_nonce

        skip_check = (_get_transaction_safety_enforcement_policy() ==
                      'ts-enforce-all-except-user-lock')

        # Regardless of the above, we always run this code for the
        # txn_safety_test
        if entity.__module__ == 'txn_safety_test':
            skip_check = False

        if skip_check:
            return

        lockid_fn = entity._transaction_safety_kaid_fn
        if callable(lockid_fn):
            lock_id = lockid_fn()
        else:
            lock_id = '<unknown lock-id>'

        if newly_created:
            # For a newly created entity, only the put() needs to be
            # under a lock.  (A newly created entity is one made via
            # constructor and not via a get call; it won't have any of
            # the _ts_* vars set.)
            if not put_lock_nonce:
                _ts_violation('Did not acquire user-lock for put() of a new '
                              'entity %s: %s' % (lock_id, type(entity)))
        # Otherwise, the user lock should have been acquired during
        # the get(), and that same lock should still be active now.
        elif not get_lock_nonce and not put_lock_nonce:
            _ts_violation('Did not acquire the user lock for %s: %s'
                          % (lock_id, type(entity)))
        elif not get_lock_nonce:
            _ts_violation('Did get() before acquiring the user lock for %s: %s'
                          % (lock_id, type(entity)))
        elif not put_lock_nonce:
            _ts_violation('Did put() after releasing the user lock for %s: %s'
                          % (lock_id, type(entity)))
        elif get_lock_nonce != put_lock_nonce:
            _ts_violation('Did a put() under a different lock than get() '
                          'for %s: %s'
                          % (lock_id, type(entity)))

    elif policy == 'written-in-transaction':
        import transaction_util
        if transaction_util.transaction_checking_is_disabled():
            # This deals with the case where transaction checking has been
            # explicitly disabled. This is just for use with the remote API,
            # which is used in a few circumstances in tests, for building the
            # test_db.
            return

        # For a newly created entity, we don't need a transaction.
        if not hasattr(entity, '_ts_get_nonce'):    # not created via a get()
            return
        get_transaction = getattr(entity, '_transaction_at_request_time', None)
        put_transaction = _transaction_object()
        if not get_transaction and not put_transaction:
            _ts_violation('Did not use a transaction: %s' % type(entity))
        elif not get_transaction:
            _ts_violation('Did the get() outside a transaction: %s'
                          % type(entity))
        elif not put_transaction:
            _ts_violation('Did the put() outside a transaction: %s'
                          % type(entity))
        elif get_transaction != put_transaction:
            _ts_violation('Did the get() and put() in different transactions: '
                          '%s' % type(entity))

    elif policy == 'written-via-cron':
        # For cron-only models, we check to see if it's being run from
        # a task queue.  We make some half-hearted efforts to filter
        # out the deferred queue (which is *not* a cron-y queue...).

        is_taskqueue = bool(os.environ.get('HTTP_X_APPENGINE_QUEUENAME'))
        # True for /_ah/queue/deferred, /_ah/queue/deferred_problemlog, etc.
        is_deferred = 'deferred' in os.environ.get('PATH_INFO', '')
        # Tests are going to write these things outside a taskqueue,
        # and that's ok.
        if not _is_running_tests() and (not is_taskqueue or is_deferred):
            _ts_violation('Written outside a task queue: %s' % type(entity))

    elif policy == 'unsafe':
        return


def _examine_tainted_put(entity):
    """Ensure we don't put the same entity twice from different python objects.

    Here's the simple case we're protecting against:
      e1 = db.get(my_key)       # python object #1
      e2 = db.get(my_key)       # python object #2
      e1.foo = bar
      e1.put()
      e2.qux = quux
      e2.put()                  # overwrites the e1 put!

    We test for that by keeping track of every get() and put() that
    happen, in order, for each key.  (So each {n,}db entity has its
    own get/put list.)  When we see a put(), we match it up to its
    corresponding get().  If any put() happened from a different
    python object, we complain.
    """
    policy = getattr(entity, '_transaction_safety_policy', None)
    # TODO(csilvers): it would be ideal to have this check for
    # third-party libs as well, but it's out of scope for us right
    # now to fix bugs in third-party libs.
    if not policy:        # true for models in third-party libraries
        return

    # Add this put() to the get-and-put list.
    get_put_list = _add_to_get_put_list(entity, 'put')
    if not get_put_list:      # means entity doesn't have a key, so is safe
        return

    # Find our matching get().
    try:
        matching_get_index = get_put_list.index(
            ('get', entity._ts_get_nonce, None))
    except ValueError:
        # This was a put() of a newly-created entity, it's definitely safe.
        return

    for (get_or_put, obj_nonce, tb) in get_put_list[matching_get_index + 1:]:
        if get_or_put == 'put' and obj_nonce != entity._ts_get_nonce:
            _ts_violation("Did a put() of the same entity from two different "
                          "python objects: %s.  Other put:\n---\n%s---\n"
                          % (type(entity), tb))


def _examine_put_state(entity):
    # Indicate we've done a put
    entity._ts_has_been_put = True

    _examine_ts_policy(entity)
    _examine_tainted_put(entity)


def hook_transaction_safety_checks():
    db_hooks.add_after_get_hook(_store_get_state)
    db_hooks.add_before_put_hook(_examine_put_state)


@contextlib.contextmanager
def _transaction_policy(temporary_policy):
    old_policy = _get_transaction_safety_enforcement_policy()
    try:
        _set_transaction_safety_enforcement_policy(temporary_policy)
        yield
    finally:
        _set_transaction_safety_enforcement_policy(old_policy)


@contextlib.contextmanager
def dangerously_suppress_transaction_safety_checks():
    """Inside this context, suppress the normal txn checks.

    Sometimes we want to do things that violate normal transactions safety
    checks because we know for other reasons that the operation will be safe.
    (For instance, backfilling old write-once entities.)

    Think long and hard before using this!  The safety checks are there for a
    reason.
    """
    with _transaction_policy('ts-enforce-none'):
        yield


@contextlib.contextmanager
def suppress_transaction_safety_checks_in_test():
    """Inside this context, suppress the normal txn checks.

    Sometimes tests do things that violate the way the code is
    normally used (maybe they modify a VideoLog in place, or
    they write a model to the datastore that's normally never
    written by appengine, to simulate another service).  This
    context-manager can be used in such situations.

    No production code should use this!  The safety checks are there
    for a reason.
    """
    assert _is_running_tests(), "Only use this in tests!"
    with _transaction_policy('ts-enforce-none'):
        yield


@contextlib.contextmanager
def disable_user_write_lock_checking_in_test():
    """Inside this context, writing user data outside the user lock won't fail.

    This is only meant to be used in tests in particular circumstances
    where we know for sure that all writes should be happening under
    the user lock (i.e.  in the context of an API request.

    This is largely meant as a migrationary measure to allow us to
    turn off user write lock checking in particular tests without
    needing to fix every single test.
    """
    with _transaction_policy('ts-enforce-all-except-user-lock'):
        yield


# ----------
# MIDDLEWARE
# ----------

class TransactionSafetyMiddleware(object):
    """When using txn_safety.py, wrap your WSGI app with this!"""
    def __init__(self, app):
        self.app = app
        hook_transaction_safety_checks()

    def __call__(self, environ, start_response):
        if hasattr(_REQUEST_STATE, 'ts_enforcement_policy'):
            del _REQUEST_STATE.ts_enforcement_policy
        if hasattr(_REQUEST_STATE, 'ts_get_put_list'):
            _REQUEST_STATE.ts_get_put_list.clear()

        return self.app(environ, start_response)


# -------------------------
# TRANSACTION_SAFETY_POLICY
# -------------------------

# These decorators set _transaction_safety_policy.  This variable
# documents how the model does get()s and put()s, and how it has to
# make sure that simultaneous put()s from different instances don't
# stomp on each other.
#
# *NOTE* that these decorators concern data corruption ONLY.  They do
# not concern consistency: two models that need to be modified in
# lockstep, or one model where you need to make sure an insert happens
# exactly once.
#
# USAGE GUIDE: when creating a new db or ndb model, use exactly one
# of the decorators below.  Go down this list and pick the first
# one that applies.
#
# 1. never_written_model -- super rare!
# 2. abstract_model -- commonly for polymodels and utility classes
# 3. structured_property_model -- for (Local)StructuredProperty models
# 4. written_once_model -- easiest to use correctly (no need for transactions)
# 5. written_in_transaction_model -- *you* put get-modify-put in a transaction
# 6. written_with_user_lock_model -- for models "pegged" to a single user
# 7. written_via_cron_model -- mostly for legacy code
# 8. dangerously_written_outside_transaction_model -- *only* for legacy code
# 9. dangerously_written_outside_transaction_model_or_user_lock -- ditto
#
# For more information about each of these, see the docstrings below.

def _set_transaction_safety(cls, value):
    # We check cls.__dict__ instead of using hasattr, because hasattr will
    # check properties on any of the superclasses too, which we don't want to
    # do. We want each model class to have exactly one transaction safety
    # policy set.
    assert "_transaction_safety_policy" not in cls.__dict__, (
        "Multiple transaction-safety decorators", cls)
    cls._transaction_safety_policy = value
    return cls


def written_with_user_lock_model(lockid_fn):
    """Decorator that says that a db or ndb model holds info about one user.

    The canonical example of a user-specific model is UserData, but many
    other models are as well: UserExercise, PromoRecord, etc.  The key
    point is that it's possible to say that instances of this model
    "belong" to a given user.

    Be careful using this decorator! -- a lock is a coarse-grained
    tool compared to a transaction, and it's easy to get lock
    contentions and timeouts when using this.  Use it only for models
    that are difficult to update in a transaction.

    This decorator takes one argument: a function (probably a lambda)
    that takes an instance of this model as an argument, and returns
    the user's lock-id.  That is, it identifies "which" user this entity
    is associated with.
    """
    def class_rebuilder(cls):
        _set_transaction_safety(cls, 'user-specific')
        cls._transaction_safety_kaid_fn = lockid_fn
        return cls

    return class_rebuilder


def written_once_model():
    """Decorator that says that a model is unchanged after initial put.

    This is used for models that are 'write-once': you create it, you
    put() it, and then all you ever do to it afterwards is read it.
    Examples are ExerciseRevision, KeyValueCache, DailyStatisticsLog,
    etc.

    Note that there is still a potential for "stomping" with immutable
    models, if two instances put() a model at the same time with the
    same key (this only works if our code explicitly specifies the
    key).  The only one of the put()s will win.  But we're not
    worrying about that for this project.
    """
    return lambda cls: _set_transaction_safety(cls, 'written-once')


def written_via_cron_model():
    """Decorator that says this model is only updated from a 'cron job'.

    This is used to annotate a model that in theory could have
    problems with simultaneous writes, but in practice does not
    because it's only ever used by one process at a time, which is
    kicked off by a timer or some such.  For instance, we might have a
    model that's only used by a daily pipeline job.  Since we only run
    one pipeline job at a time, we don't have to worry about two
    instances trying to modify the model at the same time.

    Note we use 'cron job' in a general "one thing at a time kicked
    off somehow" sense; it may include things besides what's in
    cron.yaml.
    """
    return lambda cls: _set_transaction_safety(cls, 'written-via-cron')


def written_in_transaction_model():
    """Decorator that says we manually ensure this model has transactions.

    This is used for models that manually enforce the safety of their
    get()-modify-put() updates by doing them inside a transaction.
    """
    return lambda cls: _set_transaction_safety(cls, 'written-in-transaction')


def structured_property_model():
    """Decorator that says this model is only used as a StructuredProperty.

    This means that the model will never be put() to the database on its own,
    and thus has no concerns with transations.
    """
    return lambda cls: _set_transaction_safety(cls, 'structured-property')


def abstract_model():
    """Decorator that says this model is only used as a base class.

    This means that only subclasses of this model are put().
    """
    return lambda cls: _set_transaction_safety(cls, 'abstract-model')


def never_written_model():
    """Decorator that says that the model is never put to the datastore.

    Even though this property is true of structured properties and abstract
    models, you should use those to be more precise. This decorator is only
    used for bizarre situations where neither of abstract_model or
    structured_property_model apply. See extbackup.compat.BackupInformation for
    an interesting example.
    """
    return lambda cls: _set_transaction_safety(cls, 'never-written')


def dangerously_written_outside_transaction_model():
    """Decorator that says we must manually ensure this model has transactions.

    This is used for models that need to manually enforce the safety
    of their get()-modify-put() updates, by doing them inside a
    transaction, but currently do not.  Don't add this to new models!
    Instead make them transaction-safe. :-)  The existence of even one
    instance of this model means we have a TODO.

    This differs from the '..._or_user_lock' decorator in that we know
    a user-lock is not the right choice for this model.
    """
    return lambda cls: _set_transaction_safety(cls, 'unsafe')


def dangerously_written_outside_transaction_model_or_user_lock():
    """Decorator that says we must manually ensure this model has transactions.

    This is used for models that need to manually enforce the safety
    of their get()-modify-put() updates, by doing them inside either a
    transaction or user-lock -- we haven't decided which yet -- but
    currently do not.  Don't add this to new models!  The existence of
    even one instance of this model means we have a TODO.

    This differs from dangerously_written_outside_transaction_model in
    that we haven't decided whether this model should be made
    transaction-safe via transactions or via a user lock.  Both are
    possible; transactions are preferred if it's not too much work,
    but we haven't looked into whether it is or not yet.
    """
    return lambda cls: _set_transaction_safety(cls, 'unsafe')
