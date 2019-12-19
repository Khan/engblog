title: "Go + Services = One Goliath Project"
published_on: December 20, 2019
author: Kevin Dangoor
team: Infrastructure
...

# Go + Services = One Goliath Project

*Khan Academy is embarking on a huge effort to rebuild our server software on a more modern stack in Go.*

**At Khan Academy, we don’t shy away from a challenge.** After all, we’re a non-profit with a mission to provide a “free world-class education to anyone, anywhere”. Challenges don’t get much bigger than that.

Our mission requires us to create and maintain software to provide tools which help teachers and coaches who work with students, and a personalized learning experience both in and out of school. Millions of people rely on our servers each month to provide a wide variety of features we’ve built up over the past ten years.

Ten years is a long time in technology! We chose Python as our backend server language and it has been a productive choice for us. Of course, ten years ago we chose *Python 2* because Python 3 was still very new and not well supported.

# The Python 2 end-of-life

Now, in 2019, Python 3 versions are dominant and the Python Software Foundation has said that  [Python 2 reaches its official end-of-life on January 1, 2020](https://www.python.org/doc/sunset-python-2/) , so that they can focus their limited time fully on the future. Undoubtedly, there are still *millions* of lines of Python 2 out there, but the truth is undeniable: Python 2 is on its way out.

**Moving from Python 2 to 3 is not an easy task.** Beyond that hurdle, which has been widely written about elsewhere, we also have a bunch of other APIs in libraries we use which have undergone huge changes.

All of these differences mean that we’d have to split our code to run in at least two services (the old Python 2 codebase and the Python 3 replacement) which can coexist during the transition.

For all of that work, we’d receive these benefits:

1. Likely a 10-15% boost in backend server code performance
2. Python 3’s language features

# Other languages

Given all of the work required and the relatively small benefits, we wanted to consider other options.
We started  [using Kotlin for specific jobs within Khan Academy a year ago](https://engineering.khanacademy.org/posts/kotlin-adoption.htm) . Its performance benefits have saved us money, which we can apply in other ways to help people around the world learn. **If we moved from Python to a language that is an order of magnitude faster, we can both improve how responsive our site is****and****decrease our server costs dramatically.**

Moving to Kotlin was an appealing alternative.  While we were at it, we decided to dig deeper into other options. Looking at the languages that have first-class support in Google App Engine, another serious contender appeared: Go. Kotlin is a very expressive language with an impressive set of features. Go, on the other hand, offers simplicity and consistency. The Go team is focused on making a language which helps teams reliably ship software over the long-term.

As individuals writing code, **we can iterate faster due to Go’s lightning quick compile times**. Also, members of our team have years of experience and muscle memory built around many different editors. **Go is better supported than Kotlin by a broad range of editors**.

Finally, we ran a bunch of tests around performance and found that Go and Kotlin (on the JVM) perform similarly, with Kotlin being perhaps a few percent ahead. Go, however, used a lot less memory, which means that it can scale down to smaller instances.

We still like Python, but **the dramatic performance difference which Go brings to us is too big to ignore, and we think we’ll be able to better support a system running on Go over the years**. Moving to Go will undeniably be more effort than moving to Python 3, but the performance win alone makes it worth it.

# From monolith to services

With a few exceptions, our servers have historically all run the same code and can respond to a request for any part of Khan Academy. We use separate services for storing data and managing caches, but the logic for any request can be easily traced through our code and is the same regardless of which server responds.

When a function calls another in a program, those calls are extremely reliable and very fast. This is a fundamental advantage of monoliths. **Once you break up your logic into services, you’re putting slower, more fragile boundaries between parts of your code**. You also have to consider how, exactly, that communication is going to happen. Do you put a publish/subscribe bus in between? Make direct HTTP or gRPC calls? Dispatch via some gateway?

**Even recognizing this added complexity, we’re breaking up our monolith into services**. There’s an element of necessity to it, because new Go code would have to run in a separate process at least from our existing Python.

The added complexity of services is balanced by a number of big benefits:

* By having more services which can be deployed independently, deployment and test runs can move more quickly for a single service, which means engineers will be able to spend less of their time on deployment activities. It also means they’ll be able to get changes out more quickly when needed.
* We can have more confidence that a problem with a deployment will have a limited impact on other parts of the site.
* By having separate services, we can also choose the right kinds of instances and hosting configuration needed for each service, which helps to optimize both performance and cost.

We posted a series of blog posts ( [part 1](http://engineering.khanacademy.org/posts/python-refactor-1.htm), [part 2](http://engineering.khanacademy.org/posts/slicker.htm) ,  [part 3](http://engineering.khanacademy.org/posts/python-refactor-3.htm) ) about how we had performed a significant refactoring of our Python code, drawing boundaries and creating constraints around which code could import which other code. Those boundaries provided a starting point for thinking about how we’d break our code into services. Craig Silverstein and Ben Kraft led an effort to figure out an initial set of services and how we would need to accommodate the boundaries between them.

In our current monolith, code is free to read and update any data models it needs to. To keep things sane, we made some rules around data access from services, but that’s a topic for another day.

# Cleaning house

Ten years is a long time in technology. GraphQL didn’t exist in 2009, and two years ago **we decided to migrate all of our HTTP GET APIs to GraphQL**, later deciding to also adopt GraphQL mutations. **We adopted React just after it was introduced**, and it has spread to much of our web frontend. Google Cloud has grown in breadth of features. Server architectures have moved in the direction of **independently deployable services**.

Ten years is also a long time for a product. **We have introduced an incredible number of features**, some of which have very little usage today. Some of our older features were built with patterns that we no longer think fit our best practices.

We’re going to do a lot of housecleaning in Python. We’re very aware of the  [second-system effect](https://en.wikipedia.org/wiki/Second-system_effect)  and our goal with this work is not to “create the perfect system” but rather to make it easier to port to Go. We started some of these technical migrations earlier, and some of them will continue on past the point at which our system is running in Go, but the end result will be more modern and coherent.

* We’ll only generate web pages via React server side rendering, eliminating the Jinja server-side templating we’ve been using
* We’ll use  [GraphQL federation](https://blog.apollographql.com/apollo-federation-f260cf525d21)  to dispatch requests to our services (and to our legacy Python code during the transition)
* Where we need to offer REST endpoints, we’ll do so through a gateway that converts the request to GraphQL
* We will rely more heavily on Fastly, our CDN provider, to enable more requests to be served quickly, closer to our users, and without requiring our server infrastructure to handle the request at all
* We’re going to deprecate some largely unused, outdated features that are an ongoing maintenance burden and would slow down our path forward

There are other things we might want to fix, but we’re making choices that ultimately will help us complete the project more quickly and safely.

# What’s not changing

Everything I’ve described to this point is a huge amount of change, but there is a lot that we’re not changing. As much as possible, we’re going to port our logic straight from Python to Go, just making sure the code looks like idiomatic Go when it’s done.

We’ve been using Google App Engine since day 1, and it has worked well for us and scaled automatically as we’ve grown. So, we’re going to keep using App Engine for our new Go services. We’re using Google Cloud Datastore as our database for the site, which is also staying the same. This also applies to the variety of other Google Cloud service we use, which have been performing well and scaling with our needs.

# The plan

**As of December 2019, we have our first few Go services running in production** behind an Apollo GraphQL gateway. These services are pretty small today, because the way we’re doing the migration is very incremental. This incremental switchover is another good topic to talk about on another day (subscribe to our  [RSS feed](http://engineering.khanacademy.org/rss.xml)  or  [our Twitter account](https://twitter.com/KhanAcademyEng)  to read new posts as they go live).

For us, **2020 is going to be filled with technical challenge and opportunity**: Converting a large Python monolith to GraphQL-based services in Go. We’re excited about this project, which we’ve named Goliath (you can probably imagine all of the “Go-” names we considered!). It’s a once in a decade opportunity to take a revolutionary step forward.

*If you’re also excited about this opportunity, check out   . As you can imagine, we’re hiring engineers!* [our careers page](https://www.khanacademy.org/careers)
