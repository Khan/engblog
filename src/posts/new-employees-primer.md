title: "Khan Academy: a new employee's primer"
published_on: July 20, 2015
author: Riley Shaw
team: Web Frontend
...

I recently joined the developer team at Khan Academy. Since arriving I’ve been surprised by a number of intentional decisions the organization has made to empower its developers. Whether you’re working in tech or just curious about the inner workings of Khan Academy, there’s some great wisdom in how things are done here.


## All aboard!
A benefit of working at an education startup is that everyone naturally puts a lot of thought into information design. As a result, this has been the smoothest onboarding I’ve experienced.

Onboarding actually started a few weeks before my first work day. As soon as my offer came through [Andy](http://andymatuschak.org/) sent me a short message:

> I’m sure you’re being well taken care of, but if there’s any questions I can answer for you, or any magic words you need to hear to sign that offer, please send them my way.

I said something stupid:

>  As far as magic words go, I've always been a fan of "flipendo"

...and I got **the coolest** response ever:

> OK!! [khanacademy.org/r/flipendo](https://www.khanacademy.org/r/flipendo)

Wat. He… wat? He made that? For… me? Wat.[^1]

I spent the rest of the weekend pulling out my phone to show people what this wonderful stranger had made.

I got a few more messages from the team before starting. A [fellow Canadian](http://david-hu.com/) offered a couch to crash on while I was looking for a place. And I got a message from [Jordan](http://jordanscales.com/), onboarding buddy extraordinaire.


## Onboarding buddies
Starting a new job is intimidating. When you’re new and have questions it’s hard to know who to ask, when to ask, and how often to ask. Khan Academy makes this easy by giving every new hire an explicit mentor, along with the following rules:

**Who to ask:** Your mentor. If they don’t know the answer, they’ll know who knows the answer.

**When to ask:** Now.

**How often to ask:** Probably more often than you currently are.

Having someone to relentlessly pester during my first few weeks was instrumental in getting up to speed quickly.


## One-on-ones
As soon as I arrived on my first day I went for a walk with my manager [Marcia](https://twitter.com/marcia_lee)[^2]. We strolled around the block under the beautiful California sun and learned a bit about each other. She showed me where the nearest coffee shop was. She told me that if I _ever_ had a problem someone would be there to help. It was a warm welcome that set the tone for the rest of the day. When I got back to my desk I scheduled three more walks[^3].

Khan Academy encourages these casual, personal meetings. You frequently see teammates heading outside to talk through a technical decision. Anyone can set up a one-on-one with anyone, and it makes for an open team.

## TIP
A recent-ish experiment at Khan Academy is **T**eams **I**nitiatives **P**rojects, or **TIP**. It’s a way of organizing the team across different axes.

The gist: _Teams_ represent areas of deep domain expertise like design or mobile. _Initiatives_ are cross-functional major company goals, like “Launch an SAT guided study program”. _Projects_ are like mini-initiatives; they’re scoped at 2-5 weeks and involve 1-3 people.

I enjoy working within this framework. Everyone is on a functional team, so even though we’re spread across different projects we can pool our wisdom and make big decisions. Initiatives let us move toward big targets while projects help scope them down. My favorite part, though, is a side-effect: the support initiative.


## Support rotations
Every three weeks a group of developers enters their scheduled support rotation. On support, you kill bugs. Having a team dedicated to bugs means that everyone else can focus on moving ahead with their projects.

New developers at Khan Academy start on support. _Every company should do this._ In the past I’ve felt guilty for swimming through the codebase at a new job, but on support that _was_ my job! Tracking down bugs was a great way to learn my way around the stack while still contributing. As time went by I grew more confident and started taking on bigger bugs. It was a natural progression and made me confident in my ability to make changes[^4].


## Anyone can fix anything
At Khan Academy you don’t need permission to fix things. If you come across some outdated code or CSS rules that are out of order… it’s all yours[^5]. Be the change that you wish to see in the code.

I’ll admit that I was skeptical upon hearing this. “Fixing” a small bug can lead to chaos elsewhere if you’re not familiar with the system. As such, “anyone can fix anything” might have the corollary “anyone can break everything”. But it works out pretty well when _everything is code reviewed!_


## Code reviews
Coming from a freelance background, some of my biggest projects were completed [in isolation](http://xkcd.com/1513/). Working on a team again is exciting because I get to learn from my co-workers. [Khan Academy does code reviews](http://www.arguingwithalgorithms.com/posts/13-03-14-code-reviews) for every changed line of code, which is a fantastic way to share tricks and deep contextual knowledge. It also makes deploying less scary.


## Communication
As a growing team – especially one that strives to be awesome for our remote members – we’ve put a lot of thought into internal communication. We use Hipchat heavily, and try to be [transparent with our emails](http://bjk5.com/post/71887196490/email-transparency-at-khan-academy). We have a variety of tools that we use in different contexts, and as a result I have _way_ fewer emails coming through my inbox than I’m used to. It’s great.


## Lunch
Khan Academy has delicious catered lunch, which I’ve almost come to expect as a Silicon Valley tech brat[^6]. Something surprising about lunch at KA is that _nobody takes their lunch back to their desks._ Shortly past noon the office stops typing and shares a meal with one-another. It’s a pleasant part of the day, and it’s not usually encouraged as strongly as it is here.


## Speak now
Once a week we’re treated to a technical talk from someone on our team. These cover a broad range of topics; in my time here I’ve seen talks on functional reactive programming, prototyping as a mindset, mobile architecture, database architecture, and the most ludicrous bug [Alan](http://www.alangpierce.com/) has ever seen.

We recently introduced a related series called Demo Now. As our tech-talks gradually became more polished, ad-hoc demos to the entire product team fell by the wayside. Demo Now is an attempt to encourage unrefined demos of cool projects. When everyone is experimenting and pushing their boundaries it’s important to establish a culture that encourages showing unpolished work.


## Ship ship ship
Our dev setup guide is titled “Your first day: Grok culture and get shipping”. It guides new engineers through adding themselves to the [team page](https://www.khanacademy.org/about/the-team); many accomplish this on their first day. Strong ongoing mentorship and the support rotation keep the onboarding momentum in full swing.

In my first month I owned the development of multiple projects, tackled a big bug, mentored an intern and presented a technical talk to a full room. I’ve done my first (and second and third) proper A/B test, code-reviewed an accessibility project, and volunteered as an assistant at the [Learnstorm](https://www.khanacademy.org/learnstorm) finals and as a tutor at the [Khan Lab School](http://khanlabschool.org/). I even found someone to play music with after work!

We achieve so much because we relentlessly focus on action. As [Ben](http://bjk5.com/) writes in [Shipping beats perfection explained](http://bjk5.com/post/60760280107/shipping-beats-perfection-explained)[^7]:

> Is this the right philosophy for all products? Absolutely not. But educational content is so badly needed right now, and students are so hungry, that it’d be vain of us to think satisfying our own hunger for perfection is worth more than students’ needs. We’ll get to the complete mobile app. We’ll get to better coverage of computer programming content. Maybe we’ll even get to a fully immersive physics simulation. One day.

> If you’re the type who can’t “just” leave it better but must make code perfect, then you’re satisfying your own needs instead of learners’. You’re violating “shipping beats perfection.”


## Open source
We’re committed to open source at Khan Academy[^8]. If it doesn’t store private or sensitive data, [it’s in an open repo](https://github.com/khan/). When we make something extra-useful, we turn it into a [standalone library](http://khan.github.io/) for anyone to use.

It’s cool to work somewhere that loves open source. We’re receptive to experimenting with new technologies[^9], and splitting our code into modular bits allows us to keep trying new things. We also have all sorts of contributors catching bugs and adding features for us. It’s useful and inspiring.


## These are good ideas!
Just as code reviews disperse knowledge through a team, tech companies should share their organizational processes. Collaborating as a team of software developers is a yet-unsolved problem, but things get better every day.

So take this post as an organizational diff. If something seems healthy, merge it into your own culture and see if it compiles. If you think we’re missing something, let us know!

I’ve personally had a wonderful time getting to know the KA team, and am still as unbelievably excited to be here as I was on day one.


## Footnotes

[^1]: For reference, this isn’t the first time that Andy has [gone over the top](http://bjk5.com/post/92617394126/going-over-the-top).

[^2]: My heels were injured at the time but the walk seemed important so I didn’t mention it.

[^3]: Eventually I discovered that sitting was also an option and that I didn’t have to damage my body to talk to people.

[^4]: …without breaking everything.

[^5]: Of course, you can also delegate it to support if it’s a doozy.

[^6]: We also send a small group out to Castro Street every Friday on opt-in lunch dates. This is far less common as far as I’m aware.

[^7]: This post is almost two years old. Since then we’ve released a [full mobile app](https://itunes.apple.com/us/app/khan-academy-learn-math-biology/id469863705?mt=8) and quintupled our [computer programming content](https://www.khanacademy.org/computing/computer-programming)! Looks like this “shipping” thing is working out pretty well.

[^8]: Our webapp actually used to be [completely open](https://code.google.com/p/khanacademy/source/browse/trunk/?r=2)!

[^9]: For example, our first commit using [React](https://facebook.github.io/react/) landed one week after the first public commit of React itself.
