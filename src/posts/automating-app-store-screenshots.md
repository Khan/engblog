title: "Automating App Store Screenshots"
published_on: March 27, 2017
author: Bryan Clark
team: Mobile
...

# Automating App Store Screenshots

![Khan Academy in the App Store](/images/app-store-screenshots/app-store.png)

One of the more tedious design tasks is keeping your App Store promo images up-to-date. As you add localization support and new features, it can mean taking a few days of a designer's time to update these design assets.

Our iOS app is currently available in 6 languages. Recently, we improved our iPhone app’s downloading feature, and changed its name from “Your List” to “Bookmarks”. A minor change - a few strings and a tab bar icon - but it meant we needed to update lots of screenshots in the App Store!

```
5 screenshots * 4 phone sizes * 6 locales = 180 images
```

If you’re an iOS designer, this is a major headache:

 - If your App Store screenshots are really handmade Sketch artboards, then you need to manually update 180 artboards - and make sure that the other features in the app’s design are kept up to date! Localization is a big pain here.
- If your App Store screenshots are real screenshots, then you’re looking at a long week of loading up different user profiles in different languages to take screenshots. 

Either way, **that’s probably a tedious few days' worth of somebody’s time** - which is a hard expense to justify if you’re shipping every few weeks! The result: your App Store images are either out of date, or your team is spending too much effort on this task.

A couple of months ago, our mobile team spent time automating our screenshots for the App Store and the Play Store. Now, when we want to update our App Store screenshots, **this task now takes about an hour instead of a week** - and almost all of that time is waiting for automated tests to compile and run.

To pull this off, we used [Fastlane’s `snapshot`](https://github.com/fastlane/fastlane/tree/master/snapshot) tool, and a homegrown Sketch file. Let’s dig in! 

## Step One: Write UI Tests
UI testing in Xcode is _awesome_ - the tests are quite easy to write (they can literally write themselves with a "record me" feature) When you run ‘em, your app flies through its paces in the simulator. Then, at the right moment, `snapshot` records a screenshot and files it away.

Let’s take a look at the UI test that takes a screenshot of our Bookmarks tab:

		func testPhoneBookmarks() {
			// Skip the test if snapshot's locale is empty
			guard !locale.isEmpty else { return }
	
			// Tell the iOS app we'd like to populate the Bookmarks tab 
			// with test content
			let environment = AppStoreScreenshotUITests.screenshotEnvironment(plus: [
				KHAUITestingConstants.showAppStoreBookmarksEnvironmentVariable: KHAUITestingConstants.enableKey,
				KHAUITestingConstants.localeCodeEnvironmentVariable: locale 
			])
	
			// Launch the app in the simulator
			launch(with: environment)
	
			// Tap on the Bookmarks tab (tab #3)
			XCUIApplication().tabBars.buttons.element(boundBy: 2).tap()

			// Take a screenshot!
			Screenshot.appStoreBookmarks.take()
		}

What's up with that last line, though?

`Screenshot` is a little `enum` that handles telling `snapshot` when to take a picture, and what the image should be called. It looks like this: 
	
	/// Identifiers for screenshots that we want to take.
	/// The App Store cases are uniquely identified, and numbered by their display order in the App Store.
	/// Use the `.test(string)` case for one-off test shots, e.g. `.test("ProfileUnauthenticated")`.
	internal enum Screenshot {
		case appStoreExplore, appStoreVideo, appStoreBookmarks, appStoreExercise, appStoreUserProfile
		case test(String)
	
		var imageName: String {
			switch self {
			case .appStoreExplore:
				return "AppStore_01_Explore"
			case .appStoreExercise:
				return "AppStore_02_Exercise"
			case .appStoreBookmarks:
				return "AppStore_03_Bookmarks"
			case .appStoreVideo:
				return "AppStore_04_Video"
			case .appStoreUserProfile:
				return "AppStore_05_UserProfile"
			case .test(let screenshotName):
				return "Test_" + screenshotName
			}
		}
	
		func take() {
			// this is a global function from `snapshot`
			snapshot(imageName) 
		}
	}

## Step Two: Create your Snapfile
The Snapfile is where you configure `snapshot`’s run. Ours looks like this:

	# Check out this link for what to put in this file:
	# https://github.com/fastlane/fastlane/blob/master/snapshot/README.md#snapfile
	
	scheme "Khan Academy.UITests"
	output_directory "./app-store-screenshots/snapshot-output"
	clear_previous_screenshots true
	reinstall_app true
	localize_simulator true
	workspace "./Khan Academy.xcworkspace"
	app_identifier "org.khanacademy.Khan-Academy"
	
	devices([
	  "iPhone 7",
	  "iPhone 7 Plus",
	  "iPhone SE"
	])
	
	languages([
	  "en-US",
	  "fr",
	  "es-ES",
	  "nb",
	  "pt_BR",
	  "tr"
	])
	

## Step Three: Render mock data in your app
So, we’ve got UI tests written, and `snapshot` is able to grab screenshots at the right moment. The problem is - how do you get beautiful content in there? 

One tricky thing about UI tests: you have a very limited ability to pass information into your iOS app. This is intentional - UI tests would be pretty weird if you could write code that directly manipulated views in your app! To send information into the running app, we use environment variables - which are basically just strings that the app can then read when it launches.

Remember the bit above with `KHAUITestingConstants`? When the app is running, we check to see if the `environment` contains a given variable, like so:

	/// Checks NSProcessInfo for environment variables used by UI Testing.
	/// If there are environment variables for a content item, the app will navigate to that location.
	@objc func openUITestingContentIfApplicable() {
		let environment = NSProcessInfo.processInfo().environment
	
		let shouldOpenContent = environment[KHAUITestingConstants.shouldOpenContentEnvironmentVariable] == KHAUITestingConstants.enableKey
	
		if shouldOpenContent {
			if
				let contentSlug = environment[KHAUITestingConstants.contentItemSlugVariable],
				let contentTypeString = environment[KHAUITestingConstants.contentItemTypeVariable],
				let contentType = URLTarget.contentTypeFromURLComponent(contentTypeString)
			{
				// Here's where our app navigates to the desired content.
				let urlTarget = URLTarget.ContentItem(contentType: contentType, slug: contentSlug)
				self.navigateToURLTarget(urlTarget)
			}
		}
	}

We’ve also got structs that contain good-looking content for each locale. For example, this struct populates our app’s bookmark tab with the right content for each locale:
	
	/// Contains good-looking topics and videos for the Bookmarks tab in our automated App Store screenshots.
	internal struct AppStoreScreenshotBookmarks {
	
		/// Returns a list of video slugs for App Store screenshots.
		internal static func contentSlugsForLocale(locale: ScreenshotLocale) -> [String] {
			switch locale {
			case .en_US, .tr, .es_ES:
				return [
					"matisse-blue-window",
					"introduction-to-vectors-and-scalars",
					"circulatory-system-and-the-heart",
					"introduction-to-economics",
					"introduction-to-physics",
				]	
			// etc.
		}
	
	
		/// Returns a list of topic slugs for App Store screenshots.
		internal static func topicSlugsForLocale(locale: ScreenshotLocale) -> [String] {
			switch locale {
			case .en_US, .tr, .fr, .pt_BR:
				return [
					"trigonometry",
					"entropy-chemistry-sal",
				]
			// etc.
		}
	}
	

## Step Four: Custom Layouts
Now you’ve got great content in your screenshots for each locale - what do you want to do with them?

For Khan Academy’s app, we want to inset the phone in a device, and have some text above it, like so:

![Screenshot of our app in French](/images/app-store-screenshots/fr_iPhoneSE_01_Explore.png)

Fastlane offers a tool called [`frameit`](https://github.com/fastlane/fastlane/tree/master/frameit) that gets you pretty close - but we wanted more control over the layout and background color, so I created a Sketch File that nearly-automates this step.
  
I won’t go too in-depth into breaking down the Sketch file, but here’s a quick overview of how it’s built:
 - It uses a Sketch plugin called [Sketch Replace Images](https://github.com/shakemno/sketch-replace-images), which updates image layers in the Sketch file to match similarly-named images in our `snapshot` output.
- It uses Symbols and Shared Styles to keep the design consistent across all 180 screenshots.
- We used the beautiful [Devices sketch files from Facebook Design](http://facebook.design/devices), and stripped out the shadows, textures, and colors to create our stylized white devices - then scaled them down and pixel-snapped the edges.

Our Sketch file has one-page-per-device, and looks like this:
![Our Sketch File](/images/app-store-screenshots/sketch-file-preview.png)

## Putting it all together
Now, when we want to update our screenshots, we can type in a Terminal command, and wait about 30 minutes (Swift compilation is responsible for the vast majority of that time; our Android app only takes a few minutes to do this part). Then, we open our Sketch file, run the Sketch Replace Images plugin, and export our screens - that's it!

## Want to learn more?
 - [Fastlane.tools](https://fastlane.tools) provides `snapshot` and other tools for automating app development tasks.
 - [WWDC 2015, Session 406: UI Testing in Xcode](https://developer.apple.com/videos/play/wwdc2015/406/)
 - Felix Krause has a [great talk on other things you can build with automated screenshots](https://www.youtube.com/watch?v=wOtANfkh2bI&feature=youtu.be&t=19m26s) - like automatically-adding ‘em to each pull request!