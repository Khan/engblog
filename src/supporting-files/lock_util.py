"""Utilities around managing distributed locks and leases.

These locks (technically leases, since they expire, but referred
to in this file as "locks") can be used as an alternative to
db/ndb transactions in appropriate situations.  See
   http://engineering.khanacademy.org/posts/user-write-lock.htm
for details.

NOTE: when using this library, you *MUST* use LockUtilMiddleware, as
described below.

TODO(csilvers): enforce this in code?  But I'm worried there may be
legitimate uses of lock_util outside a request context.

LOW-LEVEL API
-------------

   with lock_util.global_lock(key):
       ...

All the code within this context-manager is protected by the global
lock, and any other process that tries to acquire the global lock with
the same key will block until the context exits.  (Or until the lease
expires, controlled via the optional `lock_timeout` parameter.)

You can also acquire and release the key manually, via

   acquire_global_lock(key)
   release_global_lock(key)

This low-level API is "semi-reentrant" -- the same process can acquire
the lock multiple times, but a single release releases all of them.
(This is for historical reasons.)  It is best to treat this API as
non-reentrant.

HIGH-LEVEL API
--------------

   with lock_util.user_write_lock(lock_id):
      ...

This is similar to `global_lock`, but a) is fully re-entrant, meaning
you can nest `user_write_lock` calls without fear; and b) does some
analysis to help you discover lock violations.  In particular, each
lock request is given a unique id, and one can instrument the db/ndb
libraries to notice when locks are used improperly The instrumentation
can also notice when a datastore entity is put() without holding the
lock.

See http://engineering.khanacademy.org/posts/transaction-safety.htm
for more details on the power of lock analysis.

Note that `lock_id` is equivalent to `key` in the low-level API.  They
have different names mostly to help you distinguish what level of the
API you are in.  To make the logging maximally helpful, it's best if
you can map the lock-id you use back to a specific user (or whatever
abstract concept you're protecting with this lock).

   with lock_util.fetch_under_user_write_lock(entity) as entity_again:
      ...

This context-manager re-fetches the given entity -- either a db entity
or ndb entity -- from the datastore under the appropriate lock for
that entity.  This idiom avoids the most common error with working
with a lock: that you get() the entity outside the lock.  This is not
safe, even if you then put() it inside the lock.  This context manager
avoids that problem.

This context manager also does the most analysis to discover unsafe
uses of the user-lock.  In fact, to work properly it requires you to
implement the analysis system in
   http://engineering.khanacademy.org/posts/transaction-safety.htm

In particular, it requires you use the `@written_with_user_lock_model`
decorator, so you can define a `kaid_fn` on the entity, which takes an
entity and returns the appropriate lock-id for that entity.

MIDDLEWARE
----------

Whether you are using the low-level API or the high-level API, you
*must* use LockUtilMiddleware to clean up all per-request data
structures.  Just wrap your wsgi app within LockUtilMiddleware like
you would any other middleware:

    app = webapp2.WSGIApplication([...routes...])
    app = lock_util.LockUtilMiddleware(app)
"""

import UserDict
import contextlib
import logging
import os
import random
import threading
import time
import traceback

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import ndb


# Used when INSTANCE_ID is None (probably just for tests).
_INSTANCE_ID = random.randint(1, 1000000)
# Used when REQUEST_LOG_ID is None (probably for tests).
_REQUEST_ID = random.randint(1, 1000000)


# The default timeout we use for user-locks depends on what kind of
# request this is -- we want to make it exactly as large as the
# max-time the request can take.
_DEFAULT_HOLD_TIMEOUT_FOR_INTERACTIVE = 60
# TODO(csilvers): raise this?  But am worried about starvation if
# batch jobs can hold on to the lock for 10 minutes.
_DEFAULT_HOLD_TIMEOUT_FOR_BATCH = 60

# Interactive requests should wait for a maximum of 10s to avoid
# hitting the request timeout of 60s.
#
# TODO(jlfwong/csilvers): there's a problem right now where a machine
# acquires a lock, then hard OOMs, meaning it never releases the
# lock. This will still eventually release the lock in practice, but
# it will hold it for the full HOLD_TIMEOUT duration. It would be much
# better if we could somehow release the lock when a hard OOM happens.
#
# One idea is to have a heartbeat thread running in the background
# which has to renew the lease on the lock every few seconds, then
# have a really short HOLD_TIMEOUT, meaning that even if we hold the
# lock after a hard OOM, we at least only hold it for ~5 seconds,
# instead of 60.
_DEFAULT_WAIT_TIMEOUT_FOR_INTERACTIVE = 10

# Batch jobs should wait for a lock for as long as it can possibly be
# held.  It's okay to wait long in batch requests because the request
# timeout is 10 minutes instead of 60 seconds.
_DEFAULT_WAIT_TIMEOUT_FOR_BATCH = _DEFAULT_HOLD_TIMEOUT_FOR_BATCH


class LockAcquireFailure(Exception):
    pass


# A per-request cache.  Each thread has a separate copy.
class ThreadLocalDict(UserDict.UserDict, threading.local):
    pass

_request_cache = ThreadLocalDict()


# --------------- Memcache utilities
# We need these because the default Google client does not take a deadline.

# This is a hard-coded, somewhat arbitrarily limit.
DEFAULT_MEMCACHE_GET_DEADLINE = 0.075  # seconds
DEFAULT_MEMCACHE_SET_DEADLINE = 0.300  # seconds


def memcache_util_get_multi_async_with_deadline(
        keys, key_prefix='', namespace=None,
        deadline=DEFAULT_MEMCACHE_GET_DEADLINE):
    """Like get_multi_async(), but fails if it takes longer than deadline.

    Asynchronously looks up multiple keys from memcache in one
    operation.  Deadline is in seconds and is defaulted to a
    reasonable value unless set explicitly.

    See memcache.Client().get_multi_async documentation for details.
    """
    rpc = memcache.create_rpc(deadline=deadline)
    return memcache.Client().get_multi_async(keys, key_prefix=key_prefix,
                                             namespace=namespace, rpc=rpc)


def memcache_util_get_with_deadline(key, namespace=None,
                                    deadline=DEFAULT_MEMCACHE_GET_DEADLINE):
    """Like get(), but fails if it takes longer than deadline seconds.

    Looks up a single key in memcache.  Deadline is in seconds and is
    defaulted to a reasonable value unless set explicitly.  If the
    deadline is reached before memcache responds, None is returned.

    See memcache.get documentation for details.
    """
    async_response = memcache_util_get_multi_async_with_deadline(
        [key], namespace=namespace, deadline=deadline)
    result_dict = async_response.get_result()
    if not result_dict:
        value = None
    else:
        assert len(result_dict) == 1, result_dict
        _, value = result_dict.popitem()
    return value


def memcache_util_set_multi_async_with_deadline(
        mapping, time=0, key_prefix='', min_compress_len=0, namespace=None,
        deadline=DEFAULT_MEMCACHE_SET_DEADLINE):
    """Like set_multi_async(), but fails if it takes longer than deadline.

    Asynchronously sets multiple keys' values at once.  Deadline is in
    seconds and is defaulted to a reasonable value unless set
    explicitly.

    See memcache.Client().set_multi_async documentation for details.
    """
    rpc = memcache.create_rpc(deadline=deadline)
    return memcache.Client().set_multi_async(mapping, time=time,
                                             key_prefix=key_prefix,
                                             min_compress_len=min_compress_len,
                                             namespace=namespace, rpc=rpc)


def memcache_util_add_multi_async_with_deadline(
        mapping, time=0, key_prefix='', min_compress_len=0, namespace=None,
        deadline=DEFAULT_MEMCACHE_SET_DEADLINE):
    """Like add_multi_async(), but fails if it takes longer than deadline.

    Asynchronously adds multiple keys' values at once.  Deadline is in
    seconds and is defaulted to a reasonable value unless set
    explicitly.

    See memcache.Client().add_multi_async documentation for details.
    """
    rpc = memcache.create_rpc(deadline=deadline)
    return memcache.Client().add_multi_async(mapping, time=time,
                                             key_prefix=key_prefix,
                                             min_compress_len=min_compress_len,
                                             namespace=namespace, rpc=rpc)


def memcache_util_delete_with_deadline(
        key, seconds=0, namespace=None,
        deadline=DEFAULT_MEMCACHE_SET_DEADLINE):
    """Like delete(), but fails if it takes longer than deadline seconds.

    Deletes a key.  Deadline is in seconds and is defaulted to a
    reasonable value unless delete explicitly.

    If the deadline is reached before memcache responds,  False is returned.

    See memcache.delete documentation for details.
    """
    rpc = memcache.create_rpc(deadline=deadline)
    async_response = memcache.Client().delete_multi_async(
        [key], seconds=seconds, key_prefix='',
        namespace=namespace, rpc=rpc)
    results = async_response.get_result()
    if not results:
        return memcache.DELETE_NETWORK_FAILURE
    return results[0]


def resolve_rpc_at_end_of_request(rpc):
    """Call get_result() on this rpc at the end of the current request.

    There's nothing to do this automatically.  So if you have an RPC
    that can take all request long, but you want to make sure finishes
    before this request does, you can add it to this queue, where it
    will be resolved in middleware.
    """
    queue = _request_cache.get('rpc_async_queue', [])
    queue.append(rpc)
    _request_cache['rpc_async_queue'] = queue


def resolve_all_rpcs():
    queue = _request_cache.get('rpc_async_queue', [])
    for rpc in queue:
        rpc.get_result()


# --------------- Global lock code

def _global_lock_key(key):
    assert isinstance(key, basestring), (
        "Key '%s' must be a string, not a %s" % (key, type(key)))
    return 'global_lock_' + key.encode('utf-8')


def _global_lock_value_for_this_request():
    request_id = os.environ.get('REQUEST_LOG_ID')
    instance_id = os.environ.get('INSTANCE_ID')
    if not request_id or not instance_id:
        logging.error('Missing request id "%s" and/or instance id "%s"',
                      request_id, instance_id)
        request_id = request_id or _REQUEST_ID
        instance_id = instance_id or _INSTANCE_ID
    return '%s (instance %s)' % (request_id, instance_id)


def acquire_global_lock(key, lock_timeout=None, wait_timeout=None):
    """Acquire a 'global' lock (across all instances) for the given key.

    This is technically a 'lease' rather than a 'lock' because it can
    time out.  The timeout should be the maximum length of a request,
    which is 60 seconds for normal requests and 10 minutes for
    taskqueue requests.  (10 minutes is really long, so make this
    shorter if you can.)

    This lock is 'global', meaning that if you acquire this lock no
    other instance can acquire this lock.  (Neither can other requests
    in this instance.)  It is semi-reentrant, meaning that if the same
    request tries to acquire a lock it already has, this succeeds, but
    a single release call will still release the lock.  That is, we
    don't "nest" locks, instead subsequent locks by the same request
    are just ignored.

    TODO(csilvers): make it totally non-reentrant.

    Ideally we'd implement this using a lockservice such as ZooKeeper
    or Chubby.  But in the world we live in, we use the atomic
    operations in memcache.

    Arguments:
        key: the key to the lock
        lock_timeout: how long to hold onto the lock (actually a lease)
           once it's acquired, in seconds.  None means to use a reasonable
           default.  There is no way to acquire a global lock for forever.
        wait_timeout: how long to wait to acquire the lock before aborting
           this request, in seconds.
    """
    key = _global_lock_key(key)
    value = _global_lock_value_for_this_request()

    if lock_timeout is None:
        # TODO(csilvers): distinguish interactive from batch request
        lock_timeout = _DEFAULT_HOLD_TIMEOUT_FOR_INTERACTIVE

    is_interactive = not os.environ.get('HTTP_X_APPENGINE_QUEUENAME')

    if wait_timeout is None:
        if is_interactive:
            wait_timeout = _DEFAULT_WAIT_TIMEOUT_FOR_INTERACTIVE
        else:
            wait_timeout = _DEFAULT_WAIT_TIMEOUT_FOR_BATCH

    # This section makes locking more 'fair'.  Basically, if you're a
    # batch job trying to acquire this lock, you have to give way for
    # any interactive requests that are currently running.  So if we
    # are interactive, we need to set a value in memcache saying "this
    # user has been used interactively recently."  And if we are
    # batch, we need to query that value and if it's set, we sleep a
    # little bit to give any pending interactive jobs a chance to
    # acquire the lock before we do.
    if is_interactive:
        # We say the interactive process is "active" for 5 minutes
        # after the last interactive request.  We resolve this async()
        # late since we don't care when the set completes.

        rpc = memcache_util_set_multi_async_with_deadline(
            {key + '.interactive': 1}, time=300)
        resolve_rpc_at_end_of_request(rpc)
    else:
        # We use a fairly big deadline since we don't want to start
        # hogging the lock whenever memcache gets slow.
        if memcache_util_get_with_deadline(key + '.interactive',
                                           deadline=0.2):
            # Sleep for 1.05 second.  Since the code below waits at
            # most a second between lock tries, this will guarantee
            # that any interactive task waiting for the lock will have
            # a chance to acquire it.
            time.sleep(1.05)
            logging.info('Batch job %s waiting a sec for concurrent '
                         'interactive jobs that also want the lock' % key)

    # add() is atomic.  We use the multi-async version because it's
    # the only one whose return value distinguishes failure and error.
    # For timeout and error, we retry a few times.
    for _ in xrange(2):
        retval = memcache_util_add_multi_async_with_deadline(
            {key: value}, time=lock_timeout).get_result()
        # retval is None on error, or a {key: <status>} dict.
        add_status = retval.values()[0] if retval else None
        if add_status and add_status != memcache.ERROR:
            break

    if add_status == memcache.STORED:
        # Common case: no concurrent insert is going on.
        return

    if not add_status or add_status == memcache.ERROR:
        # means a memcache error: HTTP error, timeout, etc.  We 'fail
        # permissive' and pretend the lock was acquired.
        if add_status == memcache.ERROR:
            msg = ('Memcache error acquiring (global) memcache lock on key %s'
                   % (key))
        else:
            msg = ('Timeout or HTTP error acquiring (global) memcache lock on '
                   'key %s' % (key))
        logging.error(msg)
        return

    # https://github.com/memcached/memcached/blob/master/doc/protocol.txt#L194
    # sez that EXISTS is only used for cas(), so we should see NOT_STORED.
    # But who knows what google actually implements?  We treat them the same.
    assert add_status in (memcache.NOT_STORED, memcache.EXISTS), (
        'unknown status %s' % add_status)

    # Check if it's just us just re-acquiring a lock we already have.
    other_id = memcache_util_get_with_deadline(key) or '[nobody?]'
    if other_id == value:
        return

    # Someone else has the lock.  We just have to busy-wait for them
    # to finish.
    # TODO(csilvers): it's possible that the lock is held by a process
    # that was killed by appengine (due to OOM).  In that case we
    # should treat this lock as released.  We could do that by keeping
    # an up-to-date list of active instance-id's in memcache, and
    # checking that list here (and comparing it to other_id).
    for i in xrange(wait_timeout):
        now = time.time()
        retval = memcache_util_add_multi_async_with_deadline(
            {key: value}, time=lock_timeout).get_result()
        add_status = retval.values()[0] if retval else None
        if add_status == memcache.STORED:
            logging.debug("Waited %d seconds for the %s lock on %s "
                          "(held by %s)"
                          % (i, key, value, other_id))
            return
        elif not add_status or add_status == memcache.ERROR:
            # We 'fail permissive' here as well, and pretend that the
            # lock was acquired even though memcache errored.
            # TODO(sean): optimistic permissiveness will sometimes
            # cause problems, especially if memcache fails
            # often. Other more robust options include:
            # a) Retry the lock operation a few times, to make sure
            #    that *someone* has the key (and hope that it's us).
            # b) Store a process id along with the key, and keep retrying
            #    when we receive errors. When we (hopefully) eventually
            #    *do* get a STORED/NOT_STORED answer from memcache, we
            #    can check if we're the ones that hold the lock.
            if add_status == memcache.ERROR:
                logging.debug("Memcache error acquiring (global) memcache "
                              "lock after waiting %d seconds for the %s lock "
                              "on %s (held by %s)" % (i, key, value, other_id))
            else:
                logging.debug("Memcache timeout/network error acquiring "
                              "(global) memcache lock after waiting %d "
                              "seconds for the %s lock on %s (held by %s)" %
                              (i, key, value, other_id))
            return

        to_wait = 1 - (time.time() - now)
        if to_wait > 0:
            time.sleep(to_wait)

    raise LockAcquireFailure("Timeout after %d seconds waiting for the %s "
                             "lock for %s (held by %s)"
                             % (wait_timeout, key, value, other_id))


def release_global_lock(key):
    # TODO(jlfwong): Make this asynchronous, since we don't need to
    # block until the lock is released.
    key = _global_lock_key(key)

    # TODO(csilvers): there's a race condition here where we do the
    # get above, then the key expires in memcache, another process
    # locks it, and then our delete deletes the lock for the other
    # process.  Safer would be to do a gets() above and then a cas()
    # here.  But you can't delete with cas(), so that would require
    # having a 'None' value mean 'deleted', which would mean rewriting
    # the acquire_lock to do an add() *or* cas(), which adds
    # complexity and running time.  We'll take our chances.  Locks
    # should not commonly be expiring.

    for _ in xrange(3):      # retry a bit to release the lock
        delete_status = memcache_util_delete_with_deadline(key)
        if delete_status != memcache.DELETE_NETWORK_FAILURE:
            break
        time.sleep(0.5)
    else:
        logging.error("Failed to release_lock() on %s: network failure" % key)


@contextlib.contextmanager
def global_lock(key, lock_timeout=None, wait_timeout=None):
    acquire_global_lock(key, lock_timeout, wait_timeout)
    try:
        yield
    finally:
        release_global_lock(key)


# --------------- User lock code


_WRITE_LOCK_REQUEST_CACHE_KEY = "user_write_locks_held"


def _user_write_lock_global_key(lock_id):
    return "write_lock_%s" % lock_id


def _lock_id_map_from_request_cache():
    """Return a map s.t. if you modify the map, it modifies in the cache.

    The lock_id_map is what controls locks being re-entrant (from the
    same request).  It also assigns a unique nonce to each lock
    acquisition, so if you acquire-then-release a lock, and then
    acquire it again, we can know that the second lock is different
    from the first.  Note that a single lock_id will always have at
    most one lock active for it at a time.

    lock_id_map is a map from lock_id -> (unique nonce, lock-count)
    """
    retval = _request_cache.get(_WRITE_LOCK_REQUEST_CACHE_KEY, None)
    if retval is None:
        retval = {}
        _request_cache[_WRITE_LOCK_REQUEST_CACHE_KEY] = retval
    return retval


def release_all_user_write_locks_held_by_request():
    """Release all user write locks held in the current request."""
    lock_id_map = _lock_id_map_from_request_cache()
    for (lock_id, (_, lock_count)) in lock_id_map.items():
        for _ in xrange(lock_count):
            release_user_write_lock(lock_id)


def user_write_lock_is_held_by_request(lock_id):
    """Return True if the user write lock is held for the given lock_id.

    Does not attempt to acquire the lock if it is not held.
    """
    lock_id_map = _lock_id_map_from_request_cache()
    return lock_id in lock_id_map


def nonce_of_user_write_lock_held_by_request(lock_id):
    """Return lock-nonce, or None if no lock is held for this lock_id."""
    lock_id_map = _lock_id_map_from_request_cache()
    return lock_id_map.get(lock_id, (None, 0))[0]


def nonce_of_any_user_write_lock_held_by_request():
    """Return the nonce of *any* currently-held write lock, or None.

    This is a transitional function that is only needed for models
    where it's difficult to map from entity -> lock_id of the user
    associated with this entity.  For those models, we just assume
    that if any user-write lock is held for that entity, it's the
    right one.

    This function returns an arbitrary nonce, but if the set of locks
    held by this request doesn't change, the return value won't change
    either.
    """
    lock_id_map = _lock_id_map_from_request_cache()
    all_nonces = [nonce for (nonce, _) in lock_id_map.itervalues()]
    return min(all_nonces) if all_nonces else None


def acquire_user_write_lock(lock_id, lock_timeout=None, wait_timeout=None):
    """Acquire the user write lock for the user with the given lock_id.

    This lock is re-entrant: multiple acquires of the same key by the
    same request will not block.  Each acquire must be paired with a
    release.

    This lock must be held while writing to any user-specific models.

    Arguments:
        lock_id: an identifier of the user (or other abstract entity)
           to acquire the lock for
        lock_timeout: how long to hold onto the lock (actually a lease)
           once it's acquired, in seconds.  None means to use a reasonable
           default.  There is no way to acquire a global lock for forever.
        wait_timeout: how long to wait to acquire the lock before aborting
           this request, in seconds.

    """
    # TODO(jlfwong): Enforce that locks are acquired in lexicographical order?
    assert isinstance(lock_id, basestring), (lock_id, type(lock_id))
    lock_id_map = _lock_id_map_from_request_cache()
    if lock_id in lock_id_map:
        # Just increment the lock count.
        lock_id_map[lock_id][1] += 1
        return

    acquire_global_lock(_user_write_lock_global_key(lock_id),
                        lock_timeout=lock_timeout,
                        wait_timeout=wait_timeout)
    logging.debug("Acquired user lock for %s" % lock_id)

    # This is to help us find requests that want to acquire locks for
    # multiple users simultaneously.  This can be useful when needing
    # to avoid deadlock due to lock-aquisition order.
    if lock_id_map:
        # Exclude the last line as it's this one.
        tb = ''.join(traceback.format_stack()[:-1])
        logging.info('Already held user-lock for %s and just added %s:\n'
                     '%s\n' % (sorted(lock_id_map), lock_id, tb))

    lock_nonce = hex(random.randint(1, 1 << 32))[2:]    # get rid of the '0x'
    lock_id_map[lock_id] = [lock_nonce, 1]


def release_user_write_lock(lock_id):
    """Release the user write lock for the user with the given lock_id."""
    assert isinstance(lock_id, basestring), (lock_id, type(lock_id))
    lock_id_map = _lock_id_map_from_request_cache()
    assert lock_id in lock_id_map, (
        "Attempted to release unheld write lock for %s" % lock_id)
    assert lock_id_map[lock_id][1] > 0, ("Non-positive lock count?", lock_id)

    lock_id_map[lock_id][1] -= 1
    if lock_id_map[lock_id][1] == 0:
        release_global_lock(_user_write_lock_global_key(lock_id))
        logging.debug("Released user lock for %s" % lock_id)
        lock_id_map.pop(lock_id)


@contextlib.contextmanager
def user_write_lock(lock_id, lock_timeout=None, wait_timeout=None):
    acquire_user_write_lock(lock_id, lock_timeout, wait_timeout)
    try:
        yield
    finally:
        release_user_write_lock(lock_id)


@contextlib.contextmanager
def fetch_under_user_write_lock(entity, lock_timeout=None, wait_timeout=None,
                                null_ok=False):
    """Yield a version of the passed entity retrieved under a user write lock.

    If the entity was already retrieved under this user write lock,
    this will just yield the entity. Otherwise, it will acquire the
    user write lock, fetch a new version of the entity from the
    datastore, and yield that.

    This can only be used by models decorated with
    @db_decorators.written_with_user_lock_model.

    If null_ok is True, then we just return None if the input is None.
    """
    if entity is None:
        if null_ok:
            yield None
            return
        raise ValueError("Cannot acquire the user-lock for None")
    assert callable(entity._transaction_safety_kaid_fn), (
        "Cannot acquire the user-lock for %s; it's missing a kaid-fn"
        % entity.__name__)
    lock_id = entity._transaction_safety_kaid_fn()
    entity_lock_nonce = getattr(entity, '_ts_user_lock_id', None)
    current_lock_nonce = nonce_of_user_write_lock_held_by_request(lock_id)
    under_same_lock = (entity_lock_nonce and
                           entity_lock_nonce == current_lock_nonce)
    # If the entity is newly created (has never been get) and also has
    # never been put, we can't even re-fetch it.
    never_get_or_put = (not hasattr(entity, '_ts_get_id') and
                        not hasattr(entity, '_ts_has_been_put'))
    if under_same_lock or never_get_or_put:
        yield entity
    else:
        with user_write_lock(lock_id):
            # Re-fetch now that we have the lock.
            if isinstance(entity, db.Model):
                yield db.get(entity.key())
            elif isinstance(entity, ndb.Model):
                yield entity.key.get()
            else:
                raise ValueError("Do not know how to fetch type %s"
                                 % type(entity))


class LockUtilMiddleware(object):
    """When using lock_util, wrap your WSGI app with this!"""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            _request_cache.clear()    # just to be extra-safe
            for retval in self.app(environ, start_response):
                yield retval
        finally:
            # Now that the request is over, release all global locks
            # that the request may have acquired, in order to modify
            # per-user data.  Since these are global locks (in
            # memcache), we can't depend on the normal request_cache
            # middleware to clean them up.
            release_all_user_write_locks_held_by_request()

            # Also finish up the "no rush" RPC calls we made
            resolve_all_rpcs()

            # Finally, clear the per-request cache
            _request_cache.clear()
