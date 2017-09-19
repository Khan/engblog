title: Tips for giving your first code reviews
published_on: September 18, 2017
author: Hannah Blumberg
team: Mobile
...

At Khan Academy, (nearly) every piece of code that goes into our codebase has been reviewed by at least one other person. Code reviews help us keep code maintainable and clean, catch big-picture issues early, build a shared understanding of the codebase, and socialize new engineers. To learn more about our code review beliefs and practices, check out some oft-cited blog posts [here](http://bjk5.com/post/3994859683/code-reviews-as-relationship-builders-a-few-tips) and [here](https://www.arguingwithalgorithms.com/posts/13-03-14-code-reviews).

When I joined Khan Academy as an intern, I read a ton of documents describing the purpose, importance, and process of code reviews. Since I was a college student at the time and was accustomed to receiving feedback from professors, I felt prepared to have my code reviewed. I did not feel prepared, however, to begin reviewing code myself.

Reviewing other people's code – especially code written by smart, experienced engineers – can be really intimidating. *What could I, an intern with just a few computer science courses under my belt, contribute?*

Now that I have completed my internship and have been full time at Khan Academy for over a year, I know that everyone – even the newest of interns – can add value to the code review process.

To help you get started, here are some concrete suggestions for reviewing code for the first time:

---

## 1. Ask questions

This is probably my favorite piece of advice for getting started with code reviews. Code review comments do not have to be direct requests for changes. You might ask the author to describe the trade-offs they considered, explain how a piece of code works, or provide more context on the project.

Asking questions gives you the opportunity to learn and gives the author the opportunity to articulate, clarify, or challenge their thinking. It may also help the author identify areas of the code that are less clear and consequently harder to maintain.

![Example of asking questions](/images/tips-for-code-reviews/ask-q-1.png)

If you find a mistake or identify an area of improvement while doing a code review, you should absolutely feel empowered to share that directly. It's easy, though, to second guess yourself, especially when reviewing an experienced engineer's code. If you find yourself about to delete a code review comment, try rephrasing it as a question! Asking a question is often just as valuable to the author, and it may feel a little easier to post.

![Example of asking questions](/images/tips-for-code-reviews/ask-q-2.png)

## 2. Try pair reviewing

This is a tip I learned from one of our engineering managers, Celia La. Ask your mentor or onboarding buddy (or anyone else on your team) if they would be willing to do a "pair review" session. You and your teammate can sit together or screen share as you work through a code review together.

By watching and asking questions, you can learn more about your teammate's process and techniques.

If you are not able to set up a pair review session, you can also look at code reviews that your teammates have done for one another. Although you may not learn your teammates' processes, you will still get a sense of the type of feedback they give one another.

## 3. Review code in your IDE

This tip comes from former engineering lead and my onboarding buddy, Charlie Marsh. In Charlie's [blog post](http://www.crmarsh.com/code-review/), he describes the benefits of reviewing code in your own integrated development environment (IDE).

At Khan Academy, we typically review code through [Phabricator](https://secure.phabricator.com/)'s web interface. The [`arc patch`](https://secure.phabricator.com/book/phabricator/article/arcanist/) command allows you to apply the changes in a code review to your local copy of the codebase. From there, you can explore the code in your own IDE.

As Charlie describes, reviewing code in your IDE allows you to put yourself "in the author's shoes" and catch things you might not see in the web interface. You can navigate more naturally between files and see changes in the context of the codebase.

Reviewing code in an IDE also allows you to try out ideas before you share them so that you can suggest changes with more confidence.

##4. Comment on anything

When you are doing your first few code reviews, you should feel free to comment on anything. 

For example, you should feel comfortable pointing out small fixes that are not blocking. Although you will likely move away from these comments over time, they can help you build confidence.

If you leave "nit" (short for nitpick) level comments, it is best to distinguish them from more crucial fixes. I generally like to add the word "nit" before these comments to communicate to the author that they are not blocking.

![Example nit comment](/images/tips-for-code-reviews/comment-on-anything-1.png)

Borrowing from Ben Kamens' [blog post](http://bjk5.com/post/3994859683/code-reviews-as-relationship-builders-a-few-tips), you should also feel free to "point out the good stuff" in your comments. You might thank the author for a really helpful comment, call out a clever (but clear!) technique, or compliment the thoroughness of their testing. These comments encourage the author to continue doing the "good stuff" and help to build relationships.

![Example compliment](/images/tips-for-code-reviews/comment-on-anything-2.png)

![Example compliment](/images/tips-for-code-reviews/comment-on-anything-3.png)

## 5. Review a peer's code

Even if you are a very new or junior engineer, you can add value to any code review. That being said, it can be extra intimidating to review code written by experienced engineers. To become more comfortable and build your confidence, try finding someone who you consider a peer (maybe a fellow intern or someone who started around the same time as you) and ask if they would be interested in having their code reviewed by you and vice versa.

Reviewing a peer's code can be a more comfortable introduction to code reviews. It will also give you extra opportunities to practice! Keep in mind that you do not need to be the sole reviewer of your peer's code; you can leave comments without approving or rejecting the change.

---

Reviewing code is a skill that develops over time. The first step to improving is to just get started!

