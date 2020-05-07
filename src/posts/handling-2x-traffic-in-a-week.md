title: How Khan Academy Successfully Handled 2.5x Traffic in a Week
published_on: May 9, 2020
author: Marta Kosarchyn
team: Engineering
...
Talk about rapid scaling...

A few months ago I posted [some thoughts on scaling](https://engineering.khanacademy.org/posts/eng-principles-help-scale.htm) and promised to post more soon. Well, talk about rapid scaling — within just two weeks in March, Khan Academy site usage grew to 2.5x what it was at the same time last year and has sustained that level to date. As schools all over the world closed because of the coronavirus pandemic and students, parents, and teachers moved to distance learning, Khan Academy was able to respond, offering high-quality content and classroom experience — for free. In the month of April, we served 30 million learners on our platform. A recent national survey of parents found that [Khan Academy was the “most used online resource”](https://tytonpartners.com/library/2177-2/).

I’m proud that we absorbed this rapid growth without disrupting our users.  In addition to reacting quickly to alleviate pressure points within a few days, we had prepared in advance, and that preparation paid dividends. We scaled readily in large part because of our architecture and a rigorous practice of choosing external services carefully and using them properly.

So in this post I’ll discuss architectural aspects that play a key role in the scalability of our site.

Two fundamental components of our architecture serve us particularly well here. We use [Google Cloud](https://cloud.google.com/appengine), including AppEngine, Datastore, and Memcache, and [Fastly CDN](https://www.fastly.com/products/cdn), and they were the backbone of the **serverless and caching strategy that’s key to our scalability**.


![Architecture Diagram](../images/scaling-traffic-in-a-week.png High-level architecture)


## Serverless infrastructure

Using GCP App Engine, a fully managed environment, means we can scale very easily with virtually no effort. Even with a substantial traffic increase, our site stayed up and performed well, with minimal intervention. We didn’t need to worry about load balancing ourselves because server instances were brought up as needed without any intervention. We similarly use Datastore which scales out storage and access capacity automatically in much the same way App Engine scales out web server instances.

## Caching

Fastly CDN allows us to cache all static data and minimize server trips. Huge for scalability, it also helps us optimize hosting resources, for which costs grow linearly with usage in our App Engine serverless model. As shown in the architecture diagram, all client requests go through Fastly so we can prevent unnecessary server traffic, improving performance. We load videos primarily from YouTube and secondarily from Fastly.  This also keeps costs down as well as ensures that the videos load quickly.

In addition to caching static data in Fastly, we also extensively cache common queries, user preferences, and session data, and leverage this to speed up data fetching performance. We use Memcache liberally, in addition to exercising other key best practices around Datastore to ensure quick response times.

Our site reliability (SRE) team of course needed to be prepared with ironclad monitoring - and we were.  We noticed some slowdowns in the first few days and found that deploys were causing those hits. At our request, Google increased our Memcache capacity, and within a week we were comfortable returning to our normal continuous deployment pattern. This speed was critical, as our teams were quickly developing [resources](https://keeplearning.khanacademy.org/) to guide new site users in onboarding as easily as possible.

Overall, we work hard to choose services carefully, follow best practices, and develop our own as needed. With the right technology, careful preparation, and adjustments on the spot by our amazing engineering team, we’ve been able to serve the students, parents, and teachers who rely on us now more than ever without interruption.

-----

Khan Academy's increased usage has also increased our hosting costs, and we're a not-for-profit that relies on [philanthropic donations from folks like you](https://www.khanacademy.org/donate).
