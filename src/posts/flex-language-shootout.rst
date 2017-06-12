title: App Engine Flex Language Shootout
published_on: April 17, 2017
author: Amos Latteier
team: Infrastructure
...

This is the second time I've been to Silicon Valley. Some years ago - never mind
how long precisely - I started writing open source software. It's taken me to
some strange places like Washington DC and `Kwajalein
<https://en.wikipedia.org/wiki/Kwajalein_Atoll>`_, but never until recently to
the suburbs of San Jose.

The reason I'm here is for a hackathon. I recently was hired by Khan Academy. I
live in Vancouver, the one in Canada. I work remotely. In fact most of the
people I work closely with are remote. This is one of the great things about
this new job. Also it turns out that I get to work with smart and friendly
people. And instead of writing a CRM for insurance salespeople like I was doing
at my last gig, my job is to help anyone anywhere get a free world-class
education. There's got to be a catch. Maybe it's this hackathon.

What kind of hackathon is this anyway?
--------------------------------------

Apparently it's `healthy <http://healthyhackathon.khanacademy.org/>`_. Growing
up my mother was very focused on healthy foods. My sister and I used to break
into the carob chips, looking for anything candy-like. So if it's anything like
that I know that I'm in trouble.

The offices are covered in decorations when I arrive. This seems less like a
hackathon and more like a craft party. I feel a bit out of place, so I cut a
cape out of felt and put it on. That's better.

Rather than endurance coding, we do a lot of socializing and collecting
donations for a food bank interspersed with project work. I decide to work with
someone I don't know on a fun-sounding project.

A fun-sounding project
----------------------

The co-worker I don't know explains the project to me. Right now Khan Academy
runs on App Engine. `Classic
<https://cloud.google.com/appengine/docs/standard/>`_, not `flex
<https://cloud.google.com/appengine/docs/flexible/>`_. There's interest in
moving to flex. It turns out that they are pretty different. There's a ton of
institutional knowledge here about classic built up over years. But we don't
have a lot of experience with flex. This project is about getting some
experience with flex.

Plus the project is a language shootout. Right now most of the backend code is
in Python, but there are fantasies about moving to another language. Who doesn't
fantasize about other languages? I'm currently infatuated with `Elixir
<http://elixir-lang.org/>`_. It's possible that I like it because I haven't used
it for any serious projects yet. But I have tried writing distributed systems
(and even worse, debugging distributed systems written by others) in Python, and
that was a bad enough experience to make me look for alternatives.

Anyway we're probably not going to switch languages anytime soon, but it's fun
to dream.

The task we set ourselves is to consume a `pub/sub
<https://cloud.google.com/pubsub/>`_ feed and put the results into `BigQuery
<https://bigquery.cloud.google.com>`_. The feed collects information about about
exercises attempted by users of Khan Academy. There is a lot of exercise data.

We must first validate the message using a hmac digest. We use a secret stored
in `metadata
<https://cloud.google.com/compute/docs/storing-retrieving-metadata>`_. Next
parse the pub/sub message. Then send it to BigQuery. We have to insure that the
right table exists and then insert the data.

Oh, and we need to run a web server, cause that's how you do `push subscriptions
<https://cloud.google.com/pubsub/docs/subscriber>`_.

So it's not too much work, but not completely trivial.

The contenders
--------------

Of course I'm going to write a service in Elixir. In fact that's the reason I
chose this project.

Elixir
~~~~~~

`Elixir <http://elixir-lang.org/>`_ is a new marketing campaign for Erlang. Well
technically it's more than that, but from my point of view the great things
about Elixir are OTP and BEAM. My coworker already has the Elixir implementation
started. I only have to add a few things to get it working, but there are no
official Google Cloud libraries so that ends up being my biggest challenge.

Go
~~

`Go <https://golang.org/>`_ is a language that not many people who I know seem
to be enthusiastic about. But hey, why not try it? There are bound to be decent
Google Cloud Platform library for it, right? And it compiles fast.

Kotlin
~~~~~~

`Kotlin <http://kotlinlang.org/>`_ is a language that I haven't heard of until
recently. But my manager loves it, so I guess I should test it. Actually it
doesn't seem to be as dreadful as I expected. Plus some people say that they've
gotten the JVM working pretty well these days. One downside is that it doesn't
compile as fast as go does.

Python
~~~~~~

`Python <https://www.python.org/>`_ is the language I've hitched my professional
career to. Happily for me Python isn't dead yet. Khan Academy uses a lot of
Python. Yeah, it's slow. Also under flex you have to choose your own WSGI
server. I'm not sure we chose the best one. If we had more time I'd like to look
into this more.

Crystal
~~~~~~~

`Crystal <https://crystal-lang.org/>`_ is a language I've never heard of. But my
coworker checks in a microservice written in one night. He says it's fun.

Interlude in which my mind is blown
-----------------------------------

We're making progress on the project, mostly due to my co-worker's efforts. I'm
spending most of my time trying to understand the code he's checking in. But
then comes the Python Bee. It's like a spelling bee, but in Python. That sounds
cool; I know Python. So it turns out there's a wrinkle. You have to speak out
your program, character by character without looking at the screen while someone
else types it in for you. OK, so you have to keep it all in your head and not
mess up on indenting. I think I can do this. Oh wait, it turns out that you have
a partner, and you can't communicate with them, and you each take turns saying
the next character of the program! So it's not just keeping the program in your
head, it's guessing what program is in your partner's head too.

Two people are writing a prime number sieve in Haskell using mind reading. This
is happening right in front of me right now.

Now it's my turn. Ok, ok, ok, ok. `IndentationError`. Ugh, not only does this look
really hard, it is really hard too.

Some benchmarking results
-------------------------

We don't get around to doing message validation on all the different
microservices. So our benchmark isn't fair. In fact it's not even particularly
precise. We just start the microservices, point the pub/sub firehose at them and
see how far behind they fall during the day, and how long it takes them to catch
up with the backlog in the evening.

Still it isn't hard to see how each language fares.

========  ============================
Language  Speed
========  ============================
Kotlin    Fast
Elixir    Not quite as fast as Kotlin
Go        Pretty much as fast a Elixir 
Python    Quite a bit slower
========  ============================

We can't get Crystal running well enough to compete. We run into ssl errors and
don't have enough time to track down a solution.

After doing this sloppy benchmark I'm not sure that it's really a great argument
to switch away from Python. Speed is only one consideration among many.

In practice it seems that the quality of Google Cloud Platform libraries is
probably one of the most important factors in picking a language for our
benchmark, since we rely so heavily on Google Cloud Platform.

I am impressed with Elixir's performance, though. It almost kept up with Kotlin,
and hey confirmation bias.

I also wonder about whether we should be consuming pub/sub messages with a push
queue. I suspect that performance would be much better using a pull queue, since
then we could batch our BigQuery inserts. Often the best way to improve
performance is changing the algorithm not the language.

Anyway we present our results. People nod respectfully. Ours is just one in a
vast and riotous sea of hackathon projects.

We haven't figured out the organization's future language strategy, but we have
gotten some practical experience with App engine flex. Plus we've validated that
microservices seem to work OK for a simple task that's bounded by external APIs.

Afterward
---------

I'm still really in awe of the Python Bee performances I saw. I asked the
Haskellers how they did it. `Foldl <https://wiki.haskell.org/Fold>`_ I was told.
Foldl makes sense for this kind of thing. If you are both thinking "Foldl,
foldl, foldl" then it's easier to read each other's minds. I'm probably not
going to learn Haskell, but I know about reduce. Next year I just need to find a
partner who's also thinking "Reduce, reduce, reduce". That and remember how many
spaces we're indented.
