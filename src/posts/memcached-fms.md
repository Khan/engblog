title: Memcached-Backed Content Infrastructure
published_on: May 15, 2017
author: Ben Kraft
team: Infrastructure
...

Last post, I [wrote](/posts/memcached-profiling.htm) about how we did profiling on [App Engine's Memcached](https://cloud.google.com/appengine/docs/python/memcache/) service to plan our new content-serving infrastructure that will allow us to scale our new content tools to many more languages.  But that was all talk, and at Khan Academy we're all about having a [bias towards action](http://engineering.khanacademy.org/posts/engineering-principles.htm).  So let's talk about how we tested the new backend, rolled it out to users, and the issues we ran into along the way!

## Recap: Content serving, the old way

[Tom](http://www.arguingwithalgorithms.com/posts/14-01-03-content-store) and [Willow](/posts/evolving-our-content-infrastructure.htm) have written about our content infrastructure in the past, but as a quick recap, we have a custom content versioning system that allows content creators to edit the content and then later publish it to the site.  The end goal of that publish process is to build a new version of our content data, which includes a specific version of each item of content (such as a video, exercise, or topic) at Khan Academy.  In most cases, these are stored as a pickled python object with the metadata for a particular piece of content &ndash; the actual video data is served by YouTube.  The goal of our content serving system is to get all that data out to any frontend servers that need it to display data about that content to users, and then atomically update all of that data when a new version is published.  The frontend servers can then use this content data to find the URL of a video, the prerequisites of an exercise, or all the articles within a topic.

In principle, this is a pretty simple problem &ndash; all we need is a key-value store, mapping `(global content version, content ID)` pairs to pickled content item objects.  Then we tell all the frontend servers which content version to look for (an interesting problem in and of itself, but outside the scope of this post), and they can fetch whatever data they need.  But that doesn't make for very good performance, even if our key-value store is pretty fast.  Even after we cache certain global data, many times we need to look at hundreds of items to render a single request.  For instance, to display a [subject page](https://www.khanacademy.org/math/algebra-home) we might have to load various subtopics, individual videos and articles in the subject, exercises reinforcing those concepts, as well as their prerequisites in case students are struggling.

In our old system, we solved this problem by simply bundling up all the content data for the entire site, compressing it, loading the entire blob on each server at startup, and then loading a diff from the old version any time the content version changed.  This gave us very fast access to any item at any time.  But it took a lot of memory &ndash; and even more so as we started to version content separately for separate languages, and thus might have to keep multiple such blobs around, limiting how many languages we could version in this way.  (Between the constraints of App Engine, and the total size of data we wanted to eventually scale to, simply adding more memory wasn't a feasible solution.)  So it was time for a new system.

## Content serving, the new way

After discussing a few options, our new plan was fairly simple: store each content item separately in memcache, and fetch it in on-demand, caching some set of frequently used items in memory.  We [simulated](/posts/memcached-profiling.htm) several caching strategies and determined that choosing a fixed set of items to cache would be a good approach, with some optimizations.

We went ahead and implemented the core of the system, including the in-memory cache, and the logging to choose which items to cache.  In order to avoid spurious reloads, we stored each item by a hash of its data; then each server would, after each content update, load the mapping of item IDs to hashes, in order to find the correct version of each item.  We also implemented a switch to allow us to turn the new backend on and off easily, for later testing.

## Testing & Iterating

But things were still pretty darn slow.  It turned out we had a lot of code that made the assumption that content access was instant.  Everywhere we did something of the form
```py
for key in content_keys:
    item = get_by_key(key)
    # do something with item
```
was a potential performance issue &ndash; one memcache fetch is pretty fast, but doing dozens or hundreds sequentially adds up.  Rather than trying to find all such pieces of code, we set up a benchmark: we'd deploy both the old and the new code to separate clusters of test servers, and run some scripts to hit a bunch of common URLs on each version.  By comparing the numbers, we were able to see which routes were slower, and even run a profiler on both versions and compare the output to find the slow code.

In many cases, we could just replace the above snippet with something like the following:
```py
content_items = get_many_by_key(content_keys)
for item in content_items:
    # do something with item
```
This way, while we'd have to wait for a single memcache fetch that we didn't before, at least it would only be a single one.  In some cases, refactoring the code would have been difficult, but we could at least pre-fetch the items we'd need, and keep them in memory until the end of the request, similarly avoiding a sequential fetch.

This was a pretty effective method &ndash; on our first round of testing, half of the hundred URLs we hit were at least 50% slower at the 50th percentile, and `khanacademy.org/math` was over 7 times slower!  But after several rounds of fixes and new tests, we were able to get the new version faster on average and on most specific URLs.  Unfortunately, this didn't cover everything &ndash; some real user traffic is harder to simulate, and because caching is less effective on test versions with little traffic, there was a lot of noise in our small sample, and so small changes in performance were hard to spot, even if they affected very very popular routes where that small difference would add up.

So we moved on to live testing!  Using the switch we had built, we set things up to allow us to more or less instantly change what percentage of our servers were using the new version.  Then we rolled out to around 1% of requests.  The first test immediately showed a blind spot in our testing &ndash; we hadn't done sufficient testing of internationalized pages, and there was a showstopper bug in that code, so we had to turn off the test right away.  But with that bug fixed, we ran the next test for several hours on a Friday afternoon.  We still saw a small increase in latency overall; the biggest contributor was a few routes that make up a large fraction of our traffic that got just a little bit slower.  After more improvements, we moved on to longer tests on around 5%, then 25%.  On the last test, we had enough traffic to extrapolate how the new backend would affect load on memcache, and scale it up accordingly before shipping to all users.

## Rollout & Future work

Finally, we were able to roll out to all users!  Of course, there were still a few small issues after launch, but for the most part things worked pretty well, and our memory usage went down noticeably, as we had hoped.  We still haven't rolled out to more languages yet &ndash; but when the team working on the tooling is ready to do that, we'll be able to.

We do still have some outstanding problems with the new system, which we're working to fix.  First, we've opened ourselves up to more scaling issues with memcache &ndash; if we overload the memcache server, causing it to fail to respond to requests, this sometimes causes the frontend servers to query it even more.  Now that we depend on memcache more, these issues are potentially more common and more serious.  And the manifest that lists the hashes of each item in the current content version is still a big pile of data we have to keep around; it's not as big as the old content bundle, but we'd love to make it even smaller, allowing us to scale even more smoothly.  If you're interested in helping us solve those problems and many more, well, [we're hiring](https://www.khanacademy.org/careers)!
