title: "Receiving feedback as an intern at Khan Academy"
published_on: October 26, 2015
author: David Wang
team: Infrastructure
...


![](/images/receiving-feedback/feedback.jpg)

When my first piece of code was reviewed at Khan Academy, my mentor [Dylan](http://www.dylanv.org/) prefaced his comments with the following: 

![](/images/receiving-feedback/phab.jpg)
(Kamens’s post [here](http://bjk5.com/post/3994859683/code-reviews-as-relationship-builders-a-few-tips), Tom’s post [here](http://www.arguingwithalgorithms.com/posts/13-03-14-code-reviews))

And to be honest, I chuckled when I read that: I had already expected seeing a bunch of red during my first code review, and if I received a [ShipIt](/images/receiving-feedback/shipit.jpg) on my first go without any comments whatsoever, I would’ve questioned the efficacy of the code review process at the company :). I asked Dylan why he felt the need to open his code review with this lead-in, and he described his experience with his first code review as an intern. It would have been discouraging to receive so much critical feedback all at once, had he not received the same piece of advice. Somewhere in the middle of that conversation, he let me know that the quality of my code had little to do with the quality of my person, and that code critiques != character critiques.

This interaction with Dylan led me to wonder about feedback - as a whole in addition to code feedback - more than once throughout the course of the summer. What is Khan Academy’s view on giving feedback in general, and giving feedback to interns in particular? Why does it hurt so much to receive criticism, even when it is delivered with the best of intentions? Why is it that we feel we have to tread so carefully when we’re delivering it? 

Khan Academy and feedback
---

While every one of these questions can have an entire blog post devoted to each of them, I’m going to just give a brief overview of what I’ve discovered on all of them here. First, regarding KA’s view on feedback, after chatting with managers and poring through docs, I discovered a page on the company wiki about developing a feedback culture. Perfect! It said that the company views feedback as a gift: 
it’s given with the best of intentions 
it should be considered a positive sign that my colleagues are willing and choose to invest in me (and my development). 
All cheesiness aside, I think I’ve come to really appreciate that metaphor as much as that other one about [today being a gift](http://www.brainyquote.com/quotes/quotes/b/bilkeane121860.html). I can pinpoint instances, both in work and in school, where I’ve gotten the impression that people have given up on me. And to be honest, being ignored for me is a much worse feeling than having criticism barraged at me. In addition to this metaphor, KA views a feedback culture as one that is regular / ongoing and 360 degrees, where anyone feels comfortable asking for feedback from anyone else.

And for interns? As part of the [mentor/menteeship experience](http://bjk5.com/post/23266999170/how-intern-mentorship-works-at-khan-academy) at KA, I had weekly 1-on-1s, where I checked in with my mentor and talked about how the last 7 days have been, and whether I was getting what I wanted out of my summer experience. While it’s acknowledged that these 1-on-1s are a good time to exchange feedback between mentor and mentee, it’s not always explicitly stated that that is one of the goals. Thus, something I’m very glad I did was at the end of each 1-on-1, asking for one actionable piece of information that I could change or focus on for the next week. 

In addition to the weekly 1-on-1s, one thing I’m glad Khan Academy does is offer a more formal midpoint evaluation for each of its interns. And from the context of a single internship, the midpoint evaluation is (in my opinion) more valuable than the final evaluation: it’s less a performance evaluation (where we discuss how us interns have performed compared to what has been expected of us) and more a coaching opportunity. By getting recommendations on where we can improve, we can take steps towards playing at a higher level. And if there’s 6 weeks left to an internship during its midpoint compared with 0 at the end of the internship, the feedback given at the halfway mark allows for greater growth.

The process as a whole
---

In general, I've often asked myself why receiving feedback is so hard. After introspecting, talking to some folks, and [digging](http://fsap.cornell.edu/cms/fsap/resources/upload/How-to-Receive-Critical-Feedback.pdf) [around](https://open.buffer.com/how-to-give-receive-feedback-work/), I think that there are three things at stake: 

1. We feel wronged if a piece of feedback seems inaccurate. This leads to a host of possible reactions: we deem the feedback as simply wrong, or maybe we believe that the person giving the feedback has made unfair assumptions about the motivations that drove our behavior.
2. We might reject the feedback because of how we feel about the giver. Perhaps it was unsolicited, perhaps we believe that person doesn’t have credibility in what they’re critiquing us on, perhaps the feedback hasn’t been communicated well, or perhaps we’re unsure of the intentions of the feedback giver himself.
3. We perceive feedback as a threat: it might cause us to question our relationship with ourselves. One of our core human needs is to be accepted the way we are, and this is so ingrained in us that signs of rejection (through critical feedback, for instance) lead to the same flight-or-flight response in our limbic systems as actual threats to our physical safety.

As to treading carefully when giving feedback, I think it's a matter of taking the cautious route after briefly taking the perspective of the feedback receiver. We understand how difficult it is to be on the opposite end, and we lean towards a soft approach to make the experience more positive and less stressful. 

Lastly, I believe that after all this discussion on feedback and constructive criticism, we should not underestimate the value of compliments. Not because they’re used as part of the ["feedback sandwich" technique](http://www.aafp.org/fpm/2002/1100/p43.pdf) to make people more open to feedback, but because it’s important for us to know when we’re doing things correctly and what we could be doing more of. To borrow [the wise Ben Kamens’s words](http://bjk5.com/post/3994859683/code-reviews-as-relationship-builders-a-few-tips), “If your team isn’t taking advantage of the chance to also acknowledge good work and the little sparks of genius that pop up here and there, you’re doing it wrong.”

Takeaways
---
Looking back at my time at KA, I’m glad that they’ve been willing to throw me in the deep end and hold me accountable for the work I’ve done. During these 12 weeks, I broke part of the site for the greater part of a day, gave a company-wide presentation on social psychology of all things, and helped build [a recommendation system](http://data.khanacademy.org/2015/09/so-you-want-to-build-recommender-system_8.html) for the company hackathon. And in the spirit of growth, I’m glad that my mentors Dylan and Sergei have encouraged me to try things that are outside of my comfort range, and have provided guidance, support, and feedback across all things technical and non-technical.

When people ask me what I learned from my internship or what my most major takeaway was, I tell them the meta lesson I’ve reinforced in myself about learning, which can be described by any of the following synonymous statements: 

- To quote the eloquent [David Hu](http://david-hu.com/2015/01/14/khantemplations.html), “Assume you’re stupid so you can always be learning.”
- From Zen Buddhist Shunryu Suzuki on adopting a beginner’s mindset, “In the beginner's mind there are many possibilities, but in the expert's mind there are few.”
- With my own words: frame feedback as opportunities for coaching instead of evaluation, and frame mistakes as learning experiences instead of failures.

In case you were wondering, Dylan’s comments to me in my first code review were to write a more descriptive commit message and test plan :). I hope I received the feedback well.

