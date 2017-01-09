#Skin Shortcuts - 1.9.0

script.skinshortcuts was written with the intention of making user customizable shortcuts on the home page easier for skinners.


## What's New for Skinners

#### Version 1.9.0 - 'Leia' Test Branch

This version is the test branch for the version of the script for Kodi v19 - 'Leia'. THe opportunity is being taken to break backwards compatibility with Kodi versions, to remove old and little-used features and to do a large amount of code cleanup.

Therefore, it's important to note that there are breaking changes to the Skin Shortcuts implementation - and there may be more before the v19 version of the script is completed. Various elements of the script may also break whilst the code cleanup is ongoing. Please report any issues in the Skin Shortcuts thread on the Kodi forum along with a debug log with the scripts own debug logging option enabled in addition to Kodi's.

Please also note that the documentation has not been updated to reflect the changes, and will not be done so until the branch is considered complete.

Required skinning changes for v18:-
- Removed GUI controls 101, 102, 103 & 111 (original shortcut selection methods): _Use GUI 401 instead_
- Removed GUI control 309 (deprecated Choose Widget option): _Either move to GUI 312 method, or use a custom property_
- New GUI control 3010 (add new shortcut and select)
- Default shortcuts, overrides and templates should now be provided in _$SPECIAL://skin/extras/script.skinshortcuts_

Other new, changed or removed features for v18:-
- Changed dependencies: Removed simplejson dependancy; added [simpleeval](https://github.com/Ignoble61/script.module.simpleeval) dependancy (not currently available on any repo)
- Backwards compatibility removed, including the option to specify 'version' elements to target specific versions of shortcuts
- New ability to override static shortcut groups - common, commands, settings, pvr-tv, pvr-radio - from overrides.xml
- Removed auto-playlist generation options when selecting a source as the target for a shortcut
 
## With Thanks - Because their names don't deserve to be at the bottom :)

- Huge thanks to Ronie, whose code for listing plugins is used in this script
- Equally huge thanks to Ronie and 'Black, for their favourites code used in this script
- More huge thanks to BigNoid, for the ability to edit shortcuts, and Jeroen, for so many suggestions each of which just made the script better.
- The thanks remain absolutely huge to the translaters on Transifex for localising the script
- There almost isn't enough thanks for schimi2k for the icon and fanart
- Everyone who has contributed even one idea or line of code
- And the biggest thanks of all to Annie and my family, for feature suggestions, testing and shouting at me when I broke things

## Where To Get Help - Users

[End User FAQ](./resources/docs/FAQ.md)

If you have issues with using the script, your first port of call should be the End User FAQ. If your query isn't listed there, then the next place to ask for help is the [Kodi forum for the skin that you are using](http://forum.kodi.tv/forumdisplay.php?fid=67). There are a lot of very knowledgeable skinners and users who will be able to answer most questions.

When a question comes up that no-one in the thread can answer, the skinner may direct you to the [Skin Shortcuts thread](http://forum.kodi.tv/showthread.php?tid=178294) in the skin development for further help.

If you experience an error with the script, you are welcome to ask for help directly in the Skin Shortcuts thread in the skin development forum. However, we _require_ a [debug log](http://kodi.wiki/view/Debug_log).

Please note that this thread is primarily aimed at skin developers - if you haven't already asked in the revelant skins forum, included a debug log or are asking a question related to [banned add-ons](http://kodi.wiki/view/Official:Forum_rules/Banned_add-ons), you are not likely to recieve a warm welcome.

## Where To Get Help - Skinners

Though hopefully Skin Shortcuts will save you a lot of code in the long-run, it is a relatively complex script and so may take some time to get your head around.

To help, it includes a lot of documentation covering the various features of the script

* [What is Skin Shortcuts](./resources/docs/What is Skin Shortcuts.md)
* [Getting Started](./resources/docs/started/Getting Started.md)
* [Providing default shortcuts](./resources/docs/Providing default shortcuts.md)
* [Advanced usage topics](./resources/docs/advanced/Advanced Usage.md)
* [labelID and localisation](./resources/docs/labelID and Localisation.md)

It's highly recommended to take time to read through these documents before you begin.

If you require any assistance post on the Kodi forum and I'll do my best to assist:

[http://forum.kodi.tv/showthread.php?tid=178294](http://forum.kodi.tv/showthread.php?tid=178294)

## Documentation for different versions

The documentation with Skin Shortcuts is generally updated as features are added or changed. Therefore, the docs on Git refer to the latest build, and will include details of features that are not yet on the repo.

If you are targetting the repo version of the script you can use the tags to browse the documentation for that particular release.
