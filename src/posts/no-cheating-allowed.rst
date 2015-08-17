title: No Cheating Allowed!!
published_on: August 17, 2015
author: Phillip Lemons
team: Web Frontend
...

The problem
============
Recently, a number of students on Khan Academy found a way to cheat by taking
hints offline and not having them counted towards their online profile. When
going through exercises on Khan Academy you answer the problems given to you
and receive feedback on whether your answer was correct or incorrect. If you
get stuck on a problem you are able to take hints and have that problem counted
as incorrect. Check out `this exercise <https://www.khanacademy.org/math/early-math/cc-early-math-counting-topic/cc-early-math-counting/e/counting-out-1-20-objects>`_
if you want to try it yourself. The images below show the user getting a correct
answer and taking a hint respectively.

.. image:: /images/no-cheating-allowed/Correct_Screen.png
    :alt: Correct answer screenshot
    :width: 100%
    :align: center

.. image:: /images/no-cheating-allowed/TakingHint_Screen.png
    :alt: Taking a hint screenshot
    :width: 100%
    :align: center

The cheaters realized that if they disconnected from the internet, took the
hints, and reconnected, they would still have a problem counted as correct.
Taking offline hints worked this way because our servers expect a request from
the client when users take a hint or answer a problem. If the users were
disconnected from the internet the server would never see the request and the
request was not stored anywhere on the client so it would be lost.

How did we fix this?
====================
In order to address the offline cheating, we decided to change how the client
sends requests to the server. By utilizing the client’s local storage, we could
store failed requests to be retried once the user reconnected to the internet.
This solution has the added benefit of removing the need for the client to be
connected to the server all the time. Users with a spotty internet connection
would have a better experience because everything would work even if the
internet cut out for a short period of time.

In our new architecture, anytime a user performs an action a string representing
that action is stored in a queue that is saved to localstorage. When the queue
is consumed, each action is mapped to a function that implements the action.
This approach allows us to have more control over what happens when a request is
not received by the server. The new queue retries any actions that fail and
implements a linear backoff function so as not to be constantly sending requests
when the user is not connected to the internet.

Below is an image that shows the old architecture (left) and the new architecture
(right). If the old client never received a response from the server the request
would never be retried. In the new architecture the request is retried until it
reaches the server and we get a response.

.. image:: /images/no-cheating-allowed/HintClientArch.png
    :alt: Architecture screenshot
    :width: 100%
    :align: center

A nice consequence of this architecture is that it can be generalized to work in
other parts of our system. Code that deals with sending requests to the server
can be updated to use this architecture and work more consistently even with a
bad internet connection. Supporting an offline mode also becomes a possibility
because you can just save all of the actions the user makes and send them to the
server at a later time when the user has reconnected to the internet.

The downside
============
One of the biggest downsides with this implementation is that with some editing
of the user’s local storage, a hint request can be erased from the action queue.
We decided this was acceptable for a couple of reasons. First, our typical
classroom user is unlikely to know how to edit their local storage. Second, even
if the user edits their local storage, it is visually obvious to those in the same
room that they are up to something. A teacher can easily see students messing
around with the chrome devtools and act accordingly.

Conclusion
==========
A client based architecture makes for a much better user experience because a
spotty connection does not create a barrier to using our application. In our
case, it also made it much harder to cheat on exercise problems and was a great
way to make server requests more reliable. Additionally, this architecture
makes having an offline mode more feasible.

