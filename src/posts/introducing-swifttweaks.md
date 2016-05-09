title: "Introducing SwiftTweaks"
published_on: May 9, 2016
author: Bryan Clark
team: Mobile
...

Today, we’re releasing [SwiftTweaks](https://github.com/khan/SwiftTweaks), a way to adjust your Swift-based iOS app without needing to recompile.

![Overview of SwiftTweaks](/images/introducing-swifttweaks/overview.png)
Your users won’t see your animation study, Sketch comps, or prototypes. What they *will* see is the finished product - so it’s really important to make sure that your app feels right on a real device!

Animations that look great on your laptop often feel too slow when in-hand. Layouts that looks perfect on a 27-inch display might be too cramped on a 4-inch device. Light gray text may look subtle in Sketch, but it’s downright illegible when you’re outside on a sunny day.

For these reasons, it’s helpful to fine-tune your designs on-device - but that’s a lot of work: open Xcode, tweak your code, and wait for the app to build to device before seeing the results.

### What about Facebook Tweaks?
In Objective-C projects, I’ve cherished [Facebook’s Tweaks](https://github.com/facebook/tweaks), a tool that makes this process easy. However, while it's possible to use FBTweaks in Swift, it's far less convenient than in Objective-C.

Since [Khan Academy](https://khanacademy.org)’s iOS code is almost entirely Swift, we wanted something that would make it easy to use tweaks. (Plus: with Swift’s generic types, protocols, and all-around awesomeness, we figured we could make some improvements.)

We’ve been using SwiftTweaks for a few months now in our iOS app, and it’s been wonderful for fine-tuning gestures, adjusting animations, and toggling feature flags.

## Using SwiftTweaks
### Create a TweakLibrary
First, you create a `TweakLibrary`, which contains `Tweaks` and a `TweakStore`. (If `TweakStore.enabled` is false, then the Tweaks UI will be inaccessible and all tweaks return their default value - which means you can leave this code in-place when you ship your production app.)

```
public struct ExampleTweaks: TweakLibraryType {
	public static let colorTint = Tweak("General", "Colors", "Tint", UIColor.blueColor())
	public static let marginHorizontal = Tweak<CGFloat>("General", "Layout", "H. Margins", defaultValue: 15, min: 0)
	public static let marginVertical = Tweak<CGFloat>("General", "Layout", "V. Margins", defaultValue: 10, min: 0)
	public static let featureFlag = Tweak("Feature Flags", "Main Screen", "Show Body Text", true)

	public static let buttonAnimation = SpringAnimationTweakTemplate("Animation", "Button Animation")

	public static let defaultStore: TweakStore = {
		let allTweaks: [TweakType] = [colorTint, marginHorizontal, marginVertical, featureFlag]

		#if DEBUG
			let tweaksEnabled: Bool = true
		#else
			let tweaksEnabled: Bool = false
		#endif

		return TweakStore(
			tweaks: allTweaks.map(AnyTweak.init),
			enabled: tweaksEnabled
		)
	}()
}
```



### Calling Tweaks in your code
When you want to use a tweak in your code, use the `assign`, `bind,` and `bindMultiple` functions.

**assign** returns the current value of the tweak:

```
button.tintColor = ExampleTweaks.assign(ExampleTweaks.colorTint)
```

**bind** calls its closure immediately, and again each time the tweak changes:

```
ExampleTweaks.bind(ExampleTweaks.colorTint) { button.tintColor = $0 }
```

**bindMultiple** calls its closure immediately, and again each time any of its tweaks change:

```
// A "multipleBind" is called initially, and each time _any_ of the included tweaks change:
let tweaksToWatch: [TweakType] = [ExampleTweaks.marginHorizontal, ExampleTweaks.marginVertical]
ExampleTweaks.bindMultiple(tweaksToWatch) {
	let horizontal = ExampleTweaks.assign(ExampleTweaks.marginHorizontal)
	let vertical = ExampleTweaks.assign(ExampleTweaks.marginVertical)
	scrollView.contentInset = UIEdgeInsets(top: vertical, right: horizontal, bottom: vertical, left: horizontal)
}
```

There are also several handy `TweakGroupTemplate` types, to help you with commonly-tweaked things. Our above `ExampleTweaks` library included one for a `UIView` spring animation:

```
public static let buttonAnimation = SpringAnimationTweakTemplate("Animation", "Button Animation")
```

This single line of code creates four tweaks - for duration, delay, damping, and initial spring velocity. Each has sensible defaults (e.g. “delay can’t be negative”) - and there’s a `UIView` extension to easily use the `TweakGroup`:
`UIView.animateWithSpringAnimationTweakTemplate`

For more on using Tweaks and TweakGroupTemplates, [check out the example project](https://github.com/Khan/SwiftTweaks/blob/master/iOS%20Example/iOS%20Example/ViewController.swift).

### Accessing the interface
Lastly, we need a way to adjust our Tweaks while the app is running. The simplest way is to set your app’s `UIWindow` to be a `TweakWindow`. By default, the `TweakWindow` presents a `TweaksViewController` when you shake the device in a debug build, but you can  provide a different gesture recognizer, too.

You can also handle the presentation of a `TweaksViewController` if you prefer to not use a `TweakWindow`.

### Tweaking values
Now for the fun part - shake your phone, and your tweaks appear! Adjust booleans with a switch, numbers with a stepper or keyboard, and there’s a great color-editing interface in there, too! There’s also a “floating UI” so you can edit tweaks without leaving a screen.

Here's a preview of the SwiftTweaks example app (included in the repository):
![animated demo](/images/introducing-swifttweaks/demo.gif)

[Check it out on GitHub](https://github.com/khan/swifttweaks) and let us know what you think!
