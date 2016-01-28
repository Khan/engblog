title: "Automating Highly Similar Translations"
published_on: February 15, 2016
author: Kevin Barabash
team: Web Frontend
...

Khan Academy is available in 12 languages and is in the process of being 
translated into many more.  We also have a lot of content (videos, articles,
exercises, etc.) that needs to be translated into all of those languages.  In 
order to help translators find the most high priority items to work on we have 
a translator dashboard.

We recently redesigned this dashboard.  The main goal of this work was to 
improve translator efficiency.  We accomplished this by ensuring that the
translation status on items was up to date and that items were organized in a
way that made sense to translators as opposed to how items were stored in the 
database.

__Old Dashboard__
![old dashboard](/images/automating-translations/old-dashboard.png)

__New Dashboard__
![new dashboard](/images/automating-translations/new-dashboard.png)

In addition to the dashboard, we also created a tool to help with doing the
translations themselves.  The tool features different views of our content that
translators can quickly switch between depending of their workflow.  It also
includes a feature called __smart translations__ which can be used to automate
some of the translation work.

Before explaining how __smart translations__ works, it's helpful to understand
the problem it's trying to solve.

On Khan Academy we have lots of exercises.  Initially we used a tool called
khan-exercises to auto generate questions (along with answers and hints).  Over
time we noticed limitations in the types of questions that could be auto 
generated.  Also, it was difficult for content creators and translators to work 
with.  It was eventually replaced with another tool, [perseus](https://github.com/khan/perseus),
which empowers content creators to create specific question variants to make 
sure a skill is fully covered instead of auto-generating random ones.

As a result we have many exercises with lots of very similar strings that need
to be translated, e.g.

    Simplify $9/12$.
    Simplify $8/6$.
    Simplify $15/3$.
    ...

## How it works

The process can be broken down into the following steps:

  1. Group English strings which differ only in places that don't contain any
  natural language text, such as formulas. "Simplify $9/12$ is grouped with
  "Simplify $8/6$" but not with "Square $3/4$".
  2. Within each group, check to see if any of the English strings are already
  translated.  If they are, create a template that can be used to translate the
  rest of the strings in that group.  If we know that "Simplify $9/12$"
  translates to "Implifysay $9/12$" then we can guess that "Simplify $8/6$" will
  translated to "Implifysay $8/6$".
  3. Update the UI to show how many strings in a group can be translated based
  on the groups that have translation templates.
  4. When a user clicks "Add smart translations" we use the translation template 
  to generate suggestions for the untranslated strings in the group.
  
Here's a quick video of what a user sees when using __smart translations__:

<video width="480" controls>
  <source src="/videos/smart-translations.mp4" type="video/mp4">
  Your browser does not support HTML5 video.
</video>

## Implementation Details

The library that implements the grouping, template creation, and translation
generation is available at [Khan/translation-assistant](https://github.com/Khan/translation-assistant).

## Grouping

To better understand the problem let's look at an example string:

    "Solve for $x$.  $x - 5 = 10$"
    
This string is made up of some natural language (NL) text and some non-natural
language (non-NL) text.  In this case `"Solve for "` and `".  "` are NL text
while `"$x$"` and `"$x - 5 = 10$"` are non-NL text.

As long as strings only differ by their non-NL text we could use the translation 
for one string as a template and then just swap out the non-NL text.  We group 
strings by replacing all non-NL text with placeholders, e.g.

    "Solve for $x$.  $x - 5 = 10$"
    "Solve for $m$.  $2m + 3 = 7$"
    "Solve for $p$.  $12 = p + 6$"

map to:

    "Solve for __MATH__.  __MATH__"

The strings with placeholders are used as keys to a dictionary where each value
is an array containing objects that can be used to access the English strings
and translated strings as they're added.

## Creating/Applying Templates

The translation template contains two things:

  - a translated string with all non-NL text replaced with placeholders
  - a mapping between where each piece of math appears in the translated string 
  and where it came from in the English string

We need this mapping because words can be re-ordered or repeated depending on 
the grammar of the target language, e.g.

    "Solve for $x$.  $x - 5 = 10$" 
    => "$x$ orfay olvesay $x$.  $x - 5 = 10$"
    
In this case the template should look like this:

    {
        tmplStr: "__MATH__ orfay olvesay __MATH__.  __MATH__",
        mapping: [0, 0, 1]
    }
    
The mapping is somewhat terse, but the index of the array represents which 
`__MATH__` placeholder in the `translated` is being mapped to which piece of
math in the English string to be translated.  In this case the first piece of
math should be repeated twice followed by the second piece once.

In order to generate a new translation, we just need to extract the bits of math
from a new English string (in the same group) and then apply the mapping to 
make sure that the math ends up in the right place.

    "Solve for $m$.  $2m + 3 = 7$"
    => maths = ["$m$", "$2m + 3 = 7$"]
    
    "__MATH__ orfay olvesay __MATH__.  __MATH__", [0, 0, 1]
    => "$m$ orfay olvesay $m$.  $2m + 3 = 7$"

## Text in Math

Some of our content contains NL text inside `\text{}` blocks that are inside 
math.  We'd like to be able to automatically translate the strings within the 
`\text{}` blocks in the following way:

    "Find *red* if $\text{red} - 5 = 10$?"
    => "Indfay *edray* fiay $\text{edray} - 5 = 10$?"

To do so we have to modify our original approach to differentiate between math 
containing `\text{red}` and math containing other `\text{}`.  Instead of 
simplify using the English string with NL-text replaced, we include a list of 
the strings from within each of the `\text{}` blocks.  The key is actually a 
stringified version of the an object that looks like this:

    {
        str: "Find *red* if __MATH__?",
        texts: ["red"]
    }

We also create a mapping between English `\text{}` strings and translated ones.
In this case that mapping would look like this:

    { "red": "edray" }

When the translation assistant is suggesting translations containing `\text{}`
blocks it must perform an extra step when replacing the `__MATH__` placeholders
in the translated string.  It must update the strings within the `\text{}`
blocks, e.g.

    // text to translate
    "Find *red* if $2 = 8 - \text{red}$?"

    // insert LaTeX into template translation
    "Indfay *edray* fiay __MATH__?"
    => "Indfay *edray* fiay $2 = 8 - \text{red}$?"
    
    // replace strings inside of \text{}
    "Indfay *edray* fiay $2 = 8 - \text{red}$?"
    => "Indfay *edray* fiay $2 = 8 - \text{edray}$?"

## Conclusion

Although the examples only contain math, our exercise strings can also contain
links to images or widgets placeholders for things like text fields, multiple 
choice answers, or interactive graphs.  __Smart translations__ handles these 
non-NL text items in much the same way.

There are some limitations with this approach.  Namely, it doesn't handle
plurals correctly.  Translators still have to proof read the translations but
it definitely takes the tedious busy work of copy/paste out of the equation.

Also, if the translator makes a mistake in the initial translation and clicks
"Add smart translations" that error will be duplicated.  Luckily, it's just as
easy to fix mistakes as it is to make them.

We received lots of positive feedback from our translations on this feature.  
Here are a couple of quotes from our translators:

- ...Smart [Translations] helps us a lot (and it is fun to see the progress). 
  I like to feel real and fast progress, and still have the control over the 
  strings.
- They save a lot of time, requiring only a quick proofreading to guarantee 
  they are correct.
