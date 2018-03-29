title: "Slicker: A Tool for Moving Things in Python"
published_on: April 2, 2018
author: Ben Kraft
team: Infrastructure
...

Craig talked [last post](/posts/python-refactor-1.htm) about our project to reorganize our whole Python codebase.  This entails a lot of architectural challenges – deciding where to put each file, prioritizing which files and classes to split, and so on – which Carter will talk about more in the final post of this series.  Today, I want to set all that aside to focus on the more mechanical process of moving: what does it take to move thousands of files, classes, and functions, each of which may be referenced by dozens or hundreds of others?  We ended up writing a tool called [Slicker](https://github.com/Khan/slicker) to do it all, and the remainder of this post talks about why we needed it and how it works.

## The Problem

To understand what we need to do, let's start out with a simple application for creating and viewing articles like those on [Khan Academy](https://www.khanacademy.org/humanities/us-history/road-to-revolution/creating-a-nation/a/the-federalist-papers).[^codebase]
```python
# models.py
from google.appengine.ext import ndb  # the ORM we use

class Article(ndb.Model):
    author = ndb.StringProperty()

def get_article_by_id(article_id):
    return Article.get(...)
```
```python
# views.py
import current_user
import models

def display_article(id):
    a = models.get_article_by_id(id)
    # build some HTML based on `a`

def create_article(...):
    return models.Article(author=current_user.get(), ...)
```

Maybe we're about to add a bunch of other types of content – [videos](https://www.khanacademy.org/math/basic-geo/basic-geometry-shapes/basic-geo-properties-shapes/v/sides-corners), [projects](https://www.khanacademy.org/computing/computer-programming/programming/arrays/p/project-make-it-rain), and so on – so we want to move `models.py` to `content/article.py`.  The move itself is easy in this case: no changes to the file are necessary so we just move it.  Over in `views.py`, we need some changes: we need to replace all those calls to `models.*` with `articles.*`, and correspondingly `import models` with `from content import articles`.  Then, to keep our imports nice and sorted, we need to move that changed import up a line.
```diff
 # views.py
+from content import article
 import current_user
-import models
 
 def display_article(id):
-    a = models.get_article_by_id(id)
+    a = article.get_article_by_id(id)
     # build some HTML based on `a`
 
 def create_article(...):
-    return models.Article(author=current_user.get(), ...)
+    return article.Article(author=current_user.get(), ...)
```

This diff is easy to write manually, but we wanted to do this for thousands of files.  How?

We started by looking at existing tools.  [PyCharm](https://www.jetbrains.com/pycharm/)'s refactoring tools are indeed pretty powerful, but they didn't work out for us for several reasons.  First, PyCharm doesn't do a perfect job of fixing up all the right references.  For example, when I tried the above move with PyCharm, it successfully moved the definitions of `Article` and `get_article_by_id` to `content/article.py`, but it didn't move the import of `ndb` – it just deleted it.  I'm sure we could work around that particular bug, but it wasn't the only one.[^bug]  Second, PyCharm didn't know about our [style guide](https://github.com/Khan/style-guides/blob/master/style/python.md#imports) so we had to further modify most of the imports it added.  You might think that would be a quick process, but if PyCharm writes `from content.article import Article` everywhere (such that the code uses `Article` unqualified), and we want to change it to use `from content import article` and reference `article.Article`, that's almost as much work as the original move!  Finally, PyCharm's refactoring tools can only be used through their IDE interface and are somewhat slow; it was very convenient to be able to `git reset` and rerun a set of Slicker commands and quickly if we decided to do things a little differently halfway through.

[Rope](https://github.com/python-rope/rope), which aims to do something similar but as a plugin for other editors, is more scriptable but otherwise had similar problems.  And, surprisingly, that's about it: there aren't too many more options out there suited to this sort of use case.[^other]  In comparison to some languages, the Python community doesn't seem to have the same quantity and quality of automated code-rewriting tools.

[^codebase]: All these examples are modified from patterns that exist in our real codebase, although they are of course simplified.

[^bug]: I think in this case PyCharm gets confused because `ndb` isn't on my `PYTHONPATH`.  (It gets injected elsewhere in our code; some manual configuration could point PyCharm in the right direction.)  In another simple case I tried, when moving a function to its own file, PyCharm copied an import to the new file, despite the fact that it wasn't used in the moved function.  I suspect this has to do with inadequate handling of the first edge case I discuss below.

[^other]: If you know of others, I'd love to [hear about them](https://twitter.com/bnkrft)!

## The Old Way

Left to our own devices, we started off using handwritten Perl and sed scripts, modified for each commit we operated on.  For example, in this case, we could have done:
```sh
git grep -E -l 'models\.(Article|get_article_by_id)' \
    | xargs sed -i 's/models\.(Article|get_article_by_id)/article.\1/g'
```

This doesn't fix up imports – luckily we already had a [tool](https://github.com/Khan/fix-includes) to do some of the work; a few shell "one-liners" would parse our linter's output and pass it to `fix-includes` which would make the requisite changes.  And this was a simple case: we were moving the entire file, there was no other file in the codebase with a similar name, the imports we needed to fix all had the same syntax, with no `from` or `as`, and they were all at the top of the file, never inside a function.  Each of those complications would have required another few scripts, or a bunch of manual fixes.

Nothing beats the flexibility of tools like sed for a one-off change, but for similar operations on thousands of files, this strategy isn't sustainable.  So I started hacking together a script that would do some of the job for us.  After a few Friday afternoons, I was using it for all the moves I was doing, with some success.  Once it became clear this could make our task much easier, [Slicker](https://github.com/Khan/slicker) graduated from a quick hack to a more serious tool, focused on one thing: moving things around in Python codebases.

## Slicker

Slicker follows a similar approach, but is much more precise.  It starts by parsing each file's imports, checking whether any of them match the thing we want to move.  If they do, it searches the entire file for references that use those imports, and if so, updates both import and reference accordingly.  It does all of this, across your whole codebase, in a few seconds in most cases.

Here's a more complicated case: let's say we've got a bunch of other ways of getting articles, too, and we want to move those to a separate `article_getters.py`.  We ask Slicker to move `content.article.get_article_by_id` to `content.article_getters`.  Now, what does it need to do?  It deletes the definition from `content/article.py` – easy enough – and adds it to `article_getters.py`:
```python
# content/article_getters.py
def get_article_by_id(article_id):
    return Article.get(...)
```
You may notice a problem here: a `NameError: name 'Article' is not defined`!  We have to add a new import at the top of the new file (e.g. `from content import article`[^from]) and then replace `Article` with `article.Article`:
```python
# content/article_getters.py
from content import article

def get_article_by_id(article_id):
    return article.Article.get(...)
```
In other cases, we might have had to update references to `get_article_by_id` elsewhere in `article.py`, adding an import similarly.  Now, with the function itself moved, we need to clean up the references.  This time, since the `from content import article` is still used by `create_article`, we don't remove it; we add `from content import article_getters` by its side.
```diff
 # views.py
 from content import article
+from content import article_getters
 import current_user
 
 def display_article(id):
-    a = article.get_article_by_id(id)
+    a = article_getters.get_article_by_id(id)
     # build some HTML based on `a`
 
 def create_article(...):
     return article.Article(author=current_user.get(), ...)
```
Slicker encapsulates all of this work in a simple tool so you don't have to think about it.[^workflow]

[^from]: By default, Slicker tries to match the style of the import it is replacing – `import a.b.c` vs. `from a.b import c` vs. `from . import c` – but it also has options to prefer one style whenever possible, as we've used in this case.  At present, it always imports whole modules (`from content import article`, not `from content.article import Article`) to follow Khan Academy's [import style](https://github.com/Khan/style-guides/blob/master/style/python.md#imports), although we [would like](https://github.com/Khan/slicker/issues/22) to add more flexibility there.

[^workflow]: Combining this with the tools [Craig mentioned](/posts/python-refactor-1.htm), our full workflow has a few more steps.  First, we run Slicker to do the move, followed by the pickle-logger generator.  Then, run linters and tests and fix issues they uncover, which generally include a bunch of long or misindented lines, and hopefully not too much else.  (If you use an autoformatter, it could probably do most of this part.)  Next, we send the code out for review.  Finally, after code review, we merge from master again, run lint and tests again, and then deploy.

## Fun Edge Cases

Ahh, edge cases.  Python is nice, for our purposes, in that it has a fairly simple syntax so we don't have to look for many different ways of referring to functions.  But it's still got plenty of fun edge cases.  Some of these, Slicker handles; some, it does something that's good enough; some it ignores or warns the user.

Here's a fun one: if we have two files `content/article.py` and `content/exercise.py`, the following is legal Python:
```python
import content.article

content.exercise.get_exercise_by_name('addition-1')
```
Or rather, it's legal python as long as `content/article.py` or some other file that has already been run imports `content/exercise.py`.  Once `content.exercise` is loaded, everybody who imported anything from `content` has access to it.  Making use of this isn't a great pattern – one generally doesn't write code like the above intentionally – but Pyflakes [doesn't notice](https://github.com/PyCQA/pyflakes/issues/137), and after a while these sorts of things build up.  (We discovered them after a few moves; in many cases things will work just fine until you try to remove `content/article.py` entirely, at which point the import will fail.)

Slicker needs a lot of code dedicated to handling this case.  In particular, when we [look](https://github.com/Khan/slicker/blob/master/slicker/model.py#L207) for which imports in the file could possibly have brought in the symbol you moved, we have to include any import of a module from the same package.  We then look for code referencing those imports similar to how we would for a normal import.

Another fun case is code like this, common in tests:
```python
import mock

from content import article

@mock.patch('content.article.get_article_by_id')
def do_test(mock_get_article):
    a = article.get_article_by_id(...)
    ...
```
If we move `get_article_by_id`, we need to update the argument to `mock.patch`.  We knew about this issue from our very first moves, but for a while, we didn't even try to fix it – string literals are used in many contexts and it's hard to know when we should change any given piece of text.  But it turns out we can do pretty well: we [look](https://github.com/Khan/slicker/blob/master/slicker/replacement.py#L24) for string literals matching the fully-qualified name (`content.article.get_article_by_id`), the name as imported in this file (`article.get_article_by_id`) or the filename (`content/article.py`), looking carefully at what comes before and after to avoid false positives.  Furthermore, if the module is toplevel (e.g. `views.py`), we only look for its name as an entire string, so that we won't try to update the string `'Someone views the page'`, but will still update `mock.patch('views')`.  This isn't perfect, but it's pretty close, and it's a common enough pattern in our codebase to be worth doing.  Of course, we'll miss code that does `mock.mock('content.article.get_article_by_%s' % 'id')`, but that's super rare in comparison.  These fixes include docstrings; we also fix up [comments](https://github.com/Khan/slicker/blob/master/slicker/replacement.py#L241) in a similar fashion.

For another case where we do something imperfect but close enough, suppose you have:
```
from content import article

def get_article(name):
    return article.get_by_name(name)  # `article` is an imported module

def render_article(name):
    article = get_article(name)
    return article.render()  # `article` is a local variable
```
Knowing whether `article` refers to the module (as in the first case) or a variable (as in the second) requires very careful tracing of variable scopes, which we [haven't yet implemented](https://github.com/Khan/slicker/issues/19).  We just do the best we can, and often, it's good enough.  Sometimes we change our code to avoid this pattern entirely; it's confusing for humans too.[^avoid]

Lastly, some edge cases are clearly impossible to handle.  For example, if you do:
```python
from content import article
from content import exercise

def get_anything_by_id(content_type, content_id):
    if content_type == 'article':
        content_module = article
    else:  # content_type == 'exercise'
        content_module = exercise
    return content_module.get_by_id(content_id)
```
If we want to change the name of `article.get_by_id()`, but not `exercise.get_by_id()`, we actually have to do some refactoring here.  (In this case, we'd likely just do `article.get_by_id(content_id)` in the `if`, and similarly in the else, which is clearer anyway.  Then Slicker could do its work.)  Such a refactor isn't hard, but it's far too complex to do automatically.  For these, we don't try; where we can, we warn the user.  They're luckily rare in real code, although not unheard of.

[^avoid]: Exactly what we do is beyond the scope of this blog post, but we've developed a few patterns.  When possible, we try to choose module names that are less likely to cause conflicts.  For example, we often use the plural name when it makes sense; `users` is a much less common variable name than `user`, in our codebase at least, so it's less likely to conflict.  On the other hand, sometimes it's best to just do the more explicit import; in the above sample `import content.article` avoids this problem.  (In fact, we can ask Slicker to write all the imports it changes that way, with `-a NONE`.)

## Some Parting Thoughts

Python is a pretty interesting language to work with for this sort of thing.  For one, despite being a fairly mature language generally, and having good tooling support in most respects, automated refactoring remains underexplored.  JavaScript, for example, has [much](https://github.com/facebook/jscodeshift) [more](https://prettier.io/) [work](https://github.com/benjamn/recast) [in](http://www.graspjs.com/) [this](https://github.com/substack/node-falafel/) [area](https://github.com/cpojer/js-codemod), perhaps because the language is changing faster so tools are more necessary to keep up.

As for the language itself, on the one hand, ["explicit is better than implicit" and "simple is better than complex"](https://www.python.org/dev/peps/pep-0020/#id3) help us out a lot: doing `from ... import *` is thankfully rare enough to not worry about[^star], as opposed to some languages where it's the default.  (Things like `__import__(a_dynamic_string)` that are nearly impossible to handle are even rarer.)  Dynamic typing is less of a problem than one might think; it means we can't rename methods, but for toplevel functions it's not a big deal.  (Of course, you do lose the safety net of a type-checker, and must depend only on unit tests.)

Most of the difficulties are around the tooling we build upon.  The lack of standardized autoformatting does make code generation harder; we have to worry about where we add whitespace, rather than just doing an AST transform and letting [Prettier](https://prettier.io/) handle the rest.  Meanwhile, Python's `ast` and `tokenize` modules are helpful but they also leave a lot to be desired.  (For example they don't tell you which AST node corresponds to which token(s); luckily [someone else](https://github.com/gristlabs/asttokens) already solved that problem for us.)  So we end up having to do more work than we otherwise might.

Structuring Slicker's code to separate concerns and keep things understandable has also been an interesting challenge.  For example, we might like to separate updating references within a file from updating imports.  But it turns out deciding what import to add is intimately tied up with the changes we make later in the file, and we can't think about one without the other.  Similarly, in theory, our layer for doing the actual on-disk file editing ([`khodemod.py`](https://github.com/Khan/slicker/blob/master/slicker/khodemod.py)) shouldn't be Python-specific, but even reading a file in [requires](https://github.com/Khan/slicker/blob/master/slicker/khodemod.py#L187) looking for the [magic `coding: utf-8` comment](https://www.python.org/dev/peps/pep-0263/), defaulting to ASCII for Python 2 and [UTF-8](https://www.python.org/dev/peps/pep-3120/) for Python 3.  Keeping all of this straight in our heads and in code took a lot of refactoring, and it's still not as clean as we'd like.

So that's Slicker.  If you want to know even more of the gory details, or if you think hacking on this sort of things sounds like fun, check it out on [GitHub](https://github.com/Khan/slicker)!  We're also [hiring](https://www.khanacademy.org/careers), if you want to get paid to work on interesting problems like these in support of a free, world-class education for anyone, anywhere.  Otherwise, tune in next week for more on the benefits of reorganizing our codebase with Slicker.  Go forth and refactor!

*Thanks to Carter Bastian, Jacob Hurwitz, Daniel Jackoway, Sarah Lim, and Craig Silverstein for comments on a draft of this post.*

[^star]: It would be possible to handle this case, it's just more work (to correctly enumerate the imported names) and hasn't been worth it.
