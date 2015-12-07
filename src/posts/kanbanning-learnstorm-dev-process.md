title: "Kanbanning the LearnStorm Dev Process"
published_on: December 7, 2015
author: Kevin Dangoor
team: Web Frontend
...

In his [New Employee's Primer](http://engineering.khanacademy.org/posts/new-employees-primer.htm)
post from July, Riley Shaw wrote a little about our **T**eams **I**nitiatives
**P**rojects (TIP) style of thinking about our development work. Here's a quick
summary of TIP:

* Teams represent areas of deep domain expertise like mobile, design,
  data science,
* Initiatives are cross-functional, multi-project efforts that the
  organization believes are worth a significant investment, and
* Projects are specific pieces of work that are scoped to take 2-5 weeks for
  1-3 people.

A five-week, three-person project is substantial, so that gives you
an idea of where an initiative starts in terms of scope.

TIP was adopted in February, so 2015 is the first year in which we've had
initiatives. We don't have a specific process that each initiative uses
to manage itself, which gives each initiative the freedom to figure out its
best path forward.

## LearnStorm

I'm working on the [LearnStorm](http://learnstorm2016.org) initiative.
LearnStorm is a math challenge for students in 3rd-12th grades (and the
Irish equivalents) in the Bay Area, Chicago, Idaho and Ireland. This
initiative includes a collection of features that we're building into Khan
Academy and a large amount of work from our programs team to organize things
like helping teachers register students and in-person events. There are a bunch
of us working over several months to make this challenge the best it can be.

## Our initial development process

When we started development at the beginning of September, we used
an approach similar to what other initiatives were doing at the time:
we imagined the initiative as a collection of projects. We had rough ideas
about how long each project would take and put the projects on a first draft
timeline in a Google Sheets spreadsheet. We also had a Trello board that we
used to show the projects in progress and the projects that were coming up.
This was a useful way to think about the project at this early stage, but
it didn't take long for us to start feeling limitations in how we could adapt
our plans to handle new information.

Around the beginning of November, we switched from a general "working on
projects" mode to a "need to launch signups" mode. It became important to
track many small and medium sized tasks that needed to be done
before we could open up signups. Over a crazy few days we moved from Trello
checklists to a Google Doc and finally to a list in Asana.

That was a bumpy time.

## Smoothing the process for the second phase

LearnStorm is different from other Khan Academy initiatives to date in that we
have some hard deadlines. The challenge *will* start January 29th, 2016 for
example. When it comes to getting a project out, there's the idea that you've
got three levers to play with: scope, time and resources. For LearnStorm, the time
is fixed. We also have the whole team in place that we're going to have, so
the resources lever is also fixed (plus: [Mythical Man-Month](https://en.wikipedia.org/wiki/The_Mythical_Man-Month)).
Scope is the *only* thing we have to play with in making sure that the
challenge is ready on time.

Two to five week-long projects can contain quite a bit of scope and don't
lay that scope out in a way that makes it easy to choose between alternatives.
Larger projects also make it harder to change priorities as we learn new things
about the project.

What if there was a process that allowed us to easily see how the project is
progressing and reprioritize features based on new information?

## Enter Kanban

I had [experience](http://www.blueskyonmars.com/2014/02/18/bracketsscrumtokanban/) 
with [Kanban](https://en.wikipedia.org/wiki/Kanban_%28development%29) in the
past and thought it seemed like a good fit for our needs. Here is Wikipedia's
description of Kanban for software development:

> Kanban is a method for managing knowledge work with an emphasis on just-in-time delivery while not overloading the team members. In this approach, the process, from definition of a task to its delivery to the customer, is displayed for participants to see. Team members pull work from a queue.

Just-in-time delivery of the most important work is what makes Kanban work well for us.
Each work item that we put into our queue in Trello is no more than a few days
long. If needed, the priorities for the whole team can be changed in just a few
days without interrupting the work that's already in progress.

Plus, these small work items also provide a lot of choices for prioritization.
When working through a couple of big features, there might be pieces of each
that are lower priority and might be skipped entirely.

## But where's the big picture?

Since the beginning of the initiative, we've been having regular retrospectives
to improve how we work. We recently had our first retro since moving to Kanban
and there was a lot of positive feedback. Developers on the team found the
process of grabbing the next work item and running with it to be a good way to
focus on the most important work. The flip side is that it's hard to see the
big picture progress we're making on the overall project.

We think a partial fix for this is easy: just make a document or diagram that
groups the cards on the Kanban board with the overall project goals that
they're bringing to life. I say that this is a partial fix, because there is
a tradeoff in adopting small units of work as we have. It's much easier to
see how 5 bigger projects become a whole than 25 smaller work items. And some
of those small work items may *never* even be done.

## Choice of tools

We write automated tests and try things out along the way, but we're
still planning to have a focused testing and bug fixing period at the end of
the project.

When we were getting ready to launch signups, Asana's straightforward list
view worked well for rapidly collecting and sorting all of the feedback we
got from the testers. I've found it much harder to work with Trello boards
that have a large number of items on them, so we'll probably switch back
to Asana for that phase at the end of the Initiative.

Trello and Asana store similar kinds of data, but the views and UI features
make a huge difference in how you approach and use the tools. Unsurprisingly,
people have used their APIs to present different views on top of the same
data, but we haven't explored those third party tools yet.

## Pick a process and improve

Kanban is not the "one process to rule them all". In fact, Kanban isn't 
a single process at all, but rather a way to think about and evolve
the process you have. [Continuous improvement](https://visualstudiomagazine.com/articles/2013/06/01/continuous-improvement-and-the-agile-restrospective.aspx)
is the name of the game, and that's what we've been going for.
Our use of Kanban has helped us to collect, visualize and work on the most
important things as our initiative evolves.

