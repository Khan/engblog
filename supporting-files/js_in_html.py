"""Copyright 2015 Khan Academy Inc. - All Rights Reserved."""

import HTMLParser
import re

from third_party import i18nize_templates


_JINJA2_ELSE_RES = (re.compile(r'\{%-?\s*if\b.*?%\}'),
                    re.compile(r'\{%-?\s*(else|elif\b.*?)\s*-?%\}'),
                    re.compile(r'\{%-?\s*endif\s*-?%\}'))

_HANDLEBARS_ELSE_RES = (re.compile(r'\{\{#if\b.*?\}\}'),
                        re.compile(r'\{\{else}\}'),
                        re.compile(r'\{\{/if\}\}'))


class _FakeEmptyMatch(object):
    def __init__(self, pos):
        self.start = lambda: pos
        self.end = lambda: pos
        self.group = lambda: ''


def if_branch_iterator(content, filetype, keep_re=None,
                       else_res=None):
    """For given html/handlebars, yield versions of each if branch.

    Consider this code:
       <script>var x = { {%if cond%}y: 4{%else%}y: 5{%endif%} };</script>
    (Code like this actually exists in our codebase.)  We can't parse
    this out as 'var x = { y:4y: 5}' because that's a syntax error.
    The only reasonable course is to pick one branch of the 'if' to
    keep, and remove.  But we don't know which branch will be more
    interesting.  The solution is we pick *both* branches, and yield
    two strings holding javascript code: 'var x = { y: 4 };' and 'var
    x = { y: 5 }'.  Thus, each {%if%} in a file will double the number
    of entries returned ({%elif%}'s could increase that factor even
    more).

    Arguments:
        content: the (jinja2 or handlebars) templated code to analyze.
        filetype: "html", "jinja2", or "handlebars"
        keep_re: if specified, a regexp 'of interest'.  We only
           iterate over the branches of an 'if' statement if the if
           statement includes this regexp in it (between the if and the
           endif).  Otherwise, we just leave the if statement in
           verbatim, that is, with both branches together in the file.
           (This is an optimization to reduce the amount of blow-up
           caused by lots of if's in a file, if we only care about
           certain if statements.)
        else_res: for power users.  If specified, filetype is ignored.
    """
    if else_res:
        else_re = else_res
    elif filetype == "html":
        else_re = None
    elif filetype == "jinja2":
        else_re = _JINJA2_ELSE_RES
    elif filetype == "handlebars":
        else_re = _HANDLEBARS_ELSE_RES
    else:
        assert False, ('Expected "html", "jinja2" or "handlebars", found %s'
                       % filetype)

    def comment_out_branches(s, start, end, all_if_body_separators):
        """Given a list of (if-match, else-match, elif..., endif-match) tuples,
        -- matching {%if...%}, {%else%}, {%elif...%}, and {%endif%} --
        comment out the if-body and else-bodies of each in turn, and
        return the subset of s that was between start and end when
        s was passed in.  all the if_body_separators that do not fit
        within start and end are ignored.  Thus, if passed in
        (s, 40, 50, ...), we'll take s[40:50], do all the
        replacements we need to, and yield the new s[40:50] (which
        may have a different length now).  We use start/end instead
        of slicing so the match.start()/end() pos'es remain accurate.
        """
        # We only consider matches that are inside our start/end range.
        all_if_body_separators = [m for m in all_if_body_separators
                                  if (m[0].start() >= start and
                                      m[-1].end() <= end)]
        if not all_if_body_separators:
            yield s[start:end]
        else:
            if_body_separators = all_if_body_separators[0]  # do the first
            if_start = if_body_separators[0].start()
            if_end = if_body_separators[-1].end()
            # Since we take the if/endifs in position-order, we know
            # that nothing in the prefix needs to be rewritten.
            prefix = s[start:if_start]
            for suffix in comment_out_branches(s, if_end, end,
                                               all_if_body_separators):
                # Take each body of the if in turn.  A "body" is the
                # xxx and yyy in '{%if blah%}xxx{%else%}yyy{%endif%}'.
                for i in xrange(len(if_body_separators) - 1):
                    body_start = if_body_separators[i].end()
                    body_end = if_body_separators[i + 1].start()
                    # Recurse on any nested if's inside our body.
                    for body in comment_out_branches(s, body_start, body_end,
                                                     all_if_body_separators):
                        # Remove -- or actually just keep the newlines
                        # from, to preserve line numbers -- all of the
                        # 'if' except this one body.  (We could
                        # comment out the other parts instead of
                        # removing them, but it gets really unreadable.)
                        yield ''.join(
                            (prefix,
                             '\n' * s.count('\n', if_start, body_start),
                             body,
                             '\n' * s.count('\n', body_end, if_end),
                             suffix))

    if not else_re:
        yield content
    else:
        # The only way to avoid problems with nested if's is to
        # construct the if/endif's starting with the most compact.
        all_ifs = list(else_re[0].finditer(content))
        all_elses = list(else_re[1].finditer(content))
        all_endifs = list(else_re[2].finditer(content))
        if_tuples = []  # [(if-match, elif-match..., else-match, endif-match)]
        while all_ifs:
            match_lengths = []
            for if_match in all_ifs:
                # Find the endif that goes with this if.  This is only
                # guaranteed accurate for the most compact of the
                # if/endif's, but that's the only one we keep.
                endif_match = [m for m in all_endifs
                               if m.start() > if_match.end()][0]
                match_lengths.append((endif_match.end() - if_match.start(),
                                      if_match, endif_match))
            most_compact_if_endif = min(match_lengths)[1:]
            # Now that we've matched the most compact if/endif, remove
            # those from consideration for the next most compact.
            all_ifs.remove(most_compact_if_endif[0])
            all_endifs.remove(most_compact_if_endif[1])

            inner_elses = [m for m in all_elses
                           if (most_compact_if_endif[0].end() <= m.start()
                               <= most_compact_if_endif[1].start())]
            # If there is no explicit else, we want to add an implicit one:
            # {%if blah%}foo{%else%}{%endif%}
            if not inner_elses:
                inner_elses = [
                    _FakeEmptyMatch(most_compact_if_endif[1].start())]
            else:
                for inner_else in inner_elses:
                    all_elses.remove(inner_else)

            if_tuples.append(tuple([most_compact_if_endif[0]] +
                                   inner_elses +
                                   [most_compact_if_endif[1]]))

        # Remove tuples that don't match the keep-re.
        if keep_re:
            if_tuples = [t for t in if_tuples if
                         keep_re.search(content[t[0].start():t[-1].end()])]

        # Sort the tuples by where each begins.
        if_tuples.sort(key=lambda m: m[0].start())

        for s in comment_out_branches(content, 0, len(content), if_tuples):
            yield s


# Rules for how we handle template markup inside script tags.  We need
# to replace this markup with legal javascript, which differs
# depending on the type of construct it is.  We also have to make the
# replacement not look like template markup itself, so it doesn't get
# doubly-replaced.  Since we are putting this stuff in comments, we
# need to make sure it doesn't have internal comments.  And finally,
# we have to worry about the replacement being inside a string, so we
# get rid of quotes as well.
def _comment_out(s):
    return '/* %s */' % (s.replace('{', '[').replace('}', ']')
                          .replace('/*', '|*').replace("*/", '*|')
                          .replace('"', '%').replace("'", '%')
                          .replace('`', '%'))


_COMMENT_OUT = lambda m: _comment_out(m.group())
_EMPTY_VAR = lambda m: '{%s}' % _comment_out(m.group())

_JINJA2_MARKUP_REPLACEMENTS = (
    (re.compile(r'\{%\s*comment\s*%\}', re.DOTALL),
     lambda m: '/* [% comment %]'),
    (re.compile(r'\{%\s*endcomment\s*%\}', re.DOTALL),
     lambda m: '[% endcomment %] */'),
    (re.compile(r'\{\{.*?\}\}', re.DOTALL), _EMPTY_VAR),
    (re.compile(r'\{\#.*?\#\}', re.DOTALL), _COMMENT_OUT),
    (re.compile(r'\{%.*?%\}', re.DOTALL), _COMMENT_OUT),
)

_HANDLEBARS_MARKUP_REPLACEMENTS = (
    (re.compile(r'\{\{\s*else\s*\}\}', re.DOTALL), _COMMENT_OUT),
    (re.compile(r'\{\{\#.*?\}\}', re.DOTALL), _COMMENT_OUT),
    (re.compile(r'\{\{\/.*?\}\}', re.DOTALL), _COMMENT_OUT),
    (re.compile(r'\{\{\!.*?\}\}', re.DOTALL), _COMMENT_OUT),
    (re.compile(r'\{\{.*?\}\}', re.DOTALL), _EMPTY_VAR),
)

_SCRIPT_RE = re.compile(r'<script', re.I)


def extract_js_from_html(html, filetype, keep_re=None, file_name=None):
    """Return (many versions of) javascript code from inside an html file.

    Typically such code will be found inside a <script> tag.  If the
    javascript code has template markup in it, we replace that markup
    with something 'safe.'

    This is an iterator, and yields (at least) once for every <script>
    tag in the html, with the contents of the script tag.

    If there is {%if%} (or {{#if}}) template-markup within the html,
    we will yield multiple times for the same script tag.  Why?
    Consider this code:
       <script>var x = { {%if cond%}y: 4{%else%}y: 5{%endif%} };</script>
    (Code like this actually exists in our codebase.)  We can't parse
    this out as 'var x = { y:4y: 5}' because that's a syntax error.
    The only reasonable course is to pick one branch of the 'if' to
    keep, and comment out the other .  But we don't know which branch
    will be more interesting.  The solution is we pick *both*
    branches, and yield two strings holding javascript code: 'var x =
    { y: 4 };' and 'var x = { y: 5 }'.  Thus, each {%if%} in a file
    will double the number of entries returned; the hope is that
    'if' inside scripts is rare enough that's not a problem.  (We
    could optimize if so by only doing the full recursion for *nested*
    else's, and otherwise just hold all other else's to the first
    branch while alternating the else we're currently considering.)

    May raise HTMLParser.HTMLParseError or AssertionError
    if given malformed html as input.

    Arguments:
        html: the html fragment to extract javascript from
        filetype: "html", "jinja2", or "handlebars", to indicate
            the templating system the html is written in.
        keep_re: if specified, a regexp 'of interest'.  We only
           iterate over the branches of an 'if' statement if the if
           statement includes this regexp in it (between the if and the
           endif).  Otherwise, we just leave the if statement in
           verbatim, that is, with both branches together in the file.
           (This is an optimization to reduce the amount of blow-up
           caused by lots of if's in a file, if we only care about
           certain if statements.)

    Yields:
        Each iteration yields the contents of one <script> tag inside
        html, with all content outside that <script> tag replaced by
        blank lines (we do things this way so the line numbers before
        and afer match up), with different branches chosen for an
        if/else on each iteration.  If no javascript was found in the
        file, gives the empty iterator (that is: never yields at all).
    """
    # As a quick short-circuit, if '<script' does not appear in f,
    # it *can't* have any javascript in it, so bail.
    if not _SCRIPT_RE.search(html):
        return

    next_segment_is_script_contents = [False]
    line_number = [1]
    num_lines = 1 + html.count('\n')
    all_script_contents = []

    def callback(segment, segment_separates_nltext):
        if segment is None:
            return ''

        new_line_number = line_number[0] + segment.count('\n')

        if (next_segment_is_script_contents[0] and
               not segment.lower().startswith('</script')):  # empty script
            # We want to put this content at the right line number.
            # We also want the right number of blank lines afterwards.
            all_script_contents.append(''.join(
                ('\n' * (line_number[0] - 1),
                 segment,
                 '\n' * (num_lines - new_line_number))))

        line_number[0] = new_line_number

        # Some people sneakily abuse the script tag to store html
        # content: http://ejohn.org/blog/javascript-micro-templating/
        # They use a type='text/<not javascript>' for this.
        segment = segment.lower()
        next_segment_is_script_contents[0] = (
            segment.startswith('<script') and
            not ('type=' in segment and 'javascript' not in segment))

    if filetype == "html":
        lexer = i18nize_templates.HtmlLexer(callback)
        else_re = None
        replacements = ()
    elif filetype == "jinja2":
        lexer = i18nize_templates.Jinja2HtmlLexer(callback)
        else_re = _JINJA2_ELSE_RES
        replacements = _JINJA2_MARKUP_REPLACEMENTS
    elif filetype == "handlebars":
        lexer = i18nize_templates.HandlebarsHtmlLexer(callback)
        else_re = _HANDLEBARS_ELSE_RES
        replacements = _HANDLEBARS_MARKUP_REPLACEMENTS
    else:
        assert False, ('Expected "html", "jinja2" or "handlebars", found %s'
                       % filetype)

    try:
        lexer.parse(html)
    except HTMLParser.HTMLParseError as e:
        if file_name:
            e.msg += ', in %s' % (file_name,)
        raise
    if not all_script_contents:
        return

    for script in all_script_contents:
        # Clean up jinja2 / handlebars markup inside script tags:
        #    <script>var x = {{myvar|json}};</script>
        for (regex, replacement) in replacements:
            script = regex.sub(replacement, script)

        # Look for the if/else's and comment out one branch at a time.
        # Since this runs after we've commented out the {%if%}/etc, we
        # need to pass in our own else_res.
        commented_else_res = []
        if else_re:
            for regex in else_re:
                commented_regex = (_comment_out(regex.pattern)
                                   .replace('/*', '/\\*')
                                   .replace('*/', '\\*/'))
                commented_else_res.append(re.compile(commented_regex))
            for retval in if_branch_iterator(script, filetype, keep_re,
                                             else_res=commented_else_res):
                yield retval
        else:
            yield script
