title: "i18nize-templates: Internationalization After the Fact"
published_on: September 28, 2015
author: Craig Silverstein
team: Infrastructure
...

Khan Academy started as a collection of videos, but now has over
100,000 pieces of written content, from `exercises
<https://www.khanacademy.org/math/differential-calculus/derivative_applications/differentiation-application/e/applications-of-differentiation-in-biology--economics--physics--etc>`_
to `articles
<https://www.khanacademy.org/humanities/art-history-basics/beginners-art-history/a/cave-painting-contemporary-art-and-everything-in-between>`_
to `programming challenges
<https://www.khanacademy.org/computing/computer-programming/html-css/intro-to-html/p/challenge-write-a-poem>`_.
`All <https://tr.khanacademy.org/math/differential-calculus/derivative_applications/differentiation-application/e/applications-of-differentiation-in-biology--economics--physics--etc>`_
`of <https://es.khanacademy.org/humanities/art-history-basics/beginners-art-history/a/cave-painting-contemporary-art-and-everything-in-between>`_
`these
<https://pl.khanacademy.org/computing/computer-programming/html-css/intro-to-html/p/challenge-write-a-poem>`_
are now available in multiple languages.  But the Khan Academy codebase
was originally written to be English-only.  We had to retrofit the
codebase to support internationalization (i18n) and localization
(l10n) of written content *after* a lot of infrastructure was already
in place.  As most guides to i18n and l10n will tell you, life is much
happier if you design for them before the fact.  This was not an
option for us.

The task was made more difficult by the variety of technologies we've
used over the years.  We use 5 different HTML-rendering technologies:

1. jinja2 (for our Python server code)
2. react (for our modern JavaScript code)
3. raw JavaScript (for older JavaScript code)
4. handlebars (for HTML that has to be rendered via both Python and
   JavaScript)
5. Python (for our very old Python server code, which just wrote HTML
   directly from source)

and all of them needed to be converted to add i18n markup.


i18nize-templates
-----------------

There are plenty of tools out there to handle the actual translation of
strings; we use `Babel <http://babel.pocoo.org/>`_ and
`Jed <https://slexaxton.github.io/Jed/>`_.

And there are plenty of services out there to manage the actual
translation of strings; we use `Crowdin <http://www.crowdin.net>`_.

What is lacking is a tool that will mark up all the natural language
text in your code and templates; this is the process that determines
*what* text to show to translators.  For this task, we developed
`i18nize-templates <https://github.com/khan/i18nize_templates>`_, a
tool for finding natural language text in a variety of templating
languages, and automatically munging it to be i18n-aware.

.. class:: label

**sample input (jinja2)**:

.. code:: html

       <h2>Badges</h2>
       <p><img src="{{ badge.icon }}"
               alt="a picture of a {{ badge.label() }}">

.. class:: label

**sample output**:

.. code:: html

       <h2>{{ _("Badges") }}</h2>
       <p><img src="{{ badge.icon }}"
               alt="{{ _("a picture of a %(badge_label)s",
                         badge_label=badge.label()) }}">

.. class:: label

**sample input (handlebars)**:

.. code:: html

        <b class="from-video-author">From the author:</b>
        <textarea placeholder="Post feedback..."></textarea>
        {{{ discussionFormControls "Post feedback" }}}

.. class:: label

**sample output**:

.. code:: html

        <b class="from-video-author">{{#_}}From the author:{{/_}}</b>
        <textarea placeholder="{{#_}}Post feedback...{{/_}}"></textarea>
        {{#_}}{{{ discussionFormControls "Post feedback" }}}{{/_}}

i18nize-templates isn't magic: it can't convert ``item{#if n !=
1#}s{#endif}`` to the proper ngettext call.  But it can reduce the time
needed to annotate templates by over 90%.

i18nize-templates can convert raw HTML, jinja2 templates, and
handlebars templates.  (Due to similarities between jinja2 and django,
it may also support django templates, though this is untested.)  It
can also convert text files written using jinja2 or handlebars.

Using i18nize-templates
-----------------------

We are pleased to announce i18nize-templates as an open source Python
module.  You can install i18nize-templates via

.. code:: sh

   $ pip install i18nize-templates


Rewriting templates
===================

.. code:: sh

   $ pip install i18nize-templates

   $ echo "Hello {{world}}!" | i18nize-templates
   i18nizing -
   {{ _("Hello %(world)s!", world=world) }}

   $ echo "Hello {{world}}!" | i18nize-templates --handlebars
   i18nizing -
   {{#_}}Hello {{world}}!{{/_}}

Extracting natural language text
================================

You can also just use i18nize-templates as a Python library to easily
extract runs of natural language text from HTML and templated-HTML
(or templated-text) documents.  Here's a Python snippet we use to
fake-translate our website into our testing language, called box-language
(http://boxes.khanacademy.org):

.. code:: python

    import re
    import i18nize_templates

    def translate_to_boxes(jinja2_file_contents):
        def parser_callback(s, segment_separates_nltext):
            if s is None:
                return ''               # called at end-of-parse
            elif (segment_separates_nltext
                  or (s.startswith('{{') and s.endswith('}}'))
                  or (s.startswith('<') and s.endswith('>'))):
                return s   # do not translate
            else:
                return re.sub(r'\w', u'\u25a1', s)  # alnum -> box

        parser = i18nize_templates.Jinja2HtmlLexer(parser_callback)
        return parser.parse(jinaj2_file_contents)


Extracting JavaScript
=====================

Sometimes, i18nize-templates is useful just because it knows how to
parse templated HTML.  For instance, for some of our code, we need to
extract JavaScript (inside ``<script>`` tags) from our HTML files.
There are many tools to do this for straight HTML, but they all choke
on templated HTML.  A simple callback makes it easy to use
i18nize-templates for this task:

.. code:: python

   def extract_js_from_html(html, filetype):
       """Return JavaScript code from inside an html file."""
       next_segment_is_script_contents = [False]
       all_script_contents = []

       def callback(segment, segment_separates_nltext):
           if segment is None:    # EOF
               return ''

           # The '</script' is to check for an empty script.
           if (next_segment_is_script_contents[0] and
                  not segment.lower().startswith('</script')):
               all_script_contents.append(segment)

           segment = segment.lower()
           next_segment_is_script_contents[0] = (
               segment.startswith('<script'))

       if filetype == "html":
           lexer = i18nize_templates.HtmlLexer(callback)
       elif filetype == "jinja2":
           lexer = i18nize_templates.Jinja2HtmlLexer(callback)
       elif filetype == "handlebars":
           lexer = i18nize_templates.HandlebarsHtmlLexer(callback)
       else:
           assert False, ('Expected "html", "jinja2" or '
                          '"handlebars", found %s' % filetype)

       lexer.parse(html)
       return all_script_contents

Side note: in reality, our JavaScript extractor is a fair bit more
complicated, because of the potential use of the template conditionals
within the JavaScript:

.. code:: html

    <script>
       var x = {% if x %}true{% else %}false{% endif %};
       call_function(x{% if arg2 %}, {{arg2}}{% endif %})
    </script>

Our code actually parses out all these conditionals and yields several
versions of the JavaScript, one for each possible value of each
if/else:

.. code:: javascript

       var x = true; call_function(x);
       var x = false; call_function(x);
       var x = true; call_function(x, arg2);
       var x = false; call_function(x, arg2);

The full code of the JavaScript extractor is available
`here </supporting-files/js_in_html.py>`_.


Implementation
--------------

i18nize-templates consists of two parts: a template lexer, and a text
rewriter.  The template lexer finds runs of natural language text in
the input code, and the rewriter adds ``{{ _(...) }}`` and the like,
munging the natural language text if appropriate.

The lexers
==========

There are many Python HTML lexers, but none that can handle template
markup.  For instance, any HTML lexer would get very confused by
either of these:

.. code::

   <img title="{{get_title "foo" "bar"}}" src="...">
   <img title={% if x %}"yes"{% else %}"no"{% endif %} src="...">

(Each template language has its own parser, of course, but these
parsers are not suitable for text rewriting of the type we are
attempting here, since they parse into an AST but do not provide a way
to get from the AST back to a textual representation.)

For this reason, i18nize-templates implements its own lexers, one that
can handle raw HTML, one that can handle jinja2-annotated HTML, and
one that can handle that handlebars-annotated HTML.  They are all
based on the Python standard library module ``markupbase``, which is
what the standard libarary class ``HTMLParser`` is based on.

We did not base the lexer on HTMLParser directly, since it was too
difficult to subclass for the template-specific lexers.  This also
allowed for some simplifications: we don't parse out HTML entities,
for instance.

The lexers call a user-provided callback function for every 'element'
that they see.  There are only a few different types of elements:

* An HTML tag
* A run of text between HTML tags
* A template variable (``{{variable}}`` in jinja2)
* A template comment (``{#comment#}`` in jinja2)
* A template block construct (``{%block construct%}...{%endblock%}`` in jinja2)

The main role of the lexer, besides tokenizing the input into
elements, is to categorize each element as either **separating natural
language text** or **not separating natural language text**.

This concept is closely related to the HTML distinction between block
and inline elements.  If you have (somewhat ill-formed) HTML like the
following:

.. code:: html

   This is what I like to do:
   <ul>
      <li> Go to the movies
      <li> Read books
      <li> Sleep a <i>lot</i>
   </ul>

You want to present the translator with four different strings to
translate: "This is what I like to do" (probably you don't want to
include the colon); "Go to the movies"; "Read books"; "Sleep a
<i>lot</i>".  You don't want to present the translator with that
entire block of HTML as just one giant string to translate.

In this example, the ``<ul>`` and ``<li>`` tags **separate** blocks of
natural language text into semantically distinct blocks that can (and
should) be translated separately.  The ``<i>`` and ``</i>``, on the
other hand, do not; we don't want to tell the translator to translate
"Sleep a" and "lot" separately!

When making a callback on an element, the i18nize-templates lexers say
whether that element separates natural language text or not.

Note that while related to the concept of HTML inline elements, the
implementation of natural language text separation is slightly
different, due to the semantics of some of the HTML tags.  For
instance, ``<textarea>`` is an inline element, but we consider it to
separate natural language text ("nltext") because text inside a
textarea is semantically separate from the text before and after it.
Likewise, we special case ``<br><br>`` to separate natural language
text, since semantically it's used by HTML authors as a synonym for
``<p>``.

The rules for whether an element separates natural language text are
subtle in the details but simple in broad outline:

* **An HTML tag**: yes for block elements, no for inline elements
* **A run of text between HTML tags**: no, by definition; but yes
  inside cdata sections like ``<script>``
* **A template variable**: no
* **A template comment**: yes  (could have gone either way here)
* **A template block construct**: yes



Sub-lexers
==========

Another complication for parsing natural language text inside HTML
files and templated HTML files, is that elements such as tags and
template variables can include natural language text internally:

.. code:: html

   <img title="This is where I live" src="...">
   <div>{{ add_prefix("This is where I live") }}</div>

For this reason, the i18nize-templates driver uses two lexers.  The
main lexer emits elements from the doc.  For each element it returns
that might have natural language text inside of it, we call a
sub-lexer on the subset of the element with natural language.  In the
above example, we'd call a lexer on the value of the ``title``
attribute, and on the function argument to ``add_prefix``.

Rewriters
=========

The main driver of the "i18nize" process is the rewriter.  The
rewriter owns the lexer and sub-lexer, and uses them to find the
location of blocks of natural language text within the document.

Consider the following HTML:

.. code:: html

   <p>Hi, <b>you</b>.</p><p>How are you doing?</p>

The lexer will make the following callbacks to the rewriter:

.. code:: python

   callback_to_rewriter('<p>',  separates_nltext=True)
   callback_to_rewriter('Hi, ', separates_nltext=False)
   callback_to_rewriter('<b>',  separates_nltext=False)
   callback_to_rewriter('you',  separates_nltext=False)
   callback_to_rewriter('</b>', separates_nltext=False)
   callback_to_rewriter('.',    separates_nltext=False)
   callback_to_rewriter('</p>', separates_nltext=True)
   callback_to_rewriter('<p>',  separates_nltext=True)
   callback_to_rewriter('How are you doing?', separates_nltext=False)
   callback_to_rewriter('</p>', separates_nltext=True)
   callback_to_rewriter(None, separates_nltext=True)      # end-of-document

As a reminder, we want the rewriter to emit (assuming the document is
a jinja2 template file):

.. code:: html

   <p>{{ _("Hi, <b>you</b>.") }}</p><p>{{ _("How are you doing?") }}</p>

Its algorithm is pretty simple: when it sees a segment with
separates_nltext=False, it collects it up.  Whenever it sees a segment
with ``separates_nltext=True``, it concatenates together the
previously collected-up segments, puts ``{{ _("...") }}`` around the
whole thing, and emits it.  Then it also emits the separates_nltext
text; stuff that separates natural-language runs is never marked up,
and can always be emitted verbatim.

This work is made (much) more complicated by various optimizations we
put in to make life simpler for translators.  For instance, for HTML
like ``<p>hi</p>\n``, the newline is its own nl-text segment, but we
don't want to emit ``{{ _("\n") }}`` -- translators don't need to
translate the newline character!  Likewise, if the text is

.. code:: html

   <b>&lt; Hi &gt;</b>

it's best to emit

.. code:: html

    <b>&lt; {{ _("Hi") }} &gt;</b>

rather than

.. code:: html

   {{ _("<b>&lt; Hi &gt;</b>") }}

-- there's no need to force the translators to copy over the bold tags
and the punctuation.  So there are regexps and rather complex logic to
identify where "actual natural language text" starts and ends within a
natural-language run.

The work is also made more complicated by the syntactic changes that
are needed for rewriting, especially for jinja2.  The main problem is
that variables are treated differently once we add the ``_()`` around
the text-to-be-translated:

.. class:: label

**sample input**

.. code:: html

           Have {{days}} nice days!

.. class:: label

**sample output**

.. code:: html

           _("Have %(days) nice days!", days=days)

We also need to worry about arguments to functions and filters:

.. code:: html

        {{ some_fn("text") }}
        {{ somevar.serialize("text") }}
        {{ somevar|serialize("text") }}

Sometimes i18nize-templates just can't tell whether a string is
natural language text or not.  Consider this jinja2 snippet:

.. code:: html

      Interested in the {{ myfn("title") }}}?

Is "title" natural language text that needs to be translated?  Or is
it a label that ``somefunc`` will use to look up the title of something?
i18nize-templates can't know, so it just bails:

.. code:: html

      _("Interested in the %(myfn)s?", myfn=myfn(_TODO("title")))

The person running i18nize-templates will have to manually decide
whether the ``_TODO()`` should be removed or replaced with ``_()``.


Optimizations
-------------

i18nize-templates takes some effort to make life easier for both
translators and for the person marking up the files with natural
language text.

For translators, i18nize-templates tries hard to reduce the size of
the text to be translated, as in the example above where the ``<b>``
and ``&lt;`` were not included in the text-to-be-translated.  It does
this by hard-coding rules about which entities are alphabetical and
which are not, and likewise what trailing punctuation is part of
natural language text (`.`, `?`, etc.) and what is not (`^`, `*`,
etc).

For the person marking up the files, i18nize-templates hard-codes some
logic about whether template function arguments are natural language
text or not.  For instance, it knows that the argument to the jinja2
``groupby`` function is not natural language.  Likewise, it knows that
for any jinja2 function that takes a ``style`` argument, that argument
is the name of a CSS style and not natural language text (even though
style names may look like natural language names).

i18nize-templates has some customization functions to tell it that
particular HTML tag attributes do or do not have natural language
text, as well as particular template functions.  You can also mark
certain function parameters, or even function argument values, as not
being natural language text.  For instance, for
``myfunc(url="http://example.com")``, there are three different ways
to say that ``http://example.com`` is not nl-text: you could say
``myfunc`` has no natural language arguments, you could say parameters
named ``url`` never have natural language values, or you could say
arguments matching ``http://.*`` are never natural language.

If i18nize-templates marks a certain bit of text to be translated, but
it really shouldn't be, then you can tell i18nize-templates to leave it
alone:

.. code:: html

     {{ i18n_do_not_translate("Khan Academy:") }} Funtime!

You will need to register a function `i18n_do_not_translate` with your
template engine that is a no-op.  In Khan Academy, we do the following:

.. code:: python

   webapp2_extras.jinja2.default_config = {
     "template_path": ...
     "globals": {
       "i18n_do_not_translate": lambda s: jinja2.Markup(s)
       ...
     }
     ...
   }


Summary
-------

When Khan Academy converted our website from being all in English to
including i18n markup, i18nize-templates saved many man-months of
tedious work.  We used it for straight HTML files, jinja2, and
handlebars, and should be easy to extend to other HTML template
languages as well.

Since our conversion completed, i18nize-templates has found a second
life as a templated-HTML lexer.  It has proven particularly useful at
extracting natural language text out of (possibly templated) HTML
files.  We've also used it as an easy way to extract JavaScript out of
templated HTML files.
