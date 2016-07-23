title: Building a Really, Really Small Android App
published_on: August 22, 2016
author: Charlie Marsh
team: Mobile
...

App size is important to us.

As a team striving to deliver a free, world-class education for anyone, anywhere, it’s essential that we build an app our learners can download and keep around on-disk, no matter the quality of their data plan or device. (App size is of particular interest to us on Android given the potential for `Instant Apps <https://developer.android.com/topic/instant-apps/index.html>`_.)

For our most recent `Healthy Hackathon </posts/healthy-hackathons.htm>`_, I set off to build the smallest useful Khan Academy Android app. I set these constraints for myself:

- The app must be able to play any video in our content library (i.e., I excluded support for other content types, like practice exercises).
- The app must be polished enough to plausibly ship (i.e., it should use our color palette, include some KA branding, and so forth).
- The app should be backwards compatible to at least Android API 16, Jelly Bean (the earliest version that our existing app supports).
- **The download payload must be under 1 MB** [1].

As it turned out, this last constraint was far too conservative—the final APK clocked in at a download size of **26 kilobytes**. But before we review the numbers, let's take a look at the app itself.

A Minimally Viable Video Player
===============================

The basic flow of the app is straightforward: on each screen, you're presented with a list of topics. Tapping on a topic takes you one level deeper in the hierarchy, until you reach a playable video.

.. image:: /images/a-really-small-app/app.gif
    :alt: Navigating to a video.
    :class: align-center

.. class:: caption

    Navigating to a video (15 FPS recording).

The app is compatible back to API version 10 (Gingerbread). It also works offline, to a degree: you can navigate to a screen you’ve visited before without connectivity, even across restarts.

This whole experience clocks in at just **26 kilobytes** (20 kilobytes for pre-Lollipop devices) to download, with the APK expanding to 40 kilobytes on-disk for an L-device—far, far below my 1 MB goal, and **more than 1000 times smaller than our existing app**.

(`Here's <https://github.com/crm416/android-lite>`_ a link to the Hackathon-quality source!)

Breaking Down the APK
=====================

If our existing app is 1000 times larger than this minimally viable video player, where are we spending those extra megabytes? And what is this tiny app doing differently?

To answer these questions, I whipped out Android Studio's new `APK Analyzer <http://android-developers.blogspot.com/2016/05/android-studio-22-preview-new-ui.html>`_.

.. image:: /images/a-really-small-app/apk.png
    :alt: The output of Android Studio's APK Analyzer, when run over our minimal app
    :class: align-center

.. class:: caption

    A breakdown of the minimal video player app's APK. The estimated raw file size was a slight underestimation compared to what I measured on-disk.

In comparing this APK to that of our existing app, I bucketed app size contributions into three categories: assets (images, fonts, etc.), content, and code.

For reference, our existing Android app measures 31 MB to download and 40+ MB on-disk. (We're working hard to bring these numbers down!) The download size is roughly split between assets, content, and code as 17 MB, 10 MB, and 4 MB respectively.

For the minimal app, the :code:`classes.dex` file comprises the majority of the contribution from code, though much of the :code:`layout-*` subdirectories could also be considered 'code'; the :code:`drawable-*/` and :code:`mipmap-*` directories contain our assets; and content is nowhere to be seen.

Let's review each pillar in-turn.

Assets
------

In our existing Android app, assets (and images, in particular, which power much of our UI) make up nearly half of our download size. Worse still, since these assets (JPGs and PNGs) are already compressed, their contributions to our app’s download and on-disk sizes are roughly 1:1. Fonts are a challenge as well, since we not only package fonts for cosmetic purposes, but also to support math rendering.

The minimalist approach to assets: **Don't use any!** (Or, at least, only include essential assets, and only when necessary.) I intentionally opted for a minimal, text-based UI, which makes theming cheap and easy, since you can rely on a color palette and avoid packaging any images. Rather than using the wonderful fonts that power our existing app, I opted to mimic the system font instead (and didn't tackle math rendering in any way, given that I stuck to video content).

For the few assets that I did include, I took care to minimize their footprint in a few ways. For example, with our logo (as seen in the app bar), my goal was to package just a single version of the asset, and only for devices that would actually use it. So, to keep the contribution down, I first ran the asset through an SVG minifier and then packaged it as a single `VectorDrawable <https://developer.android.com/studio/write/vector-asset-studio.html>`_, which saved me the need to include a larger-resolution image for each density bucket, much less the font we use to render it (which would've contributed tens of KBs by itself).

I also built out a separate APK for pre-Lollipop devices to exclude the VectorDrawable asset and any other extraneous layout resources (like the custom toolbar layout).

Content Library
---------------

In our existing Android app, content (or, more accurately, our content library's metadata) makes up about 30% of our download size, though that contribution nearly triples on-disk, since these files compress quite well.

Our content library consists of tens of thousands of videos, articles, and exercises. In building out our Android app, it was important to us that learners have a snappy experience on first-run, and that they could use the app to browse through our library even while offline. For simplicity, we started off by shipping the metadata describing the structure of our content library with the APK itself, which allow for immediate navigation through the content hierarchy, regardless of connectivity status. (Unfortunately, this requires that we package a separate metadata database for each language that we support. (We're working on it!))

The minimalist approach to content: Only download the minimal metadata that you need for a given screen, as the user approaches it. To make for a snappier experience, pre-fetch content as the user moves down the topic tree, and cache liberally.

This app in particular fetches the metadata needed to render the first N child topics upon opening a new topic screen. Since each topic maps to a single HTTP request, the app can rely on a very simple URL cache to implement persistence and support offline navigation.

I also slimmed down the sheer amount of data necessary to power the UI, removing the need for certain information (like the download size for a given video or the URL at which it can be downloaded) needed in our existing Android UI. Given this minimal design, the entire topic tree could be cached on disk over time.

Code
----

In our existing Android app, code makes up a small portion of the total download size—less than 10% [2]. It is the least significant of these three pillars. In the context of a 26 KB app, though, code size becomes critical. (It's also the most interesting to optimize.)

I combined a couple different approaches to minimize code size.

First: the app has **zero dependencies**. No Retrofit, no support library, no Guava—no nothing. Instead, the codebase relies on the Android framework as much as possible, taking advantage of all the functionality that ships with Android devices. This decision impacted both the UI/UX layer and the level of abstraction at which I could operate as the engineer. For example, the app:

- Uses the system video player (:code:`VideoView` and :code:`MediaController`), rather than the nicer, more customizable, and more feature-complete :code:`ExoPlayer`.
- Implements asynchronous operations with :code:`AsyncTask`, rather than e.g., :code:`RxJava` (which we use heavily in our existing app).
- Performs all networking with :code:`HttpURLConnection` and :code:`org.json`, rather than relying on nicer libraries like :code:`OkHttp`, :code:`Retrofit`, and the like.

'Zero dependencies' also implies no Android support libraries, which has its own implications (e.g., no Fragments (if you want to support pre-Honeycomb devices), a non-uniform action bar across API versions).

(As an aside: I'd recommend that every Android engineer take a crack at building a zero-dependency app. It's a great learning experience.)

Beyond the 'no dependencies' rule, I made a few other optimizations at the end, when the APK was getting really tiny, though I tried to avoid sacrificing readability or robustness. These included:

- **Running the output APK through Facebook's bytecode optimizer**, `Redex <https://github.com/facebook/redex/>`_. This brought the download size down from 30.7 KB to 26.2 KB.
- **Removing any strings that were used merely for logging or to decorate error messages** (the justification being that these could, in theory, be reconstructed server-side). This cut another 1.4 KB.
- **Converting from enums to static integers**. I mostly did this as a joke and haven't actually analyzed the Dex dump to see how it impacted the resulting bytecode, though the download size did come down by another 1.2 KB.

All of this was on top of `Jack's <http://tools.android.com/tech-docs/jackandjill>`_ minification.

Of course, another way that I reduced code size was simply by doing *less*. Our existing app has interactive articles and exercises, adaptive streaming, offline playback, search, bookmarking, and more. And we pay for that functionality by writing and shipping more code. (In my own (early) experiments to parse our Dexfile and analyze code size contributions by package, I’ve found that our own code makes up about 27% of all instructions.)

To be able to ship a viable video player app with just an 11 KB Dexfile is pretty astounding, given that we've identified individual Swift files that contribute `over a kilobyte per line <https://twitter.com/NachoSoto/status/753365876301107200>`_ to our IPA.

Going Forward
=============

Though our existing `Android app <https://play.google.com/store/apps/details?id=org.khanacademy.android&hl=en>`_ is far larger than 26 KB, the good news is that many of the approaches that I took here were inspired by changes that we're already planning to make to that codebase.

For example, 'fetch the minimal content necessary to power a screen' is something that we're actively exploring, as is 'only package the assets that are absolutely necessary [for a given device]' (through a combination of `APK splitting <tools.android.com/tech-docs/new-build-system/user-guide/apk-splits>`_ and other optimizations).

Though we may not reduce our app size to mere kilobytes, with any luck, we'll be able to cut it down substantially using similar techniques to those explored in this post.

Interested in making slim Android apps to bring education to millions of learners globally? `Come join us <https://boards.greenhouse.io/khanacademy/jobs/15823#.V7oo55MrJE4>`_!

[1] All download sizes were taken from Android Studio 2.2's new `APK Analyzer <http://android-developers.blogspot.com/2016/05/android-studio-22-preview-new-ui.html>`_, which is still in 'Preview'. On-disk sizes were taken from the 'Total Storage' reading of the 'App Info' screen, on-device.

[2] This excludes the APK contributions that come from the JavaScript bundles that we ship with the app, which power our interactive article and exercise experiences. Those contribute to our app size in a substantial way, but the optimization story there differs significantly, and so I chose not to explore that avenue in this project.
