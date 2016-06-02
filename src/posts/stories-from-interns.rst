title: "Stories from our latest intern class"
published_on: December 21, 2015
author: 2015 Interns
team: Web Frontend
...

We sent an email out to all of the 2015 interns in early November, shortly after they had left KA. The email said that we were hoping to write a blog post on our intern class, and asked them “do you have a most memorable moment, a project you liked, a lesson learned, or really anything you'd like to share with the world in this way?” Here are four responses...

Chelsea Voss: Mobile!
=====================

I had a blast interning at Khan Academy last summer! I learned a lot during those few months.

Beyond the different projects I got to work on, one additional chance to learn something new was at the Khan Academy Healthy Hackathon – I’d like to share how this hackathon became my introduction to mobile app programming.

One of the things that I find seriously awesome about Khan Academy’s computer programming curriculum is getting to see the awesome JavaScript projects that learners come up with when given the chance to create. If you take a look at that page, you’ll find puzzle games, 2D art, interactive stories, and more – it’s great to see all of these ideas made programs, and to see so many people having fun learning to code.

For our hackathon project, fellow interns Neel Mehta, Sherman Leung, and I built an app that would browse and play these JavaScript projects from a phone. 

First, we prototyped, brainstorming several different designs for what such an app might look like, thinking about different layouts and ways the look of the UI could go…

.. image:: /images/stories-from-intern-class/chelsea.jpg
    :alt: A picture of Chelsea laying her head down on a bunch of paper.
    :class: align-center
    :target: /images/stories-from-intern-class/chelsea.jpg

.. class:: caption

	Figure 1: Late-night prototyping

…then it was build, build, build! I had never built a mobile app before, so it was pretty exciting to work on something like this from scratch. Neel had worked with Ionic before, and got me up to speed with the framework – learning was faster with tutelage!

.. image:: /images/stories-from-intern-class/screenshots.png
    :alt: Screenshots of the mobile app
    :class: align-center
    :target: /images/stories-from-intern-class/screenshots.png

.. class:: caption

	Figure 2: It lives!

The resulting app is actually pretty fun to use, since the JavaScript projects themselves are so fun. The app isn’t released, but the code for this project is up at GitHub. I’m proud of what we made, and I’m happy that I got this opportunity to learn about something new!

Alexander Irpan: Mail Time
==========================

I had a really good time at Khan Academy. The work was interesting, and it felt awesome to directly contribute to such a great site. I could go on and on about the fun things we did outside of work, but I wanted to share the craziest developer experience I had this summer.

My first intern project was to backup Khan Academy’s mailing list data. Khan Academy uses SailThru to manage most of its emails. (It turns out KA has a lot more mailing lists than you would think.) At the time, most lists were only stored on SailThru’s servers, so my project was to build a cron job that would save those mailing lists to our local Google Cloud Storage.

After building the whole backup system, I manually triggered a backup to test it out. The next day, I checked the logs, and found out it failed because requests to Sailthru’s API were sent through our internal developer client, which mocks all calls to third party services. The only way that could happen was if is_production() returned False in production.

Wait, what?

.. image:: /images/stories-from-intern-class/wat.jpg
    :alt: A large yellow duck in a river with the caption WAT.
    :class: align-center

.. class:: caption

	Figure 1: Wat

I dug through the other code that used the client, and found an existing cron job with the same problem. Taking a tip from a dev presentation on debugging, I binary searched on dates and found out that job stopped working 9 months ago.

.. image:: /images/stories-from-intern-class/meme.gif
    :alt: A reaction shot of Robert Downey Jr looking confused.
    :class: align-center

.. class:: caption

	Figure 2: WAT

Okay, wow, that was really bad, especially because no one knew about it until now. With the date, I could take advantage of source control and browse all commits that landed into production that day.

Eventually, I tracked the bug down to a config error. Khan Academy runs on Google App Engine, which supports splitting apps into modules. The cron jobs ran on the modules for backend processing, and one of the checks for is_production() was not set in that module’s config file. After fixing that, both the old cron job and the one I added started working again. Luckily, the damage from the bug was minor, since the vast majority of code using SailThru ran on modules where is_production() correctly returned True. Any lingering issues got fixed by the next job run.

All in all, it was some of the best detective work I have ever done for debugging.

Phillip Lemons: KLS
===================

My most memorable experience at Khan Academy was the annual hackathon where I got to spend the better part of the week working on a sign in system for the Khan Lab School (KLS). At KLS the students have a certain amount of flexibility on when they can arrive at school in the morning. While this flexibility is great for the parents and the students, it makes keeping track of attendance a big hassle for the teachers. I teamed up with Vishesh, another intern, to solve this problem by building an RFID sign in system that would be hooked up to a web app that parents could use to sign in their kids. The hope was that parents would be able to use RFID cards that they had already been given to get inside the building to also sign in their kids.

The first thing Vishesh and I did was get to work on designing the web app. We figured that we would need a main page that would allow parents to sign their kids in, an admin page for teachers to manage who was allowed to sign in which students, and a page that gave a list of kids who were currently signed in. I spent the next few days learning the ins and outs of AngularJS while I created the admin page. Even though what I completed didn’t amount to much, by the end I had a better insight into what it took to create a web app from scratch.

Unfortunately, I was unable to go to work over the weekend so I didn’t get to see the final product. Nonetheless I was still glad I got to work on the project. I think events like this really show that Khan Academy really practices what they preach. Khan Academy follows the idea that “anyone can fix anything” and they really want their employees to always be improving themselves even if it means taking a few days off normal work to experiment and try new things.

Vishesh Gupta: Saying Goodbye to an Old Tree
============================================

One of the things that makes KA so great is the fact that everyone really cares. About the mission, about the learners, and also about each other! All that spontaneous love in the workplace makes it impossible not to get swept up, and us interns were no exception!

In the middle of my internship, all of us received the very sad news that intern mama Marcia was leaving us :(

Marcia was such an inspiration not only because of her mad technical skills, but also her positive and caring personality.

On Marcia's last day, us interns banded together to do some spontaneous acts of kindness.

It all started when Shannon came to me in the morning and said "Let's take Marcia out to tea/dinner and give her a card!" 

I made the mistake of pinging the intern room @all and saying "We're writing Marcia a card!"

Of course, Marcia hangs out in the intern room on HipChat and she immediately waved to all of us. So that plan was a bust, and everyone was bummed/mad at me. However, where there is adversity, KA interns rise to the challenge! We decided that we'd give her a card, and then some. 

We pretended that no card was going to happen since I'd ruined it, and got to work.

First, Shannon got us all started with some amazing artwork making a badge for Marcia of a mama duck and little ducklings. Will made this available digitally online!

Then Alex suggested we get some balloons and even offered to get them himself, and Neel decided to add his inspiration of a KA flag flown at half mast. 
We all wrote her a card, and completely filled her desk with post-it notes of appreciation.

Then we promptly got out of the way so Marcia could enjoy the spectacle. After she came out of her 5 o'clock meeting, she saw her desk full of appreciative goodies, and was completely taken aback!

You can see the results for yourself!

.. image:: /images/stories-from-intern-class/group-pic.jpg
    :alt: A picture of all the interns gathered around Marcia.
    :class: align-center
    :target: /images/stories-from-intern-class/group-pic.jpg

What was so beautiful about this experience was watching all of us support each other in this expression of generosity and kindness - the minute one of us started the ball rolling, we all jumped on and just spontaneously added on ideas to make this such a heartfelt farewell.

It's this kind of fun that makes working at KA a blast! 

