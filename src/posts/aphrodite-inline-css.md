title: "Inline CSS at Khan Academy: Aphrodite"
published_on: March 29, 2016
author: Jamie Wong
team: Infrastructure
...

I won't ramble in this post about the maintenance woe that is CSS, as others have said it better in the past. In particular, Christopher "vjeux" Chedeau sparked much of this discussion in his talk [React: CSS in JS](http://blog.vjeux.com/2014/javascript/react-css-in-js-nationjs.html).

Instead, I'd like to discuss [Aphrodite](https://github.com/Khan/aphrodite), the inline styling solution we've developed at Khan Academy, the constraints that led to it, and its use in production today.

## Page weight and server-side rendering

As part of an initiative to speed up Khan Academy's core content pages, we identified that the most important predictor of page load speed was the number of bytes needed before the content was rendered. From testing different bandwidth limitations and network latencies, we found that bandwidth was a bigger predictor of page speed, not latency. You can verify this yourself by trying loading various sites and using [custom networking throttling profiles](https://developer.chrome.com/devtools/docs/device-mode#network-conditions) in the Chrome Developer tools. So cutting bytes was our goal.

To meet that goal, we opted to pursue server-side rendering.

If you're unconvinced that server-side rendering yields a fast page load, here's a simple argument. We'll focus on initial page load, before any of your static assets are cached. Assume all the sizes mentioned here are measured after gzip.

1. Let M be the byte size of the minimal HTML markup required to load your website, including script tags to load whatever client-side libraries you want.

2. Let J be the byte size of the JavaScript needed to render your page (e.g. React + other libraries + the JavaScript UI components).

3. Let S be the byte size of the server-side rendered markup for your page. This 
   would be the contents of the `<body>`.

4. Let C be the byte size of the CSS needed to render the components on the page.

Now let's examine how many bytes the client has to download before the user can see the content on the page.

In the server-side rendered case, it's M + S + C. In the client-side rendered case, it's M + J + C. So if you agree with the hypothesis that fewer bytes means a faster site, then if J > S, server-side rendering will be faster. The production build of React alone is 43KB after gzip, so if you can get your server-side rendered content markup below that, server-side rendering will get content to your users faster.

You can read posts arriving at similar conclusions from [Tom Dale of Ember](http://tomdale.net/2015/02/youre-missing-the-point-of-server-side-rendered-javascript-apps/), [Dan Webb of Twitter](https://blog.twitter.com/2012/improving-performance-on-twittercom), [Spike Brehm of Airbnb](http://nerds.airbnb.com/isomorphic-javascript-future-web-apps/), and [Turadg Aleahmad of Coursera](https://building.coursera.org/blog/2015/08/18/why-and-how-coursera-does-isomorphic-javascript-a-fast-and-snappy-quiz/).

## Constraints

So let's return to the problem of CSS. 

Given a goal of reducing bytes until content was visible, we set forth to find a CSS solution that allowed us to colocate our CSS with our React components with the following constraints:

1. We must be able to extract and deliver the CSS needed by our components when the component was server-side rendered.

2. When the client-side re-renders the components in React to make them fully interactive, the page must not dramatically change. This meant correctly handling media queries, pseudo-selectors such as :hover and :visited all in CSS, and not via JavaScript-bound events. ([:visited can't be implemented in JavaScript anyway](https://developer.mozilla.org/en-US/docs/Web/CSS/Privacy_and_the_:visited_selector)). This disqualifies libraries such as [Radium](https://github.com/FormidableLabs/radium) which use component state to emulate :hover.

3. We must deliver the absolute minimum amount of CSS necessary by only sending down CSS in use by components in the server-side rendered body. This rules out extracting all the CSS used in all of our components at compilation time, as much of that CSS would not be needed for the initial page load.

4. As to avoid increasing the time to the site being fully interactive, any runtime added must be small (< 10KB after gzip).

Unsatisfied with the existing options*, [Emily Eisenberg](https://github.com/xymostech) and I wrote [Aphrodite](https://github.com/Khan/aphrodite) to satisfy these constraints. Our primary use case is use with React components, so all of the examples that follow will be in React, though it's worth mentioning that Aphrodite does not depend on React in any way.

*: [React Look](https://github.com/rofrischmann/react-look) has since come a long way. It is in many ways more featureful, though is a larger library to send over the wire. Many of the ideas appear to be quite similar. It also has support for React Native, which Aphrodite does not. React Look, as the name suggests, is coupled to React, which Aphrodite is not. If Aphrodite doesn't interest you, check out Look.

## A simple example

Here's how Aphrodite works. First, styles are defined via a syntax inspired by [React Native's StyleSheet](https://facebook.github.io/react-native/docs/stylesheet.html), like so:

```
const styles = StyleSheet.create({
    red: {
        backgroundColor: 'red'
    },
    blue: {
        backgroundColor: 'blue'

    },
    hover: {
        ':hover': {
            backgroundColor: 'red'
        }
    },
    small: {
        '@media (max-width: 600px)': {
            backgroundColor: 'red'

        }
    }
});
```

This, by itself, does not generate any CSS. CSS is only injected into the `<head>` of the page when these classes are *used*. The injection happens in Aphrodite's `css()` function. Here's an example of using `css()` in a React component:

```
class App extends Component {
    render() {
        return <div>
            <span className={css(styles.red)}>
                This is red.
            </span>
            <span className={css(styles.hover)}>
                This turns red on hover.
            </span>
            <span className={css(styles.small)}>
                This turns red when the browser is less than 600px width.
            </span>
            <span className={css(styles.red, styles.blue)}>
                This is blue.
            </span>
            <span className={css(styles.blue, styles.small)}>
                This is blue and turns red when the browser is less than
                600px width.
            </span>
        </div>;
    }
}
```

Only once this component is rendered will the CSS be injected into the page. The css function generates CSS to inject into the page and returns an associated CSS class name. On the client-side, it will automatically inject the CSS into the <head> of the page. On the server-side, it will buffer the CSS to be flushed as one big string into the HTML response.

Let's look at a simple case:

```
<span className={css(styles.red)}>
    This is red.
</span>
```

The injected CSS for this span looks like this:

```
.red_im3wl1{color:red !important;}
```

And the span ends up looking like this in the DOM:

```
<span class="red_im3wl1">This should be red</span>
```

## Avoiding class name collisions

You may be wondering where the _im3wl1 comes from. Imagine we had two components, that each define a class with the style name red, like so:

```
const Component1 = () => <span className={css(styles1.red)}>1</span>;

const styles1 = StyleSheet.create({
    red: {
        backgroundColor: 'red'
    }
});

const Component2 = () => <span className={css(styles2.red)}>2</span>;

const styles2 = StyleSheet.create({
    red: {
        backgroundColor: '#cc1100'
    }
});
```

It would be surprising behaviour if either one of those ended up using the other's style, so we need some way to differentiate between them. We initially solved this by appending a random number to the class name. This works great… unless you want server-side rendering to work well.

## Deterministic rendering and data-react-checksum

When you render a component server-side via ReactDOMServer.renderToString, out outputs HTML that might look something like this:

```
<div id='container'
    data-reactid=".1x73ayqlreo"
    data-react-checksum="-1952287665">...</div>
```

From working with React keys, you've likely seen `data-reactid` before, but 
what's this `data-react-checksum` business? 

When your re-render your React component on the client-side to bind all your 
events and run the lifecycle starting with `componentDidMount`, 
`ReactDOM.render`
will construct a virtual DOM using your component. It then takes a checksum of 
that component tree and compares it with the one emitted by 
`ReactDOMServer.renderToString`. If it's identical it will re-use the 
server-rendered DOM tree and avoid needing to reflow the page or do any style 
recalculations. If it's different, it will replace the entire DOM tree.

This is not so great for performance, so we'd like to avoid that.

If we generate random numbers that wind up in the HTML output of our component, then the checksum certainly won't match. So we can't use random numbers, but we still need something to avoid name collisions.

We could use a simple global counter, but when would we reset that counter? Each time we render? If we do that, then we might still get name collisions between classes generated by two separate render calls.

What we really want is a 1:1 mapping between the class name and the style declarations associated with that class name. Sounds like a job for hashing!

We take a hash of the JSON stringified style declaration and use that as a suffix. On recommendation from our Dean of Infrastructure, Craig Silverstein, we used [MurmurHash](https://en.wikipedia.org/wiki/MurmurHash).

It is possible that two components will each declare their own copy of styles with the same name and the same contents, like so:

```
const Component1 = () => <span className={css(styles1.red)}>1</span>

const styles1 = StyleSheet.create({
    red: {
        backgroundColor: 'red'
    }
});

const Component2 = () => <span className={css(styles2.red)}>2</span>

const styles2 = StyleSheet.create({
    red: {
        backgroundColor: 'red'
    }
});
```

In this case, we get a class name collision on `red_im3wl1`, but that's okay, 
because they reference the exact same properties and values, so there's no 
surprising behaviour!

## Deterministic precedence

It's a common desire to apply styles from multiple CSS classes to a single element, perhaps applying some conditionally.

```
const Component = () => <div>
    <span className={css(styles.awesome)}>
        You only have to know one thing......   
    </span>
    <span className={css(styles.bold, styles.awesome)}>
        You can learn anything!
    </span>
</div>

const styles = StyleSheet.create({
    bold: {
        fontWeight: 'bold',
        color: 'black'
    },
    awesome: {
        Color: 'green'
    }
});
```

If we take the naive approach and generate two classes for the second span and attach them both as the class name, we end up in this situation:

```
<style>
.awesome_d1f3c2 {color: green;}
.bold_cfe213 {font-weight: bold; color: black;}
</style>
<div>
    <span class="awesome_d1f3c2">
        The only thing you need to know is...   
    </span>
    <span class="bold_cfe213 awesome_d1f3c2">
        You can learn anything!
    </span>
</div>
```

In a stylesheet, where there are two styles defined with equal specificity, the one that comes later in the stylesheet has precedence. In a hand-tuned stylesheet that can be confusing, but in an auto-generated one it can be disastrous!

The intent here was for "You can learn anything" to appear bold and green, but because bold was injected into CSS after awesome, the second text ends up being black! This is somewhat surprising behaviour, but it gets worse. Imagine updating the component and change it to this:

```
const Component = () => <div>
    <span className={css(styles.bold)}>
        Nobody starts knowing everything.
    </span>
    <span className={css(styles.awesome)}>
        The only thing you need to know is...   
    </span>
    <span className={css(styles.bold, styles.awesome)}>
        You can learn anything!
    </span>
</div>
```

Because `styles.bold` is passed to `css()` first, it gets injected first. 

```
<style>
.bold_cfe213 {font-weight: bold; color: black;}
.awesome_d1f3c2 {color: green;}
</style>
<div>
    <span class="bold_cfe213">
       Nobody starts knowing everything.
    </span>
    <span class="awesome_d1f3c2">
       The only thing you need to know is...   
    </span>
    <span class="bold_cfe213 awesome_d1f3c2">
       You can learn anything!
    </span>
</div>
```

This changes the order of the declarations, which changes the styling on "You can learn anything!". The order of calls to css affecting which style rules get applied is certainly surprising behaviour that we'd like to avoid.

Our solution in Aphrodite is to always generate a single class name, and handle the precedence in JavaScript instead of letting the browser decide. The result we generate looks like this:

```
<style>
.bold_cfe213 {font-weight: bold; color: black;}
.bold_cfe213-o_O-awesome_d1f3c2 {font-weight: bold; color: green;}
.awesome_d1f3c2 {color: green;}
</style>
<div>
    <span class="bold_cfe213">
        Nobody starts knowing everything.
    </span>
    <span class="awesome_d1f3c2">
        The only thing you need to know is...   
    </span>
    <span class="bold_cfe213-o_O-awesome_d1f3c2">
        You can learn anything!
    </span>
</div>
```

This can generate larger CSS, however it's not quite a combinatorial explosion. Remember that we inject only the CSS that actually gets used, so if we only ever used bold with awesome, we wouldn't generate CSS for exclusively using bold. Our first example exploring precedence order would come out like this:

```
<style>
.awesome_d1f3c2 {color: green;}
.bold_cfe213-o_O-awesome_d1f3c2 {font-weight: bold; color: green;}
</style>
<div>
    <span class="awesome_d1f3c2">
        The only thing you need to know is...   
    </span>
    <span class="bold_cfe213-o_O-awesome_d1f3c2">
        You can learn anything!
    </span>
</div>
```

## In production!

Newly written React components at Khan Academy use Aphrodite for their styling needs. If you visit [https://www.khanacademy.org/science/physics](https://www.khanacademy.org/science/physics) and view source, you should see something like this:

```
<style data-aphrodite>.wrapper_npd2t8{...
```

Despite our server-side application code being written in Python, we've managed to get server-side rendering working via dedicated rendering servers, and we've open sourced the implementation of that too. You can find it at [https://github.com/Khan/react-render-server](https://github.com/Khan/react-render-server). It won't be a drop in solution for you since it has Khan Academy specific dependencies, but it may serve as a good reference.

I've omitted details on a number of things here, like dealing with fonts, batching CSS to inject into the `<head>`, and our [fork of inline-style-prefixer](https://github.com/Khan/inline-style-prefixer) to reduce the byte size of the library, so I hope if you're interested you'll take a look at [Aphrodite on GitHub](https://github.com/Khan/aphrodite)!


