title: Switching to Slack
published_on: November 9, 2015
author: Benjamin Pollack
team: Infrastructure
...

Khan Academy recently made the decision to migrate our team chat from HipChat to
Slack. As a team, we're incredibly heavy users of ChatOps, and with so many of
KA’s employees working remotely at least a few days a week, all the little
details of a chat system can have a very disproportionate impact on the
productivity and happiness of our employees.

We'd been experiencing an increasing number of issues with HipChat: we had
connectivity problems. We had issues with message delivery. Notifications
sometimes just broke. Our remote workers especially just didn’t feel that chat
was something they could rely on, and that meant it was time to find an
alternative.

From everything we learned, we were increasingly convinced that Slack was
probably that alternative. The blocker was that we knew that switching chat
systems isn’t free; we were so bought into the HipChat ecosystem that there was
a real cost. (In fact, we had one failed attempt to migrate off HipChat in early
2014, which we had abandoned when the time investment far exceed what we had
been prepared to spend.) We needed to make sure we could do the migration in a
controlled fashion that minimized the disruption and lost time for the overall
team.

*Okay*, I hear some of you ask, *but what does it mean to be "bought in" to a
 chat system? Why’s it so hard to leave?*

## Hidden Costs

Well, because it's never that simple. You've got to handle all of the
cultural issues: you probably have a lot of rooms that serve special functions,
so you'll want to create equivalents on the new platform. And you'll also need
to update all the documentation saying what rooms are for what purpose, since
not all rooms can be named identically. And in the process, you’re going to find
a bunch of rooms whose purposes are dubious, and start having discussion on
whether to keep them.

You've also got social issues. You’ve got contractors who need access to only a
piece of the system. You have people who were administrators before, and need to
be administrators again—which also means they need to learn how to do
administration tasks all over again. You have whole parts of your organization
that probably rely on some esoteric feature of the old chat system that doesn’t
exist.

And if you're lucky enough to be a software shop, you have a whole extra class
of problems: integration points. Khan Academy has all kinds of systems that
communicate through the chat platform. We had alerting systems that notified
HipChat when systems were down or misbehaving, and we had
[Culture Cow](https://github.com/Khan/culture-cow), our
[Hubot](https://hubot.github.com/), which did everything from providing regular
reminders of how to be a KA employee, to interacting with our code review
system, to allowing creating cases in Asana, and more. In fact, our entire
deployment system was powered by HipChat.

![The deployment system was entirely driven by HipChat--and had quite a few usability issues resulting from that decision.](/images/switching-to-slack/testpages-hipchat.png)

We had a basic plan: a small team of just a couple of developers would begin
dual-wielding Slack and HipChat. We'd then begin porting our integrations over
to Slack until everything that happened in HipChat was also mirrored in Slack.
Once we were satisfied, we’d cut everyone over and kill HipChat.

## The Technical

First, we scoured our code base and looked for anything that spoke to HipChat.
While it turned out that *many* code bases talked to it in some way, we were
helped by the fact that virtually all alerting at Khan Academy works through an
open-source library of ours called [alertlib](https://github.com/Khan/alertlib).
Thus, right from the bat, we got a *lot* of mileage simply by teaching alertlib
how to speak to Slack, making sure appropriate tokens were installed,
redeploying each service, and watching to make sure identical alerts appeared in
both systems. If you use alertlib on your own site, grab our updates and you'll
get Slack support basically for free.

Most of the remaining instances were our manual integration points with
third-party services, like GitHub and Asana. But one of the nice things about
Slack’s ubiquity is that the overwhelming majority of tools that you'd want
alerting in chat already directly support Slack. In many, many cases, we were
able to delete or remove entire services, replacing them with some light
configuration or a simple plugin. Our Sheepdog service, which powered Asana
integration, could be replaced by the
[Asana Slack commands](https://asana.com/apps/slack), Jenkins by the
[Jenkins Slack plugin](https://wiki.jenkins-ci.org/display/JENKINS/Slack+Plugin),
and so on. And because Slack has keyword-based autoresponses built-in, it was
really easy to have Slack automatically tell people how commands they were used
to had changed. (For example, to respond to messages targeting `@all` by telling
them to use `@channel` instead.)

That pretty much left just the deployment system,
[Sun Wukong](https://en.wikipedia.org/wiki/Sun_Wukong). There were two issues
with Sun: first, it held a lot of state internally, meaning that every restart
could put it into an odd state, that its idea of the state of the build process
didn’t necessarily match Jenkins’, and that you couldn't run both a copy in
HipChat and a copy in Slack at the same time. To add insult to injury, while Sun
was nominally built on Hubot, it didn't actually use any of the Hubot API for
communication; while Hubot runs just fine on Slack’s API, Sun Wukong most
definitely did not.

After going through lots of variations on how to approach this problem, we ended
up settling on one we really liked. First, we modified our build jobs to publish
their job-specific state to a JSON file visible on the build server. Second,
using that JSON file combined with the Jenkins API, we modified Sun to rely
entirely on the build server’s view of the world directly. Suddenly, we could
launch versions of Sun on both chat systems and drive deployments from either
place, giving us an incredibly high degree of confidence that our most critical
tool would work fine. As a bonus, the new Sun is actually
[a simple Slack outgoing webhook](https://api.slack.com/outgoing-webhooks),
which means you don’t need to have a continuously running bot—and, in turn, that
we could move everything to just run on an App Engine
[Managed VM](https://cloud.google.com/appengine/docs/managed-vms/) instead of a
bespoke box on Amazon. We’ve
[open-sourced the project](https://github.com/Khan/slack-deploy-hooks) in case
you want to build on it.

![The new, vastly improved deployment system for Slack](/images/switching-to-slack/testpages-slack.png)

At that point, everything worked: if you were on Slack, you'd get all of the
notifications, and could perform all the actions, that you could on HipChat. But
what about everything else?

## The Social

First, simply *having* alerts appear doesn't mean they're pretty. Slack has a
really rich attachment and display system; whereas HipChat uses raw HTML for
formatting. So a lot of our alerts looked really ugly and out-of-place on Slack.

This is where a few of us using Slack and HipChat at the same time became
incredibly useful: we could see alerts come in, identify ones that were
particularly ugly, and adjust them long before anyone showed up so that
everything looked readable and attractive before people began using the system.

We also had to create chat many key chat rooms and adjust permissions before
people came over. One unique thing we do at Khan Academy is to keep an alumni
room for Elvises who have left the building: we like to stay in touch with
everyone who's had a hand in making Khan Academy great at what it does, even if
they’ve gone on to pursue different things, but we need to keep the alumni out
of sensitive rooms so we can preserve confidentiality and security. We had to
replicate that in Slack.

Second, while Sal is brilliant, he does have limits to his knowledge. Thus, we
have lots of contractors who help us cover other subject matter (and sometimes
who help us work on specific, niche technology issues). While we obviously want
to work closely with these contractors as conveniently as possible, they too
should not have unfettered access to the entire Khan Academy chat
infrastructure.

With HipChat, we actually had to have multiple, separate accounts to handle
these use-cases, but Slack gave us a totally new way to approach the problem:
*restricted accounts*, which can access only a subset of rooms and a subset of
users. These mapped perfectly to our contractors and alumni, but meant we had to
spend some time unifying the two system’s user lists and accounts.

Finally, we simply had to go through and adjust tons of documentation. That
process was very straightforward, but took time. On the bright side, since we
had new employees starting the same day we planned to do the switch, we knew
we’d have people immediately using our new documentation.

## The Switch

At that point, we were good to go. We declared Monday the official day to jump
to Slack. On that day, everyone logged on…

...and everything basically just worked. (In fact, the only issue we actually
hit was a bug in Slack’s history importer that we might write about some other
time.)

The trick with something like this is the same with any other major technical
change: if you can possibly run both systems at the same time, do. It makes
debugging a lot easier, makes sure you’re actually handling all the cases of the
original tool, and gives you great confidence you can roll back if you *do* hit
an issue.

## The End Game

The move to Slack has been absolutely worth it. Deploys are easier to read,
remote employees feel more connected, everyone trusts the chat system a lot
more, and integrating with other tools is easier than ever before. And
[people love the system](/images/switching-to-slack/hipslack-enjoyment.png)&mdash;something
we're [hardly the first people to notice](http://slackvshipchat.com/).

If you've been holding off jumping to Slack, follow our guide. It's pretty
painless and worth the effort.
