title: "Migrating to a Mobile Monorepo for React Native"
published_on: May 29, 2017
author: Jared Forsyth
team: Mobile
...

Over the past few months, we've been adding some [React
Native](https://github.com/facebook/react-native) to our existing
[iOS](https://itunes.apple.com/us/app/khan-academy-you-can-learn-anything/id469863705?mt=8)
and
[Android](https://play.google.com/store/apps/details?id=org.khanacademy.android&hl=en)
apps. We started out by just creating a `react-native` repository and adding
it as a submodule of our respective `ios` and `android` git repositories, but
we quickly found that there was a fair amount of friction in coordinating
between the three. We've now moved all of our mobile-related repositories
(including a `mobile-scripts` and a `shared-webview` repository) into a single
`mobile` [monorepo](https://danluu.com/monorepo/).

## Why did we do it?

When making changes to the bridge that JavaScript uses to get data from the
native side, we need to make the change to both the Android and the iOS
codebases, or else we'll get runtime errors. With three repositories to work
with, it was too easy to forget to add one or the other (as you're generally
developing with just one simulator open), resulting in a broken experience for
one platform or the other.

We'd also get into a state where the `master` branch of `react-native`
contained some changes that had only been coordinated with e.g. the `ios`
repo, and the `android` repo's `react-native` submodule would be several
commits behind. Then someone working on the Android side would update the
submodule, and they'd have to track down all the breakages.

In short, we started running into a lot of synchronization issues that
wouldn't happen if all of the code was in the same repository. With a
monorepo, pull requests could be combined, reviews would be more coherent, and
it would be easier to verify correctness between codebases.

### Anticipated pros

- changing bridge between JavaScript and native would be easier because
  you'd only need a single pull request instead of three
- as a result, they would be less likely to get out of sync
- not having to mess with submodules 🎉

### Anticipated cons

- we might lose Git history (this didn't turn out to be the case)
- we'd have to change all of our Jenkins build scripts
- moving all our developers to a new repository requires coordination
- we'd lose any in-flight branches and open PRs to the old repositories (we
  actually found a solution for this too)

## What were the steps?

### Setup

Make a fresh monorepo:

```sh
mkdir mobile; cd mobile; git init .
```

Have all the repos that you want to combine cloned and fully up to date

```sh
$ ls .
mobile
android
ios
react-native
```

### Preparing the repos for merging

Clone each repo into `m_reponame` (using `android` as the example) and then
move all files into a subfolder (except for `.git`, of course).

```sh
git clone android m_android
cd m_android
mkdir android
mv * .* android
mv android/.git .
```

Then commit the result: `git add . && git commit -m'move to subfolder'`

With the code for each respective codebase moved into a subdirectory, we're
then able to move them all into a single repository without having them clash
with each other. To illustrate, here's what the rough directory structure
looks like:

```
android/
  build.gradle, etc.
ios/
  AppDelegate.m, etc.
react-native/
  index.ios.js, etc.
m_android/
  android/
    build.gradle, etc.
m_ios/
  ios/
    AppDelegate.m, etc.
m_react-native/
  react-native/
    index.ios.js, etc.
```

The monorepo will then have the following structure:

```
mobile/
  android/
    build.gradle, etc.
  ios/
    AppDelegate.m, etc.
  react-native/
    index.ios.js, etc.
```

### Merge each `m_reponame` into the monorepo

Turns out git has super powers, and can totally merge in multiple unrelated
repositories and preserve all the relevant git history. Who knew?

```sh
cd mobile
git fetch ../m_android
git merge FETCH_HEAD --no-ff --allow-unrelated-histories \
    -m 'merging in android repo'
```

Again, do this for each repository that you need to merge in.

One thing I'm glossing over (that you'll have to figure out manually) is
various dotfiles that you want to be shared. `.gitignore` is fine being in the
respective subdirectories, but in our case we use Phabricator, and so we
needed to make a top-level `.arcconfig` file that merged the `.arcconfig`s
from the previous three repositories.

I also had to manually bring over submodules, by re-cloning them in the new
monorepo and checking them out at the commit where they were pinned in the
pre-monorepo repositories.

And of course the `react-native` folder was in a different place now that it
wasn't a submodule, but a peer, to the iOS and Android codebases, so we had to
update various relative paths and build scripts.

### Bringing in new changes from the old repos

After creating the monorepo, our team had a flex week where they could still
operate on the old repositories, so that they could land any outstanding code
changes that they had inflight and move over at their own pace.

If you do the same, here's how to bring in new changes to the old
repositories:

```sh
(cd android && git pull)
cd m_android
git pull ../android --no-ff \
    -m 'merging in latest android changes'
```

At this point **check for new files**. Files that were added in the `android`
repo after the monorepo move will not get automatically moved into the
`m_android/android` subdirectory. It will be pretty obvious, because the only
directory in the `m_android` repo should be `android`. If there's anything
else there, `git mv the_new_thing android && git commit -am "moving new files
into subdirectory"` before continuing.

```sh
cd ../mobile
git fetch ../m_android
git merge FETCH_HEAD --no-ff \
    -m 'merging in latest android changes'
```

This will even work if there have been changes committed to the monorepo,
although you may have to resolve merge conflicts.

### Following Git history across the monorepo divide

One of the things that surprised me the most was that Git was totally able to
track the changes, even though they came from three different repositories.
When doing `git log` for a specific file, you just need to add the `--follow`
option (which tells Git to follow the file across renames), and everything
works!

## And that's it!

We've been working with the monorepo for over a month now, and it's been well
worth it. If you're integrating React Native into two existing apps that are
currently in separate repositories, you might benefit from the shift as well!
