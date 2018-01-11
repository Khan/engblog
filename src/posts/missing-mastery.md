title: "The Case of the Missing Mastery"
published_on: January 24, 2018
author: Ian Reynolds
team: Web Frontend
...

**I was alone in Khan Academy’s normally cheery office,** my only company the long shadows cast by encroaching twilight through the second-story window and the buzzing of the single motion-sensitive light that flickered on and off above me. My desk was littered with Diet Coke cans, and `git log` would have told you reproachfully that I hadn’t written a single line of code since noon. The error report in front of me, titled _"Mastery progress reports 100%, even though circle not full"_, was confounding. It was from an middle-school aged user whose progress indicator for different mathematical "Missions" on Khan Academy was on the fritz. He would appear to lose mastery in the blink of an eye, and often there would be a complete mismatch between the displayed completion percentage and other indicators, like this progress ring that surrounds it:

<figure>
    <img src="/images/missing-mastery/wheel.png" alt="This user's progress percentage is at 82%, which doesn't remotely match the visual indicators around it."/>
    <figcaption>Something here is amiss.</figcaption>
</figure>

This kind of error can happen when rounding errors propagate or a cache tucks a stale value in with a bundle or fresh ones. But I had never seen anything this drastic or elusive. I was neck deep in logs and had six different test browsers open in six different BrowserStack tabs, and from Firefox Nightly to Internet Explorer 10, none of them allowed me to reproduce the error that the user was seeing, even when (with explicitly granted permission) I logged into his account.

Odd, for this bug was extraordinarily well-documented, with an excess of screenshots sent in over nine weeks all showing the same problem. These were interspersed with increasingly concerned messages from the user’s parents, who pleaded with us that these errors were discouraging their son from learning math and causing them to lose trust in our platform. I was determined to make this right, so I had carefully audited the code and concluded that no such bug could exist. I was as sure as I could ever be about a piece of code that it was error-free, and this bug was impossible.

<div class="bigquote">
    When you have eliminated the impossible, whatever remains, however improbable, must be the truth."
    <b>— Sherlock Holmes, The Sign of the Four</b>
</div>

I was ready to call it quits and head home for some quality work-life balance when [the voice of a famous and much more skilled detective](https://www.youtube.com/watch?v=-GnLDJAgrws) drifted unbidden through my head — and suddenly, I knew what I had on my hands. I didn’t want to believe what I was seeing. It hurt to think about. But there was no other explanation — head in my hands, eyes sore from monitor glare, I realized that I had been duped, confounded, and bamboozled by a sixth grader.

### Out of the support queue...

Let’s back up for a minute. When you support a software product used by millions of people every day, a bug affecting a single user is a rare and beautiful thing. Like a snowflake under a microscope, investigating it too closely might make it disappear forever, the heat from your muddling with the database or the browser console sufficient to melt it into nonexistence. Of the hundreds of support cases that come across Khan Academy’s desk each week, the ones representing serious defects in the code are usually reproducible and corroborated by several users. We’re very grateful for the people who take the time to report these, because we know that for every teacher, parent, or student that feels empowered to hop on [Zendesk](https://khanacademy.zendesk.com/) and tell us about their issue, there could be hundreds who will silently give up on our platform or possibly even badmouth it to their friends on the playground. Handling these tasks requires coordination between helpful users, community support, QA, and developers taking time from their primary focus for a week-long support rotation (that’s me!)

This bug was plucked from the queue during one such rotation. It was a P2, on a scale from P0 (the website is physically on fire) to P4 (we’ll get to this once we figure out this free world-class education for all thing). P2s usually bubble into the engineering support queue reproduced by QA, affecting multiple users, and related to a piece of the site that was updated in the last month or so. This was different: lone user, unreproducible, and apparently caused by code that had been in production for three years. It earned the P2 distinction only because it indicated that we were either losing data or handling it inconsistently — a very serious problem!

### ...and into the fire

And yet, as I dug deeper into the Python code that coaxed the user’s progress from the database and sent it to the browser, I realized that neither of those things could be happening. My initial suspicion was that the overall progress percentage and the finer-grained details used to render lesson-by-lesson progress data were taken from different places on the backend, and one was out of date. It’s not uncommon for the same kind of data to be represented and stored in multiple different ways depending on how and how often it needs to be accessed. But in fact, the percentage, ring, and skills breakdown were backed by the exact same piece of data from the server, and merely rendered three different ways. This challenged my initial assumption that the mastery levels were calculated incorrectly but the percentage was correct (as the user claimed), and I began to suspect that the mastery breakdown was right and the displayed percentage was wrong.

<figure>
    <img
        src="/images/missing-mastery/mission-progress.png"
        alt="The Missions progress pane showing an overall mastery percentage within a pie-chart like wheel, which fills as more subjects are mastered. To the right is a breakdown of progress by skill, and below a breakdown of skills by topic."
    />
    <figcaption>The Missions progress pane breaks down learner progress in a few different ways, but all are rendered from a single data source.</figcaption>
</figure>

I had a way to test this theory — I opened up BigQuery and asked it for all of the exercises that the user had ever completed on Khan Academy:

```
SELECT COUNT(DISTINCT exercise)
FROM [khanacademy.org:latest.ProblemLog]
WHERE id = "id_xxxx"
```

There were 381 results — this was a fairly active learner we were dealing with here. However, it was easy to verify in the Python shell that there are _way_ more than 381 exercises in sixth-grade math alone:

```
> from tutor.missions.frozen_mission import FrozenMission
> mission = FrozenMission.get_for_topic('cc-sixth-grade-math')
> sum(len(ex.all_assessment_items) for ex in mission.get_exercise_items())
# 3411
```

The logic that calculates the completion percentage has more to it than this, but completing `381/3411` or about 11% of all sixth grade math exercises will not get you anywhere near full mastery! One of two things was happening: either this user was the first in several years to encounter and report a serious error in our progress display code, or the screenshots were fabricated.

Not entirely willing to discount the first possibility but with the second looming large, I turned now to the front-end source code and read it again and again, but here, too, nothing was amiss. No rounding error, React lifecycle mishap, or SVG quirk could have caused this. A lump began to grow in my throat — it is quite a thing to accuse a user of intentional deception, but it was looking more likely by the minute.

At this point, I returned to the Zendesk thread and inspected the messages carefully. The incoming correspondence, though all originating from the same email address, was as alternately signed off by the user and his parents. Then, the smoking gun: of the dozen or so screenshots in the thread, _all of them had been sent by the child_, and usually in the morning, before the parent followed up around dinner time. It’s very possible that the parents had never seen their child’s progress disappear with their own eyes, and were relying on the before-and-after screenshots he provided to assess the situation. The perp? A kid barely old enough to use the internet unsupervised. The motive? Getting out of math exercises assigned by his parents. And the weapon of choice? The browser developer tools. When his parents weren’t looking, he was opening the "inspect element" pane in the browser and manipulating the progress text. Suddenly, I was sure of it.

<figure>
    <video
        autoplay
        loop
        src="/images/missing-mastery/cheat-screencast.webm"
        alt="A short video showing how a user could open the developer tools and change their displayed progress."
    ></video>
    <figcaption>
        The "cheating" process
         <a href="/images/missing-mastery/cheat-screencast.webm">(larger view)</a>
    </figcaption>
</figure>

But how to catch him in the act? Now exposed to the possibility of this kind of fiddling being reported as a real error, it was worth finding out how widespread it was, lest we spend even more support time on a deluge of ersatz bug reports. My coworker and team lead Brian, now as deeply invested in this tale of intrigue as I was, suggested using the [`MutationObserver`](https://developer.mozilla.org/en-US/docs/Web/API/MutationObserver) API, cooked up a few years back as a performant way to watch changes to a webpage as they occur. So I built a React component, [reproduced more fully here](https://gist.github.com/idreyn/a7e513b9ed4e31e2785fee007020db6d), that would render the displayed progress percentage and automatically revert and report any changes made to its value:

```
class MutationWatcher extends React.Component {
    componentDidMount() {
        this._observer = new MutationObserver(this.handleValueMutated)
        this._observer.observe(this._node, {
            characterData: true,
            subtree: true,
        });
    }

    componentWillUnmount() {
        if (this._observer) {
            this._observer.disconnect();
        }
    }

    handleValueMutated = () => {
        const {onMutate, tag, value} = this.props;
        const domValue = this._node.textContent;
        if (onMutate && domValue && value !== domValue) {
            onMutate(tag, value, domValue);
        }
    }

    render() {
        const {value} = this.props;
        return React.createElement(
            "span",
            {
                ref: ref => (this._node = ref),
            },
            value,
        );
    }
}
```

We installed this devious contraption into the Missions progress wheel, waited a few days, and, lo and behold, the user ID from our support ticket appeared in the logs, attempting to change his percentage from around 34% to 79% in a ludicrous leap of algebraic prowess. But where he was at least putting forth plausible numbers, we saw dozens more users attempting to change their progress to things like `100%`, `1000000%`, and `Jorge sucks!!!`.

<figure>
    <img
        src="/images/missing-mastery/bq-table.png"
        alt="A table of values that users attempted to input into their progress wheel. Most are higher percentages, like going fromr 14% to 20%, but some are ridiculous, like 18% and '100& real no fake'."
    />
    <figcaption>A sampling of the 26,720 mutation attempts to this DOM element that we saw in November and December 2017. These are representative, but relatively tame — we also saw several "over 9000"s, the entire first verse of the Imagine Dragons song "Believer", the phrase "i hope u r eaten by a whale", and many others that would be inappropriate to publish here.</figcaption>
</figure>

In retrospect, we should have seen this coming — there are already elaborate tutorials (think _Unregistered HyperCam 2_ and on-screen Notepad instructions) on how to "cheat" on Khan Academy, e.g. by fiddling with problem hints with one’s internet connection disabled. ["You’re only cheating yourselves!", we cry out from afar](http://engineering.khanacademy.org/posts/no-cheating-allowed.htm), but the middle school math students of the world take no notice — they are tech-savvier than we remember ourselves being, willing and able to break the technology we provide them with to befuddle their parents and teachers. Feeling somewhat shaken, we reported our findings to the user’s parents and closed the ticket.

### What we learned

Khan Academy is in the enviable position of expecting relatively high levels of good faith in our interaction with our user base. We offer a free service, don’t take credit card numbers or collect highly sensitive information, and by and large cooperate productively with students, teachers, and parents on the great project of spreading knowledge. Put simply, there’s comparatively little to be gained by hacking our website or engaging in social engineering with us. This time, though, I made the fatal mistake of underestimating the lengths to which a middle schooler will go to avoid doing his math homework, including months of carefully crafted deception and even (to my inner delight) surreptitious use of the developer tools to avoid doing the work assigned by his parents. I would be quite upset with this kid if I he didn’t so closely resemble my younger self, glancing over my shoulder and prodding config files on a 2000s-era eMac in a fruitless attempt to get out of hours of _Type To Learn_.

Beyond giving me a developer tall-tale to recount in increasingly elaborate detail over lunch, this episode was cause for reflection on different aspects of Khan Academy’s product and practices. KA is a non-profit, but even here time is (other people’s) money, and it’s sobering to think that without really intending to, one middle-schooler cost our organization a day or so of Bay Area Developer Salary. A distributed version of this "attack" intended to lower the signal-to-noise ratio of a software company’s support queue could be immensely frustrating, and I imagine that a well-fabricated bug reported convincingly by two dozen accounts could send a small-medium startup scrambling for a week. It’s also disheartening to see an apparently ambitious and technically-minded kid go to great pains to avoid learning about math from our product. Yes, no sixth grader really wants to learn factorization in the same way they want to play Flash games (are the kids still doing this? help!) but an idealized Khan Academy math lesson would offer the same sense of discovery and even subversion that reverse-engineering the teaching tool gives them — or, [whispers Neal Stephenson in my ear](https://en.wikipedia.org/wiki/The_Diamond_Age), might even condone such activity explicitly.

Finally, while we try to cultivate a mindset of user empathy while chipping away at often vexing and mundane support tasks, I confess that while unraveling this mystery, my empathy was with the teachers of the world — those brave souls who show up every morning with an open mind and heart, knowing full well that by the end of the day, they’ll be subject to all kinds of deception and manipulation at the hands of those that they’re being underpaid to help. While I’m proud to work for a company so invested in the future of education, it is a great privilege to be able to decide that the shenanigans of one sixth grader, once in a while, are quite enough.
