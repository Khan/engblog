title: "Schr\u00F6dinger's deploys no more: how we update translations"
published_on: October 12, 2015
author: Chelsea Voss
team: Infrastructure
...


If you’re trying to bring the best learning experience to people around the world, it’s important to, well, think about the world.

Khan Academy is translated into [Spanish](http://es.khanacademy.org/) and [Turkish](https://tr.khanacademy.org/) and [Polish](https://pl.khanacademy.org/) and more – and this includes not only text, but also the articles, exercises, and videos. Thanks to the efforts of translators, learners [around the world](http://international.khanacademy.org/) can use Khan Academy to learn in their language.

!["You can learn anything" in several languages](/images/translation-server/language_collage.png)

Internationalization is important. Internationalization is also an engineering challenge: it requires infrastructure to mark which strings in a codebase need to exist in multiple different languages, to store and look up the translated versions of those strings, and to show the user a different website accordingly. Additionally, since our translations are crowdsourced, we need infrastructure to allow translators to translate strings, to show translators where their effort is most needed, and to show these translations once they’re ready. There are many moving parts.

When I arrived at Khan Academy at the beginning of this summer, some of these moving parts in our internationalization infrastructure were responsible for most of the time our deploys took to finish. One of the things I accomplished this summer during my internship here was to banish this slowness from our deploy times.

The problem
---

Whenever we download the latest translation data from [Crowdin](http://crowdin.com/), which hosts our crowdsourced translations, we rebuild the *translation files* – files which the Khan Academy webapp can read in order to show translated webpages. The next time an engineer deploys a new version of the webapp, these new translation files are then deployed as well.

Uploading files to Google App Engine, which hosts the Khan Academy website, is usually the slowest part of our deploys; the translation files are big, so translation files in particular are a major contributor to this. So, whenever the latest translations are downloaded and rebuilt, the next deploy would be quite a bit slower while it uploaded the changed files.

Furthermore, since it’s not always the case that translation files have been rebuilt recently, as an engineer it’s hard to tell whether the deploy you’re about to make will be hit with Translations Upload Duty or not. Sometimes deploys would take around 30 minutes, sometimes they would take around 75 minutes or more:

![Graph of deploy times, before translation server](/images/translation-server/graph_before.png)

*The previous state of affairs – 30-minute deploys punctuated by 75-minute deploys. There are a couple of lulls in this graph where deploys are consistently near 30 minutes: these reflect times when our download from Crowdin was not working.*

The fix
---

We decided to rearrange the infrastructure around this so that instead of uploading translation files to Google App Engine (GAE) along with the rest of the webapp, we would upload the translation files to Google Cloud Storage (GCS) in a separate process and then modify the webapp to read the files from there.

Implementing this required making a few different changes, and the changes had to be coordinated in such a way as to keep internationalized sites up and running throughout the entire process:

1. Upload the translation files to GCS whenever they're updated.
2. Change the webapp to read translations from GCS instead of from GAE.
3. Stop uploading the now-unnecessary translation files to GAE.

These steps by themselves are enough to implement the change to make deploys faster, but we also want to make sure that this project won't break anything – so instead, the steps look something like:

1. Upload the translation files to GCS whenever they're updated. *Measure everything. (How much will this cost? How fast will the upload be?)*
2. Change the webapp to read translations from GCS instead of from GAE. *Measure everything. (How much slower is this than reading from disk? Will requests be slower?)*
3. Stop uploading the now-unnecessary translation files to GAE. *Measure everything. (Do translated sites still work?)*

One thing I experimented with while working on this project was keeping a lab notebook of sorts in a Google Doc; this was where I went to record everything I learned, from little commands that might be useful later, to dependencies I had to install, to all of the measurements I ended up making. This was a good decision. This habit and these notes did in fact turn out to be useful, frequently.

![Mythbusters' Adam Savage: "Remember kids, the only difference between screwing around and science is writing it down."](/images/translation-server/science.jpg)


The consequences
---

### Deploys are faster!

I deployed the last piece of this project on August 20, 2015. Deploy times have been more consistent since: the graph of deploy times is free of the spikes that previously indicated translation uploads.

![Graph of deploy times, after translation server](/images/translation-server/graph_after.png)

*Before and after; the change happened on 8/20.*

### Translations can be updated independently!

Now we don't require an engineer to deploy new code in order to change the translations that appear on Khan Academy – translations are updated by a separate job. Also, this opens up new possibilities – we can now do exciting things like updating our languages independently of each other, and make it so that the time between when a translator makes a translation and when that translation shows up on the main site becomes even shorter. Our internationalization efforts will be able to push forward even faster!
