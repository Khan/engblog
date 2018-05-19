title: Let's Reduce! A Gentle Introduction to Javascript's Reduce Method
published_on: July 10, 2017
author: Josh Comeau
team: Web Frontend
...

<img role="presentation" src="/images/lets-reduce/reduce-shapes.png" />


Every summer, Khan Academy recruits a few software engineer interns. As part of their onboarding, we host several brief talks introducing the technology we work with: React, Flow, Google AppEngine, and so on. I volunteered to introduce [Redux](http://redux.js.org/docs/introduction/), a tool to manage front-end state.

For this reason, I found myself looking at how Redux is taught. There are a lot of great resources for learning Redux, but few of them cover the fundamental knowledge you need to fully understand it. The more I thought about it, the more I realized that to understand Redux, you first need to understand [`Array.prototype.reduce`](https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/Array/reduce).

`reduce` is an array method, similar in spirit to `map` and `filter`, but far more flexible. Like those other methods, `reduce` is called on every item in the list, but the end result can be whatever you need; an array of data, an object, a number.

That flexibility comes at a price, though: it's pretty tough to get the hang of. Unlike those other array methods, each iteration in `reduce` is affected by the previous iteration's return value. Similar to recursion, you need to be able to keep track of the sequence of iterations in your head, and this can be a hard skill to develop. It's like building muscle memory; it takes a while for it to become intuitive and natural.

I had initially set out to write a blog post introducing Redux, but `reduce` warrants a blog post of its own. It's foundational to understanding Redux, and it's also a really neat tool to have in your toolbelt.


_**Prerequisite Knowledge:** I’ll be assuming you have an understanding of modern JavaScript, including [arrow functions](http://wesbos.com/arrow-functions/), [enhanced object literals](https://www.eventbrite.com/engineering/learning-es6-enhanced-object-literals/), and the [array spread operator](https://ponyfoo.com/articles/es6-spread-and-butter-in-depth#spread-operator). It’s probably also helpful if you know about [Array.prototype.map](https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/Array/map) and [Array.prototype.filter](https://developer.mozilla.org/en/docs/Web/JavaScript/Reference/Global_Objects/Array/filter). Once you’ve gotten that stuff down, come on back._


## Some Words That Probably Won’t Help
Every explanation I’ve seen for `reduce` tries to explain how it works using English.

The problem is, it’s a bit like trying to learn how to tie a shoelace using words alone; you may be able to understand _intellectually_ how it works… but good luck keeping your shoes on.

I expect that the “ah-ha” moment will come further on, when looking at a visualization of how it works, or trying the problem exercises for yourself. Nevertheless, I think it’s worthwhile to have these ideas grasped loosely in your mind, the soil from which understanding will grow.

First, a definition:
> **`reduce` is a way of deriving a single result from a series of values.**

A suitable analogy is assembling a layer cake. We start with a bunch of layers, and each layer needs to be frosted and assembled, producing a single cake at the end.


### Summing Values
The most common example for explaining `reduce` is using it to sum an array of numbers. Say you have the following data, and you want to calculate the total:

```js
const arr = [3, 5, 1, 4, 2];
```

`reduce` allows you to take this array of numbers, and compute a single result (in this case, the number 15).

There are, of course, many ways of solving this problem. Here’s an example that uses a `forEach` loop:

```js
let total = 0;

arr.forEach((item) => {
  total += item;
});
```

In this solution, we iterate through our list, adding each value to a variable kept in the parent state.

`reduce` works in a similar way, but doesn't involve mutating an outside variable. Here's how we'd do it:

```js
const arr = [3, 5, 1, 4, 2];

const total = arr.reduce((acc, item) => {
  return acc + item;
}, 0);
```

Right away, we can see that there are some similarities; you call it on an array, and then it calls a provided callback function on every item in that array.

`reduce` takes two arguments:

- the _callback function_, called once for every item in the array. This callback takes a parameter that we'll call `acc` (short for _accumulator_; this name will make sense soon), and the item itself.
- an _initial value_.

That _initial value_ becomes the first argument supplied to the callback as `acc`. Our _initial value_ is set to be `0`, and the first item in our array is `3`, so on the first iteration, our function body populates to `return 0 + 3`.

For every subsequent iteration, `acc` receives the _previous iteration's return value_. This is the tricky part of `reduce`. We named the parameter `acc`, because it's like a snowball rolling down a hill; it accumulates the value of each iteration. This isn't true for all `reduce` functions, but it's a good analogy in this case.

Following the sequence, the second iteration receives `3` as the `acc` parameter (since the first iteration returned `0 + 3`), and it adds that value to the next item in our array: `return 3 + 5;`.

The third iteration receives `8` as the `acc` (since 3 + 5 is 8), and returns `8 + 1`.

This process continues until the final iteration, where it returns `13 + 2`, which resolves to our final answer, `15`.


## Visualize it

As I said earlier, I don’t expect these words to work miracles.

The hardest part of learning `reduce` is developing an intuitive understanding of how data flows through it from iteration to iteration.

This visualization showcases the above example of adding values. Click the GIF to view it in its entirety:

<a href="http://reduce.surge.sh/">
<img alt="Visualization of the Reduce process" src="/images/lets-reduce/visualization.gif" />
<center><strong style="font-size: 18px;">View the visualization</strong></center>
</a>


<br /><br />
## Play with it
The best way to solidify understanding is to actually _do_ it. I **[created a JSBin](http://jsbin.com/qubodoxipo/1/edit?js,console)** with the sample `reduce` summing code; poke around with it! Sprinkle some `console.log`s around to see what the variables hold. Try messing with it, and see what happens.


## Another Example

Because `reduce` gives you full control over its output, it's extremely flexible, and not just used for summing numbers.

Let's look at a common data-wrangling concern. Let's say we have an array of user objects, and we want to create a map-like object. This is actually a pretty common problem, as libraries like Redux advocate storing data in a database-like tree structure:

```js
// Let's say our data comes back from
// the API as an array of objects:
const inputFromServer = [
  {id: 'a', name: 'Amy'},
  {id: 'b', name: 'Blanche'},
  {id: 'c', name: 'Claude'},
];

// We'd like to create a map-like object:
const desiredOutput = {
    a: {id: 'a', name: 'Amy'},
    b: {id: 'b', name: 'Blanche'},
    c: {id: 'c', name: 'Claude'},
};
```

We can't simply use `map` here, because we want to return an _object_, not an array. `reduce` to the rescue!

```js
const getMapFromArray = data => (
  data.reduce((acc, item) => {
    acc[item.id] = item;

    return acc;
  }, {})
);

getMapFromArray(inputFromServer)
// returns an object identical to `desiredOutput`.
```

Our `initialValue` is an empty object, and on each iteration, we augment it with the item provided. Each `item` in the array is added to `acc` object, keyed by its `id`.

## Practice: recreate `map` and `filter` with `reduce`

By now, it should be clear that `reduce` is an extremely flexible method, compared to `map` or `filter`.

You may be surprised to learn, though, that `map` and `filter` can be _reimplemented_ with `reduce`.

Your challenge, should you choose to accept it: Create `map` and `filter` functions that replicate the native functionality, but using `reduce` internally.

Here are some JSBins that set this up. Good luck!

###[**Implement `map`**](http://jsbin.com/vevulipige/3/edit?js,console)
###[**Implement `filter`**](http://jsbin.com/barizidelu/edit?js,console)


_Stuck? You can view the solutions [here](http://jsbin.com/nabotejeyo/edit?js,console). Do your best to figure it out before peeking, though!_



## Using the right tool for the job

`reduce` is a very handy hammer, but not every problem is a nail.

For example, you might think that this is a perfect problem statement for `reduce`:

```
Given an array of values, filter out
all negative values, and double all
remaining values.

eg. [2, -4, 6] -> [4, 12]
```

This is _totally_ solvable by `reduce`! We can write a little function that just returns the `acc` if the item is negative, and pushes in a doubled `item` if it's positive!

```js
const positiveDoubler = data => (
  data.reduce((acc, item) => {
    if (item < 0) {
      return acc;
    }

    return [...acc, item * 2];
  }, [])
);
```

This works, but this function is really doing two different things. Why not break it up into discrete steps?

```js
const isPositive = item => item >= 0;
const doubleItem = item => item * 2;

const positiveDoubler = data => (
  data
    .filter(isPositive)
    .map(doubleItem)
)
```

I think most would agree that this solution is clearer.

The moral of the story? `reduce` is awesome, but sometimes there are simpler solutions. Always strive to write code that others can easily understand.


## Shorthand Syntax

JavaScript's implementation of `reduce` offers a convenient shorthand.

I didn't mention this earlier, because I wanted to strip away all the non-essential bits before covering this little bit of syntactic sugar. In fact, if you still don't feel like you have a firm grasp on `reduce`, I'd advise skipping this section for now. It's not necessary knowledge to use `reduce`.

The shorthand allows you to omit an `initialValue`. If you do, `reduce` uses the **first two values** in the array as the first two parameters in your callback.

Let's look again at our summing example:

```js
const arr = [3, 5, 1, 4, 2];

const total = arr.reduce((acc, item) => {
  return acc + item;
});
```

If no `initialValue` is provided, then `acc` takes on the value of `3` and `item` takes on the value of `5`. For _this example specifically_, everything still works as-intended, but there are only 4 iterations instead of 5.

Note that this is not _always_ the case; Our data-wrangling example needs the initial value of `{}`.


## Conclusion

Phew! You made it.

If `reduce` still doesn't feel like it's totally sunken in yet, don't worry. Keep practicing! It's worth the effort.
