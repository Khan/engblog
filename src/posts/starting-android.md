title: "Starting Android at Khan Academy"
published_on: February 29, 2016
author: Ben Komalo
team: Mobile
...

## The journey of a thousand miles...

In March, 2015—almost 1 year ago to the day—we started developing our first Android app at Khan Academy.

![first commit](/images/starting-android/first-android-commit.png)
*A single step*

By then, Android was on version 5.0 Lollipop and nearing [1 billion active monthly users](http://www.cnet.com/news/google-io-by-the-numbers-1b-android-users-900m-on-gmail/), representing around 8 out of every 10 phones worldwide. Our mission is to provide a free world-class education for anyone, anywhere, so we had to provide a great learning experience on this platform: Android reaches billions of users, many of whom rely on their phone as their only computing device.


We launched version 1.0 of our app on the [Play Store](https://play.google.com/store/apps/details?id=org.khanacademy.android) in August 2015, having learned a ton about Android development as a team. There’s plenty more ahead, but we thought now would be a good time to share a bit of our journey.

## Libraries and foundations

Ironically, being late to the Android game came with its advantages. The platform had evolved significantly by early 2015, and we were able to target API level 16 and higher while still reaching 95% of users. Furthermore, the [Support Library](http://developer.android.com/tools/support-library/index.html) had provided fantastic new utilities like the `RecyclerView` and `CoordinatorLayout`, making modern Android “Material UI” significantly easier to build. The vibrant open-source community had also gifted us with plenty of useful libraries like [Retrofit](http://square.github.io/retrofit/) and [Picasso](http://square.github.io/picasso/), which we weren’t shy about adopting.

Of course, good utility libraries are not enough: we knew we needed strong foundations throughout our code. We enforced separation of concerns right off the bat with two separate modules in our app: an Android-agnostic “core” module, and an “app” module for Android-specific application code:

Our core module deals with tasks like fetching data, storing data, and transforming that data, while our app module reads that data, shows it to the user, and writes changes. Besides keeping our code clearer and more organized, this separation delivered a variety of secondary benefits. For instance, we can run our core module on a vanilla JVM without any Android runtime libraries or special mocking, making tests easier to write and also significantly faster to run – fast enough that we can run them as a pre-commit check before sending out a change revision:

![test run](/images/starting-android/core-tests.png)
*1290 tests in ~3s ⚡️*

Those core tests can run on our CI server without having to deal with emulators, which have proven to be difficult to maintain. This has made us more confident in our tests, instilled a test-heavy culture in our development team, and allowed us to run more extensive end-to-end tests pretty easily. For example, one test tries to download and process our content library; we run this continuously to warn the content and server teams in case they accidentally change an API in a backwards-incompatible way.

Modules add some complexity to the build setup, but the relatively small cost has been well worth paying. We’ve since added a few more small modules, though the broader separation of “core” from “app” delivered the most benefit. In the future, as we consider cross-platform code sharing solutions, we may adapt the core module to be shared across our iOS and Android apps (more on that below).

## Tools

In addition to having solid architectural foundations, we wanted to make the surrounding developer experience great. We had invested in [various](http://engineering.khanacademy.org/posts/tota11y.htm) [kinds](http://engineering.khanacademy.org/posts/i18nize-templates.htm) [of tools](http://engineering.khanacademy.org/posts/i18n-babel-plugin.htm) for our web app infrastructure, and we wanted to sharpen our tools on Android too.

We’re still far from the ideal scenario: deploying and testing UI changes end-to-end still takes too long. But tools like [Facebook’s Stetho](http://facebook.github.io/stetho/) provide a great debugging experience that can save lots of time once the app is on a device. All our network requests use [OkHttp](https://github.com/square/okhttp), and [with the right configuration](http://facebook.github.io/stetho/#integrations), Stetho can inspect them.

We’ve also created a custom `DumperPlugin`, which runs arbitrary commands in our app via the command line. Here we force our app to sync new content from the server:

```
$ dumpapp ka-debug update-topic-tree
Kicked off service to update topic tree
```

For automating releases, we use [Triple-T’s Gradle plugin](https://github.com/Triple-T/gradle-play-publisher) to upload APKs to the Play Store. Our CI server publishes a new build from `master` every night to our alpha channel (internal employees). We use Git tags to track the version code; each build increments the number and makes a new tag (though we bump the marketing-oriented “version name” manually).

We’re still building out lots of tooling to make things easier, including our still-nascent linting tools. If you’ve got favorites to share, we’d love to chat.

## Many miles ahead

Our team has learned a lot in the last year. Not only have we come a long way in building out our technical capabilities, but our fantastic design team has also adapted to thinking about new features in a holistic fashion; all three platforms (web, iOS and Android) are considered up front and designs are typically done simultaneously so the learning experience can make sense regardless of how you access it.

That being said, we’re still a fairly small team, and re-building a feature three times is costly. We’re actively exploring possibilities for [mobile code sharing strategies](https://docs.google.com/document/d/1zEBxHsbXaKlvzwYxzoElkF8K8rZ0vaXmiWoLUtsd0Tg/edit#), but have yet to find a satisfactory solution. There’s also much to learn as a broader team about coordinating work across three platforms. Should we build features on one platform before starting work on the rest, for validation’s sake? How should we best enable our content creators to make compelling experiences that are flexible and can adapt to the learner’s device?

Despite the challenges ahead, we’re excited to be building on Android. More importantly, we’re excited about the possibility of reaching vast numbers of learners through the platform. There’s a lot more we’re working on, like bringing the interactive exercises and other features learners have enjoyed on our website and in our iOS app to Android. We’re also thinking about ways to deliver our content in extremely limited connectivity environments, and other situations which can benefit from a native Android app. Excited about empowering learners using mobile technology? [Come join us](https://www.khanacademy.org/careers).
