#!/usr/bin/env python

"""A tool to generate a regexp that matches all our static resources.

We use this regexp with Fastly, so Fastly knows what urls should go to
GCS (where we store our static resources) rather than GAE.

We get the list of static resources by parsing handlers*.yaml.

Fastly has a 512-character limit on the size of our regexp, so we do
quite a bit of work to reduce the regexp to as few bytes as possible!

Our main trick is that we don't try to come up with a regexp that
captures a list of all the static-file handlers we have.  Rather, we
come up with a regexp that uniquely distinguishes static from dynamic
handlers.  The difference is subtle but important: by ignoring urls
that don't match either, we can come up with a much smaller regexp.

Here's a simple example: suppose we only had two handlers, a static
handler /foo (which serves foo.html) and a dynamic handler /bar (which
runs some python code).  Since all requests are either /foo or /bar,
this script doesn't need to emit a regexp like `^/foo$` to match the
static requests; it can use `^/f`, the uniquely identifying prefix.

One problem with this scheme is we play fast and loose with dynamic
urls that start with regxp metachars (e.g. `^(.*/p/.*)` which is a
real handler re) -- we just assume they never can match static routes.
So this approach could lead to some errors, though in practice I don't
think it does.
"""

import os
import re
import sys

# Set up the path so we can do local includes.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import appengine_tool_setup

appengine_tool_setup.fix_sys_path()

import modules_util
import route_map


def get_static_regexps():
    """This is Khan Academy-specific."""
    handlers = modules_util.module_yaml('default')['handlers']
    retval = set()

    for handler in handlers:
        if handler.GetHandlerType() == 'static_dir':
            retval.add('^' + handler.url + '/')
        elif handler.GetHandlerType() == 'static_files':
            retval.add('^' + handler.url + '$')

    return sorted(retval)


def get_dynamic_prefixes():
    """For a url for a dynamic route, return the literal prefix.

    'Literal prefix' is everything up to the first regexp metacharacter.

    This is Khan Academy-specific.
    """
    retval = set()

    # Matches all literal chars (not regexp metachars), but we do
    # allow a leading ^.
    prefix_re = re.compile(r'^[^$.?*+()<>\[\]]+')

    all_routes = route_map.generate_route_map()
    for routes_for_one_handler in all_routes:
        if ('<file>' in routes_for_one_handler[1] or
               '<directory>' in routes_for_one_handler[1]):
            # This is a static handler, so ignore it.
            continue

        handler_regex = routes_for_one_handler[0].pattern
        if handler_regex in ('^.*$', '^/.*$'):
            # This is the catch-all handler, so we need to add in all
            # its routes.  The route-info proper starts at list elt 2.
            for route_info in routes_for_one_handler[2:]:
                url = route_info[0].pattern
                m = prefix_re.match(url)
                if m:
                    retval.add(url[:m.end()])
        else:
            # We can just use the url that matches this handler as
            # a whole.
            m = prefix_re.match(handler_regex)
            if m:
                retval.add(handler_regex[:m.end()])

    return retval


def _shorten_one_regexp(regex, dynamic_prefixes):
    """Remove chars from a regexp where they don't add any value."""
    # The common case we encourage in handler files is '/(...)'
    if regex.startswith('^/(') and regex.endswith(')$'):
        regex = '^/' + regex[3:-2] + '$'
    elif regex.startswith('^/(') and regex.endswith(')/'):
        regex = '^/' + regex[3:-2] + '/'

    if regex.endswith('.*$'):
        regex = regex[:-3]

    # Finally, and this is our big win: our main job here is to
    # distinguish urls for static content with urls for dynamic
    # content.  So if some prefix of this url is found to not be
    # the prefix of any of the dynamic urls, we can shorten this
    # regexp to just <prefix>.
    #
    # One danger of this approach is that whenever anyone adds a new
    # dynamic route, it may change what prefix is unique.  But people
    # may forget to run this script every time they add a new route.
    # So to reduce the risk of having a too-fragile prefix, we force
    # the prefix to end on a `/`.
    is_dynamic_prefix = (
        lambda s: any(p.startswith(s) for p in dynamic_prefixes))

    for i in xrange(1, len(regex)):
        # Once we get to a regex character, we're done; this technique
        # only works for *literal* prefixes.
        if regex[i] in '()[].*?+<>':
            break
        if not is_dynamic_prefix(regex[:i]):
            # NOTE: These next 3 lines are just to make the resulting
            # regexp a bit less brittle in the face of new routes
            # being introduced in the future.  If we need the space,
            # we can remove these lines and still get correct output.
            for j in xrange(i, len(regex)):
                if regex[j] == '/':
                    return regex[:j + 1]
            return regex   # No subsequent / found, oh well.

    return regex


def _combine_regexps(regex_list, dynamic_prefixes):
    """Return 're|re|re|re', as shortened as possible."""
    # First, get rid of some unnecessary chars in the re's.
    regex_list = sorted(set(_shorten_one_regexp(r, dynamic_prefixes)
                            for r in regex_list))

    # If one regex is a strict prefix of another (which implies it
    # doesn't end with a `$`), we can remove the longer one.
    for i in xrange(len(regex_list) - 1, 0, -1):
        while (i < len(regex_list) and
                   regex_list[i].startswith(regex_list[i - 1])):
            del regex_list[i]

    # We can't combine regexps if one has backreferences, due to
    # the fact we introduce parens.  Let's just check for that.
    assert not any(re.search(r'\\\d', r) for r in regex_list), (
        "We don't support backreferences in handler regexps!")

    # Our main way of shortening is to combine shared prefixes.  First
    # we sort the list of regexps.  Then, we find the entry with the
    # longest chared prefix with its neighbor, and replace it (and
    # subsequent entries if they also share the same prefix) with a
    # combined regexp: `<prefix>(a|b|c|...)`.  We repeat until we're
    # down to one regexp.
    # Because adding parens when we're already inside parens is
    # dangerous, we treat every capture-group in the input as a single
    # 'character'.  TODO(csilvers): work with nested parens.
    _RE_CHARS = re.compile(r'(\((?:\\.|[^\)]*)\)|[^\(])')
    regex_list_chars = [_RE_CHARS.findall(r) for r in regex_list]
    while len(regex_list_chars) > 1:
        prefix_len_and_index = []
        for i in xrange(len(regex_list_chars) - 1):
            for char_i in xrange(min(len(regex_list_chars[i]),
                                     len(regex_list_chars[i + 1]))):
                if (regex_list_chars[i][char_i] !=
                        regex_list_chars[i + 1][char_i]):
                    break
            prefix_len_and_index.append((char_i, i))

        prefix_len_and_index.append((-1, len(regex_list_chars) - 1))

        # This `key` causes us to return the lowest index with the long-prefix.
        (prefix_len, start_index) = max(prefix_len_and_index,
                                        key=lambda li: (li[0], -li[1]))
        for (end_prefix_len, end_index) in prefix_len_and_index[start_index:]:
            if end_prefix_len != prefix_len:
                break

        # OK, now we can combine all the regexps in [start_index, end_index].
        # Normally we do '(suffix1|suffix2|suffix3|...)' but if all
        # the suffixes are on char long we can do '[...]' instead.
        if all(len(regex_list_chars[i][prefix_len:]) == 1
               for i in xrange(start_index, end_index + 1)):
            new_regexp = regex_list_chars[start_index][:prefix_len] + ['[']
            for i in xrange(start_index, end_index + 1):
                new_regexp.extend(regex_list_chars[i][prefix_len])
            new_regexp.append(']')
        else:
            new_regexp = regex_list_chars[start_index][:prefix_len] + ['(']
            for i in xrange(start_index, end_index + 1):
                new_regexp.extend(regex_list_chars[i][prefix_len:])
                new_regexp.append('|')
            # Now replace the last '|' with a ')' instead.
            new_regexp[-1] = ')'

        # Replace the old regexps with this new one.  Even though the
        # new regexp doesn't have that paren-expression as a single
        # char, it's safe since we know that doesn't prefix-match
        # anything else.
        regex_list_chars[start_index] = new_regexp
        del regex_list_chars[start_index + 1: end_index + 1]

    return ''.join(regex_list_chars[0])


def _has_regex_metachar(s):
    # This function isn't very good, since it doesn't look for
    # backslashes.  So we limit it to metacharacters that we'd not be
    # likely to backslash, like '+'.  We also purposefully leave out ^
    # and $, since sometimes those get automatically added even to
    # static urls.
    return any(c in s for c in '()[]*?+')


def main():
    static_regexps = get_static_regexps()
    dynamic_prefixes = get_dynamic_prefixes()

    # Remove all top-level urls from our list that are static files
    # (and not regexps): things like /favicon.ico.  We don't put
    # resources at the top level if we can help it, so such urls are
    # likely to be fetched by third parties like browers, and those
    # third-parties won't be hitting the CDN anyway, so why have the
    # CDN try to serve them?  It just makes our output regexp longer,
    # which we can't really afford.
    static_regexps = [r for r in static_regexps if
                      r.count('/') > 1 or _has_regex_metachar(r)]

    return _combine_regexps(static_regexps, dynamic_prefixes)


if __name__ == '__main__':
    print main()

