title: "Copy-pasting more than just text"
published_on: August 31, 2015
author: Sam Lau
team: Web Frontend
...

## The Result
I'll skip to the happy ending. This little feature implements more sophisticated
copy-pasting for the interactive widgets we use for our exercises and articles,
making life for our content creators easier. See it in action:

![copypastehooray](https://samlaucodes.files.wordpress.com/2015/07/copypasta.gif?w=1000)

Notice that the copied content is just text, but when it's pasted the metadata
associated with the text is copied over properly. For example, the image URL is
copied over properly and the number line's starting value is still 3 after being
copied and pasted back and forth between the two text boxes.

## First, About Perseus
Our exercises are created using [Perseus][perseus], a question editor and
renderer that makes it simple to create interactive problems. Before we had
Perseus, we had a framework called [Khan Exercises][khan-exercises]. However,
to write exercise content, content writers essentially had to know how to
program. As you can imagine, this made scaling up work on content difficult.

Perseus, which is what you see in that animation above, allows for easier
interactive content creation through widgets. For example, the animation above
features an image and a number line widget. [This live exercise][exercise]
features a transformer widget.

[perseus]: https://github.com/Khan/perseus#perseus
[khan-exercises]: https://github.com/Khan/khan-exercises#khan-academy-exercises
[exercise]: https://www.khanacademy.org/math/geometry/transformations/hs-geo-rotations/e/defining-rotations

## The Problem
Before, copy-pasting worked like this:

![copypastesad](https://samlaucodes.files.wordpress.com/2015/07/nocopypasta.gif?w=1000)
*Those are sad faces, if you couldn't tell.*

Perseus is becoming more and more useful to us. In fact, during my internship my
mentor and I worked on functionality to use Perseus to write our articles.
It quickly became clear that we'd have to put our rush to implement features on
hold in order to iron out some annoying issues with the editor. One of
these issues was the fact that if content creators wanted to move or duplicate
a widget, they'd have to make a new widget and manually input all the
settings they wanted.

In the case of the image above, they would have to copy over the image URL as
well as other metadata, like the caption and the alt text. We thought that it'd
be great if copy-pasting worked transparently for our content creators.

## The Approach
There are essentially two components that I want to remember when a content
creator cuts or copies a piece of text. First, is the copied text itself. This
usually looks something like:

    Hello, this is some text and here's an image widget.

    [[☃ image 1]]

The `[[☃ image 1]]` is a placeholder that tells Perseus that there is an
image widget there. Then, there is the metadata associated with the widget
itself, such as the image URL. This metadata is stored in a Javascript object as
a React prop in Perseus, which means that if we can move that metadata around
properly along with the basic text we'll have what we want. For example, the
metadata for an image widget can look something like:

    "image 1": {
        "type": "image",
        "alignment": "block",
        "graded": true,
        "options": {
            <some more metadata>,
            "backgroundImage": {
                "url": "doge.gif",
                "width": 537,
                "height": 529
            },
            "labels": [],
            "alt": "",
            "caption": "I am a doge."
        },
    }

How can we allow regular copy-pasting of plain text to work correctly as well as
handle the case where there are widgets to move around?

## localStorage to the Rescue
Our solution was to listen for cut, copy, and paste events. On a cut / copy, we
look through the text for widgets. We grab the associated metadata of each
widget we find and save 'em in `localStorage`. On a paste, we see if
`localStorage` has some metadata that we've previously cut / copied. If so, then
pull it in.

[You can find the basic implementation in this commit][commit1]. It
ended up being just a few lines of Javascript and I was very pleased with how it
worked. One nice bonus from using `localStorage` was that widgets could be
copied over from different web pages entirely. For example, if a content creator
wants to move widgets from one question to another, he/she can copy the widgets
in one question's editor, browse to the page with the other question's editor,
and paste the widgets in.

[commit1]: https://github.com/Khan/perseus/commit/e693b679fd799845da47ed8d6d5b04c6e2e4a0b2

## But Wait...
That commit above gave content creators some basic functionality that saved many
frustrating minutes re-entering in widget settings. However, there were a number
of issues and edge cases that remained. Can you think of some after looking at
that commit?

Here are the ones that were most immediately obvious after we deployed this
feature:

1. Name conflicts. Ex. pasting an `[[☃ image 1]]` in a text box that already
contained an `[[☃ image 1]]`. In the commit I linked above, I simply ignore the
pasted widget in the case of a name conflict.
2. `localStorage` data isn't cleared after a paste. The original reason for this
was that we could conceivably want to paste the same widget in multiple places.
However, this means that we could potentially have weird behavior if we paste a
widget, then copy text from another website, then paste that text in. Since we
still have the metadata in `localStorage`, we'll try to move that data into the
exercise / article.
3. Suppose we 1. copy some text that contains widgets in Perseus, 2. decide
to go to another web page and copy some text from there, and 3. paste that text
instead of the original text with widgets. Since step 1 moves metadata into
`localStorage` and when we paste we simply look for the presence of that data,
we'll erroneously pull that metadata in even though the text we're
actually pasting wasn't originally from Perseus.

## Making Copy-Paste Do More Things Properly
I resolved the above issues as follows:

1. Instead of totally ignoring the pasted widget in the event of a name
conflict, I rename the widgets safely. For example, if the section already
contains a widget called `[[☃ image 2]]` and I want to paste in widgets
`[[☃ image 1]]` and `[[☃ image 2]]`, we'll rename the first widget to
`[[☃ image 3]]` and the second to`[[☃ image 4]]`. That is, we'll look at the
highest-numbered widget already in the section of the same type and make sure
all of the widgets we're about to paste in are numbered higher than that one.
2. I clear `localStorage` after a paste. This saves headache since content
creators don't really need to paste the same widget everywhere anyway.
3. In addition to saving the metadata in `localStorage`, I also save the copied
plaintext itself. On a paste, I check the text that's about to be pasted and
only move widget metadata in if the plaintext matches the one previously copied
from Perseus. This is a bit strict but ensures that only text from Perseus will
trigger widget metadata pasting.

[These changes are implemented in this follow-up commit.][commit2]

[commit2]: https://github.com/Khan/perseus/commit/4d122c7db1c8938d1e6debb48dade1cb180c1190

There are almost certainly definitely more weird edge cases but these covered
the majority of use cases for content creators. Shipping beats perfection, after
all. Our content creators have been loving this feature, and it's always a fun
one to show others.

[If you'd like to try it out for yourself go ahead and check out the Perseus
demo!](http://khan.github.io/perseus)

PS: I had an amazing time during my Khan Academy internship. If you're
interested in working with brilliant people who care about each other and the
future of education please check 'em out! I'd love to personally answer any
questions you have and you can find me on [Github](https://github.com/samlau95).
