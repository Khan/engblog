title: Our Transition to React Native
published_on: July 9, 2020
author: Bryan Clark
team: Engineering
...

In 2017, Khan Academy started using React Native in our iOS and Android apps. As of this year<sup>1</sup>, we’ve reached a big milestone: our transition to React Native is complete! Every screen in the app is rendered in React Native<sup>2</sup>.

The initial experiment with React Native in 2017 was motivated by a few factors:

* **The design of iOS and Android apps  were nearly identical**, with similar interaction-design, features, and content.
* **Maintaining two codebases is challenging,** with different data designs, bugs, and coordination for developing new features. (More on this in a minute.)
* **Our mobile team is small**<sup>3</sup>, so the transition didn’t require coordinating large numbers of engineers.
* **Our website was already using React**, so we had in-house expertise with the concepts and tools to help with the transition.


Let’s talk a bit more about the challenges of maintaining two separate codebases:

* **Different bugs would appear on different platforms.** Of course this is the case with React Native, too, but it’s far less-common.
* **Implementing a new feature required coordination** of design, engineering, and testing across two platforms. That meant that you needed at least two engineers (iOS & Android), ideally available at the same time - and for a team as small as ours, that was pretty hard to do!
* **Once a feature was built, it was hard to change** because you’d have to change it on both platforms. It was hard to adjust & update designs.
* **Architectures varied a lot between the platforms.** Our iOS codebase was four years older than our Android codebase. iOS had Swift, ReactiveCocoa, Cartography, and CoreData. Android had its own set of dependencies and data-flow designs. The differences here added up - it wasn’t often straightforward to borrow a feature from the other platform, and it wasn’t easy to review the other platform’s code, so our engineers were largely siloed by platform.


# Making the transition

The transition essentially moved in three phases: Exploration, Straddling, and Extinction. (Basecamp’s  [Hill Chart](https://basecamp.com/shapeup/3.4-chapter-12#work-is-like-a-hill)  is a great metaphor for this.)

**Exploration (early 2017)** was early work to add bridges between native and Javascript code, with our very first screens in React Native, like the Search tab. Nearly all of the networking, data, business logic, and all that “client-side backend” stuff was passed over a bridge. This involved lots of boilerplate, so it was pretty tedious.

**Straddling (mid-2017 to mid-2018)** was the hardest, for sure. We had decided to use React Native, but were far from the finish line. We now had three things to think about: native iOS, native Android, and the React Native code. Engineers needed to know two (or more) paradigms to make changes, and there was lots to learn!

**Extinction (mid-2018 to mid-2020)** was my favorite part. This phase started with our “Streaming Topic Tree” project, a multi-month effort where we fully transitioned our content database (our many courses, videos, articles, and exercises) from a big bundled native database (e.g. CoreData) to a lightweight, caching library written in Javascript. Now that our client-side content database was in React Native, we didn’t need to pass nearly as much over the bridges we’d built, and could start deleting lots of native code. This year’s v7.0 release was the final push to upgrade our last native screen to React Native, while unifying the navigation design across phones and tablets.

# A mixture of native and React Native


<iframe width="560" height="315" src="https://www.youtube.com/embed/JCTvvkV9eyc" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>

**We use React Native for the “contents of a screen”, and native code for the navigation around those screens.** There are a few underlying reasons, but it’s essentially a balance of “where does the complex implementation live” vs “what makes a native app feel native”.

**The vast majority of “business logic” for our apps lives in the screen’s content** (like the contents of our Home tab’s cards, or the downloading rules for our Bookmarks tab). By comparison, the contents of a tab bar or navigation bar don’t depend much on business logic.

**However, navigation bars and navigation controllers written in React Native feel *fake* in small ways that add up.** A native navigation controller gives us the correct swipe-to-go-back gesture, as well as the correct animation timings for push/pop animations. A native navigation bar handles notched-iPhones with ease. Wrapping each screen in a native UIViewController also gives us familiar places in a screen’s lifecycle when needed. (There are libraries out there that have worked hard to mimic system-standard navigation bars; we’ve not found one that meets our needs.)

**When we started that experiment in 2017, our rule was that the app had to still “feel” native.** There are some places where it’s imperfect, for sure, but we feel confident that the compromises we’ve made have allowed us to vastly improve our apps in many other ways!

# Internationalization & localization

**There are two pieces to translations for the mobile app: content and platform strings.** Content strings come from our content management system; examples include questions in our interactive exercises, the contents and subtitles for a video, or the text in an article. (Many of these content strings are part of that “Streaming Topic Tree” I mentioned earlier.)  Platform strings are defined in our mobile apps’ codebase; examples include the text in a “Sign up” button, a tab bar item’s title, or the text shown in our Settings screen.

**We’ve got some excellent homemade infrastructure for maintaining platform strings.** You define a string in JavaScript, and we’ve built scripts that copy the string over to native iOS and Android strings. This has been quite helpful; we can easily reuse strings across native and React Native without issue, which greatly helped in that “straddling” transition period.

**From 2015-2019, our app only supported six locales, but now we’re at nineteen!** A shared iOS & Android implementation helped us get a streaming topic tree, which meant that adding additional languages wouldn’t bloat our app size. Additionally, we were able to design components in React Native that handle non-Latin characters with ease. Our mobile team is no longer the constraint on expanding our mobile apps’ reach — it’s whether we’ve got enough of our (massive) content library translated to a particular locale. This has been a huge morale boost to our international advocates; they’re really excited to have a proper mobile app for communities around the world.

# How React Native feels

*This section’s a bit more of a personal-opinion, so uh, keep that in mind! Your mileage may vary.*

**Moving to React Native hasn’t been perfectly rosy**— there have been bumps along the way, like learning a new language, a new component lifecycle, and more. The “straddling” period was particularly challenging; there was a lot of tedious boilerplate code in bridging our native and React Native code!

**On a personal level, I miss a lot about Swift** - in particular, associated-value enums, convenience initializers, named parameters, and the ease of adding functions and vars to structs and classes.

However, there have been a lot of perks to React Native!

* **React Native has felt far more malleable than UIKit**; it feels great to shape and refactor code. The code you write for a UICollectionView is different than a UITableView is different than a UIStackView, for example — but in React Native, you kinda just… don’t have to worry about it? For the most part, you can cut-and-paste code when refactoring, and it’s pretty trivial to change something from a grid to a list. (There’s a lot of overlap between this perk and many of the perks of SwiftUI.)
* **Developer tooling is excellent.** Xcode is where I came up as a developer, so I know its quirks, but my true love is now VSCode. It’s been a new vocabulary to learn, for sure — but the fact that I’ve got a VSCode plugin that autoformats my code when I hit save? Incredible! There are so many linters and auto-fixers that our code reviews really don’t involve many nitty styleguide fixes: the computer’s doing the formatting for us, and it just feels so *helpful*.
* **I’m making an Android app, and I’m barely proficient in writing Android apps!** I know enough to add an extra parameter or function, but I’m no architect on Android… yet I’m able to reach our much-larger population of Android learners and build features for them! This is well in-line with our mission and my personal values, and it has felt so nice to be able to participate here.
* **I feel more ready to participate in our web frontend.** I’m a mobile developer at heart, but now that I’m familiar with React Native, it’s not much of a stretch to help out on our webapp, and a good portion of our mobile team is already doing exactly that! It feels great to branch out and explore web development (and we’ve got web engineers contributing to our mobile codebase, too!).

# Where we are now

Our iOS and Android apps share a single codebase, with engineers specializing in features of the app, rather than platform. This means we’re way better about improving the quality of a given feature over time, and we can make incremental improvements to features, rather than feeling like we need to get everything in the initial version.

* **Shared infrastructure** made it far easier for us to transition to GraphQL, which in turn is simplifying our  [server-side transition to Go](https://engineering.khanacademy.org/posts/goliath.htm).

* **Our apps are significantly smaller.** Switching from a big bundled content-library database to a streaming one dramatically reduced our app size. Yes, this could’ve been done natively, but it was easier to implement this in a single place rather than coordinating it in two.

* **We’re a far better dance partner with our website.** During this transition, we took care to make our mobile designs resemble the information design of our website, which simplifies adding new cross-platform features like our new Mastery Challenge feature. Engineers have been able to bounce between web and mobile when they’re interested, which makes us feel closer with the organization as a whole. (If you’re a frontend engineer interested in Khan Academy, you’d be able to help build features across our mobile apps and the website!)

* **We’ve still got native code in the app,** and that’s wonderful! When needed, we can hop back to Xcode or Android Studio and implement platform-specific features, like iPad multitasking.

* **We’ve got a [robust design system](https://www.designsystems.com/about-wonder-blocks-khan-academys-design-system-and-the-story-behind-it/),**  which helps our designers and engineers quickly put together improvements to our products. For mobile, this shows up in some key ways, like having standards and prebuilt components that handle touch-highlights, accessibility, loading states, and more.

# What’s next?

**The main engineering project at Khan Academy right now is [Goliath](https://engineering.khanacademy.org/posts/goliath.htm),**  where we’re re-architecting our backend into a collection of Go services. Our unified mobile infrastructure has helped us in this transition:  even though our mobile team is a half-dozen people, we’re still able to build new features and fixes! Our apps are in a far better place to improve and expand their capabilities, localizations, quality, and performance.

**One last caveat before finishing up here:** *Fully native apps are also terrific*, and many of us still really enjoy working on them in our other projects. (Personally, my heart still belongs to Xcode, and I really enjoy thinking in Swift!) That said, our transition to React Native has been a huge boon to our team. It isn’t the One True Choice For Everyone, but it’s worked marvelously for us!

[Discuss on Hacker News](https://news.ycombinator.com/item?id=23784576)

-----

Footnotes:

1. What took us three years? We’ve got a small team, and for the most part, only transitioned screens when we were working on them.
2. Well, nearly-every screen. There’s a one-off Android language-selection screen that isn’t in React Native, and we don’t have a pressing need to migrate it to React Native, so it’s likely to stick around for a while!
3. The mobile team size has varied over the years, but we generally have about a half-dozen mobile engineers.
