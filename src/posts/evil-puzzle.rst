title: How wooden puzzles can destroy dev teams
published_on: July 6, 2015
author: John Sullivan
team: Web Frontend
...

Last week a mysterious double-sided puzzle appeared at `Khan Academy <https://www.khanacademy.org/>`_.

.. image:: /images/mysterious-puzzle.jpg
    :alt: A picture of the mysterious puzzle
    :width: 75%
    :align: center
    :target: /images/mysterious-puzzle.jpg

To solve the puzzle you must fit all four pieces inside the recessed area (the pieces will not entirely fill the area). We found a solution to the easy side after only a few days [#easy_solution]_ but nobody could get close to solving the hard side. So **five** of us at Khan Academy began writing our own solvers.

The first question we each faced was how to best represent the positions of the pieces. Laying a triangular grid over each side was intuitive enough, but it wasn't obvious how the cells should be addressed.

Naturally we all came up with different systems  [#such_coordinates]_. I went with a system that used two perpendicular axes, with the origin at the bottom left.

.. image:: /images/triangular-grid.png
    :alt: An image of the triangular grid
    :width: 75%
    :align: center

.. image:: /images/johns-coordinates.png
    :alt: An image illustrating my coordinate system
    :width: 75%
    :align: center
    :target: /images/johns-coordinates.png

I had a problem though. Once I manually input a piece into this coordinate system, I needed to rotate and reflect that piece into 12 different alignments. Reflection was easy, but despite my best efforts, I couldn't figure out how to rotate the pieces programmatically once they were placed into my grid.

After smashing my head against the problem for an hour and getting nowhere, I gave up [#emily_rotation]_ and manually inputted the three rotations necessary for each piece (all the other alignments could be expressed as reflections of those rotations).

Now I just had to write the logic to try every possible placement of the pieces, but I was behind.

Ben Eater had already finished `his solver <https://www.khanacademy.org/computer-programming/spin-off-of-puzzle/4900481558249472>`_ and it was churning away. His solver didn't do any pruning of the search space though (and took some time to check each placement), so he estimated that the solver would finish in around 2 years. I felt good about my chances of finding a solution before then.

.. image:: /images/eaters-solver.gif
    :alt: Ben Eater's solver
    :align: center

To try and be a little faster I added in some logic to skip large parts of the search space where possible. This worked by laying down a piece at a time, and only trying the other ones if there were no collisions.

For example, first my program would lay down Piece A somewhere. If Piece A collided with a wall, my program would not try laying down Piece B yet, but would instead move Piece A somewhere else.

This ended up working well and soon I had `a solver <https://github.com/brownhead/damn-puzzle/blob/master/boom.js>`_ that could brute force the puzzle in less than a minute.

.. image:: /images/solver.gif
    :alt: My solver
    :width: 50%
    :align: center

`Emily Eisenberg <https://github.com/xymostech>`_ finished `her solver <https://github.com/xymostech/wood-puzzle/blob/master/src/Main.hs>`_ around the same time and we were able to confirm our results. **The hard side of the puzzle was unsolvable**.

Clearly there was a very evil puzzle master in our ranks.

.. image:: /images/evil-kitty.gif
    :alt: An evil kitten
    :width: 50%
    :align: center

`Jamie Wong <http://jamie-wong.com/>`_ readily admitted to bringing in the puzzle, but despite the staggering proof to the contrary, he was adamant that a solution existed. He said our solvers all shared a fatal flaw.

After a few hints, Emily and I did find the answer [#hard_solution]_. Which was good, because none of us had gotten any work done for awhile.

.. [#easy_solution] If you want to spoil it for yourself, here is `a picture of the solved easy side </images/easy-solved.jpg>`_.
.. [#such_coordinates] Ben Eater decided to side-step the issue by drawing the shapes directly onto the screen. Cam Christensen came up with a coordinate system with two axes that formed a 60° angle and he convinced Emily Eisenberg to use the same system. `Justin Helps <https://twitter.com/Helpsypoo>`_ used a vertex-based coordinate system (rather than piece-based) that made rotation and reflection easy, but collision detection super hard.
.. [#emily_rotation] `Emily, however, was able to easily figure out rotation <https://github.com/xymostech/wood-puzzle/blob/f7ea685855c06531debcc9e6105451c934a00cde/src/Main.hs#L35>`_
.. [#hard_solution] You don't really want me to give you the answer do you? That would be boring.
