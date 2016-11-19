title: "Interning at Khan Academy: from student to intern"
published_on: November 19, 2016
author: Shadaj Laddad
team: Web Frontend
...

This past summer, I had the amazing opportunity to work on a product I use as a student every day -- Khan Academy. During my internship, I worked on the web frontend team on the XOM (x-on-mobile) initiative to bring Khan Academy exercises to mobile devices. In this blog post, I’ll be going through a highly-compressed summary of my two months at Khan Academy, but since most of my work here was in open-source projects you can check out my work in detail on GitHub ([https://github.com/Khan/perseus/commits?author=shadaj](https://github.com/Khan/perseus/commits?author=shadaj), [https://github.com/Khan/math-input/commits?author=shadaj](https://github.com/Khan/math-input/commits?author=shadaj)).

# Part 1: ramping up

My first day at Khan Academy was a whirlwind of activities. From setting up my laptop to having a 1:1 with my mentor and finally adding myself to the interns page, I had a lot of things to do. As soon as I settled down with my first deploy, I got to work on the XOM initiative, starting with improving the math keypad.

As part of the XOM initiative, the team had designed a math keypad that could be used to type in expression responses to mathematics problems in a mobile-friendly way. I started by fixing some bugs to get familiar with the math keypad codebase, such as disabling gestures on the static sidebar. Once I had a good idea of how the keypad worked, I was able to start working on adding new features our designers had crafted. I worked on things such as using square icons for representing empty blocks, and learned in the process how important it is to make these small changes to create a great experience for students.

At Khan Academy, we use React.js, something I had worked with before, but only in the context of [Scala.js](https://www.scala-js.org) applications. As part of making changes to the math keypad, I had to learn how to write idiomatic ES6 code. Working on Khan Academy gave me a great opportunity to see use of React with ES6 in a production environment, and left me with many ideas on how React.js could be used more seamlessly with Scala.js. In addition to learning React and ES6, I got a chance to work with the plethora of open-source libraries at Khan Academy such as Aphrodite ([https://github.com/khan/aphrodite](https://github.com/khan/aphrodite)) and KaTeX ([https://github.com/khan/katex](https://github.com/khan/katex)).

![changes to the math keypad](/images/interning-at-khan-academy/image_0.png)

*an early screenshot of changes to the math keypad*

# Part 2: iframes, iframes, iframes

Now that I was used to the flow of picking a task, creating a code review, and deploying my changes, I started on my first project -- improving our content editor to be mobile first. This involved pulling together specs for what types of devices students use Khan Academy on, rendering content with the new styles the rest of the team was working on, isolating the rendered content to prevent styles leaking from the rest of the editor, and implementing touch emulation for interacting with the mobile previews.

To implement the isolation of content, I decided to render previews inside of iframes. In addition to providing style isolation, iframes also made it possible to properly render components that are rendered directly to the body, such as the math keypad I worked on earlier. To transfer data between the parent editor and the child iframe, the parent first stores a JS object representation of the exercise content in a global variable and then sends a message ([http://ejohn.org/blog/cross-window-messaging/](http://ejohn.org/blog/cross-window-messaging/)) to the iframe. When the iframe receives this message, it grabs the global JS object from the parent (because the iframe and parent are on the same domain this is allowed by the browser) and renders that content. With this implementation, preview updates happen immediately after content edits, and with a special `shouldComponentUpdate` iframe loads are minimized so that in most cases, the only loading delay happens during the initial editor load.

![interactive mobile previews](/images/interning-at-khan-academy/image_1.png)

*live-updated interactive mobile previews with iframes!*

After these changes were implemented, I got the chance to work with content creators to test out my changes and make sure they didn’t interrupt their creation process. By working with content creators, I was able to understand exactly what they were hoping to get out of my changes, and I was able to tune the goals of my project to these needs to make sure that it was helping the content creators as much as possible. With all the kinks worked out, I was able to finally deploy the content editor that is now used by content creators every day!

# Part 3: crispEdges for the win!

Moving on from the mobile-first content editor, I began work on my next project -- making KA’s interactive graphing widgets work on mobile devices. Since new designs for the mobile experience were needed, I worked with Louis, a fellow intern on the design team. On Khan Academy, interactive graphs are rendered with SVGs, so most of my work dealt with rendering the SVG elements for different graph parts with the new styles.

![changes to the graph widget](/images/interning-at-khan-academy/image_2.png)

*some changes to the graph widget: larger points and deletion tooltips*

One of the most interesting things I learned in this project was the shape-rendering CSS style. On SVG elements, you can apply the shape-rendering style to give the renderer hints on what to prioritize when rendering the elements. In the case of this project, I used the shape-rendering property with the crispEdges value to make lines render more crisply. This is especially useful for grid lines, which sit perfectly horizontal and vertical. By setting crispEdges on these lines, the renderer knows to render them lined up with pixel rows instead of blurring the line to higher and lower rows. On mobile devices, especially those with higher resolutions, this small change makes a large difference in how the graphs look.

![the effects of crispEdges](/images/interning-at-khan-academy/image_3.png)

*if you look closely, you can see the effects of crispEdges here*

# Conclusion

All in all, my internship at Khan Academy gave me an amazing experience to have an impact on learners around the world and learn many new technologies. From building new tools for content editors to creating a brand new experience for students using interactive graphs, I was able to work on a wide variety of areas. I’m super thankful to my mentor Kevin for all his help throughout my internship, the XOM team for being super encouraging on all my projects, my fellow interns for great lunchtime discussions, and the entire Khan Academy team for creating such a great place to work.

Onwards!
