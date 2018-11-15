title: "Dyslexic Friendly Font - Khan Academy's New Accessibility Feature"
published_on: December 15, 2018
author: Dasani Madipalli
team: Web Frontend
...

Khan Academy's mission is to bring free world class education for anyone, anywhere.
This includes making our written content accessible for everyone. In order to make our content
more accessible to our dyslexic users, we added a new [accessibility user setting](https://www.khanacademy.org/settings/account) to change the websites font more dyslexic friendly! This change will allow users to change the website's font from Lato, our standard body text font, to [OpenDyslexic](https://www.opendyslexic.org).

This setting is currently only available in the English and Spanish versions of the site. Additionally the font will not override reading passages in the test prep sections as the font there is attempting to mimic actual test prep environments. The font will also not override fonts used for mathematical equations since they have special characters that might not be present.

If it sounds like something that may help you or someone you know digest Khan Academy’s written content better, here’s how you can access it:

### Enabling the Setting

1. Click on your Settings tab:

![Settings Page on Khan Academy](/images/dyslexic-friendly-fonts/settings.png)

2. Then go to Accessibility and check the box that says ‘Make Font Dyslexic Friendly’ and press ‘Save Changes’ :

![Accessibility Settings Section in User Settings Page](/images/dyslexic-friendly-fonts/before.png)

3. Your version of Khan Academy should now look something like this:

![View of Settings Section after Dyslexic Friendly Font Setting is Turned On](/images/dyslexic-friendly-fonts/after.png)

### How it Helps

The aim of this setting is to allow users to have the opportunity to change the font of the website to something that is might be more comforting and easier to read. While the font does not “cure” dyslexia it remedies some symptoms that some people with dyslexia experience. As described in the OpenDyslexic website, the font acts as a form of additional support similar to how highlighting a text book might help someone remember important facts of a passage.

Fonts intended to help dyslexic users take measures to make certain letters more distinguishable from one another. For instance in OpenDyslexic, the letters are weighted in certain areas to indicate direction. A capital W is more weighted on the bottom and a capital M is more weighted on the top. This helps a dyslexic user distinguish between an M and a W, which can sometimes be confusing due to their similar shape. Below you can see an image that shows the contrast on how different letters that are often confusing for dyslexic users are displayed in different fonts.

![Image Comparing different letters in different fonts](/images/dyslexic-friendly-fonts/font-comparision.png)

OpenDyslexic font may not work for all people with dyslexia, but attempts to remedy some of its symptoms. You can find more information about the font and how it was created [here](https://www.opendyslexic.org/about).

The research around dyslexic friendly fonts is still in the preliminary stages and there is no hard evidence to show that it significantly improves reading experiences for people with dyslexia.

Everyone is different, and some fonts work better for people with dyslexia than others. Our intention in releasing this feature was to provide the option to change Khan Academy’s font to one that may provide some ease. We feel that if there’s some chance that this feature will help some learners absorb information more effectively, we’re willing to give it a try.

### The Making

Overriding our standard body text font with OpenDyslexic was a fairly straightforward approach. I first accessed our font files from the website. Once I added the font files to our GitHub repo, I created a css template for the font using @fontface. Here’s an example of what that might look like:

```css
/* regular Open Dyslexic font */
@font-face {
   font-family: 'Open Dyslexic';
   src: url('/fonts/OpenDyslexic-Regular.otf')
        format('opentype');
   font-style: normal;
   font-weight: normal;
}

/* italic Open Dyslexic font */
@font-face {
   font-family: 'Open Dyslexic';
   src: url('/fonts/OpenDyslexic-Italic.otf')
        format('opentype');
   font-style: italic;
   font-weight: normal;
}

/* bold Open Dyslexic font */
@font-face {
   font-family: 'Open Dyslexic';
   src: url('/fonts/OpenDyslexic-Bold.otf')
        format('opentype');
   font-weight: bold;
   font-style: normal;
}

/* bold and italic Open Dyslexic */
@font-face {
   font-family: 'Open Dyslexic';
   src: url('/fonts/OpenDyslexic-BoldItalic.otf')
        format('opentype') ;
   font-weight: bold;
   font-style: italic;
}
```

At Khan Academy we [lazy load](https://www.filamentgroup.com/lab/font-events.html) our fonts. In order to override our standard body text font Lato I just needed to see where it was loaded, check if the user settings were being used and load OpenDyslexic instead.

In order to do that, I first set up our css styling for the default and upgraded fonts. The upgraded font will only be used if it has already been downloaded onto the user’s machine while the default font face allows the user to still see and read the page if the download is still happening:

```less
body {
    font-family: 'Helvetica', 'Corbel', sans-serif;

    &.fonts-loaded-default {
        font-family: 'Lato', 'Helvetica', 'Corbel', sans-serif;
    }
    &.fonts-loaded-dyslexic {
        font-family: 'Open Dyslexic', 'Helvetica', 'Corbel', sans-serif;
    }
}
```

Then I overrode the body styling:

```JavaScript
<script>
    const fontLoadedClassName = userProfile && userProfile.useDyslexicFriendlyFont ? ‘fonts-loaded-dyslexic’ : ‘fonts-loaded-default’;
    const upgradedFontName = userProfile && userProfile.useDyslexicFriendlyFont ? ‘Open Dyslexic’ : ‘Lato’;

    if (document.cookie[fontLoadedClassName]) {
        document.body.className += fontLoadedClassName;
    } else {
        const font = newFontFaceObserver(upgradedFontName);
        font.load().then(() => {
            document.body.className += fontLoadedClassName;
            document.cookie = `${fontLoadedClassName} = true`;
        })
    }
</script>
```

Also please note that this not the actual code I wrote, but a similar representation of the logic we used. Hope this helps you to add a similar feature to your own websites and applications


### Help Make Khan Academy More Accessible

A lot of our accessibility features were motivated by user feedback and requests. We really do value user input and would love to hear what you think will help make Khan Academy easier to access and use. Do you have any other suggestions for how we can make Khan Academy more accessible to everyone? Please let us know [here](https://khanacademy.zendesk.com/hc/en-us).
