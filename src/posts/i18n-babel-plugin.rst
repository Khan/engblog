title: Babel in Khan Academy's i18n Toolchain
published_on: June 22, 2015
author: Kevin Barabash
team: Web Frontend
...

We've been using ES6 (along with JSX) for sometime at Khan Academy.  Right now,
we're using `jstransform <https://github.com/facebook/jstransform>`_ to compile
our ES6 and JSX code to ES5, but we'd like to switch to `babel <http://babeljs.io/>`_.
Some of the reasons for doing this include:

- better support for ES6 + ES7
- allows us to use `eslint <https://github.com/babel/babel-eslint>`_ making it 
  easier for open source contributors to run tests in projects such as 
  `perseus <https://github.com/Khan/perseus>`_.

i18n Workflow
-------------

Our i18n workflow on the frontend uses a custom plugin for jstransform which 
converts certain JSXElements into special function calls. 

.. class:: label
    
**input**:

.. code::

    <$_ first="Hayao" last="Miyazaki">
        Hello, %(first)s %(last)s
    </$_>
    <$i18nDoNotTranslate>var x = 5;</$i18nDoNotTranslate>

.. class:: label

**desired output**: 

.. code:: javascript

    $_({ first: "Hayao", last: "Miyazaki" }, 
        "Hello, %(first)s %(last)s!"
    );
    $i18nDoNotTranslate("var x = 5;");

While babel has support for JSX, it transforms all JSXElements into calls to
``React.createElement()``.  This would result in the following incorrect output: 

.. class:: label

**actual output**:

.. code:: javascript

    React.createElement(
        $_,
        { first: "Motoko", last: "Kusanagi" },
        "Hello, %(first)s %(last)s!"
    );
    React.createElement($i18nDoNotTranslate, null, 
        "var x = 5");

Plugin
------

Before we can switch to babel, we need to customize babel's output when it
encounters ``<$_>`` or ``<$i18nDoNotTranslate>`` tag.  We can use babel's
`plugin architecture <http://babeljs.io/docs/advanced/plugins/>`_.

It's relatively straight forward.  Each plugin is a node module which exports a 
single function which returns a ``babel.Transformer`` instance.  
``babel.Transformer`` takes two arguments: the name of the transformer as a 
string and an object containing callbacks.

.. code:: javascript

    module.exports = function (babel) {
        var t = babel.types;
        return new babel.Transformer("i18n-plugin", {
            JSXElement: function (node, parent, scope, file) {
                // inspect node, parent, scope, etc.
                // construct a tree and return its root
                
                // example: 
                // construct a new "CallExpression"
                // assumes callee and args exist
                var call = t.callExpression(callee, args);
                
                // copy the location from the source node 
                // so that line numbers can be maintained
                call.loc = node.loc;
                return call;
            }
        }
    };

After the JavaScript source is parsed, babel will run the callback on each 
node it finds in the AST of the specified type.  An AST 
(`Abstract Syntax Tree <https://en.wikipedia.org/wiki/Abstract_syntax_tree>`_)
is a tree structure where each node represents a part of the syntatic structure of
a piece of code such as statements, expressions, identifiers, literals, etc.
The keys for the object should be one of the node types listed in the 
`babel source <https://github.com/babel/babel/blob/master/src/babel/types/visitor-keys.json>`_.
This list of nodes extends Mozilla's original `Parser API <https://developer.mozilla.org/en-US/docs/Mozilla/Projects/SpiderMonkey/Parser_API>`_.

Some notes about the example:

- babel.types provides functions for creating new nodes
- babel also supports calling on exit, or calling on both enter and exit if needed
- full source code for the plugin as available in `Khan/i18n-babel-plugin <https://github.com/Khan/i18n-babel-plugin>`_.

Matching Output
---------------

When developing this plugin it was important that we match the output we were
getting from jstransform so that babel could be a drop-in replacement without
having to modify other parts of our build chain.  In particular we needed to
ensure that we were maintaining both line numbers in compiled code as well as
whitespace within translation strings.

Line Numbers
============
Maintaining line numbers is important because not all of our build chain is 
source map aware.  In particular kake, our custom build system, does not know
how to deal with source maps.  Babel's "retainLines" options takes care of this 
for us.

We did however find one issue with "retainLines".  If a method call had 3 or 
more arguments then Babel would ignore "retainLines" and pretty print it so
that each argument was on a separate line.  Babel's maintainer sebmck was quite
responsive and provided an update within a couple of hours.

Whitespace
==========
As for whitespace within localized strings, any changes in the whitespace means
that the string is essentially a different string which means that that string
would need to be re-translated into different languages for all our localized
sites.

In order to make sure that our Babel plugin produces calls to ``$_()`` with the 
same strings as jstransform we need to compare all of the JavaScript strings.
One of our build steps generates a .pot file (used by Gettext `http://en.wikipedia.org/wiki/Gettext <http://en.wikipedia.org/wiki/Gettext>`_) 
containing all of the strings  on the site that need to be localized.  We 
generated .pot files using both the jstransform and babel workflows and compared 
them using a python script.  

The script uses `polib <https://pypi.python.org/pypi/polib>`_ to parse the .pot 
files generated by the two workflows and iterate through the entries.  It looks 
at the occurrences property to pick out the items that came from javascript and 
creates a dict from msgid->entry.

.. class:: label

**example.pot**:

.. code::

    #: modules/user/views_handler_filter_user_name.inc:29
    msgid "Enter a comma separated list of user names."
    msgstr ""
    #: modules/user/views_handler_filter_user_name.inc:112
    msgid "Unable to find user: @users"
    msgid_plural "Unable to find users: @users"
    msgstr[0] ""
    msgstr[1] ""

We then compared the two dicts and looked for differences in occurrences or strings.  
There were a few discrepancies in line numbers which had to be investigated manually.  
It turned out that the jstransform line numbers were off by a line from the source 
line numbers.  While this was not an issue, there were quite a few strings that 
weren't the same.  Close inspection of these revealed that the differences were 
differences in whitespace.

Various patterns of carriage returns and spaces were producing the differences
in whitespace.  Creating test cases (and fixes) for a few of these situations 
and then re-running our string comparison script allowed us to quickly narrow
the large number of mismatched strings into a relatively few test cases.  Below
are two fixtures used by the harness which compiles **input.jsx** using our babel
plugin and compares the output against **expected.js**.

.. class:: label

**test/fixtures/i18n-line-feed/input.jsx**:

.. code:: 
    :number-lines:

    var a = <$_>hello,
            world!
            </$_>;
    var b = <$_>
            
            hello,
            world!</$_>;
    var c = <$_>
            {"hello, "}
            world!
            </$_>;
    var d = <$_>
    hello, world!</$_>;

.. class:: label

**test/fixtures/i18n-line-feed/expected.js**:

.. code:: javascript 
    :number-lines:

    var a = $_(null, "hello, world!");
    
    
    var b = $_(null, "hello, world!");
    
    
    
    var c = $_(null, 
    "hello, ", "world!");
    
    
    var d = $_(null, "hello, world!");

Issues
------

We also wanted to make sure that all of JavaScript was being compiled correctly
before rolling out these changes to all of our developers.  We had already 
refactored our build scripts to compile our ES6 and JSX files so that we could
extract localizable strings.

let
===
We started with manual testing.  The homepage wasn't loading.  Uh-oh.
Investigation revealed that the compiled code contained the ``let`` keyword
which most browsers don't support.  What's weird about this is that we didn't
use ``let`` in any of source code.  Where was it coming from?

In the new build script we specify a whitelist of transformers for babel to use.
This list is conservative.  We wanted to match the functionality of jstransform
and then adopt other features on an "as needed" basis.  Here's the initial list
of transformers we were using:

- es6.arrowFunctions
- es6.classes
- es6.destructuring
- es6.parameters.rest
- es6.templateLiterals
- es6.spread
- es7.objectRestSpread

After doing some hunting I found out that some of the es6 transfomers actually 
desugar ES6 to other ES6.  In this case the es6.classes transformer was 
producing code with ``let``.

.. class:: label

**source.js**:

.. code:: javascript

    class MyAwesomeClass { ... }

.. class:: label

**compiled.js**:

.. code:: javascript

    let MyAwesomeClass = function() { ... }

The fix was pretty simple, add ``es6.blockScoping`` to the whitelist.

functionName transformer shadows globals
========================================
The next issue we ran into was with a seemingly innocuous method.  Here's the 
full mixin to give some context:

.. class:: label

**set-interval-mixin.js**:

.. code:: javascript

    var SetIntervalMixin = {
        componentWillMount: function() {
            this.intervals = [];
        },
        setInterval: function setInterval(fn, ms) {
            this.intervals.push(setInterval(fn, ms));
        },
        componentWillUnmount: function() {
            this.intervals.forEach(clearInterval);
        }
    };

It adds a setInterval method to other classes and makes sure that the intervals
are cleaned up with the component unmounts.

The issue is that ``setInterval`` was being transformed to this:

.. code:: javascript

    setInterval: function setInterval(fn, ms) {
        setInterval(fn, ms);
    }

By default babel turns anonymous function expressions into named function 
expressions.  In most cases this wouldn't be an issue, but in this case the 
named function shadows the global ``setInterval``.  When the ``setInterval`` 
method is called on the object it ends up calling itself.  The second time it's
called, ``this`` is bound to ``window`` and it blows up.

This issue was fixed after I erroneously reported it as a React bug and Ben 
Alpert correctly reported it as a babel bug and Sebastian McKenzie, maintainer 
of babel, fixed it.

Summary
-------

We're looking forward to use babel so that we can leverage the power of ES6's
new features.  Babel's plugin architecture is easy and helped maintain our i18n
workflow without a lot of work.  The minor issues that did crop up were quickly
resolved.

Thanks
------

We'd like to thank babel's maintainer Sebastian McKenzie for the quick turnaround
when it came to dealing issues in babel.  Also, Ben Alpert was helpful in 
pointing out edge cases we hadn't thought about.
