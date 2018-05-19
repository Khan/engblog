title: "What's New in OSS at Khan Academy"
published_on: April 3, 2017
author: Brian Genisio
team: Web Frontend
...

At Khan Academy, we rely heavily on Open Source Software (OSS).  The majority of our software is built upon OSS and we love giving back to the community when we find nuggets of code we think other will find useful.

If you're ever curious to see what we're up to with OSS, take a look at [https://khan.github.io](https://khan.github.io).  Some of the most recent additions to that page are highlighted below.

## Mu Lambda
[Mu Lambda](https://github.com/khan/mu-lambda) is a small library of functional programming utilities for JavaScript.  Our front-end codebase is using more and more functional concepts lately and we need some help composing our functions via utilities.  Unfortunately, most of the great OSS options out there today are rather heavy-weight from a payload perspective.  Mu Lambda is 1/10th the size of the popular options out there!  One caveat: it doesn't have monad support (which is partially how we reduce the payload size.)  If you want to see it in action, check out the [tests](https://github.com/Khan/mu-lambda/blob/master/test/test.js).

## React Balance text
[React Balance Text](https://github.com/khan/react-balance-text) is a React wrapper for the Adobe Web Platform's [Balance-Text](https://github.com/adobe-webplatform/balance-text) project which aims to help eliminate [text rags and widows](https://www.fonts.com/content/learning/fontology/level-2/text-typography/rags-widows-orphans) in page copy by making sure the text is as "balanced" as possible across all lines.

Before we built our wrapper, we contributed to their project to help remove the jQuery dependancy.  It didn't seem prudent to have a React component which relied on jQuery.  In today's browser ecosystem, a component like Balance-Text no longer needs anything that jQuery can offer.  We collaborated with Adobe to create version 3.0 of Balance-Text and then wrote a simple wrapper around it for React.

The usage is simple and clean:

```
<BalanceText style={containerTextStyle}>
    Dispassionate extraterrestrial observer another world, as a patch of light! Extraplanetary! Colonies great turbulent clouds Orion's sword. Venture, circumnavigated vastness is bearable only through love? Tendrils of gossamer clouds quasar cosmos a still more glorious dawn awaits quasar decipherment Drake Equation citizens of distant epochs cosmic ocean consciousness, are creatures of the cosmos not a sunrise but a galaxyrise galaxies, colonies vastness is bearable only through love as a patch of light shores of the cosmic ocean and billions upon billions upon billions upon billions upon billions upon billions upon billions.
</BalanceText>
```

See the [project's storybook](https://khan.github.io/react-balance-text/) for more details and use cases.

## Fuzzy Match Utils
[Fuzzy Match Utils](https://github.com/Khan/fuzzy-match-utils) is a collection of string matching algorithms designed with [React Select](https://github.com/JedWatson/react-select) in mind.  Internally, it uses the [Levenshtein distance](https://en.wikipedia.org/wiki/Levenshtein_distance) and [longest common subsequence](https://en.wikipedia.org/wiki/Longest_common_subsequence_problem) algorithms which employs [dyanamic prorogramming](https://en.wikipedia.org/wiki/Dynamic_programming) to measure the difference between two string sequences.  Instead of matching strings literally, it uses a "fuzzy" approach.  For example, if you searched for "Bay High", it will do well to find "Bayside High School" in a list of schools.  We use these utilities in some of our React Select implementations to help the user filter long lists of options more effectively.

## React Multi-Select
Speaking of React Select, [React Multi Select](https://github.com/Khan/react-multi-select) is a multiple select component for React (which also uses Fuzzy Match Utils), modeled after the React Select look and feel. React Select is awesome, and we use it a lot, but the way it handles multiple options didn't jive with some new user experiences we are working on.  React Select uses a tagging approach where we preferred a dropdown of checkboxes.  

We wrote React Multi Select to have the same look and feel as React Select, but with a different UX when the user selects the dropdown, specifically designed for the multiple selection use case.  We used the [React Component Development Kit](https://github.com/storybooks/react-cdk) which uses [React Storybook](https://github.com/storybooks/react-storybook) to help us show use cases.  Because of this, you can demo the component in the [project's storybook](https://khan.github.io/react-multi-select/)

![animation of react-multi-select](/images/new-oss-activity/react-multi-select.gif)

## Keeping everything else alive
In addition to these new projects, we've been keeping our other OSS projects updated as well.  For example, we've landed several performance-related updates to [Aphrodite](https://github.com/Khan/aphrodite) thanks to public contributor [Joe Lencioni](https://github.com/lencioni).  In [KaTeX](https://github.com/Khan/KaTeX), we've also incorporated several pull requests from the community.  Check out our [OSS page](http://khan.github.io) for more projects.
