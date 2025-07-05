title: Profiling App Engine Memcached
published_on: May 1, 2017
author: Ben Kraft
team: Infrastructure
...

Last year, Willow wrote about how we [optimized our in-memory content data](/posts/evolving-our-content-infrastructure.htm) to take up less space.  But this was always a temporary solution: if we want to have a separate content tree for each language, we knew we would need to break up the monolithic content blob, and pull in content on-demand.

In principle, doing this is simple -- we already use [App Engine's Memcached](https://cloud.google.com/appengine/docs/python/memcache/), so all we need to do is change our data structures to pull in content from there whenever someone asks for it.  But that might be some unknown amount slower -- many requests access dozens or even hundreds of content items, which right now is plenty fast!  We had several ideas for how to improve access patterns and speed things up, but we didn't want to spend a couple months building one only to find it wasn't fast enough.  We had some vague guesses as to how often we access content, what requests would be the worst, and how fast Memcached is, but we didn't really know.  So last fall we set out to find out.

## Measuring Memcached latency

First we just wanted to answer a simple question: how fast is a Memcached access on App Engine?  Despite our heavy use of Memcached, we didn't really have a good estimate!  So we wrote a simple API endpoint to profile a Memcached get:

```py
@app.route('...')
@developer_required
def profile_memcached():
    num_bytes = int(request.args.get(num_bytes))
    data = os.urandom(num_bytes)
    key = 'profile_memcache_%s' % base64.b64encode(os.urandom(16))
    success = memcache.set(key, data)
    if not success:
        raise RuntimeError('Memcached set failed!')

    get_start = time.time()
    data_again = memcache.get(key)
    get_end = time.time()

    memcache.delete(key)
    return flask.jsonify(
        time=get_end - get_start,
        correct=data == data_again,
        key=key)
```

A thread pool and ten thousand API calls later, we had some data!

<figure>
    <img src="/images/memcached-profiling/by-size.png"
         alt="Graph of Memcached latency data" />
    <figcaption>
        Memcached latency distribution over 10,000 requests.  On the x-axis, the inverted percentile (so "1" is the 99th percentile), on a log-scale.  On the y-axis, latency in seconds, on a log-scale.  Each line is a different size of value in Memcached, from 1 to 1 million bytes.  So for a 1 million byte value (the uppermost line), the median latency is about 11ms, the 99th percentile is 21ms, and the 99.9th percentile is 43ms.
    </figcaption>
</figure>

We got a few things out of this data right away.  First of all, latency is in the 1-4ms range for most requests, and nearly always below 10ms.   Second, for all except very large values, the size of the value doesn't make a big difference in latency; even for very large values the difference is less than the factor of difference in value sizes.

But adding as many as a hundred serial 1-4ms fetches to each request wouldn't be an acceptable latency cost.  We did another series of tests and found that the response time for a single multi-get was similar to that of a single get.  So in principle, we could rewrite all our code fetch entities in bulk, but that would be difficult and time-consuming to do across our entire codebase, and we didn't know how effective it would be.

## Simulating Memcached latency

Luckily, we had another pile of data at our disposal.  For a small percentage of our requests, we set up logging to record which content items were accessed in the request.  We initial used this to get simple aggregates: data on how many items were accessed in a particular request, for example.  But along with the Memcached profiling data, we could do more: we could simulate how much slower a request would be if it had to make a particular number of Memcached hits.

We started by assuming that every content item accessed was a Memcached fetch (the first time in the request).  This was, as expected, too slow: over 10% of requests got at least 50% slower.  We could hand-optimize a few problematic routes, but not all of them, so we needed a more general strategy.  One natural option was to cache some data in-memory on each instance.

Since we had this data, we could simulate particular strategies for caching some content items in memory.  We simulated both an LRU cache and choosing in advance a fixed set of items to cache, with several sizes of each.  The latter strategy did significantly better than the LRU cache.  This remained true even if we used the chronologically first half of the data to decide which items to cache, and measured against the second half, which we took as validation that we could actually choose a fairly accurate set in practice.

<figure>
    <img src="images/memcached-profiling/static-cache.png"
         alt="Graph of simulated fixed-cache data" />
    <figcaption>
        Simulated increased request latency distribution over all instrumented requests.  On the x-axis, the inverted percentile, on a log-scale, as in the above graph.  On the y-axis, fraction of increased latency, on a log-scale.  Each line is a different caching strategy, with or without the multi-get of children.  For example, at the 90th percentile, without a cache we see a latency increase around 50%; a fixed cache reduces that to 10%, vs. 12% for an LRU cache.
    </figcaption>
</figure>

However, our results still weren't quite as good as we wanted; even excluding a few pages we figured could be manually optimized, we were still adding 25% or more to 5% of requests.  But we still hadn't made use of the multi-gets we profiled.  First we simulated immediately pulling all children of a topic into cache with a single multi-get for the duration of the request whenever we requested the topic, which we knew would be fairly easy to do.  This wasn't enough, but after several variations on it, we found a strategy that did: if, whenever we loaded a topic page, we pulled in all descendants of that topic (again with a single multi-get), down to some depth, that helped a lot.  While it would require code changes, we thought they should be simple enough to be manageable, with nowhere near as many unknowns as "now fix up all problematic code paths".

## Doing it for real

Since then, we've implemented the system for real, which I'll talk about in our next blog post!  Not everything worked out as planned, of course.  But to build this system out in reality took months, and testing out different caching strategies in production would have days or weeks of turnaround time, whereas in our simulations we could test out a new strategy in just a few minutes.  It required some guessing about our codebase -- knowing that "on topic pages, pull in every descendant of the topic at the start" was something we could implement, while, say, "pull in every item we need to render the page at once" definitely wasn't.  Of course, a lot of things we didn't know, but we felt much more confident moving forward with actually implementing a months-long engineering effort with some assurance that the plan has some chance of working.  And now we know, a lot more precisely, just what performance we can expect from App Engine Memcached.

## Appendix: App Engine Memcached latency data

If you also use App Engine's dedicated Memcached service, you may find the below data useful.  Note that each sample was taken over the course of an hour or so, so it doesn't account for rare events like memcache outages or more generally capture latency over time.  That's also a potential source of difference between the two tables; they were measured at different times.

### Fetch latency by size

<div class="x-scrollable">
    <table>
        <thead>
            <tr><th>%ile</th><th>1B</th><th>10B</th><th>100B</th><th>1KB</th><th>10KB</th><th>100KB</th><th>1MB</th></tr>
        </thead>
        <tbody>
            <tr><th>5</th><td>1.38</td><td>1.35</td><td>1.36</td><td>1.41</td><td>1.47</td><td>2.33</td><td>8.29</td></tr>
            <tr><th>25</th><td>1.72</td><td>1.70</td><td>1.70</td><td>1.84</td><td>1.92</td><td>2.94</td><td>9.88</td></tr>
            <tr><th>50</th><td>2.34</td><td>2.29</td><td>2.28</td><td>2.71</td><td>2.69</td><td>3.77</td><td>11.16</td></tr>
            <tr><th>75</th><td>3.71</td><td>3.67</td><td>3.72</td><td>4.01</td><td>4.09</td><td>5.08</td><td>12.65</td></tr>
            <tr><th>90</th><td>4.66</td><td>4.60</td><td>4.66</td><td>4.83</td><td>4.92</td><td>6.00</td><td>14.22</td></tr>
            <tr><th>95</th><td>5.33</td><td>5.27</td><td>5.45</td><td>5.50</td><td>5.76</td><td>6.74</td><td>15.46</td></tr>
            <tr><th>99</th><td>10.56</td><td>9.93</td><td>11.35</td><td>9.47</td><td>11.83</td><td>12.11</td><td>21.09</td></tr>
            <tr><th>99.9</th><td>34.59</td><td>24.57</td><td>38.44</td><td>26.97</td><td>30.57</td><td>41.15</td><td>42.84</td></tr>
        </tbody>
        <caption>
            Memcache latency for a single get of a string value of the given size, over 10,000 samples for each size, in milliseconds.
        </caption>
    </table>
</div>

### Multi-get latency

<div class="x-scrollable">
    <table class="data-table">
        <thead>
            <tr><th>%ile</th><th>1 key</th><th>3 keys</th><th>5 keys</th><th>10 keys</th><th>100 keys</th></tr>
        </thead>
        <tbody>
            <tr><th>50</td><td>3.06</td><td>3.87</td><td>4.00</td><td>3.70</td><td>8.29</td></tr>
            <tr><th>75</td><td>4.30</td><td>4.66</td><td>4.77</td><td>5.02</td><td>9.94</td></tr>
            <tr><th>90</td><td>5.17</td><td>5.46</td><td>5.61</td><td>6.30</td><td>11.88</td></tr>
            <tr><th>95</td><td>6.01</td><td>6.60</td><td>6.77</td><td>7.64</td><td>14.12</td></tr>
            <tr><th>99</td><td>17.22</td><td>17.64</td><td>25.23</td><td>23.01</td><td>32.20</td></tr>
            <tr><th>99.9</td><td>92.18</td><td>234.90</td><td>225.22</td><td>70.10</td><td>108.81</td></tr>
        </tbody>
        <caption>
            Memcache latency for a multi-get get of several 1KB string values, over 10,000 samples for each size, in milliseconds.
        </caption>
    </table>
</div>
