"""Functions to hook into the lifecycle of ALL db and ndb models.

In contrast to doing this on a per-model basis, the hooks registered here will
be invoked whenever *any* model is put or retrieved from the datastore.

This is an extension of the officially supported ndb hooks, that also
supports db models.  For consistency, we do our own hooking even for
ndb.

The key methods here are add_before_put_hook and add_after_get_hook.
"""

import functools
import logging

from google.appengine.api import datastore
from google.appengine.api import datastore_types
from google.appengine.ext import db
from google.appengine.ext import ndb


_put_hooks = []
_get_hooks = []
_db_hooks_installed = False

# Placeholder value used when `transaction` cannot yet be fetched
_TRANSACTION_STATE_NOT_EVALUATED = object()


def _transaction_object():
    """Return the transaction this entity is currently under, or None."""
    try:
        return getattr(datastore._GetConnection(), 'transaction', None)
    except Exception as e:
        # Probably means the internal _GetConnection() function went away.
        logging.error("datastore._GetConnection() isn't working!: %s" % e)
        return None


def _wrap_up_put(func):
    """Wrap a put method to invoke the put hooks before a real put()."""
    @functools.wraps(func)
    def wrapper(model_or_models, *args, **kwargs):
        for hook in _put_hooks:
            if hasattr(model_or_models, '__iter__'):
                # We explicitly list-ify here, because model_or_models could be
                # a generator, and we don't want to exhaust the generator then
                # pass the exhausted generator to the real put method.
                model_or_models = list(model_or_models)
                for model in model_or_models:
                    hook(model)
            else:
                hook(model_or_models)

        return func(model_or_models, *args, **kwargs)

    return wrapper


def _run_get_hooks(model_or_models, transaction):
    """Run the get hooks on all the models contained in model_or_models.

    Different db/ndb methods return models in different ways. This method deals
    with that variety.

    See _wrap_up_nonclassmethod_get.__doc__ for information on the transaction
    argument.
    """
    if isinstance(model_or_models, (db.Model, ndb.Model)):
        # This prevents double runs in cases where we hook one method that
        # calls a different method we hook (e.g. db.Model.get_or_insert calls
        # db.get).
        if hasattr(model_or_models, '_db_util_get_hooks_run'):
            return

        model_or_models._db_util_get_hooks_run = True

        # If `transaction` has the placeholder value because it hasn't been
        # fetched by this point, then fetch it now.
        if transaction is _TRANSACTION_STATE_NOT_EVALUATED:
            transaction = _transaction_object()

        model_or_models._transaction_at_request_time = transaction

        for hook in _get_hooks:
            hook(model_or_models)

    elif isinstance(model_or_models, (list, tuple)):
        if not model_or_models:
            # Empty! Nothing to do here!
            return

        # Special case: ndb.Query.fetch_page returns a (results, cursor,
        # more tuple).
        if isinstance(model_or_models[-1], bool):
            return _run_get_hooks(model_or_models[0], transaction=transaction)
        for model in model_or_models:
            _run_get_hooks(model, transaction=transaction)

    elif model_or_models is None:
        # Nothing came back from the datastore, so nothing to hook.
        pass

    elif isinstance(model_or_models, (ndb.Key, datastore_types.Key)):
        # Keys only query; hooks don't need to run.
        pass

    else:
        logging.error("Tried to run get hooks on unexpected type %s (%s)",
                      model_or_models, type(model_or_models))


def _run_hooks_iter(iterator, transaction):
    """Wrap an iterator to run the get hooks during iteration.

    See _wrap_up_nonclassmethod_get.__doc__ for information on the transaction
    argument.
    """
    for result in iterator:
        _run_get_hooks(result, transaction=transaction)
        yield result


def _wrap_up_nonclassmethod_get(func,
                                transaction=_TRANSACTION_STATE_NOT_EVALUATED):
    """Wrap a get method to invoke the get hooks.

    If func might be a classmethod, use _wrap_up_get instead.

    transaction: This is the transaction that was active (if any) when an
    asynchronous request was made. This information is passed along and
    eventually accessible on the model instance as
    _transaction_at_request_time. If the request was not asynchronous,
    TRANSACTION_STATE_NOT_EVALUATED is used as a placeholder, and transaction
    is given a value later.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = func(*args, **kwargs)

        if (not isinstance(ret, (db.Model, ndb.Model))
            and hasattr(ret, 'get_result')):
            # The result is a future - we don't have the models yet, and we
            # don't want to force the future to resolve now, so instead we
            # wrap the instance's get_result, and invoke the hooks when it
            # gets called.

            # We want to know which transaction was active at the time when the
            # request was made, not when the future from the request is
            # resolved. These are almost always the same thing, except in ndb
            # tasklets, where futures are resolved before the ndb context is
            # restored.
            #
            # Specifically, these lines show the future being resolved before
            # the ndb context (and therefore the TransactionalConnection) is
            # restored:
            #
            # (from google/appengine/ext/ndb/tasklets.py:_on_future_completion)
            #
            #   val = future.get_result()
            #   self._help_tasklet_along(ns, ds_conn, gen, val)
            #
            cur_transaction = _transaction_object()

            ret.get_result = _wrap_up_nonclassmethod_get(
                    ret.get_result, transaction=cur_transaction)
        elif (not isinstance(ret, (db.Model, ndb.Model))
                and hasattr(ret, 'next')):
            return _run_hooks_iter(ret, transaction=transaction)
        else:
            _run_get_hooks(ret, transaction=transaction)

        return ret

    return wrapper


def _wrap_up_get(func):
    """Wrap a get method to invoke the put hooks before a real put().

    Gracefully deals with classmethods.
    """
    if getattr(func, 'im_self', None) is not None:
        # For classmethods, we pull the unbound method out of the method in
        # order to invoke it with the dynamically bound class (i.e. we want
        # the "cls" argument to be UserData, not db.Model).
        return classmethod(_wrap_up_nonclassmethod_get(func.im_func))
    else:
        return _wrap_up_nonclassmethod_get(func)


def _ensure_db_hooks_installed():
    """Idempotently ensure that the DB hooks are installed (monkeypatched)."""
    global _db_hooks_installed

    # Only wrap once
    if _db_hooks_installed:
        return

    _db_hooks_installed = True

    # This is the minimal subset of methods that need wrapping for all puts
    # - the other methods of putting a model go through one of these codepaths.
    ndb.Model.put_async = _wrap_up_put(ndb.Model.put_async)
    ndb.Model.put = _wrap_up_put(ndb.Model.put)
    db.Model.put = _wrap_up_put(db.Model.put)
    db.put_async = _wrap_up_put(db.put_async)

    # We try to keep this to as small a set as possible that covers all of the
    # methods of retrieving an entity for efficiency and to minimize the number
    # of times we run the callback for each model retrieval.
    db.Model.get_or_insert = _wrap_up_get(db.Model.get_or_insert)
    db.get_async = _wrap_up_get(db.get_async)
    db.Query.run = _wrap_up_get(db.Query.run)

    ndb.Key.get_async = _wrap_up_get(ndb.Key.get_async)
    ndb.Model.get_or_insert = _wrap_up_get(ndb.Model.get_or_insert)
    ndb.Model.get_or_insert_async = _wrap_up_get(ndb.Model.get_or_insert_async)
    ndb.Query.fetch_async = _wrap_up_get(ndb.Query.fetch_async)
    ndb.Query.fetch_page_async = _wrap_up_get(ndb.Query.fetch_page_async)
    ndb.QueryIterator.next = _wrap_up_get(ndb.QueryIterator.next)

    def wrap_map_async(func):
        @functools.wraps(func)
        def wrapper(self, callback, *args, **kwargs):
            # We want to know which transaction was active at the time when the
            # request was made, not when the future from the request is
            # resolved. See comment in _wrap_up_nonclassmethod_get for more
            # information.
            cur_transaction = _transaction_object()

            def hooked_callback(*args):
                # ndb.Query.map_async has two signatures for callbacks. The
                # default one takes callbacks with a single argument. If the
                # pass_batch_into_callback argument to map_async is used, the
                # callback instead accepts 3 arguments.
                if len(args) == 1:
                    (model_or_key,) = args
                else:
                    assert len(args) == 3, args
                    (_, _, model_or_key) = args

                _run_get_hooks(model_or_key, transaction=cur_transaction)
                if callback is not None:
                    return callback(*args)
                else:
                    return model_or_key

            return func(self, hooked_callback, *args, **kwargs)

        return wrapper

    ndb.Query.map_async = wrap_map_async(ndb.Query.map_async)


def add_before_put_hook(callback):
    """Register a function to be called before any entity is put().

    This will be invoked during the execution of any of the following methods,
    and will be called before any RPC is sent to datastore. The callback's only
    argument will be the model about to be put (an instance of db.Model or
    ndb.Model).

    - db.put
    - db.put_async
    - db.Model.put
    - ndb.put_multi
    - ndb.put_multi_async
    - ndb.Model.put
    - ndb.Model.put_async
    """
    _ensure_db_hooks_installed()
    _put_hooks.append(callback)


def add_after_get_hook(callback):
    """Registers a function to be called after any model is fetched.

    This will be invoked immediately after the execution of any of the
    following methods, and will be called after the RPC has returned and the
    model is reconstructed. This means for asynchronous queries, the callback
    is invoked after the data has actually been converted into a model.
    The callback's only argument will be the model retrieved from the
    datastore.

    Note that this isn't called on the construction of
    a new model in memory (i.e. for models that don't exist in the datastore
    yet.)

    - db.Model.get
    - db.Model.get_by_id
    - db.Model.get_by_key_name
    - db.Model.get_or_insert
    - db.get
    - db.get_async
    - db.Query.run
    - db.Query.get
    - db.Query.fetch

    - ndb.Key.get
    - ndb.Key.get_async
    - ndb.Model.get_by_id
    - ndb.Model.get_by_id_async
    - ndb.Model.get_or_insert
    - ndb.Model.get_or_insert_async
    - ndb.Query.fetch
    - ndb.Query.fetch_async
    - ndb.Query.fetch_page
    - ndb.Query.fetch_page_async
    - ndb.Query.get
    - ndb.Query.get_async
    - ndb.Query.iter
    - ndb.Query.map
    - ndb.Query.map_async
    - ndb.get_multi
    - ndb.get_multi_async
    """
    _ensure_db_hooks_installed()
    _get_hooks.append(callback)
