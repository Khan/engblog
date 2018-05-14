title: "What do software architects at Khan Academy do?"
published_on: May 14, 2018
author: Kevin Dangoor
team: Infrastructure
...

“Architect” is a new role in Khan Academy’s engineering team this year, and my colleague, [John](https://twitter.com/jeresig), and I have stepped into this role. John has been with Khan for seven years now, mostly focused on frontend development. I’ve just reached three years here, having spent time in frontend development and engineering management. There are many possible paths to this role, and I’ve seen quite a few definitions of it, so I thought I’d share our view of being an architect.

## The role of an architect
The Wikipedia article about software architects [leads with this](https://en.wikipedia.org/wiki/Software_architect):

> A software architect is a software expert who makes high-level design choices and dictates technical standards, including software coding standards, tools, and platforms.

My view is a subtle shift from that one: **an architect acts as a sort of product manager for the system in which software is built**. This “system” consists of the coding standards, tools, platforms, and even processes used by the engineers on the team to build features for their users. Architects look for ways in which the system can better serve the engineers.

The Wikipedia definition describes the architect as “making” the design choices and “dictating” the standards. For me, that evokes images of an architect handing a scroll to a messenger who then walks among the engineers declaring, “On this, the 14th of May, 2018, we hereby decree that all files shall use four spaces for indentation.”

As a product manager for the system, I look out for ways to make things better and then work with the engineers and engineering management to make the changes come to fruition. It’s a lot more collaboration than it is dictation.

That’s enough vague, high-level talk. Let’s talk about things that actually consume time in my day.

## We guide architecture change
Though I was joking about the Great Indentation Decree of May 2018, we _do_ need coding standards to help engineers make sense of our system. If you’ve ever been part of a protracted technical argument, you know that these can sometimes be draining and not a productive use of time.

At Khan Academy, we’ve adopted [DACI](https://www.atlassian.com/team-playbook/plays/daci) as a decision-making framework. DACI stands for Driver, Approver(s), Contributors, Informed and specifies the roles involved in making a decision. The architects and other engineering leaders act as the “approvers” on architecture changes. You could interpret that as “the architects make the decision,” which makes this process sound like the “dictating change” approach from Wikipedia, but that’s not how DACI works.

In DACI, the Driver makes sure that the change has the right contributors involved and the Approvers “own” the decision, ensuring that concerns have been accounted for. Are there potential security implications to the change? If so, we’ll make sure our security lead is a contributor.

The Driver and Contributors together work out the details of the change and, ideally, the actual decision is self-evident by the end of their work. As the approvers in those cases, architects and other engineering leaders make sure that all of the questions have been resolved.

In the cases in which there are two choices, we have to pick one, and the differences between the two are minor, the approver will indeed make the choice. This wasn’t necessary in the vast majority of cases we’ve seen so far.

Every architecture change we make goes into a [decision log](http://thinkrelevance.com/blog/2011/11/15/documenting-architecture-decisions) so that future-us can understand _why_ our system works the way it does, making it easier to understand when it should change again.

This process is intentionally designed to be lightweight, so that we can move quickly and efficiently. A simple, uncontroversial change can be written up and approved in a day.

What kinds of changes have we made this way? A few recent examples:

* We’ve adopted rules for how we would deprecate public API endpoints
* We’ve created standards for React components that we use site-wide
* We have a second language (Kotlin) that is an acceptable choice for building services

Being a part of all of these changes helps architects maintain a broad view of work that’s happening in our system, which helps us guide further changes to it.

## Architects help our guilds
Khan Academy’s teams are built around product areas, so we’ve established guilds that look out for our technology across the product areas. We have four guilds currently: web frontend, backend, mobile, and data engineering.

Guilds have the ability to influence how a portion of our development time is used, for things like [breaking apart our Python code](http://engineering.khanacademy.org/posts/python-refactor-1.htm) or creating a [wholly new set of UI components](https://github.com/Khan/wonder-blocks). John and I help organize the guild work for the frontend and backend guilds, respectively.

## Communication
Architects spend a lot of time on communication tasks to help everyone stay in sync about the current state of our system and how it’s evolving. Architecture diagrams, roadmaps, project plans, this blog, a newsletter of relevant technology stories, and meetings are all pieces of what we do as architects.

The newsletter (see below) helps ensure that everyone in engineering has seen some stories about how technology that affects us is changing.

![Signal Boost newsletter](/images/architects/signalboost.png)

The diagrams, which we’re creating in part following the [C4 model](http://c4model.com), are a useful tool for communicating about our system. I’ve been working on a proposal for a change to our system and I was able to take pieces out of our diagrams and create new ones that made the step-by-step progression in the proposal much clearer.

![Sample c4 architecture diagram](/images/architects/c4sample.png)

## Code
Architects are programmers and John and I both exercise those skills as part of the job.

## Managers and architects
Architects aren’t typically people managers, and that is the case for both John and me. When it comes to our development process and how projects are going, our managers take the lead. Technical leadership within engineering is shared by architects and managers, with managers taking more responsibility for delivery of the product (the “what”) and architects focusing more on the state of the architecture (the “how”).

I spend time each week talking with an engineer on the team to find out how things are working for them. That helps me get a view across the organization of how the system is working, and a cross-cutting perspective I can share with managers when there are things we can improve.

## PMs for the system
I’m fond of the “product manager for the system” definition of software architect. The users of the system are our software engineers, QA, and others who are ultimately working to deliver features for learners, teachers and coaches who use Khan Academy, and we want to help that system deliver better and faster.

_Thanks to Marta Kosarchyn, David Flanagan, Scott Grant, and John Resig for their feedback on this post._