title: "Fun with slope fields, css and react"
published_on: August 05, 2015
author: Marcos Ojeda
team: Web Frontend
...

A while ago, we needed to send out a notification to all our [LearnStorm](https://www.khanacademy.org/learnstorm) winners inviting them to the Finals event in Mountain View. It's a big deal! Only *200 Students* from all of the bay area got invited to the event.

Because most (if not all) of them were under 13, we couldn't email[^coppa] them so we needed to make something that would catch their eye the next time they visited the website.

And, as with the most fun projects, there was very little time to actually work on this: from start to finish, this was bounded to around three days, so in terms of design, it would need to be nice, but it couldn't be 100% totally new shiny design work: compromises would need to be made.

[^coppa]: let's put it this way, i am *not* a lawyer, but i *do* know that [COPPA](https://www.ftc.gov/tips-advice/business-center/guidance/complying-coppa-frequently-asked-questions) prevents everyone from collecting any personally identifiable information for anyone under 13 (that includes email addresses, but it's totally fair game to ask for their parents' address).

## step one: notifications

You have probably gotten a notification on Khan Academy before, and readily dismissed it like so much purple rain.[^purplerain]

[^purplerain]: > ... "Purple rain," later the title of a 1984 song, album, and film (and the tour that supported both the album and film), from the artist Prince. Although it is not known if there is actually any connection, both Mikel Toombs of The San Diego Union and Bob Kostanczuk of the Post-Tribune have written that Prince got the title directly from "Ventura Highway". Asked to explain the phrase "purple rain" in "Ventura Highway", Gerry Beckley has responded: "You got me". (via [wikipedia](https://en.wikipedia.org/wiki/Ventura_Highway#Legacy))

![a default ka notification in portuguese](/images/slopefields/Mjew.png)

And why not, it's certainly... *distinctive*, but that purple rectangle is not exactly injecting anybody's retinas with "notification delight," so step one was figuring out how to make the notifications look nicer.

## step two: learnstorm?

The next step of research was teasing apart learnstorm's visual style: the [slope field](https://www.khanacademy.org/math/differential-equations/first-order-differential-equations/differential-equations-intro/v/slope-field-to-visualize-solutions) motif is the heart of learnstorm's identity.[^sloperefresh] In making this notification banner I knew that I wanted echo the identity, but from another angle or perspective. To do that I would need to grok that slope field a little better because already at this point, i knew i wanted to incorporate it into the banner in some way.

[^sloperefresh]: A refresher: a slope field (naturally) is the slope (and often magnitude) of a differential equation plotted along a grid. You can use slope fields to build intuition about the nature of first order differential equations, their tangent points, and so forth.

![the learnstorm page](/images/slopefields/JGuX.png)

But wait a second... math??? we can't even [center a div](http://howtocenterincss.com), how can we possibly do anything with slope fields?

Actually, let's step back even further... differential equations? what's a slope field again?

### step yak: a math detour

My thinking went: our contest is rooted in differential equations, it'll probably help to revisit them. [^1803revisited]

[^1803revisited]: slope fields make up the lion's share of the early weeks of a diff eq class and are by far the least interesting part: all the applied and domain-specific uses of differential equations end up being wayyyyy more interesting.

And after a brief while you find that a slope field is basically what it claims to be: the slope of a differential equation calculated at periodic points on a plane. And differential equations only express *the feel* of an equation, not exactly what it looks like because they're missing several constant values.

So for a plain ol' circle *y^2 + x^2 = 1*, you'd get *y' = -x/y + c* (which you could find via [implicit differentiation](https://www.khanacademy.org/math/differential-calculus/taking-derivatives/implicit_differentiation/v/implicit-differentiation-1)), but again' all that's saying is that the slope for this differential equation at *any point* is the *x* value divided by the *y* value times negative one plus some arbitrary *c* (which, for us, we'll just pretend is zero). For whatever point, you just enter x and y into that equation and *that's the slope.*[^slopedetour] neat!

[^slopedetour]: in a blog post full of detours, i should point out how satisfying it is to end up at an early 'solution' that requires the simplest of computations.

But when we attempt to draw this (say on paper or digitally), we don't actually want *y'*, we want whatever **direction** *y'* corresponds to so we can point a triangle in that direction. With a simple equation like *y' = -x / y* , we run into this problem where for zeroey *y* values we have infinitely positive or negative *y'* and what do you do with that?

Well, `Math` to the rescue! Specifically the standard [atan2](https://en.wikipedia.org/wiki/Atan2) method which returns the angle in radians (from the origin) for the point at *(x,y)*. It's a special function which calculates the arctangent *but* is smart enough to compensate for zero denominators in pretty much the same way you would.[^divzero]

[^divzero]: because it takes the denominator as an argument, `atan2` avoids the standard movie trope of "tricking" the computer by having it try to divide by zero.

Looking at the `atan2` implementation, you find that it does the kind of "intuitive limit-ey division" that you're often asked to do in the first weeks of a calc class. Instead of `NaN` you get ±π/2 and instead of 0 you get 0 or π. It's great! And it's *exactly* what we need. For a given *(x,y)* pair, you get a corresponding radian value.

Also, recall, we have a diff eq that is given by *y' = -x/y*, we can use `atan2` to find the slope of each point on the plane.[^atan2deets] Ok, we know how we might use this, now we just need to get started actually drawing it.

[^atan2deets]: specifically, you're going to ask for `radians = Math.atan2(y, -x)`

## step two: prototyping

The first step of prototyping this was a small python script that i wrote for [PlotDevice](http://plotdevice.io/)[^plod]

[^plod]: plotdevice is great! it's a python-based drawing application i'm real fond of. Take a look, you might like it! If you like the idea behind processing but you're whatever on java, then you'll probably enjoy it.

Again, remember that i didn't have too much time to work on this project, I needed to be certain that I could fake out a new spin on learnstorm identity so if I began to run out of time, I could, at the very least, render a cute static image as the background for the banner.

![a first sketch with nodebox](/images/slopefields/HB9P.png)

Well, this looks promising! But the day is young: could i... animate this?

Stepping back, let's do a small crit[^crytime] here: part of what makes the learnstorm identity cool is that you get this round vibe *even though* everything is stuck on a grid. Breaking the grid in this case would not only require me animating each dart but animating them along circular paths which, i mean, would look *awesome* but... umm... maybe let's save that for LearnStorm 2016 when we have more time...

[^crytime]: a crit (not *[that crit](https://en.wikipedia.org/wiki/Criterium)*) is a time to look over design work with your peers, evaluate and discuss what's succeeding, what's not (and for both, *why*), and offer suggestions for how it could communicate what it needs to most efectively.

Also, let's take this moment to visibly and vocally *Pivot*.[^sandhillfootnote] Because i spent the morning trying to figure out how to procedurally draw slope fields, i *already* have (a sort of) infrastructure for generating slope fields, but the problem is that i want something i can easily animate. Time for a new differential equation!

[^sandhillfootnote]: I mean, we're *already* in the bay area, what sort of blog post from a startup doesn't enthusiastically and vigorously talk and rationalise pivoting as a way of life.

Maybe we can just make something up, something... real easyish, like...

*y' = x + y*

and if you plot this out correctly, you end up seeing something like this:

![swooooop!](/images/slopefields/sdKS.png)

but say you make a mistake[^herpderp] and remove that super "interesting" `atan2` we just learned about, you get something... *novel.*

[^herpderp]: who does that? *i* wouldn't do that. who would do such a thing?

![it's like a wave](/images/slopefields/4TcL.png)

What's happening is that if you pick a row or a column, you find that the rotation values are monotonically increasing but at a slightly different starting point and because the atan2 isn't around, the darts just continue rotating and rotating...

Ok, so now we have a moderately intriguing slope field which, let's be honest, is something of an accidental slope field at the moment.

So, back to our project: how do we animate it? Well, the neat thing again is that if you walk along the y axis (or x axis) every dart rotates however much you moved. So let's say you start with that static image above and, for each point, you increase *y* or *x* in that *y' = x + y* by a little without actually moving the point, they *all* appear to rotate just a little bit more counterclockwise, like so:

<iframe src="http://gfycat.com/ifr/LinearWideeyedHorsefly" frameborder="0" scrolling="no" height="150" style="-webkit-backface-visibility: hidden;-webkit-transform: scale(1);" ></iframe>

Which is great and hypnotic. But how do we incorporate this into the announcement banner?

My first instinct was animated gif: but the gifs ended up being multi-megabyte monstrosities and movies no better. Even the gyfcat embed up a few paragraphs ago is, at worst, 4M and, at best, a 400k webp movie. and the quality... i mean, you have eyes, just *look* at it... it's let's just say, not the best. Ugh, this is not a very complicated thing! it's just a bunch of triangles rotating round and round and...

## wait a minute

Instead of actually rendering some background image and scaling it up, why not do the animation in the browser using a technique you may have heard of called [Dynamic HTML](http://en.wikipedia.org/wiki/Dynamic_HTML).[^dhtml]

[^dhtml]: "...a more elegant weapon for a more civilized age" -- [alec guiness](https://www.youtube.com/watch?v=0aRtupiY9Dw)

## staggering animations

Here's how I would roughly do it: i would use a *single* dart image, lay out a bunch of them on a grid and then rotate them with css. At first i thought

> I can set each dart's from-rotation and it's to-rotation dynamically!

And i would use `css` to start each dart's animation at, say, some radian value, setup a keyframe animation to rotate 2π radians over some fixed time scale and then call it a day. Genius!

But because[^pleasemaildan] there's no easy way to create a parameterized css animation with arbitrary start/end points and because it *felt* wasteful to specify a new animation starting at some radian value going a full 2π for all radian values, i instead opted for a more, shall we say, lo-fi approach.

[^pleasemaildan]: please, feel free to correct me on hn

Instead, each dart would use the *exact-same 2π rotation animation*, but to stagger the animations, I would set each dart's *animation delay* to achieve the same effect. Then, I would set this field of spinning darts on a z-index below an actual html notification.

## implementing this

My [first attempt](https://gist.github.com/nsfmc/fc241d6f97a4b3b5203d/95b38bcc9707128c2b1d0501d22f48d070eea036) did something comical: because i had already generated the animation above using plotdevice as part of my testing, i already had a series of timing offsets along with x/y positions so i printed the starting rotation for each dart and saved that as a json array which i loaded directly into a *very* small react template yielding something approximately like the

```javascript
// a massive array of rotation offsets
var dartRot = [0, 0.234, 0.469,
              ..., a few megabytes more, ...];

for (var i=0; i < dartRot.length; i += 1){
  style = { animationDelay: dartRot[i], ..., };
  return <dart style={style} />;
}
```

I iterated over *all the values* and then used that to set the animation delay. My goodness! how ridiculous! That's basically as bad as writing out all those css animations one-by-one. But i mean, the takeaway was that *the idea* was not bad *even if* my initial implementation was.

Instead, I set down the project for the day and it took until the next morning to realize that i could do something *much* less ridiculous:

```javascript
for (var x=0; x < dartCols; x += 1){
  for (var y=0; y < dartRows; y += 1){
    // what's that... a... *computed* delay?!
    style = { animationDelay: (x+y), ..., };
    return <dart style={style} />;
  }
}
```

This wasn't even that much more work, i had already done much of it in python,  i just needed to translate it! Here's basically a demo of that react implementation.[^democaveat]

[^democaveat]: In this demo, the darts are all displayed `inline-block` just to avoid having to be distracted by setting position manually

<a class="jsbin-embed" href="http://jsbin.com/cemewot/embed?output">JS Bin on jsbin.com</a><script src="http://static.jsbin.com/js/embed.min.js?3.34.0"></script>

The nice thing here is that not only is the code *not* packed with magic arrays, it's also wayyyyyy more obvious what's going on. Even setting the x/y positions (*not shown*) in the style object is more obvious and the code you end up with allows you to think in terms of a unit grid but render elements by twiddling the knobs of your various scale factors.

Because the animation works by setting an animation delay, it slowly staggers into being. So when the banner appears, everything starts off pointing to one direction only to eventually fall in line at some point along the animation delay.

At Khan Academy, we have a neat tool to let you prototype a react component in the context of the site called the React Sandbox. It works on the local dev server and lets you get a quick jsbin/fiddle environment but with all the goodies you've come to expect on the site. Using it, you get something like this:

![an image of the header inside the react sandbox](/images/slopefields/quV1.png)

The design isn't super mind blowing: it's a spin on the regular learnstorm header, but it's... *alive*! And, more importantly, it transfers the gravity of the original learnstorm header into celebrating the accomplishments of our regional winners and brings the identity to life even if it doesn't directly animate the circular slope field.

## lessons learned

Well, aside from the fact that it's fun to use math to make cool notifications, the main lesson (i think), is that by thinking about prototyping (and parametrizing) early on, you can come up with interesting ways of procedurally generating animations later on even when your environment (like css) is constrained.

Part of this was definitely baked into the early differential equation investigations. Later this was teased out using python and in the end, even though the animation was implemented using react, the various explorations let me realize that this is the sort of thing that you could implement with anything else like d3 or even good ol' jQuery or handlebars.

In the end, somebody who had received the notification by visiting the site would see this (except animating):

![final learnstorm banner, in situ](/images/slopefields/YQtk.png)

If you saw the notification, congrats on participating in learnstorm! It was great fun making something for you :)
