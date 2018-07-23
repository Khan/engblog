title: "Using static analysis in Python, JavaScript and more to make your system safer"
published_on: July 26, 2018
author: Kevin Dangoor
team: Infrastructure
...

<img src="/images/White-Lint-711890.jpg" style="float:left; padding-right: 1em;"> "Linting" source code to look for errors is nothing new ([the original “lint” tool turned turned forty this year!](https://en.wikipedia.org/wiki/Lint_(software))), but most places I worked prior to Khan Academy didn’t use linters as extensively as we do here. So, I thought I’d share a bit about a few of our custom linters in hopes that others may invest a little time to prevent more bugs.

## For more than just formatting
JavaScript programmers will be familiar with tools like [ESLint](https://eslint.org) and Python programmers may be familiar with [pylint](https://www.pylint.org). Teams spend time arguing about what their code style is and then configure the linters to enforce that consistent style. For many folks, I’d imagine that their primary experience with linters is something along the lines of “oh, that’s the tool that complains when I put my brace in the wrong place.”

I’m a big fan of [Prettier](https://prettier.io), which has completely eliminated both formatting errors _and_ discussion of code formatting for our JavaScript code. Even with code formatting being a “solved problem”, we rely more on linters than ever. They serve the important purpose of maintaining code quality by preventing known bad patterns from sneaking in.

## Staying in sync
In our web application, we’ve got code written in JavaScript, Python, and Kotlin. One bit of complexity that naturally comes up when from having multiple languages is that sometimes you’ll need to keep files in sync. Imagine that we’ve duplicated a small bit of logic between two of the languages, or that there’s an interface shared between the two that must be changed in tandem. Sure, we do our best to minimize those case, but they can be hard to avoid entirely.

Our `code_syncing_lint.py`  linter is set up to handle this problem. It defines this comment format:

```py
# sync-start:<tag> <filename>
# sync-end:<tag>
```

`tag` is a name you give to the block of code. The linter ensures that if you make a change in one file in a given commit, there must also be a change in the block with the same `tag` name in `filename` as well.

## Frontend best practices
Khan Academy has been around for several years now and JavaScript development has changed a lot over those years. Where we used to use Handlebars and LESS files for defining our client-side views, we now use React with [Aphrodite](https://github.com/Khan/aphrodite/). At this point, if someone creates a new Handlebars or LESS file in our repository, they’re working against the direction we’re pushing for our frontend.

So, we have a linter that makes sure that no new files of those types are created. That linter comes complete with a whitelist of the files we haven’t yet managed to get rid of. As much as possible, when we introduce a new lint rule, we fix up all of the lint discovered by the rule. Rewriting a Handlebars template as React components is a non-trivial change, so this linter has a whitelist of those pre-existing files that are allowed to break the rule.

## You can lint images, too
One of our engineers, Colin Fuller, noticed that some of the images on our [team page](https://www.khanacademy.org/about/the-team) looked off. The page is a grid of photos cropped to the same sizes, but some of the photos looked stretched. During our February [Healthy Hackathon](http://engineering.khanacademy.org/posts/healthy-hackathons.htm), Colin wrote a linter that double checks that every team photo is the same size. The linter is only about 50 lines of Python, comments included.

## Avoiding tests that accidentally overwrite others
Have you ever copy/pasted an existing unit test to create a new test case for a different variation? Sometimes, all you want to do is call the function under test with different arguments, so copy/paste is the easy solution.

Imagine you have a piece of a test class that looks like this, after a copy/paste:

```py
def test_foo1(self):
    self.assertEqual(1, foo("one"))

def test_foo1(self):
    self.assertEqual(2, foo("two"))
```

It’s pretty easy to forget to change the test method name and not notice that the original test will no longer be called. We have a linter that watches for this.

## Avoiding problems with third-party libraries
Third-party libraries don’t always work the way we’d want them to. Many times, the right answer is to put up a pull request for the library. But what happens if the behavior of the library is _by design_?

We’ve got a case of that in our codebase. For example, we use [persistgraphql](https://github.com/apollographql/persistgraphql) to extract GraphQL queries from our client-side code so that we can allow only specific queries to run. The problem we ran into is that persistgraphql reformats the queries in a way that works fine for their main use case, but could make the queries not match up with what our server-side code expects. Our solution is a linter that guarantees that the query in the JavaScript code will exactly match the query expected by the server.

## You can import _this_ but you can’t import _that_
As part of our [Great Python Refactoring](https://engineering.khanacademy.org/posts/python-refactor-1.htm), we instituted new rules about which code was allowed to import which other code, to help avoid future similar tangles. We could impose restrictions via Python import hooks, but we wouldn’t find out about those problems until runtime. Our `components_lint.py` linter ensures at commit time that we aren’t breaking the rules.

Of course, the Great Python Refactoring didn’t take care of _every_ bothersome import, but the linter has a simple whitelist that we’ll whittle down as we continue to clean things up.

## Tip: Keep linters fast with regular expressions
Yes, yes, we all know [you can’t parse HTML with a regular expression](https://stackoverflow.com/a/1732454/15851). When you need to be correct 100% of the time, you need to use a proper parser. But many times a regular expression will suffice and be _much_ faster. While regular expression syntax can seem quite obscure (or become [a maintenance nightmare](https://stackoverflow.com/a/800847/15851)), regexes can actually be easier to understand than code designed to traverse a parse tree.

As an added bonus, linters like our `code_syncing_lint` mentioned earlier can work on Python, JavaScript, and Kotlin files without needing three separate parsers and a whole lot more code.

But beware! It’s easy for a regex to not properly handle legitimate, real world code files, so just keep that tradeoff in mind. Linters are like any other code, though, so you can write unit tests to verify the expected cases as we have for ours.

## Lint all the things!
Once you have the basic hooks in place to run linters automatically, you’ll doubtless find many ways in which you can prevent common sorts of bugs from creeping in to your system. [ESLint has rules](https://eslint.org/docs/rules/) to help you with frequent JavaScript mistakes, but I’d bet there are other potential pitfalls that are unique to your environment.

I hope this tour of some of our linters gives you ideas for some of your own.

_Thanks to Ben Kraft, Craig Silverstein, and Amos Latteier for their suggestions of good example linters from our code, and Scott Grant for editing advice._