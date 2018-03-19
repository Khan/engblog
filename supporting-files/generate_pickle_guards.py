#!/usr/bin/env python2

"""A script to make files that will log when refactors cause pickling errors.

This is intended for use when moving files around where we aren't sure
what symbols might be pickled and what symbols might not be.

We store pickled data in databases and in other caches, and when
you pickle a class or function it stores the absolute path to the
class/function: foo.bar.myfunc. If you move that class/function to
another file, or otherwise rename it, then you can't unpickle the data
anymore, because the unpickler tries to load foo.bar.myfunc and can't
find it!

We have code to handle this in pickle_util.py, but that code needs to
know the old and new locations for each problematic symbol.  When
moving a bunch of files around there are so many symbols we can't be
sure we've got them all.  So we use this script as a safeguard.

What it does is create a file under the old name with a big `import *`
to import all the moved symbols under the old name.  Then they can be
found by the unpickler.  But we log if we ever need to use this file,
so we can find the problematic unpickles in the log and add them to
pickle_util to be handled properly.

Eventually, once we've cleared up all issues that the logs show up,
we'll be able to delete all the files that this script creates.

This uses `git` to determine what files have moved, that need
pickle guards.  If you do not use git, you will need to specify the
files in some other way.
"""

import os
import re
import subprocess
import sys


_TOP_LEVEL_SYMBOL_RE = re.compile(r'^(?:def|class)\s+(\w+)\s*[(:]',
                                  re.MULTILINE)

_PICKLE_LOGGER_CONTENTS = """\
import logging

# __file__ probably ends with '.pyc', convert that to .py
logging.error("Should not be importing %%s, update pickle_util.py"
              %% (__file__[:-1] if __file__.endswith('.pyc') else __file__))

%s
"""


def _module_for_file(filename):
    """Return the module-name corresponding to the given filename."""
    base, _ = os.path.splitext(filename)
    if os.path.basename(base) == '__init__.py':
        base = os.path.dirname(base)
    else:
        base, _ = os.path.splitext(filename)
    module = base.replace(os.path.sep, '.')
    return module


def _top_level_symbols(contents):
    """Return a list of all top-level classes/functions defined in fname."""
    return sorted(_TOP_LEVEL_SYMBOL_RE.findall(contents))


def _should_write_pickle_logger(outfile, new_file):
    # If it is not a python file then just ignore it, without even warning
    if not outfile.endswith('.py'):
        return False

    if os.path.exists(outfile):
        print ('WARNING: ignoring %s (importing %s): %s already exists'
               % (outfile, new_file, outfile))
        return False

    with open(new_file) as f:
        new_contents = f.read()

    if not _top_level_symbols(new_contents):
        print ('INFO: ignoring %s, it has no top-level symbols to forward'
               % new_file)
        return False

    print "Creating pickle logger for %s in %s" % (new_file, outfile)
    return True


def _write_pickle_logger(outfile, new_file):
    """Write a file to outfile that imports everything from new_file."""
    with open(new_file) as f:
        new_contents = f.read()

    what_to_import = _top_level_symbols(new_contents)
    if not what_to_import:    # no need for a forwarding file
        print ('INFO: ignoring %s, it has no top-level symbols' % new_file)
        return

    import_lines = ['from %s import %s  # NoQA: E501,F401(unused import)'
                    % (_module_for_file(new_file), symbol)
                    for symbol in what_to_import]

    # In the process of moving things out of this directory, the
    # subdirectory the old module came from may have been deleted.
    dir_parts = os.path.dirname(outfile).split(os.sep)
    for i in xrange(1, len(dir_parts) + 1):
        dir = os.path.join(*dir_parts[:i])
        if not dir:
            continue
        try:
            os.mkdir(dir)
        except OSError:   # probably directory already exists
            pass
        open(os.path.join(dir, '__init__.py'), 'a').close()

    with open(outfile, "w") as f:
        f.write(_PICKLE_LOGGER_CONTENTS % '\n'.join(import_lines))


def _parse_file_move(file_move):
    """Return the (old_filename, new_filename) tuple for a file move."""
    _, old_filename, new_filename = file_move.split()
    return (old_filename, new_filename)


def main(compare_with):
    cmd = [
        'git', 'diff', '-M', '--name-status', '--diff-filter=R', compare_with
    ]

    # Run the `git diff` command to list all file moves since a revision
    try:
        file_moves = subprocess.check_output(cmd)
    except subprocess.CalledProcessError:
        sys.exit("Could not diff against revision %s\n" % compare_with)

    # Try to make a pickle logger for each file move
    for line in file_moves.splitlines():
        old_file, new_file = _parse_file_move(line)
        if _should_write_pickle_logger(old_file, new_file):
            _write_pickle_logger(old_file, new_file)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--revision", default="HEAD",
                        help="The revision you want to compare against.")
    args = parser.parse_args()

    main(args.revision)
