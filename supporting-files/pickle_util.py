"""A wrapper around pickle and cPickle that support symbol renaming.

Sometimes classes, class instances, functions, or other symbols are
pickled.  When we rename those symbols -- even by just moving them to
another file -- then the pickled data cannot be unpickled anymore,
since the unpickler can no longer find the symbol where it expects.

To fix it, we keep a map in this file of oldname->newname.  Then,
whenever we unpickle an object and see oldname, we can instantiate a
newname instead.

We also add a few more optimizations: we use cPickle rather than
pickle whenever we can, and when pickling we default to protocol 2
rather than the inefficient protocol 0.

Note this code has only been tested on python2.
"""

import cPickle
import cStringIO
import logging
import pickle
import sys


# Every time you move path.to.module.symbol to some.other.path.symbol2,
# add an entry like this to this dict:
#     ('path.to.module', 'symbol'): ('some.other.path', 'symbol2')
# If you then move it *again* to 'a.third.location.symbol3', replace the
# entry above with these two entries:
#     ('path.to.module', 'symbol'): ('a.third.location', 'symbol3')
#     ('some.other.path', 'symbol2'): ('a.third.location', 'symbol3')
_SYMBOL_RENAME_MAP = {
    ('users.info', '_update_users'): ('accounts.info', '_update_users'),
    ('compat_key', '_CompatKey'): ('lib.compat_key', 'CompatKey'),
    ('compat_key', 'CompatKey'): ('lib.compat_key', 'CompatKey'),
}


def _renamed_symbol_loader(module_name, symbol_name):
    """Return a symbol object for symbol symbol_name, loaded from module_name.

    The trick here is we look in _SYMBOL_RENAME_MAP before doing
    the loading.  So even if the symbol has moved to a different module
    since when this pickled object was created, we can still load it.
    """
    (actual_module_name, actual_symbol_name) = _SYMBOL_RENAME_MAP.get(
        (module_name, symbol_name),   # key to the map
        (module_name, symbol_name))   # what to return if the key isn't found

    # This is taken from pickle.py:Unpickler.find_symbol()
    try:
        __import__(actual_module_name)   # import the module if necessary
    except ImportError:
        logging.error("Unable to import %s for %s", module_name, symbol_name)
        raise
    module = sys.modules[actual_module_name]
    return getattr(module, actual_symbol_name)


def Unpickler(fileobj):
    """Like cPickle.Unpickler, but with our symbol-renamer.

    Note that like cPickle.Unpickler, this is not actually a class and
    you therefore can't subclass it.  It also doesn't allow us to load
    classes that changed from new- to old-style, so if you need that,
    see StyleChangeUnpickler below.
    """
    # With cPickle, to override how global-lookup is done, you just define
    # find_global.  See the docs for details:
    # https://docs.python.org/2/library/pickle.html#subclassing-unpicklers
    unpickler = cPickle.Unpickler(fileobj)
    unpickler.find_global = _renamed_symbol_loader
    return unpickler


class StyleChangeUnpickler(pickle.Unpickler):
    """Like pickle.Unpickler, but with our symbol-renamer and NEWOBJ hack.

    Like Unpickler, above, this uses our symbol-renamer.  Unlike Unpickler, it
    also adds a hack to allow loading an old-style class that was pickled as
    new-style.  (Python handles the other direction just fine.)  It's necessary
    because some App Engine classes are new-style in Standard but old-style in
    python-compat and dev.  Note that we can only implement this hack against
    pickle's Unpickler, not cPickle's, so we try that one first and only use
    this one if it fails.
    """
    # With pickle, we have to override load_global, again see the docs:
    # https://docs.python.org/2/library/pickle.html#subclassing-unpicklers
    def load_global(self):
        module = self.readline()[:-1]
        name = self.readline()[:-1]
        self.append(_renamed_symbol_loader(module, name))

    # Not in the documentation, but what the source code requires
    pickle.Unpickler.dispatch[pickle.GLOBAL] = load_global

    # This lets us support the new-style-to-old-style hack.
    # Note it depends on the pickle protocol being >=2, and using pickle, not
    # cPickle, to unpickle.  VERY FRAGILE!
    def load_newobj(self):
        args = self.stack.pop()
        cls = self.stack[-1]
        try:
            obj = cls.__new__(cls, *args)
            self.stack[-1] = obj
        except AttributeError:        # cls is actually an old-style class
            k = len(self.stack) - 1   # point to the markobject
            self.stack.extend(args)
            self._instantiate(cls, k)
    pickle.Unpickler.dispatch[pickle.NEWOBJ] = load_newobj


def dumps(obj, protocol=cPickle.HIGHEST_PROTOCOL):
    """Return a pickled string of obj: equivalent to pickle.dumps(obj)."""
    try:
        return cPickle.dumps(obj, protocol)
    except Exception:
        logging.error("Unable to pickle '%s'", obj)
        raise


def loads(s):
    """Return an unpickled object from s: equivalent to pickle.loads(s)."""
    unpickler = Unpickler(cStringIO.StringIO(s))
    try:
        try:
            return unpickler.load()
        except cPickle.UnpicklingError:
            # We may have hit the NEWOBJ problem.  Try again using
            # NewobjSafeUnpickler in that case.
            unpickler = StyleChangeUnpickler(cStringIO.StringIO(s))
            return unpickler.load()
    except Exception:
        logging.error("Unable to unpickle '%s'", s)
        raise
